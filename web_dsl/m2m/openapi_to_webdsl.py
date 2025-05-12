import re
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse
from jinja2 import Environment, FileSystemLoader
from web_dsl.definitions import TEMPLATES_PATH


# ======== Template Setup ========
env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/openapi"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)
template = env.get_template("openapi_to_webdsl.jinja")


# ====== Help Classes ===========
class RESTApi:
    def __init__(self, name: str, base_url: str, headers=None, auth=None):
        self.name = name
        self.base_url = base_url
        self.headers = headers or {}
        self.auth = auth


class RESTEndpoint:
    def __init__(
        self, name: str, connection: str, path=None, method=None, body=None, params=None
    ):
        self.name = name
        self.connection = connection
        self.path = path
        self.method = method
        self.body = body or {}
        self.params = params or {}


class Entity:
    def __init__(
        self, name: str, description: str, source: str, attributes: dict, strict: bool
    ):
        self.name = name
        self.description = description
        self.source = source
        self.attributes = attributes
        self.strict = strict

    @property
    def attribute_list(self):
        return [map_openapi_type(n, s) for n, s in self.attributes.items()]


# ===== Component mapping ========
attribute_map = {
    "Text": "content",
    "Gauge": "value",
    "ProgressBar": "value",
    "Image": "source",
}


# ========== Helper Functions ==============
def clean_path(path: str) -> str:
    path = re.sub(r"{(\w+)}", r"\1", path.strip("/"))
    return path.replace("/", "_") or "root"


def is_supported_verb(verb: str) -> bool:
    return verb.upper() in {"GET", "POST", "PUT", "DELETE"}


def map_openapi_type(name: str, schema: dict) -> str:
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    return f"{name}: {type_map.get(schema.get('type', 'string'), 'str')}"


# ========== Server and Connection Handling ==============
def resolve_server_info(servers: List[dict]) -> str:
    if not servers:
        return "http://default.api"
    url = servers[0].get("url", "")
    for var, var_data in servers[0].get("variables", {}).items():
        url = url.replace(f"{{{var}}}", var_data.get("default", ""))
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "", "", "", ""))


def register_server(
    servers: List[dict], seen: Dict[str, str], apis: List[RESTApi]
) -> str:
    base_url = resolve_server_info(servers)
    if base_url not in seen:
        name = re.sub(r"\W+", "_", base_url).strip("_") or f"api_{len(seen)+1}"
        seen[base_url] = name
        apis.append(RESTApi(name=name, base_url=base_url))
    return seen[base_url]


# ========= Schema and Entity Processing ==============
def resolve_schema_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    if ref.startswith("#/components/schemas/"):
        name = ref.split("/")[-1]
        return model.get("components", {}).get("schemas", {}).get(name, {})
    return {}


def extract_schema_props(
    schema: dict, parent: str, source: str, entities: dict, model: dict
) -> List[str]:
    generated = []

    if "$ref" in schema:
        schema = resolve_schema_ref(schema["$ref"], model)

    if not schema or schema.get("type") != "object":
        if schema.get("type") == "array":
            items = schema.get("items", {})
            if "$ref" in items:
                items = resolve_schema_ref(items["$ref"], model)
            if items.get("type") == "object":
                generated += extract_schema_props(
                    items, parent, source, entities, model
                )
        return generated

    name = re.sub(r"\W+", "_", schema.get("title", f"{parent}__Entity"))
    if name not in entities:
        entities[name] = Entity(
            name=name,
            description=schema.get("description", ""),
            source=source,
            attributes=schema.get("properties", {}),
            strict=not schema.get("additionalProperties", True),
        )
        generated.append(name)

    return generated


# ========== Component Annotations ==============
def parse_component_annotations(
    description: str, ep_name: str, entity_name: str
) -> List[Dict[str, Any]]:
    annotations = re.findall(r"webdsl\.(\w+)\.(\w+(?:\.\w+|\[\d+\])*)", description)
    result = []
    for ctype, path in annotations:
        ctype = ctype.capitalize()
        if ctype in attribute_map:
            comp = {
                "name": f"{ep_name}__{ctype}_{path.replace('.', '_').replace('[', '_').replace(']', '_')}",
                "type": ctype,
                "entity": entity_name,
                attribute_map[ctype]: path,
            }
            result.append(comp)
    return result


def process_operation(
    path: str,
    verb: str,
    operation: dict,
    conn_name: str,
    entities: dict,
    model: dict,
) -> tuple[RESTEndpoint, List[Dict[str, Any]]]:
    ep_name = f"{verb.lower()}__{clean_path(path)}"
    generated_entities = set()

    # Handle request body
    if rb := operation.get("requestBody", {}).get("content"):
        for content in rb.values():
            generated_entities.update(
                extract_schema_props(
                    content.get("schema", {}), ep_name, ep_name, entities, model
                )
            )

    # Handle response and infer main entity
    main_entity = None
    for code, resp in operation.get("responses", {}).items():
        if code == "200":
            for content in resp.get("content", {}).values():
                schema = content.get("schema", {})
                new_entities = extract_schema_props(
                    schema, ep_name, ep_name, entities, model
                )
                generated_entities.update(new_entities)
                if new_entities:
                    main_entity = entities[new_entities[0]]
                break
        if main_entity:
            break

    # Use all related entities for annotation mapping
    description = operation.get("description", "")
    components = []
    for entity_name in generated_entities:
        components += parse_component_annotations(description, ep_name, entity_name)

    endpoint = RESTEndpoint(
        name=ep_name, connection=conn_name, path=path, method=verb.upper()
    )
    return endpoint, components


# ========= Main Transformation Function ==============
def transform_openapi_to_webdsl(model: Dict[str, Any]) -> str:
    apis, endpoints, components = [], [], []
    seen, entities = {}, {}

    default_conn = (
        register_server(model.get("servers", []), seen, apis)
        if model.get("servers")
        else "default_api"
    )

    for path, operations in model.get("paths", {}).items():
        if not isinstance(operations, dict):
            continue
        conn_name = (
            register_server(operations.get("servers", []), seen, apis)
            if "servers" in operations
            else default_conn
        )
        for verb, op in operations.items():
            if isinstance(op, dict) and is_supported_verb(verb):
                if "servers" in op:
                    conn_name = register_server(op["servers"], seen, apis)
                endpoint, comps = process_operation(
                    path, verb, op, conn_name, entities, model
                )
                endpoints.append(endpoint)
                components.extend(comps)

    info = model.get("info", {})
    return template.render(
        title=re.sub(r"\W+", "_", info.get("title", "API")) or "API",
        description=info.get("description", "This is a generated webpage."),
        apis=apis,
        endpoints=endpoints,
        entities=entities.values(),
        components=components,
    )
