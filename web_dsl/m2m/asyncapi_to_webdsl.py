import re
import yaml
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
from web_dsl.definitions import (
    TEMPLATES_PATH,
)  # Assuming this is defined in your project
import os


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
        self.source_topic_name = source_topic_name
        self.attributes = attributes
        self.strict = strict

    @property
    def attribute_list(self):
        return [
            map_asyncapi_type_to_dsl(name, schema)
            for name, schema in self.attributes.items()
        ]


# ========== Helper Functions ==============
def clean_name(name: str) -> str:
    name = re.sub(r"[^\w.-]+", "_", name)
    name = name.strip("_")
    if not name:
        return "unnamed_item"
    if name[0].isdigit():
        name = "_" + name
    return name.replace("-", "_").replace(".", "_")


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
        "date-time": "str",
        "uuid": "str",
    }

    openapi_type = schema.get("type", "string")
    openapi_format = schema.get("format")

    dsl_type = "str"  # Default
    if openapi_format and openapi_format in format_type_map:
        dsl_type = format_type_map[openapi_format]
    elif openapi_type in type_map:
        dsl_type = type_map[openapi_type]

    if openapi_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            item_type_name = "item"  # placeholder name for recursion
            item_dsl_type_str = map_asyncapi_type_to_dsl(item_type_name, items_schema)
            # Extract just the type part, e.g., "str" from "item: str"
            item_type = (
                item_dsl_type_str.split(": ", 1)[-1]
                if ": " in item_dsl_type_str
                else "any"
            )
            dsl_type = f"list[{item_type}]"
        else:
            dsl_type = "list"  # Generic list if items schema is missing

    return f"{name}: {dsl_type}"


def resolve_asyncapi_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        print(f"Warning: External reference not supported: {ref}")
        return {}

    parts = ref.split("/")[1:]
    current = model
    for part in parts:
        part = part.replace("~1", "/").replace("~0", "~")  # JSON Pointer unescaping
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            print(f"Warning: Could not resolve reference part '{part}' in {ref}")
            return {}
    return current


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


def parse_host_string(
    host_str: str, protocol_dsl_type: Optional[str]
) -> Tuple[str, Optional[int]]:
    parsed_url = urlparse(f"//{host_str}")
    hostname = parsed_url.hostname or host_str.split(":")[0]
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
        entity_name_candidate = schema.get("title", base_name)  # Prefer schema title
        entity_name = clean_name(entity_name_candidate)

        if entity_name not in entities:
            entities[entity_name] = Entity(
                name=entity_name,
                description=schema.get("description"),
                source_topic_name=source_topic_dsl_name,
                attributes=schema.get("properties", {}),
                strict=not schema.get("additionalProperties", True),
            )
            generated_entity_names.append(entity_name)

            for prop_name, prop_schema in schema.get("properties", {}).items():
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


