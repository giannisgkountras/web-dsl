from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters


class CommlibClient:
    def __init__(self):

        broker_config = {
            "host": "localhost",
            "port": 1883,
        }

        self.connection_params = ConnectionParameters()

        self.mqtt_node = Node(
            node_name="mqtt_node", connection_params=self.connection_params
        )

        self.subscribers = {}
        self.publishers = {}

    def subscribe(self, topic, callback):
        """Subscribe to a topic using the active node."""
        if topic in self.subscribers:
            print(f"Already subscribed to {topic}")
            return

        subscriber = self.mqtt_node.create_subscriber(topic=topic, on_message=callback)
        self.subscribers[topic] = subscriber
        subscriber.run()
        print(f"Subscribed to {topic}.")

    def publish(self, topic, message):
        """Publish a message to the given topic."""
        # Ensure message is not None or empty
        if not message:
            print(f"Attempted to publish an empty message to {topic}")
            return

        if topic not in self.publishers:
            publisher = self.mqtt_node.create_publisher(topic=topic)
            self.publishers[topic] = publisher
        else:
            publisher = self.publishers[topic]

        try:
            publisher.publish(message)
            print(f"Published message to {topic}.")
        except Exception as e:
            print(f"Failed to publish message to {topic}: {e}")


if __name__ == "__main__":
    client = CommlibClient()
    client.publish("test", {"message": "Hello, world!"})
    client.subscribe("test", lambda message: print(f"Received message: {message}"))
    while True:
        pass
