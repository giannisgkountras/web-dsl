import asyncio
import threading
import logging
import uvicorn
import httpx
import os
import hashlib
import json
import time
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, Any, Dict, Tuple
from fastapi import FastAPI, HTTPException, Security, status
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from websocket_server import WebSocketServer
from commlib_client import BrokerCommlibClient
from db_connector import DBConnector
from utils import (
    load_config,
    load_endpoint_config,
    load_db_config,
    convert_object_ids,
    transform_list_of_dicts_to_dict_of_lists,
)

# Load the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY", "API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "SECRET_KEY")
api_keys = [API_KEY]
api_key_header = APIKeyHeader(name="X-API-Key")

# In-memory cache for proxy requests: key -> (timestamp, response)
request_cache: Dict[str, Tuple[float, Any]] = {}

# Locks for each cache key to prevent race conditions
cache_locks: Dict[str, asyncio.Lock] = {}

FRESHNESS_WINDOW = 1.0  # seconds


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
                strict=broker_info.get("strict", False),
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


def generate_restcall_cache_key(request: RESTCallRequest) -> str:
    """Generate a unique cache key for REST call requests."""
    raw_key = f"restcall|{request.name}|{request.path}|{request.method}|{json.dumps(request.body, sort_keys=True)}"
    return hashlib.sha256(raw_key.encode()).hexdigest()


@app.post("/restcall")
async def rest_call(request: RESTCallRequest, api_key: str = Security(get_api_key)):
    """Make a REST call to a specified endpoint, with caching based on freshness."""

    # Validate endpoint configuration
    current_endpoint = endpoint_config.get(request.name)
    if not current_endpoint:
        raise HTTPException(
            status_code=404, detail=f"Endpoint '{request.name}' not found"
        )

    # Construct URL
    host = current_endpoint.get("host")
    port = current_endpoint.get("port")
    if port and port not in [0, 80, 443]:
        url = f"{host}:{port}{request.path}"
    else:
        url = f"{host}{request.path}"

    # Generate cache key
    cache_key = generate_restcall_cache_key(request)
    now = time.time()

    # Get or create a lock for this cache key
    lock = cache_locks.get(cache_key)
    if lock is None:
        lock = asyncio.Lock()
        cache_locks[cache_key] = lock

    # Use the lock to synchronize cache access
    async with lock:
        # Check cache again after acquiring lock (another request might have updated it)
        cached = request_cache.get(cache_key)
        if cached and (now - cached[0] < FRESHNESS_WINDOW):
            logging.info("Returning cached response")
            return cached[1]  # Return cached response

        # If cache is stale or missing, make the request
        try:
            async with httpx.AsyncClient() as client:
                logging.info("Making new request to REST endpoint")
                response = await client.request(
                    method=request.method.upper(),
                    url=url,
                    headers=current_endpoint.get("headers", {}),
                    json=request.body,
                )
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    data = response.json()
                else:
                    data = response.text

                # Cache the new response with the current time
                request_cache[cache_key] = (time.time(), data)
                return data

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
    query: Optional[Any] = (
        None  # For MySQL, the SQL statement. For Mongo, you might ignore this.
    )
    filter: Optional[dict] = None  # For MongoDB, this is the filter for the query.


def generate_query_cache_key(request: QueryRequest) -> str:
    """Generate a unique cache key for query requests."""
    raw_key = (
        f"query|{request.connection_name}|{request.database or ''}|"
        f"{request.collection or ''}|{json.dumps(request.query, sort_keys=True) if request.query else ''}|"
        f"{json.dumps(request.filter, sort_keys=True) if request.filter else ''}"
    )
    return hashlib.sha256(raw_key.encode()).hexdigest()


