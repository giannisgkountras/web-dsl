from textx import metamodel_from_file
from os.path import join
from web_dsl.definitions import THIS_DIR


def set_defaults(model):
    pass


def validate_screen(screen):
    for component in getattr(screen, "components", []):
        entity = component.entity
        type_obj = component.type

        if hasattr(type_obj, "value"):
            attr = type_obj.value
            if attr not in entity.attributes:
                raise Exception(
                    f"Component '{component.name}' uses attribute '{attr.name}' "
                    f"from entity '{attr._tx_parent.name}', but 'refersTo:' is '{entity.name}'"
                )


def validate_model(model):
    for screen in model.screens:
        validate_screen(screen)


def get_metamodel(debug: bool = True, global_repo: bool = True):
    metamodel = metamodel_from_file(
        join(THIS_DIR, "grammar", "webpage.tx"),
        auto_init_attributes=True,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
    )
    metamodel.register_obj_processors({"Component": component_processor})
    metamodel.register_scope_providers(
        {
            "Gauge.value": component_value_scope,
            # Add other scope providers if needed
        }
    )

    return metamodel


def build_model(model_path: str):
    """
    This function builds a model from a given language file.

    Parameters:
    model_path (str): The path to the language file.

    Returns:
    model: The built model object representing the language.
    """
    mm = get_metamodel(debug=False)  # Get the metamodel for the language

    model = mm.model_from_file(model_path)  # Parse the model from the file
    set_defaults(model)  # Set default values for the model
    validate_model(model)  # Validate
    return model  # Return the built model


def component_processor(component):
    # Set a reference to the component on its type object (e.g., Gauge)
    if hasattr(component.type, "value"):
        # KAI OSA ALLA XREIAZONTAI AFTO EINAIGIA TO GAUGE
        component.type._component = component


def component_value_scope(obj, attr, attr_ref):
    print(f"Resolving value for {obj.__class__.__name__}, attr_ref: {attr_ref}")
    if hasattr(obj, "_component"):
        component = obj._component
        print(f"Found _component: {component.name}")
    else:
        raise AttributeError(
            f"'{obj.__class__.__name__}' object has no attribute '_component'"
        )
    entity = component.entity
    return entity.attributes
