import os
import secrets
import base64
import subprocess
from jinja2 import Environment, FileSystemLoader, TemplateError
from .language import build_model
from textx.model import get_children_of_type
import traceback
from web_dsl.definitions import TEMPLATES_PATH
from textx import generator


def generate_api_key(length=32):
    key = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(key).rstrip(b"=").decode("utf-8")


# Set up the Jinja2 environment and load templates
frontend_env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/frontend"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)
backend_env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/backend"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)

frontend_base_dir = os.path.join(os.path.dirname(__file__), "base", "frontend_base")
backend_base_dir = os.path.join(os.path.dirname(__file__), "base", "backend_base")

screen_template = frontend_env.get_template("screen_template.jinja")
app_template = frontend_env.get_template("app_template.jinja")
index_html_template = frontend_env.get_template("index_html_template.jinja")
websocket_context_config_template = frontend_env.get_template(
    "websocket_context_config.jinja"
)
dot_env_frontend_template = frontend_env.get_template("dot_env_template.jinja")
dot_env_backend_template = backend_env.get_template("dot_env_template.jinja")

config_template = backend_env.get_template("config_template.jinja")
endpoint_config_template = backend_env.get_template("endpoint_config.jinja")
db_config_template = backend_env.get_template("db_config.jinja")
dockerfile_template = backend_env.get_template("dockerfile_template.jinja")
user_roles_template = backend_env.get_template("user_roles_template.jinja")

docker_compose_template = backend_env.get_template("docker_compose_template.jinja")


