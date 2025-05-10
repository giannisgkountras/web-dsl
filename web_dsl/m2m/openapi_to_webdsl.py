import re
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Any
from urllib.parse import urlparse, urlunparse
from web_dsl.definitions import TEMPLATES_PATH

# Set up Jinja2 environment
env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/openapi"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)

template = env.get_template("openapi_to_webdsl.jinja")


# Data classes for DSL elements
class RESTApi:
    def __init__(
        self,
        name: str,
        base_url: str,
        headers: Dict[str, Any] = None,
        auth: str = None,
    ):
        self.name = name
        self.base_url = base_url
        self.headers = headers or {}
        self.auth = auth


class RESTEndpoint:
    def __init__(
        self,
        name: str,
        connection: str,
        path: str = None,
        method: str = None,
        body: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
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
        self.source = source  # Single string, not a set
        self.attributes = attributes
        self.strict = strict

    @property
    def attribute_list(self):
        """Return a list of formatted attribute strings for the template."""
        return [
            map_openapi_type(name, schema) for name, schema in self.attributes.items()
        ]


# Helper functions
def clean_path(path: str) -> str:
    """Clean an OpenAPI path by removing parameter braces and replacing slashes with underscores."""
    path = path.strip("/")  # Remove leading/trailing slashes
    path = re.sub(r"{(\w+)}", r"\1", path)  # Replace {param} with param
    path = path.replace("/", "_")  # Replace slashes with single underscores
    return path if path else "root"  # Use 'root' for empty paths (e.g., '/')


def is_supported_verb(verb: str) -> bool:
    """Check if the HTTP verb is supported."""
    return verb.upper() in {"GET", "POST", "PUT", "DELETE"}


def resolve_server_info(servers: List[dict]) -> str:
    """Resolve the base URL from a list of OpenAPI server objects."""
    if not servers:
        return "http://default.api"  # Fallback for missing servers
    url = servers[0].get("url", "")
    for var, details in servers[0].get("variables", {}).items():
        url = url.replace(f"{{{var}}}", details.get("default", ""))
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "", "", "", ""))


def register_server(
    servers: List[dict], seen: Dict[str, str], apis: List[RESTApi]
) -> str:
    """Register a server and return its connection name, adding to apis if new."""
    base_url = resolve_server_info(servers)
    if base_url not in seen:
        name = re.sub(r"\W+", "_", base_url).strip("_") or f"api_{len(seen)+1}"
        seen[base_url] = name
        apis.append(RESTApi(name=name, base_url=base_url))
    return seen[base_url]


def resolve_schema_ref(ref: str, model: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a schema reference to the actual schema definition."""
    if ref.startswith("#/components/schemas/"):
        schema_name = ref.split("/")[-1]
        components = model.get("components", {})
        schemas = components.get("schemas", {})
        return schemas.get(schema_name, {})
    return {}


def extract_schema_props(
    schema: dict, parent_name: str, source: str, entities_dict: dict, model: dict
):
    """Extract properties from an OpenAPI schema and create an entity."""
    if "$ref" in schema:
        schema = resolve_schema_ref(schema["$ref"], model)  # Resolve schema references
    if not schema or "type" not in schema:
        return

    if schema["type"] == "object":
        # Use schema title if available, otherwise construct name from endpoint
        entity_name = schema.get("title", f"{parent_name}__Entity")
        entity_name = re.sub(r"\W+", "_", entity_name)  # Clean non-word characters
        description = schema.get("description", "")
        strict = not schema.get("additionalProperties", True)
        props = schema.get("properties", {})

        # Only create entity if it doesn’t already exist
        if entity_name not in entities_dict:
            entities_dict[entity_name] = Entity(
                name=entity_name,
                description=description,
                source=source,  # Single endpoint name
                attributes=props,
                strict=strict,
            )
    elif schema["type"] == "array":
        # Recursively process array items if they are objects
        items = schema.get("items", {})
        if "$ref" in items:
            items = resolve_schema_ref(items["$ref"], model)
        if items.get("type") == "object":
            extract_schema_props(items, parent_name, source, entities_dict, model)


def process_operation(
    path: str,
    verb: str,
    operation: dict,
    conn_name: str,
    entities_dict: dict,
    model: dict,
) -> "RESTEndpoint":
    """Process an OpenAPI operation to create an endpoint and extract schemas."""
    path_clean = clean_path(path)
    ep_name = f"{verb.lower()}__{path_clean}"  # e.g., post__rouleta
    parent_name = ep_name  # Used for entity naming

    # Process request body
    if rb := operation.get("requestBody", {}).get("content"):
        for mime, item in rb.items():
            schema = item.get("schema", {})
            extract_schema_props(schema, parent_name, ep_name, entities_dict, model)

    # Process responses
    for code, resp in operation.get("responses", {}).items():
        if content := resp.get("content"):
            for mime, item in content.items():
                schema = item.get("schema", {})
                extract_schema_props(schema, parent_name, ep_name, entities_dict, model)

    return RESTEndpoint(
        name=ep_name, connection=conn_name, path=path, method=verb.upper()
    )


def map_openapi_type(name, schema):
    """Map OpenAPI schema types to Python-like type annotations."""
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    attr_type = schema.get("type", "string")  # Default to "string" if type is missing
    return f"{name}: {type_map.get(attr_type, 'str')}"


def transform_openapi_to_webdsl(model: Dict[str, Any]) -> str:
    """Transform an OpenAPI specification into a WebDSL model string."""
    apis: List[RESTApi] = []
    endpoints: List[RESTEndpoint] = []
    entities_dict: Dict[str, Entity] = {}
    seen: Dict[str, str] = {}

    # Register top-level server with fallback
    default_servers = model.get("servers", [])
    default_conn = (
        register_server(default_servers, seen, apis)
        if default_servers
        else "default_api"
    )

    # Process paths and operations
    for path, methods in model.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        conn_name = default_conn
        if "servers" in methods:
            conn_name = register_server(methods["servers"], seen, apis)
        for verb, operation in methods.items():
            if not isinstance(operation, dict) or not is_supported_verb(verb):
                continue
            if "servers" in operation:
                conn_name = register_server(operation["servers"], seen, apis)
            endpoint = process_operation(
                path, verb, operation, conn_name, entities_dict, model
            )
            endpoints.append(endpoint)

    # Render the template with Entity objects directly
    title = model.get("info", {}).get("title", "API")
    title = re.sub(r"\W+", "_", title)  # Clean non-word characters
    if not title:
        title = "API"
    description = model.get("info", {}).get(
        "description", "This is a generated webpage."
    )

    return template.render(
        title=title,
        description=description,
        apis=apis,
        endpoints=endpoints,
        entities=entities_dict.values(),
    )
