from commlib.node import Node
from commlib.transports.redis import ConnectionParameters as RedisConn
from commlib.transports.mqtt import ConnectionParameters as MQTTConn
import asyncio
import os


class CommlibClient:
    def __init__(self):

        redis_pass = os.getenv("REDIS_PASSWORD")

        broker_config = {
            "host": "localhost",
            "port": 1883,
            "username": "",
            "password": "",
        }

        # FOR USE WITH JUNIOR CAR
        # self.mqtt_conn_params = MQTTConn()

        self.mqtt_gui_conn_params = MQTTConn()

    def subscribe(self, topic, callback):
        """Subscribe to a topic using the active node."""
        if topic in self.subscribers:
            self.logger.warning(f"Already subscribed to {topic}")
            return

        subscriber = self.active_receive_node.create_subscriber(
            topic=topic, on_message=callback
        )
        self.subscribers[topic] = subscriber
        subscriber.run()
        self.logger.info(f"Subscribed to {topic} using {self.active_receive_source}.")

    def publish(self, topic, message):
        """Publish a message to the given topic."""
        # Ensure message is not None or empty
        if not message:
            self.logger.warning(f"Attempted to publish an empty message to {topic}")
            return

        if topic not in self.publishers:
            publisher = self.mqtt_gui_node.create_publisher(topic=topic)
            self.publishers[topic] = publisher
        else:
            publisher = self.publishers[topic]

        try:
            publisher.publish(message)
            self.logger.info(f"Published message to {topic} using MQTT.")
        except Exception as e:
            self.logger.error(f"Failed to publish message to {topic}: {e}")

    def start_listener(self):
        """Starts background listeners for all subscribed topics."""
        for topic, subscriber in self.subscribers.items():
            subscriber.run()
            self.logger.info(f"Listening for messages on {topic}")