def generate(model_path, gen_path):
    # Read and parse the DSL model
    print(f"Reading model from: {model_path}")
    model = build_model(model_path)
    # Create the output directory with frontend and backend subdirectories
    print(f"Creating output directory: {gen_path}")
    os.makedirs(gen_path, exist_ok=True)
    os.makedirs(os.path.join(gen_path, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(gen_path, "backend"), exist_ok=True)

    # Copy the base frontend project contents to the output directory
    print(f"Copying frontend base contents to: {gen_path}")
    subprocess.run(
        ["cp", "-r", f"{frontend_base_dir}/.", os.path.join(gen_path, "frontend")]
    )

    # Copy the base backend project contents to the output directory
    print(f"Copying backend base contents to: {gen_path}")
    subprocess.run(
        ["cp", "-r", f"{backend_base_dir}/.", os.path.join(gen_path, "backend")]
    )

    # ========= Generate frontend files============
    # Prepare the output directories
    screens_dir = os.path.join(gen_path, "frontend", "src", "screens")
    if not os.path.exists(screens_dir):
        os.makedirs(screens_dir, exist_ok=True)

    # Generate the screen components
    for screen in model.aggregated_screens:

        # Get all entities used in this screen
        all_components = get_children_of_type("Component", screen)

        # Get all component references
        all_component_references = get_children_of_type("ComponentRef", screen)

        # Augument the components with the references
        for component_ref in all_component_references:
            all_components.append(component_ref.ref)

        # Get all entities used in this screen
        entities = set()
        for component in all_components:
            if getattr(component, "entity", None) is not None:
                entities.add(component.entity)

        # Get all conditions used in this screen
        all_conditions = get_children_of_type("Condition", screen)
        for condition in all_conditions:
            if getattr(condition, "entities", None) is not None:
                entities_list = list(condition.entities)
                for entity in entities_list:
                    entities.add(entity)

        # Get all repetitions used in this screen
        all_repetitions = get_children_of_type("Repetition", screen)
        for repetition in all_repetitions:
            if getattr(repetition, "entities_list", None) is not None:
                entities_list = list(repetition.entities)
                for entity in entities_list:
                    entities.add(entity)

        # Transform the entities into a list
        entities = list(entities)
        print(f"Generating screen: {screen.name}")
        try:
            html_content = screen_template.render(screen=screen, entities=entities)
        except TemplateError as e:
            print("Jinja2 Template Error:", e)
            traceback.print_exc()
        output_file = os.path.join(screens_dir, f"{screen.name}.jsx")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated: {output_file}")

    # Generate additional files like App.jsx and index.html
    app_content = app_template.render(
        webpage=model.processed_webpage, screens=model.aggregated_screens
    )
    app_output_file = os.path.join(gen_path, "frontend", "src", "App.jsx")
    with open(app_output_file, "w", encoding="utf-8") as f:
        f.write(app_content)
    print(f"Generated: {app_output_file}")

    index_html_content = index_html_template.render(webpage=model.processed_webpage)
    index_html_output_file = os.path.join(gen_path, "frontend", "index.html")
    with open(index_html_output_file, "w", encoding="utf-8") as f:
        f.write(index_html_content)
    print(f"Generated: {index_html_output_file}")

    # Generate websocket context config file
    websocket_context_config_content = websocket_context_config_template.render(
        websocket=model.processed_websocket
    )
    websocket_context_config_output_file = os.path.join(
        gen_path, "frontend", "src", "context", "websocketConfig.json"
    )
    with open(websocket_context_config_output_file, "w", encoding="utf-8") as f:
        f.write(websocket_context_config_content)
    print(f"Generated: {websocket_context_config_output_file}")

    # Generate .env frontend file
    api_key = generate_api_key()
    secret_key = generate_api_key()
    env_frontend_content = dot_env_frontend_template.render(
        api=model.processed_api, api_key=api_key, secret_key=secret_key
    )
    env_frontend_output_file = os.path.join(gen_path, "frontend", ".env")
    with open(env_frontend_output_file, "w", encoding="utf-8") as f:
        f.write(env_frontend_content)
    print(f"Generated {env_frontend_output_file}")

    # ========= Generate backend files============

    # Generate .env backend file
    env_backend_content = dot_env_backend_template.render(
        api_key=api_key, secret_key=secret_key
    )
    env_backend_output_file = os.path.join(gen_path, "backend", ".env")
    with open(env_backend_output_file, "w", encoding="utf-8") as f:
        f.write(env_backend_content)
    print(f"Generated {env_backend_output_file}")

    # Generate users roles config file
    users = model.aggregated_users
    user_roles_config_file = os.path.join(gen_path, "backend", "user_roles.yaml")
    user_roles_config_content = user_roles_template.render(users=users)
    with open(user_roles_config_file, "w", encoding="utf-8") as f:
        f.write(user_roles_config_content)
    print(f"Generated: {user_roles_config_file}")

    # # Collect all components from the model to get what attributes of entities are actually used
    # components = get_children_of_type("Component", model)
    # for component in components:
    #     print(component.type.__dict__)

    # Gather all topics from the model
    entities = get_children_of_type("Entity", model)
    topic_configs = []
    if model.aggregated_entities:
        for entity_obj in model.aggregated_entities:
            # collect attributes
            attributes = [attr.name for attr in entity_obj.attributes]
            # Ensure entity_obj.source and entity_obj.source.connection are resolved
            if (
                hasattr(entity_obj, "source")
                and entity_obj.source
                and entity_obj.source.__class__.__name__ == "BrokerTopic"
                and hasattr(entity_obj.source, "connection")
                and entity_obj.source.connection
                # ensure the connection isnt already in the list
                and entity_obj.source.connection.name
                not in [
                    config.get("broker", None)
                    for config in topic_configs
                    if config.get("topic", None) == entity_obj.source.topic
                ]
            ):
                topic_configs.append(
                    {
                        "topic": entity_obj.source.topic,
                        "broker": entity_obj.source.connection.name,
                        "attributes": attributes,
                        "strict": (
                            entity_obj.strict
                            if hasattr(entity_obj, "strict")
                            else False
                        ),  # Default if strict not present
                        # gather all roles as strings
                        "allowed_roles": [
                            role.name for role in entity_obj.source.allowed_roles
                        ],
                    }
                )

    # Collect all brokers
    all_brokers = set()
    for broker in model.aggregated_brokers:
        all_brokers.add(broker)
    all_brokers = list(all_brokers)
    config_dir = os.path.join(gen_path, "backend")
    config_output_file = os.path.join(config_dir, "config.yaml")
    config_content = config_template.render(
        brokers=all_brokers,
        websocket=model.processed_websocket,
        api=model.processed_api,
        topic_configs=topic_configs,
    )
    with open(config_output_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Generated: {config_output_file}")

    # Generate rest api config file
    # all_rest_apis = get_children_of_type("RESTApi", model)

    endpoint_config_dir = os.path.join(gen_path, "backend")
    endpoint_config_output_file = os.path.join(
        endpoint_config_dir, "endpoint_config.yaml"
    )
    endpoint_config_content = endpoint_config_template.render(
        all_rest_apis=model.aggregated_restapis,
        all_rest_endpoints=model.aggregated_endpoints,
    )
    with open(endpoint_config_output_file, "w", encoding="utf-8") as f:
        f.write(endpoint_config_content)
    print(f"Generated: {endpoint_config_output_file}")

    # Generate Database config
    mysql_databases_list = []
    mongo_databases_list = []
    if model.aggregated_databases:
        for db in model.aggregated_databases:
            if db.__class__.__name__ == "MySQL":
                mysql_databases_list.append(db)
            elif db.__class__.__name__ == "MongoDB":
                mongo_databases_list.append(db)

    db_config_dir = os.path.join(gen_path, "backend")
    db_config_output_file = os.path.join(db_config_dir, "db_config.yaml")
    db_config_content = db_config_template.render(
        mysql_databases=mysql_databases_list, mongo_databases=mongo_databases_list
    )
    with open(db_config_output_file, "w", encoding="utf-8") as f:
        f.write(db_config_content)
    print(f"Generated: {db_config_output_file}")

    # Generate dockerfile
    dockerfile_output_file = os.path.join(gen_path, "backend", "Dockerfile")
    dockerfile_content = dockerfile_template.render(
        websocket=model.processed_websocket, api=model.processed_api
    )
    with open(dockerfile_output_file, "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    print(f"Generated: {dockerfile_output_file}")

    # ========= Generate docker-compose file============
    docker_compose_output_file = os.path.join(gen_path, "docker-compose.yml")
    docker_compose_content = docker_compose_template.render(
        websocket=model.processed_websocket, api=model.processed_api
    )
    with open(docker_compose_output_file, "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    print(f"Generated: {docker_compose_output_file}")

    return gen_path


def map_attribute_class_names_to_types(attribute):
    """
    Maps the class names of the attributes to their types.
    """

    attribute_types = {
        "IntAttribute": "int",
        "FloatAttribute": "float",
        "BoolAttribute": "bool",
        "StringAttribute": "string",
        "ListAttribute": "list",
        "DictAttribute": "dict",
    }
    if attribute.__class__.__name__ not in attribute_types:
        raise ValueError(f"Unsupported attribute type: {attribute.__class__.__name__}")
    return attribute_types[attribute.__class__.__name__]


# @generator("web_dsl","Application")
