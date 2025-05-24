import re
import yaml
import os

from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException

from .openapi_to_webdsl import parse_component_annotations
from web_dsl.definitions import TEMPLATES_PATH


# ======== Template Setup ========
env = Environment(
    loader=FileSystemLoader(os.path.join(TEMPLATES_PATH, "transformations")),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)
template = env.get_template("asyncapi_to_webdsl.jinja")

# ====== Component mapping (reused from OpenAPI)===========
attribute_map = {
    "Text": "content",
    "Gauge": "value",
    "ProgressBar": "value",
    "Image": "source",
    "LineChart": "",
    "BarChart": "",
    "PieChart": "",
    "JsonViewer": "",
    "Table": "",
}

protocol_to_dsl_type_map = {
    "mqtt": "MQTT",
    "mqtts": "MQTT",
    "amqp": "AMQP",
    "amqps": "AMQP",
    "redis": "REDIS",
    "rediss": "REDIS",
}

default_ports = {
    "MQTT": 1883,
    "AMQP": 5672,
    "REDIS": 6379,
}

type_map = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "list",
    "object": "dict",
}
format_type_map = {
    "date-time": "str",
    "uuid": "str",
}


# ====== Helper Classes ===========
class Broker:
    def __init__(
        self,
        name: str,
        protocol_type: str,
        host: str,
        port: Optional[int],
        auth: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.protocol_type = protocol_type
        self.host = host
        self.port = port
        self.auth = auth or {}


class BrokerTopic:
    def __init__(
        self,
        name: str,
        connection_name: str,
        topic_address: str,
        channel_messages: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.connection_name = connection_name
        self.topic_address = topic_address
        self.channel_messages = channel_messages or []


class Entity:
    def __init__(
        self,
        name: str,
        source_topic_name: str,
        attributes: dict,
    ):
        self.name = name
        self.source_topic_name = source_topic_name
        self.attributes = attributes

    @property
    def attribute_list(self):
        return [
            map_asyncapi_type_to_dsl(name, schema)
            for name, schema in self.attributes.items()
        ]


def map_asyncapi_type_to_dsl(name: str, schema: dict) -> str:
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    return f"{name}: {type_map.get(schema.get('type', 'string'), 'str')}"


# ========== Helper Functions ==============
def clean_name(name: str) -> str:
    name = re.sub(r"[^\w.-]+", "_", name)
    name = name.strip("_")
    if not name:
        return "unnamed_item"
    if name[0].isdigit():
        name = "_" + name
    return name.replace("-", "_").replace(".", "_")


def resolve_operations_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if ref.startswith("#/channels/"):
        name = ref.split("/")[-1]
        return model.get("channels", {}).get(name, {}).get("address", "NO_ADDRESS")
    return {}


def resolve_message_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if ref.startswith("#/channels/"):
        channel_name = ref.split("/")[2]
        message_name = ref.split("/")[-1]
        message_content = (
            model.get("channels", {})
            .get(channel_name, {})
            .get("messages", {})
            .get(message_name, {})
            .get("$ref", "")
        )

        actual_message_name = message_content.split("/")[-1] if message_content else ""

        resolved_message = (
            model.get("components", {}).get("messages", {}).get(actual_message_name, {})
        )
        return resolved_message
    return {}


def resolve_payload_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if ref.startswith("#/components/schemas/"):
        schema_name = ref.split("/")[-1]
        return model.get("components", {}).get("schemas", {}).get(schema_name, {})
    return {}


def transform_asyncapi_to_webdsl(asyncapi_path):
    try:
        with open(asyncapi_path, "r") as f:
            model = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")

    brokers, broker_topics, components, entities = [], [], [], []

    info = model.get("info", {})

    # Get Broker connections
    for broker in model.get("servers", {}):
        name = broker
        broker_info = model["servers"][broker]
        protocol = broker_info.get("protocol", "mqtt")
        webdsl_protocol = protocol_to_dsl_type_map.get(protocol, "")
        host = broker_info.get("host", "")
        port = broker_info.get("port", default_ports.get(webdsl_protocol, None))
        auth = {"ursernamem": "", "password": ""}

        brokers.append(
            Broker(
                name=clean_name(name),
                protocol_type=webdsl_protocol,
                host=host,
                port=port,
                auth=auth,
            )
        )

    # Get broker topics
    for topic_name, topic_info in model.get("operations", {}).items():
        if len(brokers) == 1:
            broker_names = [brokers[0].name]
        else:
            broker_names = topic_info.get("servers", ["default"])

        name = clean_name(topic_name)
        channel = topic_info.get("channel", {}).get("$ref", "")
        channel_messages = topic_info.get("messages", {})
        topic = resolve_operations_ref(channel, model)

        for i, broker_name in enumerate(broker_names):
            newBrokerTopicInstance = BrokerTopic(
                name=f"{name}_{i}" if len(broker_names) > 1 else name,
                connection_name=broker_name,
                topic_address=topic,
                channel_messages=channel_messages,
            )
            broker_topics.append(newBrokerTopicInstance)

    # Get Entities
    for broker_topic in broker_topics:
        broker_topic_name = broker_topic.name
        messages = broker_topic.channel_messages
        resolved_messages = []
        for message in messages:
            message_ref = message.get("$ref", "")
            resolved_message = resolve_message_ref(message_ref, model)
            if resolved_message:
                resolved_messages.append(resolved_message)

        resolved_schemas_messages = []
        for message in resolved_messages:
            message_name = message.get("name", "unnamed_message")
            message_schema = message.get("payload", {}).get("$ref", {})
            resolved_schema = resolve_payload_ref(message_schema, model)
            resolved_schemas_messages.append(
                {"schema": resolved_schema, "message_name": message_name}
            )

        for entry in resolved_schemas_messages:
            schema = entry.get("schema", {})
            message_name = entry.get("message_name", "")

            newEntity = Entity(
                name=f"{message_name}_{broker_topic_name}",
                source_topic_name=broker_topic_name,
                attributes=schema.get("properties", {}),
            )

            entities.append(newEntity)

    return template.render(
        title=clean_name(info.get("title", "AsyncAPI_Generated_App")),
        description=info.get("description"),
        version=info.get("version"),
        brokers=brokers,
        topics=broker_topics,
        entities=entities,
        components=components,
    )
