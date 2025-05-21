import re
import yaml
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
from web_dsl.definitions import TEMPLATES_PATH
import os


# ======== Template Setup ========
env = Environment(
    loader=FileSystemLoader(
        os.path.join(TEMPLATES_PATH, "transformations")
    ),  # Store templates in a 'templates' subdirectory
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
    "LineChart": "",  # These will just use default placeholders in template
    "BarChart": "",
    "PieChart": "",
    "JsonViewer": "",
    "Table": "",
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
    ):
        self.name = name
        self.connection_name = connection_name
        self.topic_address = topic_address


class Entity:
    def __init__(
        self,
        name: str,
        description: Optional[str],
        source_topic_name: str,
        attributes: dict,
        strict: bool,
    ):
        self.name = name
        self.description = description
        self.source_topic_name = (
            source_topic_name  # Name of the BrokerTopic this entity's data comes from
        )
        self.attributes = attributes  # Dict of {attr_name: schema_obj}
        self.strict = strict

    @property
    def attribute_list(self):
        return [
            map_asyncapi_type_to_dsl(name, schema)
            for name, schema in self.attributes.items()
        ]


# ========== Helper Functions ==============
def clean_name(name: str) -> str:
    name = re.sub(
        r"[^\w.-]+", "_", name
    )  # Allow dot and hyphen for more readable names from topics
    name = name.strip("_")
    if not name:
        return "unnamed_item"
    if name[0].isdigit():  # Ensure valid identifier
        name = "_" + name
    return name.replace("-", "_").replace(".", "_")  # Replace for DSL syntax if needed


def map_asyncapi_type_to_dsl(name: str, schema: dict) -> str:
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    format_type_map = {
        "date-time": "datetime",  # Example, adjust to your DSL's types
        "uuid": "str",  # Usually represented as string
    }

    openapi_type = schema.get("type", "string")
    openapi_format = schema.get("format")

    if openapi_format and openapi_format in format_type_map:
        dsl_type = format_type_map[openapi_format]
    else:
        dsl_type = type_map.get(openapi_type, "str")

    # Handle arrays with item types
    if openapi_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:  # Could be empty if not specified
            item_type = map_asyncapi_type_to_dsl("item", items_schema).split(": ", 1)[
                -1
            ]  # Get type part
            dsl_type = (
                f"list[{item_type}]"  # Or however your DSL represents typed lists
            )
        else:
            dsl_type = "list"  # Generic list

    return f"{name}: {dsl_type}"


def resolve_asyncapi_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        # External refs not supported in this basic version
        print(f"Warning: External reference not supported: {ref}")
        return {}

    parts = ref.split("/")[1:]  # Skip '#'
    current = model
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            print(f"Warning: Could not resolve reference part '{part}' in {ref}")
            return {}
    return current


protocol_to_dsl_type_map = {
    "kafka": "KAFKA",
    "kafka-secure": "KAFKA",
    "mqtt": "MQTT",
    "mqtts": "MQTT",
    "amqp": "AMQP",
    "amqps": "AMQP",
    "redis": "REDIS",
    "rediss": "REDIS",
    # Add other protocols your DSL supports: "ws", "http" (for WebSockets/WebHooks)
}

default_ports = {
    "KAFKA": 9092,
    "MQTT": 1883,
    "AMQP": 5672,
    "REDIS": 6379,
}


def parse_host_string(
    host_str: str, protocol_dsl_type: Optional[str]
) -> Tuple[str, Optional[int]]:
    parsed_url = urlparse(
        f"//{host_str}"
    )  # Add scheme for proper parsing if host is hostname:port
    hostname = (
        parsed_url.hostname or host_str.split(":")[0]
    )  # Fallback for simple "host:port"
    port = parsed_url.port
    if port is None and protocol_dsl_type:
        port = default_ports.get(protocol_dsl_type)
    return hostname, port


