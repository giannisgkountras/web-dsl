import asyncio
import threading
import websockets
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters
from commlib.msg import PubSubMessage

# Global variable to hold the main event loop
global_event_loop = None


# Define a custom message type for MQTT messages
class MQTTMessage(PubSubMessage):
    data: str


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.connected_websockets = set()

    async def send_message(self, message: str):
        """Send a message to all connected WebSocket clients."""
        if self.connected_websockets:
            await asyncio.gather(
                *[ws.send(message) for ws in self.connected_websockets]
            )

    async def websocket_handler(self, websocket):
        """Handle new WebSocket connections."""
        self.connected_websockets.add(websocket)
        try:
            async for _ in websocket:
                pass  # Keep the connection alive
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.connected_websockets.remove(websocket)

    async def start_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(
            self.websocket_handler, self.host, self.port, origins=None
        ):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever


class MQTTCommlibClient:
    def __init__(
        self,
        host: str,
        port: int,
        topics: list,
        ws_server: WebSocketServer,
    ):
        self.port = port
        self.topics = topics
        self.ws_server = ws_server
        # Setup connection parameters for the MQTT broker
        self.conn_params = ConnectionParameters(
            host=host,
            port=port,
        )
        self.node = Node(node_name="mqtt_node", connection_params=self.conn_params)
        self.subscribers = []

    def on_message_callback(self, topic: str):
        """Generate a callback for a specific topic."""

        def callback(msg):
            print(f"Received from {topic}: {msg}")
            message_with_prefix = f"{topic}: {msg}"
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(
                self.ws_server.send_message(message_with_prefix), global_event_loop
            )

        return callback

    def subscribe(self):
        """Subscribe to all specified topics."""
        for topic in self.topics:
            subscriber = self.node.create_subscriber(
                topic=topic,
                on_message=self.on_message_callback(topic),
            )
            self.subscribers.append(subscriber)

    def run(self):
        """Run the commlib node to start listening for MQTT messages."""
        print("Starting MQTT commlib node...")
        self.node.run()


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
    )
    mqtt_client.subscribe()

    # Run the MQTT client in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_client.run, daemon=True)
    mqtt_thread.start()

    # Start the WebSocket server in the asyncio event loop
    await ws_server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
