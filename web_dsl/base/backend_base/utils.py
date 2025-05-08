import yaml
import os
from bson import ObjectId


def load_config(config_path="config.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as file:
        return yaml.safe_load(file)


def load_endpoint_config(config_path="endpoint_config.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as file:
        return yaml.safe_load(file)


def load_db_config(config_path="db_config.yaml"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, config_path)
    with open(full_path, "r") as file:
        return yaml.safe_load(file)


def convert_object_ids(documents):
    """Recursively convert ObjectId to str in dicts or lists."""
    if isinstance(documents, list):
        return [convert_object_ids(doc) for doc in documents]
    elif isinstance(documents, dict):
        return {key: convert_object_ids(value) for key, value in documents.items()}
    elif isinstance(documents, ObjectId):
        return str(documents)
    else:
        return documents


def transform_list_of_dicts_to_dict_of_lists(data):
    """
    Transforms a list of dictionaries into a dictionary of lists.
    Example:
        Input: [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        Output: {"a": [1, 3], "b": [2, 4]}
    """
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return {key: [row[key] for row in data] for key in data[0].keys()}
    return data  # fallback if not a list of dicts
