from textx import metamodel_from_file
from jinja2 import Environment, FileSystemLoader
import subprocess

base_path = "./web-dsl/"
# Load the grammar
webpage_mm = metamodel_from_file(base_path + "grammar/syntax/screens.tx", debug=False)

# Set up Jinja environment
env = Environment(loader=FileSystemLoader(base_path + "templates"))
template = env.get_template("screen_template_react.jinja")

# Read and parse the model
try:
    with open(base_path + "grammar/examples/test.dsl", "r", encoding="utf-8") as f:
        model = webpage_mm.model_from_str(f.read())

    # Generate JSX for each screen
    for screen in model.screens:
        html_content = template.render(screen=screen)

        # Create output filename (e.g.: "MainScreen.jsx")
        output_file = f"generated/react/{screen.name}.jsx"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated: {output_file}")

    # Format the generated files
    print("Formatting the generated files...")
    subprocess.run(["npx", "prettier", "--write", "generated/react/*.jsx"])

except Exception as e:
    print(f"Error: {e}")
