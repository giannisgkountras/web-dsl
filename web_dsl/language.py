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
    CrudTable,
    BarChart,
    PieChart,
    Input,
    Label,
    Form,
)

from .lib.condition import Condition

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
    CrudTable,
    Condition,
    BarChart,
    PieChart,
    Input,
    Label,
    Form,
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
            "CrudTable.attributes": component_entity_attributes_scope,
        }
    )

    return metamodel


# def set_defaults(model):
#     pass


def validate_model(model):
    """Validates the model."""
    all_entities = get_children_of_type("Entity", model)
    strict_entities = strict_entities = [e for e in all_entities if e.strict]

    all_components = get_children_of_type("Component", model)
    components_referencing_strict_entities = [
        c for c in all_components if c.entity and c.entity in strict_entities
    ]

    errors = validate_components_with_strict_entities(
        components_referencing_strict_entities
    )
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f" - {error}")
        raise TextXSemanticError(f"Model validation failed with {len(errors)} errors.")


def validate_components_with_strict_entities(components):
    errors = []
    for component in components:
        if not hasattr(component, "entity") or not component.entity:
            continue

        if not getattr(component.entity, "strict", False):
            continue

        # Collect all formatted attribute paths from the component type
        attribute_paths = []

        # Find all attributes that look like formatted paths (lists of mixed str/int)
        for attr_name in dir(component.type):
            if attr_name.startswith("_"):
                continue
            attr = getattr(component.type, attr_name)
            if isinstance(attr, list) and all(isinstance(p, (int, str)) for p in attr):
                attribute_paths.append(attr)
            elif isinstance(attr, list) and all(
                isinstance(p, list) and all(isinstance(e, (int, str)) for e in p)
                for p in attr
            ):
                # This handles lists of paths, like yValues = [[0, 'temp'], [0, 'pressure']]
                attribute_paths.extend(attr)

        strict_entity_attributes = component.entity.attributes
        strict_entity_attributes_names = [a.name for a in strict_entity_attributes]

        for attribute in attribute_paths:
            if not attribute:  # skip empty lists
                continue
            attribute_root = attribute[0]

            if attribute_root not in strict_entity_attributes_names:
                errors.append(
                    f"Component '{component.name}' uses attribute '{attribute_root}' not allowed by strict entity '{component.entity.name}'"
                )
                continue
    return errors


def build_model(model_path: str):
    """Builds a model from a DSL file."""
    print(f"Attempting to build model from: {model_path}")
    # Get the metamodel with the model processor registered
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)
    # set_defaults(model)  # Set default values for the model
    validate_model(model)  # Validate
    return model  # Return the built model
