# --- Imports ---
from textx import metamodel_from_file, TextXSemanticError, get_metamodel, language
from textx.model import get_children_of_type
from textx.scoping.providers import FQNImportURI
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
    Table,
    BarChart,
    PieChart,
    Input,
    Label,
    Form,
    ProgressBar,
)

from .lib.condition import Condition
from .lib.repetition import Repetition
from .lib.entity import Entity
from .lib.computed import ComputedAttribute, Atom
from .validate import validate_model

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
    Table,
    Condition,
    BarChart,
    PieChart,
    Input,
    Label,
    Form,
    Repetition,
    ProgressBar,
    Entity,
    ComputedAttribute,
    Atom,
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
    grammar_path = join(THIS_DIR, "grammar", "web_dsl.tx")  # Adjust path if needed
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
            # "Gauge.value": component_entity_attributes_scope,
            "Component.entity": FQNImportURI(),
            "ComponentRef.ref": FQNImportURI(),
            "Entity.source": FQNImportURI(),
            "NestedAccessPathEntity.entity": FQNImportURI(),
            "Publish.broker": FQNImportURI(),
            "Publish.endpoint": FQNImportURI(),
            "Condition.component": FQNImportURI(),
            "Condition.componentElse": FQNImportURI(),
            "ElseClause.componentElse": FQNImportURI(),
            "Repetition.compoonentRef": FQNImportURI(),
            "Repetition.componentElseRef": FQNImportURI(),
            "MySQLQuery.connection": FQNImportURI(),
            "MongoDBQuery.connection": FQNImportURI(),
            "RESTEndpoint.connection": FQNImportURI(),
            "BrokerTopic.connection": FQNImportURI(),
            "Entity.overloads": FQNImportURI(),
            "WebPage.navbar_screens": FQNImportURI(),
        }
    )

    metamodel.register_model_processor(model_proc)

    return metamodel


# def set_defaults(model):
#     pass


def build_model(model_path: str):
    """Builds a model from a DSL file."""
    print(f"Attempting to build model from: {model_path}")
    # Get the metamodel with the model processor registered
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)

    # set_defaults(model)  # Set default values for the model
    validate_model(model, model_path)  # Validate

    return model  # Return the built model


def get_model_webpage(model):
    webpage = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            webpage += get_children_of_type("WebPage", m)
    else:
        webpage = get_children_of_type("WebPage", model)
    return webpage[0] if webpage else None


def get_model_entities(model):
    entities = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            entities += get_children_of_type("Entity", m)
    else:
        entities = get_children_of_type("Entity", model)
    return entities


def get_model_components(model):
    components = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:

            components += get_children_of_type("Component", m)
    else:
        components = get_children_of_type("Component", model)

    return components


def get_model_screens(model):
    screens = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:

        for m in model._tx_model_repository.all_models:
            screens += get_children_of_type("Screen", m)
    else:
        screens = get_children_of_type("Screen", model)
    for screen in screens:
        for role in screen.allowed_roles:
            print(role.name)
    return screens


def get_model_brokers(model):
    brokers = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            brokers += get_children_of_type("MQTTBroker", m)
            brokers += get_children_of_type("AMQPBroker", m)
            brokers += get_children_of_type("RedisBroker", m)
    else:
        brokers += get_children_of_type("MQTTBroker", model)
        brokers += get_children_of_type("AMQPBroker", model)
        brokers += get_children_of_type("RedisBroker", model)
    return brokers


def get_model_brokertopics(model):
    brokertopics = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            brokertopics += get_children_of_type("BrokerTopic", m)
    else:
        brokertopics = get_children_of_type("BrokerTopic", model)
    return brokertopics


def get_model_databases(model):
    databases = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            databases += get_children_of_type("MySQL", m)
            databases += get_children_of_type("MongoDB", m)
    else:
        databases += get_children_of_type("MySQL", model)
        databases += get_children_of_type("MongoDB", model)
    return databases


def get_model_mysqlqueries(model):
    dbqueries = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            dbqueries += get_children_of_type("MySQLQuery", m)
    else:
        dbqueries += get_children_of_type("MySQLQuery", model)
    return dbqueries


def get_model_mongodbqueries(model):
    dbqueries = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            dbqueries += get_children_of_type("MongoDBQuery", m)
    else:
        dbqueries += get_children_of_type("MongoDBQuery", model)
    return dbqueries


def get_model_restapis(model):
    restapis = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            restapis += get_children_of_type("RESTApi", m)
    else:
        restapis = get_children_of_type("RESTApi", model)
    return restapis


def get_model_endpoints(model):
    endpoints = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            endpoints += get_children_of_type("RESTEndpoint", m)
    else:
        endpoints = get_children_of_type("RESTEndpoint", model)
    return endpoints


def get_model_api(model):
    api = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            api += get_children_of_type("API", m)
    else:
        api = get_children_of_type("API", model)
    return api[0] if api else None


