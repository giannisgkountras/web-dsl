import os
import subprocess
import glob
from textx import metamodel_from_file
from jinja2 import Environment, FileSystemLoader
from .language import build_model

# Set up the Jinja2 environment and load templates
env = Environment(
    loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)

screen_template = env.get_template("screen_template_react.jinja")
app_template = env.get_template("app_template_react.jinja")
index_html_template = env.get_template("index_html_template.jinja")

frontend_base_dir = os.path.join(os.path.dirname(__file__), "frontend_base")


def generate_frontend(model_path, gen_path):
    # Read and parse the DSL model
    print(f"Reading model from: {model_path}")
    model = build_model(model_path)

    # Copy the base frontend project contents to the output directory
    print(f"Copying frontend base contents to: {gen_path}")
    subprocess.run(["cp", "-r", f"{frontend_base_dir}/.", gen_path])

    # Prepare the output directories
    screens_dir = os.path.join(gen_path, "src", "screens")
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
    app_output_file = os.path.join(gen_path, "src", "App.jsx")
    with open(app_output_file, "w", encoding="utf-8") as f:
        f.write(app_content)
    print(f"Generated: {app_output_file}")

    index_html_content = index_html_template.render(webpage=model)
    index_html_output_file = os.path.join(gen_path, "index.html")
    with open(index_html_output_file, "w", encoding="utf-8") as f:
        f.write(index_html_content)
    print(f"Generated: {index_html_output_file}")

    # Optionally run Prettier to format the generated files

    # DOCKER DOES NOT HAVE NPM INSTALLED

    # print("Formatting the generated files...")
    # jsx_files = glob.glob(os.path.join(gen_path, "**", "*.jsx"), recursive=True)
    # if jsx_files:
    #     subprocess.run(["npx", "prettier", "--write", *jsx_files])
    # else:
    #     print("No .jsx files found to format.")

    return gen_path
