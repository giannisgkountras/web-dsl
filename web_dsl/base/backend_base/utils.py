import yaml
import os


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