def get_model_websocket(model):
    websocket = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            websocket += get_children_of_type("Websocket", m)
    else:
        websocket = get_children_of_type("Websocket", model)
    return websocket[0] if websocket else None


def get_model_repetitions(model):
    repetitions = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            repetitions += get_children_of_type("Repetition", m)
    else:
        repetitions = get_children_of_type("Repetition", model)
    return repetitions


def get_model_conditions(model):
    conditions = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            conditions += get_children_of_type("Condition", m)
    else:
        conditions = get_children_of_type("Condition", model)
    return conditions


def model_proc(model, metamodel):
    """
    Processes the main model and augments it with aggregated elements
    from all imported models.
    'model' is the instance of the root rule (e.g., 'Model') for the main file.
    """
    print("Running model processor...")

    # Use your existing get_model_X functions which correctly iterate
    # through model._tx_model_repository.all_models
    model.aggregated_screens = get_model_screens(model)
    model.aggregated_entities = get_model_entities(model)
    model.aggregated_reusable_components = get_model_components(model)
    model.aggregated_brokers = get_model_brokers(model)
    model.aggregated_databases = get_model_databases(model)
    model.aggregated_restapis = get_model_restapis(model)
    model.aggregated_endpoints = get_model_endpoints(model)
    model.aggregated_mysqlqueries = get_model_mysqlqueries(model)
    model.aggregated_mongodbqueries = get_model_mongodbqueries(model)
    model.aggregated_brokertopics = get_model_brokertopics(model)
    model.processed_webpage = get_model_webpage(model)
    model.processed_api = get_model_api(model)
    model.processed_websocket = get_model_websocket(model)

    # Resolve overloads
    resolve_entity_overloads(model)

    # Finilize all repetitions with the new entities
    # This is needed due to the need for formatted paths
    # with base being the entity name
    all_repetitions = get_model_repetitions(model)
    for rep in all_repetitions:
        try:
            finalize_repetition(rep)
        except Exception as e:
            print(f"Error finalizing repetition: {e}")

    # Finilize all conditions with the new entities
    # This is needed due to the need for formatted paths
    # with base being the entity name
    all_conditions = get_model_conditions(model)
    for cond in all_conditions:
        try:
            finalize_condition(cond)
        except Exception as e:
            print(f"Error finalizing condition: {e}")


def resolve_entity_overloads(model):
    overload_map = {}
    all_entities = get_model_entities(model)
    for entity in all_entities:
        if hasattr(entity, "overloads") and entity.overloads:
            overload_map[entity.overloads] = entity

    print("Overload map:")
    for k, v in overload_map.items():
        print(f"{k.name} -> {v.name}")

    print("Patching references...")
    patch_references(model, overload_map)


def patch_references(obj, overload_map, visited=None):
    if visited is None:
        visited = set()

    obj_id = id(obj)
    if obj_id in visited:
        return
    visited.add(obj_id)

    if isinstance(obj, list):
        for i, item in enumerate(obj):
            try:
                if item in overload_map:
                    obj[i] = overload_map[item]
                    print(f"Patched reference: {obj[i]} -> {overload_map[item].name}")
                else:
                    patch_references(item, overload_map, visited)
            except TypeError:
                patch_references(item, overload_map, visited)

    elif hasattr(obj, "__dict__"):
        for attr in dir(obj):
            if attr.startswith("_"):
                continue
            try:
                value = getattr(obj, attr)
            except Exception:
                continue  # Skip inaccessible attributes

            if isinstance(value, (str, int, float, bool, type(None))):
                continue

            try:
                if value in overload_map and value is not overload_map[value]:
                    print(f"Patched reference: {obj} -> {overload_map[value]}")
                    setattr(obj, attr, overload_map[value])
                else:
                    patch_references(value, overload_map, visited)
            except TypeError:
                patch_references(value, overload_map, visited)


def finalize_repetition(rep):
    """
    Finalizes the repetition component by setting its attributes to formatted paths
    """
    rep.entities = set()
    rep.item = rep.format_attribute_path(rep.raw_item)
    rep.data = rep.format_attribute_path(rep.raw_data) if rep.raw_data else None
    rep.dataElse = (
        rep.format_attribute_path(rep.raw_dataElse) if rep.raw_dataElse else None
    )
    rep.condition = rep.format_condition(rep.raw_expr) or "true"
    rep.entities_list = list(rep.entities)


def finalize_condition(cond):
    """
    Finalizes the condition component by setting its attributes to formatted paths
    """
    cond.entities = set()
    cond.condition = cond.format_condition(cond.raw_condition) or "true"
    cond.entities_list = list(cond.entities)


@language("web_dsl", "*.wdsl")
def web_dsl_language():
    """
    DSL for building web applications.
    """
    return get_metamodel()


def get_model_grammar(model_path):
    mm = get_metamodel()
    grammar_model = mm.grammar_model_from_file(model_path)
    return grammar_model
