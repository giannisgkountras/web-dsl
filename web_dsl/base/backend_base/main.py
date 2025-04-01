import asyncio
import threading
import logging
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from websocket_server import WebSocketServer
from commlib_client import BrokerCommlibClient
from utils import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load configuration from config.yaml
config = load_config()

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
        host=ws_config.get("host", "0.0.0.0"), port=ws_config.get("port", 8765)
    )

    # Extract multiple broker connection settings
    broker_configs = config.get("brokers", [])

    broker_threads = []

    for broker_info in broker_configs:
        topics = []
        for topic in broker_info.get("topics", []):
            topics.append(topic.get("topic"))
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
    message: dict
    topic: str


# Publish API endpoint
@app.post("/publish")
async def publish_message(request: PublishRequest):
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


if __name__ == "__main__":
    asyncio.run(main())