def parse_component_annotations(
    x_webdsl_content: str, ep_name: str, entity_name: str
) -> List[Dict[str, Any]]:
    if isinstance(x_webdsl_content, list):
        content = "\n".join(x_webdsl_content)
    elif not isinstance(x_webdsl_content, str):
        content = ""
    else:
        content = x_webdsl_content

    result = []
    new_rx = re.compile(
        r"(?:-\s*)?"
        r"(?:"
        r"(?P<path>\w+(?:\[\d+\])?(?:\.\w+)*)"
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
            path = path.replace("response", "this", 1)
        elif path and not path.startswith("this"):
            print(
                f"Warning: Component path '{path}' in x-webdsl for {ep_name} should start with 'response.' or 'this.' Using as is."
            )

        if ctype not in attribute_map:
            print(
                f"Warning: Unsupported component type '{ctype}' in x-webdsl for {ep_name}."
            )
            continue

        suffix = (
            path.replace(".", "_").replace("[", "_").replace("]", "_")
            if path
            else (f"_r{row}_c{col}" if row or col else "")
        )
        if not suffix and len(result) > 0:
            suffix = f"_comp{len(result)}"

        name_safe = clean_name(f"{ep_name}_{ctype}{'_' if suffix else ''}{suffix}")

        comp = {
            "name": name_safe,
            "type": ctype,
            "entity": entity_name,
            "row": row,
            "col": col,
        }
        if attribute_map[ctype]:
            comp[attribute_map[ctype]] = path
        elif path:
            comp["data_source_path"] = path
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

    if model.get("asyncapi", "").split(".")[0] != "3":
        raise HTTPException(
            status_code=400, detail="This transformer only supports AsyncAPI 3.x.x"
        )

    brokers: List[Broker] = []
    broker_topics: List[BrokerTopic] = []
    entities: Dict[str, Entity] = {}
    components: List[Dict[str, Any]] = []

    processed_brokers_by_asyncapi_name: Dict[str, Broker] = {}
    asyncapi_servers = model.get("servers", {})
    if not asyncapi_servers and "error" not in model:
        print("Warning: No 'servers' found at the root of the AsyncAPI document.")

    for server_key, server_data in asyncapi_servers.items():
        protocol = server_data.get("protocol")
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

        for var_name, var_data in server_data.get("variables", {}).items():
            default_val = var_data.get("default", "")
            host_str = host_str.replace(f"{{{var_name}}}", default_val)

        hostname, port = parse_host_string(host_str, protocol_dsl_type)
        if port is None:
            print(
                f"Warning: Could not determine port for server '{server_key}' ({host_str}). DSL might require it."
            )

        auth_details = None
        security_reqs = server_data.get("security", [])
        if security_reqs:
            first_req = security_reqs[0] if security_reqs else {}
            first_scheme_name = next(iter(first_req.keys()), None)
            if first_scheme_name:
                scheme_def_ref = (
                    model.get("components", {})
                    .get("securitySchemes", {})
                    .get(first_scheme_name, {})
                )
                # For AsyncAPI 3.0, securitySchemes are directly under components
                # No need for resolve_asyncapi_ref if it's directly under components.securitySchemes
                # If it were a $ref like "#/components/securitySchemes/myScheme", resolve_asyncapi_ref would be used by schema parser.
                # Here we assume it's defined directly or we'd need to handle $ref to scheme.

                # For simplicity, assuming security schemes are defined directly in components
                scheme_def = scheme_def_ref  # If it was a $ref, it should have been resolved before or handled here
                if isinstance(scheme_def_ref, dict) and "$ref" in scheme_def_ref:
                    scheme_def = resolve_asyncapi_ref(scheme_def_ref["$ref"], model)

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

    if not brokers and "operations" in model:
        print("Warning: Operations exist but no valid brokers could be defined.")

    created_broker_topics: Dict[str, BrokerTopic] = {}

    for op_id, op_data in model.get("operations", {}).items():
        # In AsyncAPI 3.0, operation.channel is a Reference Object
        channel_ref_obj = op_data.get("channel")
        if not channel_ref_obj or "$ref" not in channel_ref_obj:
            print(
                f"Warning: Operation '{op_id}' has no valid channel reference. Skipping."
            )
            continue
        channel_ref = channel_ref_obj["$ref"]

        channel_data = resolve_asyncapi_ref(channel_ref, model)
        if not channel_data:
            print(
                f"Warning: Could not resolve channel '{channel_ref}' for operation '{op_id}'. Skipping."
            )
            continue

        channel_address = channel_data.get("address")
        if not channel_address:
            # AsyncAPI 3.0 spec: "If the channel name is a SCIM filter, or a specific protocol requires a different format,
            # the address field SHOULD be used to provide the actual channel name."
            # Fallback to channel key if address is missing but might not always be correct.
            channel_key = channel_ref.split("/")[-1]
            print(
                f"Warning: Channel for operation '{op_id}' (key: {channel_key}) has no 'address' field. Using key '{channel_key}' as address. This might be incorrect."
            )
            channel_address = channel_key  # Fallback

        if not channel_address:
            print(
                f"Warning: Channel for operation '{op_id}' has no address and key could not be determined. Skipping."
            )
            continue

        target_server_api_name = None
        # AsyncAPI 3.0: operation.servers is an array of Server Objects, not references
        # channel.servers is also an array of Server Objects
        op_servers = op_data.get("servers")
        channel_servers = channel_data.get("servers")

        # Simple selection: first server from operation, then channel, then root
        if op_servers and isinstance(op_servers, list) and op_servers:
            # We need the *key* of the server from the root `servers` object.
            # The server object itself doesn't contain its original key.
            # This requires matching the server object, which is complex.
            # For simplicity, we assume if servers are specified at op/channel,
            # they must have been processed from the root `servers` dict.
            # This part needs careful implementation if strict server matching is required.
            # Let's assume for now that if specified, it matches one of the processed_brokers_by_asyncapi_name keys.
            # This is a simplification: AsyncAPI 3 allows inline server definitions which are not handled here.
            # We will try to match by `host` and `protocol` if direct key is not available.
            # A better approach would be to pre-process all server definitions (root, channel, op)
            # and uniquely identify them.

            # Simplified: try to find a server by matching host and protocol if it was defined inline.
            # This section is a placeholder for a more robust server resolution strategy for AsyncAPI 3.0 inline servers.
            # For now, we rely on the operation/channel server *being one of the root-defined servers*
            # or we fall back to the first root server.
            # To truly support AsyncAPI 3 server overrides, we'd need to process these inline server definitions
            # and create Broker objects for them if they are new/different.
            # The current code primarily processes `model.servers`.

            # For now, let's assume `op_data.servers` or `channel_data.servers` refers to one of the
            # keys from the global `servers:` definition if it's not an inline definition.
            # If AsyncAPI 3.0 allows `servers: [{host: "...", protocol: "..."}]` directly in operation,
            # then this logic needs to create a broker on the fly or match it.
            # The current logic expects `servers: [ { $ref: "#/servers/myServerKey" } ]` or `servers: [ "myServerKey" ]` effectively.
            # AsyncAPI 3.0: "An array of Server Objects. [...] This field is OPTIONAL.
            # If provided, it SHOULD override the server definitions on the parent Channel Object."

            # Sticking to the previous logic of server name from root, or fallback.
            # This means we don't fully support overriding with completely new server definitions at op/channel level yet.
            # We'd need to find a server from `processed_brokers_by_asyncapi_name` that matches characteristics.
            # This part is complex. Fallback to first available broker if specific server cannot be easily matched.
            pass  # Placeholder for improved server matching

        if not target_server_api_name and processed_brokers_by_asyncapi_name:
            target_server_api_name = next(
                iter(processed_brokers_by_asyncapi_name.keys()), None
            )

        if (
            not target_server_api_name
            or target_server_api_name not in processed_brokers_by_asyncapi_name
        ):
            if not brokers:
                print(
                    f"Error: No servers defined in AsyncAPI spec, but operation '{op_id}' requires one. Skipping topic/entity generation."
                )
                continue
            else:
                # print(f"Warning: Server for operation '{op_id}' not explicitly found. Assigning to first available broker: {brokers[0].name}.")
                assigned_broker = brokers[0]
        else:
            assigned_broker = processed_brokers_by_asyncapi_name[target_server_api_name]

        topic_dsl_name_part = clean_name(channel_address)
        broker_topic_dsl_name = clean_name(
            f"{op_id}_{assigned_broker.name}_{topic_dsl_name_part}_topic"
        )
        topic_unique_key = f"{assigned_broker.name}::{channel_address}"

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

        all_generated_entity_names_for_op = set()
        messages_to_process_refs_or_objs = []

        # AsyncAPI 3.0: operation.messages is an array of Reference Objects to Message Objects
        # AsyncAPI 3.0: channel.messages is a map of Message Objects (or Reference Objects)
        operation_messages_refs = op_data.get("messages")  # Array of Reference Objects
        channel_messages_map = channel_data.get(
            "messages"
        )  # Map {msgId: Message Object | Reference Object}

        if operation_messages_refs:
            for ref_obj in operation_messages_refs:
                if isinstance(ref_obj, dict) and "$ref" in ref_obj:
                    messages_to_process_refs_or_objs.append(ref_obj)
        elif channel_messages_map:
            for msg_id, msg_obj_or_ref in channel_messages_map.items():
                messages_to_process_refs_or_objs.append(
                    msg_obj_or_ref
                )  # Can be Message or Reference

        for item_ref_or_obj in messages_to_process_refs_or_objs:
            message_data = None
            msg_ref_for_error = "inline message"

            if (
                isinstance(item_ref_or_obj, dict) and "$ref" in item_ref_or_obj
            ):  # It's a Reference Object
                msg_ref = item_ref_or_obj["$ref"]
                msg_ref_for_error = msg_ref
                message_data = resolve_asyncapi_ref(msg_ref, model)
            elif isinstance(item_ref_or_obj, dict):  # It's an inline Message Object
                message_data = item_ref_or_obj

            if not message_data:
                print(
                    f"Warning: Could not resolve or use message for operation '{op_id}' (item: {msg_ref_for_error})."
                )
                continue

            payload_schema = message_data.get("payload", {})
            if "$ref" in payload_schema:
                payload_schema = resolve_asyncapi_ref(payload_schema["$ref"], model)

            entity_base_name_candidate = (
                message_data.get("title")
                or message_data.get("name")
                or f"{op_id}_payload"
            )
            entity_base_name = clean_name(entity_base_name_candidate)

            generated_entity_names = extract_schema_props_asyncapi(
                payload_schema,
                entity_base_name,
                current_broker_topic.name,
                entities,
                model,
            )
            all_generated_entity_names_for_op.update(generated_entity_names)

        x_webdsl_content = op_data.get("x-webdsl", model.get("x-webdsl", ""))
        if x_webdsl_content:
            if not all_generated_entity_names_for_op:
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
                op_components = parse_component_annotations(
                    x_webdsl_content, clean_name(op_id), entity_n
                )
                components.extend(op_components)

    info = model.get("info", {})
    return template.render(
        title=clean_name(info.get("title", "AsyncAPI_Generated_App")),
        description=info.get("description"),
        version=info.get("version"),
        brokers=brokers,
        topics=broker_topics,
        entities=list(entities.values()),
        components=components,
    )
