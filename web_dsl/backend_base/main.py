import asyncio
import threading
from websocket_server import WebSocketServer
from commlib_client import MQTTCommlibClient

# Global variable to hold the main event loop
global_event_loop = None


async def main():
    global global_event_loop
    global_event_loop = asyncio.get_running_loop()  # Capture the main event loop

    # Create a WebSocket server instance
    ws_server = WebSocketServer(host="0.0.0.0", port=8765)

    # Create an MQTT client that subscribes to multiple topics
    topics = ["topic/one", "topic/two", "topic/three"]
    mqtt_client = MQTTCommlibClient(
        host="localhost",
        port=1883,
        topics=topics,
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