def extract_schema_props_asyncapi(
    schema: dict,
    base_name: str,
    source_topic_dsl_name: str,
    entities: Dict[str, Entity],
    model: Dict[str, Any],
) -> List[str]:
    generated_entity_names = []

    if not schema:
        return generated_entity_names

    if "$ref" in schema:
        schema = resolve_asyncapi_ref(schema["$ref"], model)

    schema_type = schema.get("type")

    if schema_type == "object":
        # Use title from schema if available, otherwise generate from base_name
        entity_name_candidate = schema.get("title", base_name)
        entity_name = clean_name(entity_name_candidate)

        if entity_name not in entities:
            entities[entity_name] = Entity(
                name=entity_name,
                description=schema.get("description"),
                source_topic_name=source_topic_dsl_name,
                attributes=schema.get("properties", {}),
                strict=not schema.get(
                    "additionalProperties", True
                ),  # common default for additionalProperties is true
            )
            generated_entity_names.append(entity_name)

            # Recursively process properties if they are objects or arrays of objects
            for prop_name, prop_schema in schema.get("properties", {}).items():
                # Pass a modified base_name to avoid clashes if nested anonymous objects exist
                generated_entity_names.extend(
                    extract_schema_props_asyncapi(
                        prop_schema,
                        f"{entity_name}_{prop_name}",
                        source_topic_dsl_name,
                        entities,
                        model,
                    )
                )

    elif schema_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            # If array of objects, process the item schema
            generated_entity_names.extend(
                extract_schema_props_asyncapi(
                    items_schema,
                    f"{base_name}_item",
                    source_topic_dsl_name,
                    entities,
                    model,
                )
            )

    return generated_entity_names


# Re-use from OpenAPI transformer, ensure it's available or copy it here
def parse_component_annotations(
    x_webdsl_content: str, ep_name: str, entity_name: str
) -> List[Dict[str, Any]]:
    if isinstance(x_webdsl_content, list):
        content = "\n".join(x_webdsl_content)
    elif not isinstance(x_webdsl_content, str):
        content = ""  # Ignore if not string or list
    else:
        content = x_webdsl_content

    result = []
    # Regex from your OpenAPI example
    new_rx = re.compile(
        r"(?:-\s*)?"
        r"(?:"
        r"(?P<path>\w+(?:\[\d+\])?(?:\.\w+)*)"  # Path like response.foo or response.items[0].bar
        r"\s*->\s*"
        r")?"
        r"(?P<ctype>\w+)"
        r"(?:\s*@\s*(?P<row>\d+)\s*,\s*(?P<col>\d+))?"
    )

    for m in new_rx.finditer(content):
        path = m.group("path")
        ctype = m.group("ctype")
        row = int(m.group("row")) if m.group("row") else 0
        col = int(m.group("col")) if m.group("col") else 0

        if path and path.startswith("response"):
            path = path.replace("response", "this", 1)  # Replace first occurrence
        elif path and not path.startswith("this"):  # Allow 'this' directly
            print(
                f"Warning: Component path '{path}' in x-webdsl for {ep_name} should ideally start with 'response.' or 'this.' Using as is."
            )

        if ctype not in attribute_map:
            print(
                f"Warning: Unsupported component type '{ctype}' in x-webdsl for {ep_name}."
            )
            continue

        suffix = (
            path.replace(".", "_").replace("[", "_").replace("]", "_")
            if path
            else (
                f"_r{row}_c{col}" if row or col else ""
            )  # ensure suffix is non-empty if no path
        )
        # Ensure suffix is not empty to avoid name collisions for components without path/pos
        if (
            not suffix and len(result) > 0
        ):  # if multiple components without path/pos for same ep/entity
            suffix = f"_comp{len(result)}"

        name_safe = clean_name(f"{ep_name}_{ctype}{'_' if suffix else ''}{suffix}")

        comp = {
            "name": name_safe,
            "type": ctype,
            "entity": entity_name,
            "row": row,
            "col": col,
        }
        # Add the specific data binding attribute for the component type
        if attribute_map[
            ctype
        ]:  # If there's a specific field to bind (e.g., "content" for Text)
            comp[attribute_map[ctype]] = path
        elif (
            path
        ):  # For components like Table, JsonViewer where path might be the root object
            comp["data_source_path"] = (
                path  # Generic path if no specific attribute_map key
            )

        result.append(comp)
    return result


