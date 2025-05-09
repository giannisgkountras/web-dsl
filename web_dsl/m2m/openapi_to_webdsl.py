import re
from jinja2 import Environment, FileSystemLoader, TemplateError
from web_dsl.definitions import TEMPLATES_PATH
from typing import Tuple, List, Dict, Any
from urllib.parse import urlparse, urlunparse

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


# Helpers
def is_supported_verb(verb: str) -> bool:
    return verb.upper() in {"GET", "POST", "PUT", "DELETE"}


def resolve_server_info(servers: List[dict]) -> str:
    """
    Given a list of OpenAPI Server objects, substitute variables
    and return the base URL (scheme://host[:port][basePath]).
    """
    if not servers:
        raise ValueError("No servers defined")
    # take first by default
    url = servers[0].get("url", "")
    # substitute template vars
    for var, details in servers[0].get("variables", {}).items():
        url = url.replace(f"{{{var}}}", details.get("default", ""))
    parsed = urlparse(url)
    # reconstruct up to path but drop any trailing paths beyond basePath
    base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path or "", "", "", ""))
    return base_url


def transform_openapi_to_webdsl(
    model: Dict[str, Any],
) -> str:
    """
    Extracts RESTApi and RESTEndpoint data from an OpenAPI model.
    Creates a unique RESTApi for each distinct base URL.
    """
    apis: List[RESTApi] = []
    endpoints: List[RESTEndpoint] = []
    seen: Dict[str, str] = {}  # base_url -> api_name

    def register_server(servers: List[dict]) -> str:
        base_url = resolve_server_info(servers)
        if base_url not in seen:
            name = re.sub(r"\W+", "_", base_url).strip("_") or f"api_{len(seen)+1}"
            seen[base_url] = name
            apis.append(RESTApi(name=name, base_url=base_url))
        return seen[base_url]

    # Register top-level server
    default_conn = register_server(model.get("servers", []))

    # Walk through paths and operations
    for path, methods in model.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        # path-level override
        conn_name = default_conn
        if "servers" in methods:
            conn_name = register_server(methods["servers"])
        for verb, operation in methods.items():
            if not isinstance(operation, dict) or not is_supported_verb(verb):
                continue
            # operation-level override
            if "servers" in operation:
                conn_name = register_server(operation["servers"])
            # params
            params = {
                p["name"]: {"in": p.get("in"), "schema": p.get("schema")}
                for p in operation.get("parameters", [])
            }
            # body
            body = None
            if rb := operation.get("requestBody"):
                body = rb.get("content", {})
            # endpoint name
            ep_name = f"{verb.upper()}_{path.strip('/').replace('/', '_') or 'root'}"
            endpoints.append(
                RESTEndpoint(
                    name=ep_name,
                    connection=conn_name,
                    path=path,
                    method=verb.upper(),
                    body=body,
                    params=params,
                )
            )

    # Generate the WebDSL model
    title = model.get("info", {}).get("title", "API")
    if not title:
        title = "My webpage"
    description = model.get("info", {}).get("description", "")
    if not description:
        description = "This is a generated webpage."

    webdsl_model = template.render(
        title=title, description=description, apis=apis, endpoints=endpoints
    )

    return webdsl_model
