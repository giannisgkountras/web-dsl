import asyncio
import threading
from websocket_server import WebSocketServer
from commlib_client import BrokerCommlibClient
from utils import load_config

# Global variable to hold the main event loop
global_event_loop = None


async def main():
    # Load configuration from config.yaml
    config = load_config()

    # Extract Broker and WebSocket settings
    broker_connection_parameters = config.get("broker_connection_parameters", {})
    broker_info = config.get("broker_info", {})
    ws_config = config.get("websocket", {})

    global global_event_loop
    global_event_loop = asyncio.get_running_loop()  # Capture the main event loop

    # Create a WebSocket server instance
    ws_server = WebSocketServer(
        host=ws_config.get("host", "0.0.0.0"), port=ws_config.get("port", 8765)
    )

    # Create a broker client that subscribes to multiple topics

    broker_client = BrokerCommlibClient(
        name=broker_info.get("name"),
        broker_connection_parameters=broker_connection_parameters,
        type=broker_info.get("type"),
        topics=broker_info.get("topics", []),
        ws_server=ws_server,
        global_event_loop=global_event_loop,
    )
    broker_client.subscribe()

    # Run the MQTT client in a separate thread
    broker_thread = threading.Thread(target=broker_client.run, daemon=True)
    broker_thread.start()

    # Start the WebSocket server in the asyncio event loop
    await ws_server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
