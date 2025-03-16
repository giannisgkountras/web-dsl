import os
import subprocess
from jinja2 import Environment, FileSystemLoader
from .language import build_model

# Set up the Jinja2 environment and load templates
frontend_env = Environment(
    loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates/frontend"),
    trim_blocks=True,
    lstrip_blocks=True,
)
backend_env = Environment(
    loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates/backend"),
    trim_blocks=True,
    lstrip_blocks=True,
)

frontend_base_dir = os.path.join(os.path.dirname(__file__), "frontend_base")
backend_base_dir = os.path.join(os.path.dirname(__file__), "backend_base")

screen_template = frontend_env.get_template("screen_template_react.jinja")
app_template = frontend_env.get_template("app_template_react.jinja")
index_html_template = frontend_env.get_template("index_html_template.jinja")
websocket_context_config_template = frontend_env.get_template(
    "websocket_context_config.jinja"
)

config_template = backend_env.get_template("config_template.jinja")


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

    # ========= Generate backend files============
    # Gather all topics from the model
    all_topics = set()
    for screen in model.screens:
        for element in screen.elements:
            collect_topics(element, all_topics)
    all_topics = list(all_topics)
    print(f"Found topics: {all_topics}")

    config_dir = os.path.join(gen_path, "backend")
    config_output_file = os.path.join(config_dir, "config.yaml")
    config_content = config_template.render(
        broker=model.broker, websocket=model.websocket, topics=all_topics
    )
    with open(config_output_file, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Generated: {config_output_file}")
    return gen_path


def collect_topics(node, topics_set):
    """
    Recursively collect topics from LiveComponent nodes into a set.

    Args:
        node: A node in the parsed tree.
        topics_set: A set to store unique topic strings.
    """
    # Get the class name of the node
    node_type = node.__class__.__name__

    # Handle LiveComponent nodes
    if node_type == "LiveComponent":
        topics_set.add(node.topic)

    # Handle ReusableComponent nodes
    elif node_type == "ReusableComponent":
        referenced_component = node.ref.definition  # Resolve the reference
        if referenced_component.__class__.__name__ == "LiveComponent":
            topics_set.add(referenced_component.topic)

    # Handle structural nodes like Row or Column
    elif node_type in ("Row", "Column"):
        for element in node.elements:
            collect_topics(element, topics_set)
