import asyncio
from commlib.node import Node
import json


class BrokerCommlibClient:
    def __init__(
        self,
        name: str,
        broker_connection_parameters,
        type: str,
        topics: list,
        ws_server,
        global_event_loop,
    ):
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
        self.connection_parameters = conn_params(**broker_connection_parameters)
        self.node = Node(node_name=name, connection_params=self.connection_parameters)
        self.name = name
        self.subscribers = []
        self.global_event_loop = global_event_loop
        self.pub = self.node.create_mpublisher()

    def on_message_callback(self, topic: str):
        """Generate a callback for a specific topic."""

        def callback(msg):
            try:
                json_msg_with_prefix = f'{{"{topic}": {json.dumps(msg)}}}'
            except Exception as e:
                print(f"Failed to convert message to JSON: {e}")
                return
            # print(f"Sending to WebSocket: {json_msg_with_prefix}")
            # Schedule the coroutine in the main event loop
            asyncio.run_coroutine_threadsafe(
                self.ws_server.send_message(json_msg_with_prefix),
                self.global_event_loop,
            )

        return callback

    def subscribe(self):
        """Subscribe to all specified topics."""
        for topic in self.topics:
            print(f"Subscribing to topic: {topic}")
            subscriber = self.node.create_subscriber(
                topic=topic,
                on_message=self.on_message_callback(topic),
            )
            self.subscribers.append(subscriber)

    def publish(self, message: dict, topic: str):
        """Publish a message to a specific topic."""
        try:
            self.pub.publish(message, topic)
            print(f"Published message to {topic}: {message}")
        except Exception as e:
            print(f"Failed to publish message: {e}")

    def run(self):
        """Run the commlib node to start listening for MQTT messages."""
        print("Starting MQTT commlib node...")
        self.node.run()
