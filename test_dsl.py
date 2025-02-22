from textx import metamodel_from_file

base_path = "./web-dsl/grammar/"
# Load the grammar
webpage_mm = metamodel_from_file(base_path + "syntax/screens.tx", debug=False)

# Read the example file
with open(base_path + "examples/test.dsl", "r", encoding="utf-8") as f:
    dsl_text = f.read()

# Parse the model
try:
    model = webpage_mm.model_from_str(dsl_text)

    # Print parsed structure
    for screen in model.screens:
        print(f"\nScreen: {screen.name} (URL: {screen.url})")
        print(f"Title: {screen.title}")
        if screen.description:
            print(f"Description: {screen.description}")

        def print_structure(elements, indent=2):
            for element in elements:
                print(" " * indent + f"- {element.__class__.__name__}")
                if hasattr(element, "elements"):
                    print_structure(element.elements, indent + 2)

        print_structure(screen.elements)

except Exception as e:
    print(f"Error parsing DSL: {e}")
