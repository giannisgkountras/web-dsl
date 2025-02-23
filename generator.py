from textx import metamodel_from_file
from jinja2 import Environment, FileSystemLoader

base_path = "./web-dsl/"
# Load the grammar
webpage_mm = metamodel_from_file(base_path + "grammar/syntax/screens.tx", debug=False)

# Set up Jinja environment
env = Environment(loader=FileSystemLoader(base_path + "templates"))
template = env.get_template("screen_template.jinja")

# Read and parse the model
try:
    with open(base_path + "grammar/examples/test.dsl", "r", encoding="utf-8") as f:
        model = webpage_mm.model_from_str(f.read())

    # Generate HTML for each screen
    for screen in model.screens:
        html_content = template.render(screen=screen)

        # Create output filename (e.g.: "MainScreen.html")
        output_file = f"generated/{screen.name}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Generated: {output_file}")

except Exception as e:
    print(f"Error: {e}")
