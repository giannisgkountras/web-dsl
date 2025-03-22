import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from .language import build_model

# Set up the Jinja2 environment and load templates
frontend_env = Environment(
    loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates/frontend"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)
backend_env = Environment(
    loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates/backend"),
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
live_component_template = frontend_env.get_template("live_component.jinja")
custom_line_chart_template = frontend_env.get_template(
    "components/line_chart_template.jinja"
)
logs_template = frontend_env.get_template("components/logs_template.jinja")

config_template = backend_env.get_template("config_template.jinja")
dockerfile_template = backend_env.get_template("dockerfile_template.jinja")

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

    # Gather all live copmonents from the model
    live_components = set()
    for screen in model.screens:
        for element in screen.elements:
            collect_live_components(element, live_components)
    live_components = list(live_components)

    # ========= Generate frontend files============
    # Prepare the output directories
    screens_dir = os.path.join(gen_path, "frontend", "src", "screens")
    if os.path.exists(screens_dir):
        subprocess.run(["rm", "-rf", screens_dir])
    os.makedirs(screens_dir, exist_ok=True)

    # Generate the screen components
    for screen in model.screens:
        html_content = screen_template.render(screen=screen)
        output_file = os.path.join(screens_dir, f"{screen.name}.jsx")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated: {output_file}")

    # Generate additional files like App.jsx and index.html
    app_content = app_template.render(webpage=model, screens=model.screens)
    app_output_file = os.path.join(gen_path, "frontend", "src", "App.jsx")
    with open(app_output_file, "w", encoding="utf-8") as f:
        f.write(app_content)
    print(f"Generated: {app_output_file}")

    index_html_content = index_html_template.render(webpage=model)
    index_html_output_file = os.path.join(gen_path, "frontend", "index.html")
    with open(index_html_output_file, "w", encoding="utf-8") as f:
        f.write(index_html_content)
    print(f"Generated: {index_html_output_file}")

    # Generate websocket context config file
    websocket_context_config_content = websocket_context_config_template.render(
        websocket=model.websocket
    )
    websocket_context_config_output_file = os.path.join(
        gen_path, "frontend", "src", "context", "websocketConfig.json"
    )
    with open(websocket_context_config_output_file, "w", encoding="utf-8") as f:
        f.write(websocket_context_config_content)
    print(f"Generated: {websocket_context_config_output_file}")

    # Generate component files
    components_dir = os.path.join(gen_path, "frontend", "src", "components")

    for component in live_components:
        # CustomLineChart component
        if component.definition.__class__.__name__ == "LineChart":
            custom_line_chart_output_file = os.path.join(
                components_dir, "CustomLineChart.jsx"
            )
            with open(custom_line_chart_output_file, "w", encoding="utf-8") as f:
                f.write(
                    custom_line_chart_template.render(
                        element=component, chart=component.definition
                    )
                )
            print(f"Generated: {custom_line_chart_output_file}")

        # Logs component
        if component.definition.__class__.__name__ == "Logs":
            logs_output_file = os.path.join(components_dir, "Logs.jsx")
            with open(logs_output_file, "w", encoding="utf-8") as f:
                f.write(
                    logs_template.render(element=component, logs=component.definition)
                )
            print(f"Generated: {logs_output_file}")

    # ========= Generate backend files============

    # Gather all topics from the model
    topic_configs = []
    for component in live_components:
        topic_configs.append(
            {
                "topic": component.topic,
                "broker": component.entity.source.ref.name,
            }
        )
    print("Topic Configs: ", topic_configs)
    # Collect all brokers
    all_brokers = set()
    for broker in model.brokers:
        all_brokers.add(broker)
    all_brokers = list(all_brokers)

    config_dir = os.path.join(gen_path, "backend")
    config_output_file = os.path.join(config_dir, "config.yaml")
    config_content = config_template.render(
        brokers=all_brokers, websocket=model.websocket, topic_configs=topic_configs
    )
    with open(config_output_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Generated: {config_output_file}")

    dockerfile_output_file = os.path.join(gen_path, "backend", "Dockerfile")
    dockerfile_content = dockerfile_template.render(websocket=model.websocket)
    with open(dockerfile_output_file, "w", encoding="utf-8") as f:
        f.write(dockerfile_content)
    print(f"Generated: {dockerfile_output_file}")

    # ========= Generate docker-compose file============
    docker_compose_output_file = os.path.join(gen_path, "docker-compose.yml")
    docker_compose_content = docker_compose_template.render(websocket=model.websocket)
    with open(docker_compose_output_file, "w", encoding="utf-8") as f:
        f.write(docker_compose_content)
    print(f"Generated: {docker_compose_output_file}")

    return gen_path


def collect_live_components(node, live_components):
    """
    Recursively collect LiveComponent nodes into a list.

    Args:
        node: A node in the parsed tree.
        live_components: A list to store LiveComponent nodes.
    """
    # Get the class name of the node
    node_type = node.__class__.__name__

    # Handle LiveComponent nodes
    if node_type == "LiveComponent":
        live_components.add(node)

    # Handle ReusableComponent nodes
    elif node_type == "ReusableComponent":
        referenced_component = node.ref.definition  # Resolve the reference
        if referenced_component.__class__.__name__ == "LiveComponent":
            live_components.add(referenced_component)

    # Handle structural nodes like Row or Column
    elif node_type in ("Row", "Column"):
        for element in node.elements:
            collect_live_components(element, live_components)


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
