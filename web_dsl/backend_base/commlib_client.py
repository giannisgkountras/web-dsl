import asyncio
from commlib.node import Node


class BrokerCommlibClient:
    def __init__(
        self,
        name: str,
        type: str,
        host: str,
        port: int,
        topics: list,
        ws_server,
        global_event_loop,
    ):
        self.port = port
        self.topics = topics
        self.ws_server = ws_server

        if type == "MQTT":
            from commlib.transports.mqtt import ConnectionParameters as conn_params

        elif type == "AMQP":
            from commlib.transports.amqp import ConnectionParameters as conn_params

        elif type == "REDIS":
            from commlib.transports.redis import ConnectionParameters as conn_params
        else:
            print(f"Unknown broker type: {type}")
            return

        # Setup connection parameters for the broker
        self.connection_parameters = conn_params(
            host=host,
            port=port,
        )
        self.node = Node(node_name=name, connection_params=self.connection_parameters)
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
