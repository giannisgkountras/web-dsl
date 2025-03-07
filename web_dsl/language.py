from textx import metamodel_from_file
from os.path import join
from .definitions import THIS_DIR, MODEL_REPO_PATH, BUILTIN_MODELS


def get_metamodel(debug: bool = False, global_repo: bool = True):
    metamodel = metamodel_from_file(
        join(THIS_DIR, "grammar", "webpage.tx"),
        auto_init_attributes=True,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
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
    return model  # Return the built model
