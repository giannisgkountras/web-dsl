from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters
import asyncio

# Topics to subscribe to
TOPICS = ["topic/one", "topic/two", "topic/three"]


mqtt_conn_params = ConnectionParameters(
    host="localhost",
    port=1883,
)

node = Node(node_name="mqtt_node", connection_params=mqtt_conn_params)


def on_message(topic):
    """Generate a callback function for a given topic."""

    def callback(msg):
        print(f"Received from {topic}: {msg.data}")
        asyncio.run(send_to_websockets(topic, msg.data))

    return callback


# Create a subscriber for each topic
subscribers = [
    node.create_subscriber(topic=topic, on_message=on_message(topic))
    for topic in TOPICS
]


async def send_to_websockets(topic, message, connected_websockets):
    """Send message to all connected WebSocket clients with topic information."""
    if connected_websockets:
        payload = f"{topic}: {message}"
        await asyncio.gather(*[ws.send(payload) for ws in connected_websockets])