@app.post("/queryDB")
async def query(request: QueryRequest, api_key: str = Security(get_api_key)):
    """
    Endpoint to run MySQL or MongoDB queries based on the provided request.
    - For MySQL: returns results in the form {column1: [...], column2: [...], ...}
    - For MongoDB: returns documents as-is
    - Caches results for 1 second to reduce database load
    """
    # Generate cache key
    cache_key = generate_query_cache_key(request)
    now = time.time()

    # Get or create a lock for this cache key
    lock = cache_locks.get(cache_key)
    if lock is None:
        lock = asyncio.Lock()
        cache_locks[cache_key] = lock

    # Use the lock to synchronize cache access
    async with lock:
        # Check cache after acquiring lock
        cached = request_cache.get(cache_key)
        if cached and (now - cached[0] < FRESHNESS_WINDOW):
            logging.info("Returning cached response")
            return cached[1]  # Return cached response

        # Cache miss: execute the query
        if request.query != {}:  # MySQL
            result = db_connector.mysql_query(
                connection_name=request.connection_name,
                database=request.database,
                query=request.query,
            )
            if result is None:
                raise HTTPException(
                    status_code=500, detail="Error executing MySQL query"
                )

            # Transform list of dicts into dict of lists
            transformed_result = transform_list_of_dicts_to_dict_of_lists(result)
            logging.info("EXECUTED MYSQL QUERY")

            # Cache the result
            request_cache[cache_key] = (time.time(), transformed_result)
            return transformed_result

        elif request.collection:  # MongoDB
            result = await asyncio.to_thread(
                db_connector.mongo_find,
                connection_name=request.connection_name,
                collection=request.collection,
                filter=request.filter or {},
            )
            if result is None:
                raise HTTPException(
                    status_code=500, detail="Error executing Mongo query"
                )

            # Clean _id fields
            cleaned_result = convert_object_ids(result)

            # Transform list of dicts into dict of lists
            transformed_result = transform_list_of_dicts_to_dict_of_lists(
                cleaned_result
            )
            logging.info("EXECUTED MONGO QUERY")

            # Cache the result
            request_cache[cache_key] = (time.time(), transformed_result)
            return transformed_result

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid request: 'database' or 'collection' must be specified",
            )


class ModifyDBRequest(BaseModel):
    connection_name: str
    database: Optional[str] = None
    collection: Optional[str] = None
    query: Optional[Any] = (
        None  # For MySQL, the SQL statement. For Mongo, you might ignore this.
    )
    filter: Optional[dict] = None  # For MongoDB, this is the filter for the query.
    modification: Optional[str] = None  # The update operation to perform
    new_data: Optional[dict] = None  # New data to be inserted or updated
    dbType: Optional[str] = None  # Type of database (MySQL or MongoDB)


@app.post("/modifyDB")
async def modify_db(request: ModifyDBRequest, api_key: str = Security(get_api_key)):
    """
    Endpoint to modify MySQL or MongoDB databases based on the provided request.
    - For MySQL: executes the SQL statement (e.g., INSERT, UPDATE, DELETE).
    - For MongoDB: performs the specified modification operation (e.g., update, delete, insert).
    """
    # Handle MySQL modifications
    if request.dbType == "mysql":
        success = db_connector.execute_query(
            connection_name=request.connection_name,
            database=request.database,
            query=request.query,
        )
        if not success:
            raise HTTPException(
                status_code=500, detail="Error executing MySQL modification"
            )
        return {"status": "success", "engine": "MySQL"}

    # Handle MongoDB modifications
    elif request.dbType == "mongo":
        operation = request.modification.lower()
        # Convert _id to ObjectId for MongoDB update and delete
        if (
            operation in ["update", "delete"]
            and request.filter
            and "_id" in request.filter
        ):
            try:
                request.filter["_id"] = ObjectId(request.filter["_id"])
            except:
                raise HTTPException(status_code=400, detail="Invalid _id format")

        if operation == "update":
            result = await asyncio.to_thread(
                db_connector.mongo_update,
                connection_name=request.connection_name,
                collection=request.collection,
                filter=request.filter or {},
                update=request.new_data,
            )
        elif operation == "delete":
            result = await asyncio.to_thread(
                db_connector.mongo_delete,
                connection_name=request.connection_name,
                collection=request.collection,
                filter=request.filter or {},
            )
        elif operation == "insert":
            result = await asyncio.to_thread(
                db_connector.mongo_insert,
                connection_name=request.connection_name,
                collection=request.collection,
                document=request.new_data,
            )
        else:
            raise HTTPException(
                status_code=400, detail="Unsupported MongoDB modification operation"
            )

        if result is None:
            raise HTTPException(
                status_code=500, detail=f"Error performing MongoDB {operation}"
            )
        return {"status": "success", "engine": "MongoDB", "operation": operation}

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid request: 'query' and 'database' or 'collection' must be specified",
        )


if __name__ == "__main__":
    asyncio.run(main())
