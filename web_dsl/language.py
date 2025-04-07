# --- Imports ---
from textx import (
    metamodel_from_file,
    TextXSemanticError,
    get_metamodel,
    get_children_of_type,
)
from os.path import join, dirname
from .lib.component import (
    Component,
    ComponentType,
    Gauge,
    Notification,
    Image,
    Alive,
    LineChart,
    Publish,
    LiveTable,
    JsonViewer,
    Text,
)

# Map grammar rules to Python classes
custom_classes = [
    Component,
    ComponentType,
    Gauge,
    Notification,
    Image,
    Alive,
    LineChart,
    Publish,
    LiveTable,
    JsonViewer,
    Text,
    # Add other classes here
]


THIS_DIR = dirname(__file__)


def resolve_references_post_build(model, metamodel):
    # Get all components
    all_components = get_children_of_type("Component", model)
    for component in all_components:
        # Set parent for type object if it exists
        if hasattr(component, "type") and component.type:
            component.type.parent = component

            # Resolve references for the type (e.g., Gauge)
            if hasattr(component.type, "resolve_references"):
                component.type.resolve_references()


def get_metamodel(debug: bool = False, global_repo: bool = True):
    """Creates and configures the textX metamodel."""
    grammar_path = join(THIS_DIR, "grammar", "webpage.tx")  # Adjust path if needed
    print(f"Loading grammar from: {grammar_path}")

    metamodel = metamodel_from_file(
        grammar_path,
        auto_init_attributes=True,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
        classes=custom_classes,
    )
    # Register the reference resolver
    metamodel.register_model_processor(resolve_references_post_build)
    return metamodel


# def set_defaults(model):
#     pass


# def validate_screen(screen):
#     pass


# def validate_model(model):
#     for screen in model.screens:
#         validate_screen(screen)


def build_model(model_path: str):
    """Builds a model from a DSL file."""
    print(f"Attempting to build model from: {model_path}")
    # Get the metamodel with the model processor registered
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)
    # set_defaults(model)  # Set default values for the model
    # validate_model(model)  # Validate
    return model  # Return the built model
