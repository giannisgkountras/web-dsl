from textx import metamodel_from_file
from jinja2 import Environment, FileSystemLoader
import subprocess

base_path = "./web-dsl"
generated_path = "./generated/frontend"
# Load the grammar
webpage_mm = metamodel_from_file(f"{base_path}/grammar/syntax/screens.tx", debug=False)

# Set up Jinja environment
env = Environment(loader=FileSystemLoader(f"{base_path}/templates"))
screen_template = env.get_template("screen_template_react.jinja")
app_template = env.get_template("app_template_react.jinja")
index_html_template = env.get_template("index_html_template.jinja")
# Read and parse the model
try:
    with open(f"{base_path}/grammar/examples/test.dsl", "r", encoding="utf-8") as f:
        model = webpage_mm.model_from_str(f.read())

    # Clear the directory before generating the files
    subprocess.run(["rm", "-rf", f"{generated_path}/src/screens"])
    subprocess.run(["mkdir", "-p", f"{generated_path}/src/screens"])

    # Generate JSX for each screen
    for screen in model.screens:
        html_content = screen_template.render(screen=screen)

        # Create output filename (e.g.: "MainScreen.jsx")
        output_file = f"{generated_path}/src/screens/{screen.name}.jsx"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated: {output_file}")

    # Generate the App.jsx file that contains links to all pages
    app_content = app_template.render(screens=model.screens)
    app_output_file = f"{generated_path}/src/App.jsx"
    with open(app_output_file, "w", encoding="utf-8") as f:
        f.write(app_content)
    print(f"Generated: {app_output_file}")

    # Generate the index.html file for the app
    index_html_content = index_html_template.render(webpage=model)
    index_html_output_file = f"{generated_path}/index.html"
    with open(index_html_output_file, "w", encoding="utf-8") as f:
        f.write(index_html_content)
    print(f"Generated: {index_html_output_file}")

    # Format the generated files
    print("Formatting the generated files...")
    subprocess.run(["npx", "prettier", "--write", f"{generated_path}/*/*.jsx"])

except Exception as e:
    print(f"Error: {e}")
