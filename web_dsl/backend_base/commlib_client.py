import asyncio
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters


class MQTTCommlibClient:
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        topics: list,
        ws_server,
        global_event_loop,
    ):
        self.port = port
        self.topics = topics
        self.ws_server = ws_server
        # Setup connection parameters for the MQTT broker
        self.conn_params = ConnectionParameters(
            host=host,
            port=port,
        )
        self.node = Node(node_name=name, connection_params=self.conn_params)
        self.subscribers = []
        self.global_event_loop = global_event_loop

    def on_message_callback(self, topic: str):
        """Generate a callback for a specific topic."""

        def callback(msg):
            print(f"Received from {topic}: {msg}")
            message_with_prefix = f"{topic}: {msg}"
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(
                self.ws_server.send_message(message_with_prefix), self.global_event_loop
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
