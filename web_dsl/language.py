from textx import metamodel_from_file
from os.path import join
from web_dsl.definitions import THIS_DIR


def set_defaults(model):
    pass


def validate_screen(screen):
    pass


def validate_model(model):
    for screen in model.screens:
        validate_screen(screen)


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
    set_defaults(model)  # Set default values for the model
    validate_model(model)  # Validate
    return model  # Return the built model


# Run the file locally to test the function
if __name__ == "__main__":
    model = build_model("web_dsl/examples/test.wdsl")
    print(model)
