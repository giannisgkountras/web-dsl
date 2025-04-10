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
    Logs,
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
    Logs,
    # Add other classes here
]


THIS_DIR = dirname(__file__)


def component_entity_attributes_scope(obj, attr, attr_ref):
    component = obj.parent  # obj is ComponentType (e.g., Gauge), parent is Component
    # attr is the attribute of the component (e.g., value)
    # attr_ref is the reference to the attribute

    if component and hasattr(component, "entity") and component.entity:
        entity = component.entity
        entity_attributes = entity.attributes
        entity_attributes_names = [a.name for a in entity_attributes]

        # Check if the attribute reference is valid
        if attr_ref.obj_name not in entity_attributes_names:
            raise TextXSemanticError(
                f"Attribute '{attr_ref.obj_name}' not found in entity '{entity.name}'"
            )
        # Find the matching attribute
        matching_attribute = next(
            (a for a in entity_attributes if a.name == attr_ref.obj_name), None
        )
        if not matching_attribute:
            raise TextXSemanticError(
                f"No attribute '{attr_ref.obj_name}' found in entity '{entity.name}'"
            )
        return matching_attribute
    else:
        raise TextXSemanticError("Component has no entity defined")


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

    metamodel.register_scope_providers(
        {
            "Gauge.value": component_entity_attributes_scope,
            "Text.content": component_entity_attributes_scope,
            "Notification.message": component_entity_attributes_scope,
            "LineChart.xValue": component_entity_attributes_scope,
            "LineChart.yValues": component_entity_attributes_scope,
            "LiveTable.columns": component_entity_attributes_scope,
            "JsonViewer.attributes": component_entity_attributes_scope,
            "Logs.attributes": component_entity_attributes_scope,
            "Image.source": component_entity_attributes_scope,
        }
    )

    return metamodel


# def set_defaults(model):
#     pass


# def validate_model(model):
#     """Validates the model."""
#     pass
# Check for duplicate attribute names in global entities
# Add more validation logic as needed
# For example, check for required attributes, etc.


def build_model(model_path: str):
    """Builds a model from a DSL file."""
    print(f"Attempting to build model from: {model_path}")
    # Get the metamodel with the model processor registered
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)
    # set_defaults(model)  # Set default values for the model
    # validate_model(model)  # Validate
    return model  # Return the built model
