from goal_dsl.language import (
    build_model as goal_build_model,
    get_model_entities as goal_get_model_entities,
)
from jinja2 import Environment, FileSystemLoader
from textx.model import get_children_of_type
from web_dsl.definitions import TEMPLATES_PATH


env = Environment(
    loader=FileSystemLoader(f"{TEMPLATES_PATH}/transformations"),
    trim_blocks=True,
    lstrip_blocks=True,
    extensions=["jinja2.ext.loopcontrols"],
)
template = env.get_template("goaldsl_to_webdsl.jinja")

attribute_class_name_to_webdsl = {
    "FloatAttribute": "float",
    "IntAttribute": "int",
    "StringAttribute": "str",
    "BoolAttribute": "bool",
    "ListAttribute": "list",
    "DictAttribute": "dict",
}


def transform_goaldsl_to_webdsl(goaldsl_content):
    """
    Transforms GOAL DSL content to WebDSL content.

    Args:
        goaldsl_content (str): The GOAL DSL content to be transformed.

    Returns:
        str: The transformed WebDSL content.
    """
    # Build the GOAL DSL model
    goal_model = goal_build_model(goaldsl_content)

    # Extract entities from the GOAL DSL model
    all_goal_entities = goal_get_model_entities(goal_model)
    # Process the attribute types
    for entity in all_goal_entities:
        for attr in entity.attributes:
            attr_type = attribute_class_name_to_webdsl.get(
                attr.__class__.__name__, "str"
            )
            # add the attribute type to the attribute
            attr.webdsl_type = attr_type

    # Extract all brokers from the GOAL DSL model
    all_goal_mqtt_brokers = get_children_of_type("MQTTBroker", goal_model)
    all_goal_amqp_brokers = get_children_of_type("AMQPBroker", goal_model)
    all_goal_redis_brokers = get_children_of_type("RedisBroker", goal_model)

    # Extract all rest endpoints from the GOAL DSL model
    all_goal_rest_endpoints = get_children_of_type("RESTEndpoint", goal_model)
    for endpoint in all_goal_rest_endpoints:
        if getattr(endpoint, "base_url", None) is not None:
            endpoint.webdsl_path = endpoint.base_url + endpoint.path
        else:
            endpoint.webdsl_path = endpoint.path

    return template.render(
        entities=all_goal_entities,
        mqtt_brokers=all_goal_mqtt_brokers,
        amqp_brokers=all_goal_amqp_brokers,
        redis_brokers=all_goal_redis_brokers,
        rest_endpoints=all_goal_rest_endpoints,
    )
