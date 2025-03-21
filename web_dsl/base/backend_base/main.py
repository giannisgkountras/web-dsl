import asyncio
import threading
import logging
from websocket_server import WebSocketServer
from commlib_client import BrokerCommlibClient
from utils import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global variable to hold the main event loop
global_event_loop = None


def run_broker_client(broker_client, broker_name):
    """Runs the broker client and handles exceptions to prevent crashes."""
    try:
        broker_client.run()
    except Exception as e:
        logging.error(f"Broker '{broker_name}' encountered an error: {e}")


async def main():
    # Load configuration from config.yaml
    config = load_config()

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
        try:
            # Attempt to create a broker client
            broker_client = BrokerCommlibClient(
                name=broker_info.get("name"),
                broker_connection_parameters=broker_info.get(
                    "broker_connection_parameters", {}
                ),
                type=broker_info.get("type"),
                topics=broker_info.get("topics", []),
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
            broker_threads.append(broker_thread)
            broker_thread.start()

            logging.info(f"Successfully connected to broker: {broker_info.get('name')}")

        except Exception as e:
            logging.error(f"Failed to connect to broker {broker_info.get('name')}: {e}")

    # Start the WebSocket server in the asyncio event loop
    await ws_server.start_server()

    # Wait for all broker threads to complete
    for thread in broker_threads:
        thread.join()


if __name__ == "__main__":
    asyncio.run(main())
