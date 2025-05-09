import re
from jinja2 import Environment, FileSystemLoader, TemplateError
from web_dsl.definitions import TEMPLATES_PATH
from typing import Tuple, List, Dict, Any

env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/openapi"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)

template = env.get_template("openapi_to_webdsl.jinja")


# -- your existing helpers reused here --


class RESTApi:
    def __init__(
        self,
        name: str,
        host: str,
        port: int = None,
        headers: Dict[str, Any] = None,
        auth: str = None,
    ):
        self.name = name
        self.host = host
        self.port = port
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


def is_supported_verb(verb: str) -> bool:
    return verb.upper() in {"GET", "POST", "PUT", "DELETE"}


def retrieve_server_info(model: dict) -> Tuple[str, str, int]:
    servers = model.get("servers", [])
    if not servers:
        raise ValueError("No servers defined")
    server = servers[0]
    url = server.get("url", "")
    # substitute template vars
    for var, details in server.get("variables", {}).items():
        url = url.replace(f"{{{var}}}", details.get("default", ""))
    m = re.match(r"^(https?://)?([^:/]+)(:(\d+))?(/.*)?$", url)
    if not m:
        raise ValueError(f"Invalid URL: {url}")
    print(m.groups())
    print(f"URL: {url}")
    host = m.group(1) + m.group(2)
    port = int(m.group(4)) if m.group(4) else None
    return host, url, port


# -- new transformation function --


def transform_to_rest_dsl(
    model: Dict[str, Any],
) -> Tuple[List[RESTApi], List[RESTEndpoint]]:
    apis: List[RESTApi] = []
    endpoints: List[RESTEndpoint] = []

    # 1. Build one RESTApi per unique server
    global_host, global_base, global_port = retrieve_server_info(model)
    # give it a name based on host
    default_api_name = re.sub(r"\W+", "_", global_host) or "api"
    apis.append(RESTApi(name=default_api_name, host=global_host, port=global_port))
    # index by tuple for lookup
    api_index = {(global_host, global_port): default_api_name}

    # if there are additional top-level servers, register them too
    for srv in model.get("servers", [])[1:]:
        host, base, port = retrieve_server_info({"servers": [srv]})
        name = re.sub(r"\W+", "_", host) or f"api_{len(apis)}"
        apis.append(RESTApi(name=name, host=host, port=port))
        api_index[(host, port)] = name

    # 2. Walk all paths & operations
    for path, methods in model.get("paths", {}).items():
        # check for path-level override
        if srv_list := methods.get("servers"):
            host, base, port = retrieve_server_info({"servers": srv_list})
        else:
            host, base, port = global_host, global_base, global_port

        conn_name = api_index.setdefault((host, port), default_api_name)

        for verb, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            if not is_supported_verb(verb):
                continue

            # operation-level server override?
            if op_srv := operation.get("servers"):
                h2, b2, p2 = retrieve_server_info({"servers": op_srv})
                conn_name = api_index.setdefault((h2, p2), conn_name)

            # collect params
            params = {}
            for p in operation.get("parameters", []):
                params[p.get("name")] = {"in": p.get("in"), "schema": p.get("schema")}

            # collect requestBody as body definition
            body = None
            if rb := operation.get("requestBody"):
                # naive: just dump the content object
                body = rb.get("content", {})

            # name the endpoint by method + sanitized path
            ep_name = f"{verb.upper()}_{path.strip('/').replace('/','_') or 'root'}"
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

    return apis, endpoints


def transform_openapi_to_webdsl(openapi_data, output_path):
    """
    Transform OpenAPI specification to WebDSL model.
    """

    # Parse the OpenAPI specification
    apis, endpoints = transform_to_rest_dsl(openapi_data)
    for api in apis:
        print(api.__dict__)
    # print(f"APIs: {apis}")
    # print(f"Endpoints: {endpoints}")

    # Generate the WebDSL model
    webdsl_model = template.render(openapi_spec=openapi_data)

    # Write the WebDSL model to the output path
    with open(output_path, "w") as f:
        f.write(webdsl_model)
