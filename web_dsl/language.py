# --- Imports ---
from textx import (
    metamodel_from_file,
    TextXSemanticError,
    get_metamodel,
    get_children_of_type,
)
from textx.scoping import Postponed  # May be needed to check for unresolved refs
from os.path import join, dirname
import logging

# --- Setup (Logging, THIS_DIR) ---
logging.basicConfig(
    level=logging.INFO
)  # INFO level is usually good for production/users
log = logging.getLogger(__name__)

try:
    THIS_DIR = dirname(__file__)
except NameError:
    THIS_DIR = "."


# --- Model Processor ---
def resolve_references_post_build(model, metamodel):
    """
    Model processor to manually resolve specific references like Gauge.value
    after the main model linking is done.
    """

    all_components = get_children_of_type("Component", model)
    errors = []  # Collect errors

    for component in all_components:
        component_name = getattr(component, "name", "<unnamed Component>")
        component_type_obj = getattr(component, "type", None)

        # --- Resolve Gauge.value ---
        if component_type_obj and component_type_obj.__class__.__name__ == "Gauge":
            gauge_obj = component_type_obj

            # Check if 'value' attribute exists and needs resolution
            if hasattr(gauge_obj, "value"):
                current_value = gauge_obj.value
                target_attribute_name = None

                # Check if it's an unresolved reference proxy.
                if hasattr(current_value, "obj_name"):
                    target_attribute_name = current_value.obj_name

                # Handle TextX's internal Postponed reference if default resolution failed
                elif isinstance(current_value, Postponed):
                    target_attribute_name = current_value.obj_name

                if target_attribute_name:
                    # 1. Get the referenced Entity from Component
                    if not hasattr(component, "refersTo") or component.refersTo is None:
                        msg = (
                            f"Component '{component_name}' (containing Gauge) lacks required 'refersTo' "
                            f"Entity reference needed to resolve attribute '{target_attribute_name}'."
                        )
                        log.error(msg)
                        errors.append(TextXSemanticError(msg, obj=component))
                        continue  # Skip this gauge

                    entity = component.refersTo
                    # Handle case where refersTo itself might be unresolved
                    if isinstance(entity, Postponed):
                        msg = (
                            f"Component '{component_name}' has unresolved 'refersTo' reference "
                            f"'{entity.obj_name}'. Cannot resolve Gauge value '{target_attribute_name}'."
                        )
                        log.error(msg)
                        errors.append(TextXSemanticError(msg, obj=component))
                        continue

                    entity_name = getattr(entity, "name", "<unnamed Entity>")
                    log.debug(f"    Component refersTo Entity: '{entity_name}'")

                    # 2. Search for the attribute in the Entity
                    found_attribute = None
                    if hasattr(entity, "attributes"):
                        for attribute in entity.attributes:
                            if (
                                hasattr(attribute, "name")
                                and attribute.name == target_attribute_name
                            ):
                                found_attribute = attribute
                                break
                    else:
                        log.warning(
                            f"    Entity '{entity_name}' has no 'attributes' field defined."
                        )
                        # This might be an error depending on DSL rules

                    # 3. Assign or Record Error
                    if found_attribute:
                        log.debug(
                            f"    Attribute '{target_attribute_name}' found in Entity '{entity_name}'. Assigning to Gauge.value."
                        )
                        gauge_obj.value = found_attribute  # Replace the reference proxy
                    else:
                        msg = (
                            f"Attribute '{target_attribute_name}' (referenced by Gauge in Component "
                            f"'{component_name}') NOT FOUND in Entity '{entity_name}'."
                        )
                        log.error(msg)
                        # Create error referencing the gauge's value attribute position
                        errors.append(
                            TextXSemanticError(
                                msg,
                                obj=(
                                    current_value
                                    if hasattr(current_value, "_tx_position")
                                    else gauge_obj
                                ),
                            )
                        )

                elif current_value is not None:
                    log.debug(
                        f"    Gauge value for Component '{component_name}' seems already resolved or is not a reference ({type(current_value).__name__})."
                    )
            else:
                log.debug(
                    f"    Gauge in component '{component_name}' has no 'value' attribute."
                )
    if errors:
        raise errors[0]


# --- Metamodel Setup ---
def get_metamodel(debug: bool = False, global_repo: bool = True):
    """Creates and configures the textX metamodel."""
    grammar_path = join(THIS_DIR, "grammar", "webpage.tx")  # Adjust path if needed
    log.info(f"Loading grammar from: {grammar_path}")

    scope_providers = {}

    obj_processors = {}

    metamodel = metamodel_from_file(
        grammar_path,
        auto_init_attributes=True,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
    )

    # Register handlers
    metamodel.register_scope_providers(scope_providers)
    metamodel.register_obj_processors(obj_processors)

    # *** Register the Model Processor ***
    metamodel.register_model_processor(resolve_references_post_build)
    return metamodel


# --- Model Building ---
def build_model(model_path: str):
    """Builds a model from a DSL file."""
    log.info(f"Attempting to build model from: {model_path}")
    # Get the metamodel with the model processor registered
    mm = get_metamodel(debug=False)

    try:
        # Parsing, linking (standard), and THEN model processing happens here:
        model = mm.model_from_file(model_path)
        log.info("Model build process completed.")  # Model processor ran if no errors
        return model
    except TextXSemanticError as e:
        # Log semantic errors clearly (might come from parser or model processor)
        line = getattr(e, "line", "N/A")
        col = getattr(e, "col", "N/A")
        log.error(
            f"Semantic Error building model: {e.message} at {model_path}:({line},{col})"
        )
        raise  # Re-raise the exception
    except Exception as e:
        # Log other unexpected errors
        log.exception(f"Unexpected error building model from {model_path}: {e}")
        raise  # Re-raise the exception
