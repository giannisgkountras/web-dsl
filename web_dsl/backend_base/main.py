import asyncio
import threading
from websocket_server import WebSocketServer
from commlib_client import MQTTCommlibClient
from utils import load_config

# Global variable to hold the main event loop
global_event_loop = None


async def main():
    # Load configuration from config.yaml
    config = load_config()
    # Extract MQTT and WebSocket settings
    mqtt_config = config.get("mqtt", {})
    ws_config = config.get("websocket", {})

    global global_event_loop
    global_event_loop = asyncio.get_running_loop()  # Capture the main event loop

    # Create a WebSocket server instance
    ws_server = WebSocketServer(
        host=ws_config.get("host", "0.0.0.0"), port=ws_config.get("port", 8765)
    )

    # Create an MQTT client that subscribes to multiple topics
    mqtt_client = MQTTCommlibClient(
        name=mqtt_config.get("name", "mqtt_client"),
        host=mqtt_config.get("host", "localhost"),
        port=mqtt_config.get("port", 1883),
        topics=mqtt_config.get("topics", []),
        ws_server=ws_server,
        global_event_loop=global_event_loop,
    )
    mqtt_client.subscribe()

    # Run the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_client.run, daemon=True)
    mqtt_thread.start()

    # Start the WebSocket server in the asyncio event loop
    await ws_server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