# ========= Main Transformation Function ==============
def transform_asyncapi_to_webdsl(asyncapi_path: str):
    try:
        with open(asyncapi_path, "r") as f:
            model = yaml.safe_load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"AsyncAPI file not found: {asyncapi_path}"
        )
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid YAML in AsyncAPI file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading AsyncAPI file: {str(e)}"
        )

    brokers: List[Broker] = []
    broker_topics: List[BrokerTopic] = []
    entities: Dict[str, Entity] = {}  # Store by entity name
    components: List[Dict[str, Any]] = []

    # --- 1. Process Servers -> Broker objects ---
    # Store by their AsyncAPI name for lookup
    processed_brokers_by_asyncapi_name: Dict[str, Broker] = {}
    asyncapi_servers = model.get("servers", {})
    if (
        not asyncapi_servers and "error" not in model
    ):  # AsyncAPI < 2.5.0 might have servers under `components` (unlikely but check spec version if issues)
        print("Warning: No 'servers' found at the root of the AsyncAPI document.")

    for server_key, server_data in asyncapi_servers.items():
        protocol = server_data.get("protocol")
        protocol_version = server_data.get("protocolVersion")  # unused for now
        host_str = server_data.get("host")

        if not protocol or not host_str:
            print(
                f"Warning: Server '{server_key}' is missing protocol or host. Skipping."
            )
            continue

        protocol_dsl_type = protocol_to_dsl_type_map.get(protocol.lower())
        if not protocol_dsl_type:
            print(
                f"Warning: Protocol '{protocol}' for server '{server_key}' is not supported. Skipping."
            )
            continue

        # Resolve variables in host_str (basic substitution)
        for var_name, var_data in server_data.get("variables", {}).items():
            default_val = var_data.get("default", "")
            host_str = host_str.replace(f"{{{var_name}}}", default_val)

        hostname, port = parse_host_string(host_str, protocol_dsl_type)
        if port is None:  # If still None after default lookup
            print(
                f"Warning: Could not determine port for server '{server_key}' ({host_str}). DSL might require it."
            )

        auth_details = None
        # Basic security scheme handling (can be expanded)
        security_reqs = server_data.get("security", [])
        if security_reqs:
            # For simplicity, take the first security requirement and its first scheme
            # In real AsyncAPI, security is complex (OAuth flows, multiple options)
            first_req = security_reqs[0] if security_reqs else {}
            first_scheme_name = next(iter(first_req.keys()), None)
            if first_scheme_name:
                scheme_def = resolve_asyncapi_ref(
                    f"#/components/securitySchemes/{first_scheme_name}", model
                )
                if scheme_def.get("type") == "userPassword":
                    auth_details = {
                        "username": "YOUR_USERNAME",
                        "password": "YOUR_PASSWORD",
                        "type": "userPassword",
                    }
                elif scheme_def.get("type") in ("scramSha256", "scramSha512"):
                    auth_details = {
                        "username": "YOUR_USERNAME",
                        "password": "YOUR_PASSWORD",
                        "type": scheme_def.get("type"),
                    }
                elif scheme_def.get("type") == "X509":
                    auth_details = {
                        "type": "X509",
                        "description": scheme_def.get(
                            "description", "X.509 certificate authentication"
                        ),
                    }
                # Add more security types as needed (apiKey, http, oauth2 etc.)

        broker_name = clean_name(server_key)
        broker_obj = Broker(
            name=broker_name,
            protocol_type=protocol_dsl_type,
            host=hostname,
            port=port,
            auth=auth_details,
        )
        brokers.append(broker_obj)
        processed_brokers_by_asyncapi_name[server_key] = broker_obj

    if (
        not brokers and "operations" in model
    ):  # If there are operations but no servers, it's problematic
        print(
            "Warning: Operations exist but no valid brokers could be defined. DSL generation might be incomplete."
        )

    # --- 2. Process Operations (links Channels, Messages, Servers) ---
    # Store created BrokerTopic DSL objects by a unique key (broker_name + channel_address) to avoid duplicates
    created_broker_topics: Dict[str, BrokerTopic] = {}

    for op_id, op_data in model.get("operations", {}).items():
        channel_ref = op_data.get("channel", {}).get("$ref")
        if not channel_ref:
            print(f"Warning: Operation '{op_id}' has no channel reference. Skipping.")
            continue

        channel_key = channel_ref.split("/")[
            -1
        ]  # Get the key from #/channels/channelKey
        channel_data = resolve_asyncapi_ref(channel_ref, model)
        if not channel_data:
            print(
                f"Warning: Could not resolve channel '{channel_ref}' for operation '{op_id}'. Skipping."
            )
            continue

        channel_address = channel_data.get("address")
        if not channel_address:
            print(
                f"Warning: Channel for operation '{op_id}' (key: {channel_key}) has no address. Skipping."
            )
            continue

        # Determine server for this operation
        # Priority: Operation.servers -> Channel.servers -> Root.servers
        # We'll pick the *first* applicable server for simplicity for the DSL.
        target_server_api_name = None
        if "servers" in op_data and op_data["servers"]:
            target_server_api_name = op_data["servers"][0]
        elif "servers" in channel_data and channel_data["servers"]:
            target_server_api_name = channel_data["servers"][0]
        elif processed_brokers_by_asyncapi_name:  # Fallback to first defined server
            target_server_api_name = next(
                iter(processed_brokers_by_asyncapi_name.keys()), None
            )

        if (
            not target_server_api_name
            or target_server_api_name not in processed_brokers_by_asyncapi_name
        ):
            if not brokers:  # No servers defined at all
                print(
                    f"Error: No servers defined in AsyncAPI spec, but operation '{op_id}' requires one. Skipping topic/entity generation for this op."
                )
                continue  # Cannot create a topic without a broker
            else:  # Server specified but not found or no server specified and using default
                print(
                    f"Warning: Server '{target_server_api_name}' for operation '{op_id}' not found or not specified. Assigning to first available broker: {brokers[0].name}."
                )
                assigned_broker = brokers[0]

        else:
            assigned_broker = processed_brokers_by_asyncapi_name[target_server_api_name]

        # Create BrokerTopic if it doesn't exist for this broker + address
        # Use a cleaned version of channel_address for the DSL topic name part
        topic_dsl_name_part = clean_name(channel_address)
        # For AsyncAPI, op_id is more unique for "what is happening on the topic"
        broker_topic_dsl_name = clean_name(
            f"{op_id}_{assigned_broker.name}_{topic_dsl_name_part}_topic"
        )

        topic_unique_key = (
            f"{assigned_broker.name}::{channel_address}"  # Key for global uniqueness
        )

        if topic_unique_key not in created_broker_topics:
            current_broker_topic = BrokerTopic(
                name=broker_topic_dsl_name,
                connection_name=assigned_broker.name,
                topic_address=channel_address,
            )
            broker_topics.append(current_broker_topic)
            created_broker_topics[topic_unique_key] = current_broker_topic
        else:
            current_broker_topic = created_broker_topics[topic_unique_key]
            # If the same topic is used by multiple operations, we might want to ensure entity names are distinct
            # or that x-webdsl is aggregated. For now, entities are tied to message names.

        # Process Messages and Create Entities
        # An operation can have multiple messages (e.g. oneOf)
        all_generated_entity_names_for_op = set()
        for msg_item_ref_obj in op_data.get("messages", []):
            msg_ref = msg_item_ref_obj.get("$ref")
            if not msg_ref:
                continue

            message_data = resolve_asyncapi_ref(msg_ref, model)
            if not message_data:
                print(
                    f"Warning: Could not resolve message '{msg_ref}' for operation '{op_id}'."
                )
                continue

            payload_schema = message_data.get(
                "payload", {}
            )  # Payload itself can be the schema or contain $ref
            if "$ref" in payload_schema:
                payload_schema = resolve_asyncapi_ref(payload_schema["$ref"], model)

            # Base name for entity: message name, or operation ID + "payload"
            entity_base_name = message_data.get("name", f"{op_id}_payload")

            # Extract schema properties into Entity objects
            # source_topic_dsl_name is the name of the BrokerTopic instance
            generated_entity_names = extract_schema_props_asyncapi(
                payload_schema,
                entity_base_name,
                current_broker_topic.name,
                entities,
                model,
            )
            all_generated_entity_names_for_op.update(generated_entity_names)

        # Process x-webdsl for Components, associate with this operation and its entities
        x_webdsl_content = op_data.get(
            "x-webdsl", model.get("x-webdsl", "")
        )  # Check op, then root
        if x_webdsl_content:
            if not all_generated_entity_names_for_op:
                # Create a default entity if no schema but x-webdsl is present
                default_entity_name = clean_name(f"{op_id}_DefaultEntity")
                if default_entity_name not in entities:
                    entities[default_entity_name] = Entity(
                        name=default_entity_name,
                        description="Default entity for UI components",
                        source_topic_name=current_broker_topic.name,
                        attributes={},
                        strict=False,
                    )
                all_generated_entity_names_for_op.add(default_entity_name)
                print(
                    f"Note: x-webdsl found for operation '{op_id}' but no clear payload schema. Created default entity '{default_entity_name}'."
                )

            for entity_n in all_generated_entity_names_for_op:
                # Use op_id as the 'endpoint name' for component naming context
                op_components = parse_component_annotations(
                    x_webdsl_content, clean_name(op_id), entity_n
                )
                components.extend(op_components)

    # --- 3. Prepare data for template ---
    info = model.get("info", {})
    return template.render(
        title=clean_name(info.get("title", "AsyncAPI_Generated_App")),
        description=info.get("description"),
        version=info.get("version"),
        brokers=brokers,
        topics=broker_topics,  # Renamed from broker_topics for consistency with template
        entities=list(entities.values()),
        components=components,
    )
