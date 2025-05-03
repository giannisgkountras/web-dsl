import asyncio
import threading
import logging
import uvicorn
import httpx
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, Any
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from websocket_server import WebSocketServer
from commlib_client import BrokerCommlibClient
from db_connector import DBConnector
from utils import load_config, load_endpoint_config, load_db_config

# Load the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY", "API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "SECRET_KEY")
api_keys = [API_KEY]
api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key"
    )


# Configure logging
logging.basicConfig(level=logging.INFO)

# Load configuration from config.yaml
config = load_config() or {}
endpoint_config = load_endpoint_config()
db_config = load_db_config()

# Global variable to hold the main event loop
global_event_loop = None

broker_clients = []  # Store broker clients for access in FastAPI

app = FastAPI()

# Allow all origins (unsafe for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

db_connector = DBConnector(db_config)


async def start_fastapi():
    """Starts FastAPI server using Uvicorn."""
    uvicorn_config = uvicorn.Config(
        app,
        host=config.get("api", {}).get("host", "0.0.0.0"),
        port=config.get("api", {}).get("port", 8000),
        log_level="info",
    )
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


def run_broker_client(broker_client, broker_name):
    """Runs the broker client and handles exceptions to prevent crashes."""
    try:
        broker_client.run()
    except Exception as e:
        logging.error(f"Broker '{broker_name}' encountered an error: {e}")


async def main():

    # Extract WebSocket settings
    ws_config = config.get("websocket", {})

    global global_event_loop
    global_event_loop = asyncio.get_running_loop()  # Capture the main event loop

    # Create a WebSocket server instance
    ws_server = WebSocketServer(
        host=ws_config.get("host", "0.0.0.0"),
        port=ws_config.get("port", 8765),
        secret_key=SECRET_KEY,
    )

    # Extract multiple broker connection settings
    broker_configs = config.get("brokers") or []

    broker_threads = []

    for broker_info in broker_configs:
        raw_topics = (
            broker_info.get("topics") or []
        )  # this ensures it's a list, even if None
        topics = [topic.get("topic") for topic in raw_topics if topic.get("topic")]
        allowed_attributes = {
            topic_info.get("topic"): topic_info.get("attributes")
            for topic_info in raw_topics
            if topic_info.get("attributes") is not None
        }
        print(f"Allowed attributes: {allowed_attributes}")
        if not topics:
            continue

        try:
            # Attempt to create a broker client
            broker_client = BrokerCommlibClient(
                name=broker_info.get("name"),
                broker_connection_parameters=broker_info.get(
                    "broker_connection_parameters", {}
                ),
                type=broker_info.get("type"),
                topics=topics,
                ws_server=ws_server,
                global_event_loop=global_event_loop,
                allowed_topic_attributes=allowed_attributes,
            )
            broker_client.subscribe()

            # Run each broker client in a separate thread (not daemon)
            broker_thread = threading.Thread(
                target=run_broker_client,
                args=(broker_client, broker_info.get("name")),
                daemon=False,
            )
            broker_clients.append(broker_client)
            broker_threads.append(broker_thread)
            broker_thread.start()

            logging.info(f"Successfully connected to broker: {broker_info.get('name')}")

        except Exception as e:
            logging.error(f"Failed to connect to broker {broker_info.get('name')}: {e}")

    # Run FastAPI in the background
    asyncio.create_task(start_fastapi())

    # Start the WebSocket server in the asyncio event loop
    await ws_server.start_server()

    # Wait for all broker threads to complete
    for thread in broker_threads:
        thread.join()


class PublishRequest(BaseModel):
    broker: str
    message: Any
    topic: str


# Publish API endpoint
@app.post("/publish")
async def publish_message(
    request: PublishRequest, api_key: str = Security(get_api_key)
):
    """Publish a message to a specific topic of a broker."""
    broker = request.broker
    message = request.message
    topic = request.topic

    for broker_client in broker_clients:
        if broker_client.name == broker:
            try:
                # Publish the message to the specified topic
                broker_client.publish(message, topic)
                return {"status": "success", "message": f"Message sent to {topic}"}
            except Exception as e:
                logging.error(f"Failed to publish message: {e}")
                return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Broker {broker} not found"}


class RESTCallRequest(BaseModel):
    name: str  # Name of the REST call
    path: str
    method: str
    # params: dict
    body: dict


@app.post("/restcall")
async def rest_call(request: RESTCallRequest, api_key: str = Security(get_api_key)):
    """Make a REST call to a specified endpoint."""
    # Load endpoint configuration
    current_endpoint = endpoint_config.get(request.name)
    print(f"Endpoint config: {current_endpoint}")
    if not current_endpoint:
        raise HTTPException(
            status_code=404, detail=f"Endpoint '{request.name}' not found"
        )

    # Use only dict-style access for current_endpoint
    host = current_endpoint.get("host")
    port = current_endpoint.get("port")

    # Build the URL – omit port if it is 0, 80, or 443
    if port and port not in [0, 80, 443]:
        url = f"{host}:{port}{request.path}"
    else:
        url = f"{host}{request.path}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method.upper(),
                url=url,
                headers=current_endpoint.get("headers", {}),
                json=request.body,
            )

            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                return response.text

    except httpx.RequestError as e:
        logging.error(f"HTTP request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred.")


# Request Body Model
class QueryRequest(BaseModel):
    connection_name: str
    database: Optional[str] = (
        None  # For MySQL: target database; ignored for Mongo queries.
    )
    collection: Optional[str] = (
        None  # For MySQL this is a table; for Mongo, treat as collection.
    )
    query: str  # For MySQL, the SQL statement. For Mongo, you might ignore this.
    filter: Optional[dict] = None  # For MongoDB, this is the filter for the query.


@app.post("/queryDB")
async def query(request: QueryRequest, api_key: str = Security(get_api_key)):
    """
    Endpoint to run MySQL or MongoDB queries based on the provided request.
    - For MySQL: returns results in the form {column1: [...], column2: [...], ...}
    - For MongoDB: returns documents as-is
    """
    if request.database:  # MySQL
        result = db_connector.mysql_query(
            connection_name=request.connection_name,
            database=request.database,
            query=request.query,
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Error executing MySQL query")

        # Transform list of dicts into dict of lists
        if isinstance(result, list) and result and isinstance(result[0], dict):
            transformed = {}
            for key in result[0].keys():
                transformed[key] = [row[key] for row in result]
            return transformed
        else:
            return result  # fallback in case it's not a list of dicts

    elif request.collection:  # MongoDB
        result = db_connector.mongo_find(
            connection_name=request.connection_name,
            collection=request.collection,
            filter=request.filter or {},
        )
        if result is None:
            raise HTTPException(status_code=500, detail="Error executing Mongo query")
        return result

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid request: 'database' or 'collection' must be specified",
        )


if __name__ == "__main__":
    asyncio.run(main())
