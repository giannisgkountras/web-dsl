import os
import click
from rich.console import Console
from rich import pretty

from web_dsl.language import build_model
from web_dsl.generate import generate
from web_dsl.m2m.openapi_to_webdsl import transform_openapi_to_webdsl
from web_dsl.m2m.goaldsl_to_webdsl import transform_goaldsl_to_webdsl
from web_dsl.m2m.asyncapi_to_webdsl import transform_asyncapi_to_webdsl

pretty.install()
console = Console()

ASCII_HEADER = r"""
 /$$      /$$           /$$       /$$$$$$$   /$$$$$$  /$$      
| $$  /$ | $$          | $$      | $$__  $$ /$$__  $$| $$      
| $$ /$$$| $$  /$$$$$$ | $$$$$$$ | $$  \ $$| $$  \__/| $$      
| $$/$$ $$ $$ /$$__  $$| $$__  $$| $$  | $$|  $$$$$$ | $$      
| $$$$_  $$$$| $$$$$$$$| $$  \ $$| $$  | $$ \____  $$| $$      
| $$$/ \  $$$| $$_____/| $$  | $$| $$  | $$ /$$  \ $$| $$      
| $$/   \  $$|  $$$$$$$| $$$$$$$/| $$$$$$$/|  $$$$$$/| $$$$$$$$
|__/     \__/ \_______/|_______/ |_______/  \______/ |________/
"""


@click.group(
    help=(
        "webdsl: A CLI for validating your DSL model and\n"
        "generating web application boilerplate from it.\n\n"
        "Examples:\n"
        "  webdsl validate path/to/model.wdsl\n"
        "  webdsl generate path/to/model.wdsl [output_dir]\n"
    ),
    invoke_without_command=True,
)
@click.version_option(message="webdsl version %(version)s")
@click.pass_context
def cli(ctx):
    """Main entry point for the webdsl CLI."""
    if ctx.invoked_subcommand is None:
        console.print(ASCII_HEADER, style="cyan")
        console.print("Use [bold]webdsl --help[/bold] to see available commands.\n")


@cli.command(
    "validate",
    help="Validate your model file for syntax and semantic errors.",
    short_help="Validate a .wdsl model",
)
@click.argument(
    "model_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
def validate(model_path):
    """
    Validate a .wdsl model file.

    Examples:
      webdsl validate examples/entity_test.wdsl
    """
    try:
        build_model(model_path)
        console.print("✔ Model is valid.", style="green")
    except Exception as e:
        console.print(f"✖ Validation failed:\n{e}", style="bold red")
        raise SystemExit(1)


@cli.command(
    "generate",
    help="Generate project files from your model.",
    short_help="Generate code from model",
)
@click.argument(
    "model_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_dir",
    required=False,
    default="generated",
    type=click.Path(file_okay=False, writable=True),
)
def generate_command(model_path, output_dir):
    """
    Generate web application boilerplate from your .wdsl model.

    If OUTPUT_DIR is omitted, it defaults to a directory named 'generated'.

    Examples:
      webdsl generate examples/my_model.wdsl
      webdsl generate examples/my_model.wdsl ./my_output_folder
    """
    try:
        output = os.path.abspath(output_dir)

        if os.path.exists(output) and not os.path.isdir(output):
            raise click.ClickException(
                f"Output path '{output}' exists and is not a directory."
            )

        console.print(f"Creating output directory: {output}", style="cyan")
        os.makedirs(output, exist_ok=True)

        console.print(f"Generating from model: {model_path}", style="yellow")
        generate(model_path, output)

        console.print(
            f"✔ Generation complete. Files created at: {output}", style="green"
        )

    except Exception as e:
        console.print(f"✖ Generation error:\n{e}", style="bold red")
        raise SystemExit(1)


@cli.group(help="Transform specifications into WebDSL models.")
def transform():
    pass


@transform.command("openapi", help="Convert OpenAPI spec to WebDSL model.")
@click.argument(
    "openapi_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_file",
    required=False,
    default="generated_model.wdsl",
    type=click.Path(file_okay=True, writable=True),
)
def openapi_command(openapi_path, output_file):
    """
    Convert OpenAPI spec to a webdsl model.

    If OUTPUT_FILE is omitted, it defaults to 'generated_model.wdsl'.

    Examples:
      webdsl openapi examples/openapi_spec.yaml
      webdsl openapi examples/openapi_spec.yaml ./my_model.wdsl
    """
    try:
        output = os.path.abspath(output_file)

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)

        console.print(f"Converting OpenAPI spec: {openapi_path}", style="yellow")
        generated_file = transform_openapi_to_webdsl(openapi_path)

        if generated_file:
            with open(output, "w") as f:
                f.write(generated_file)
            console.print(f"✔ Generated file saved to: {output}", style="green")
        else:
            console.print("✖ No file generated.", style="red")

    except Exception as e:
        console.print(f"✖ Conversion error:\n{e}", style="bold red")
        raise SystemExit(1)


@transform.command("goaldsl", help="Convert GoalDSL spec to WebDSL model.")
@click.argument(
    "goaldsl_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_file",
    required=False,
    default="generated",
    type=click.Path(file_okay=False, writable=True),
)
def goaldsl_command(goaldsl_path, output_file):
    """
    Convert GoalDSL spec to webdsl model.

    If OUTPUT_PATH is omitted, it defaults to a directory named 'generated'.

    Examples:
      webdsl goaldsl examples/goaldsl_spec.gdsl
      webdsl goaldsl examples/goaldsl_spec.gdsl ./my_output_folder
    """
    try:
        output = os.path.abspath(output_file)

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)

        console.print(f"Transforming GoalDSL: {goaldsl_path}", style="yellow")
        generated_file = transform_goaldsl_to_webdsl(goaldsl_path)

        if generated_file:
            with open(output, "w") as f:
                f.write(generated_file)
            console.print(f"✔ Generated file saved to: {output}", style="green")
        else:
            console.print("✖ No file generated.", style="red")

    except Exception as e:
        console.print(f"✖ Conversion error:\n{e}", style="bold red")
        raise SystemExit(1)


@transform.command("asyncapi", help="Convert AsyncAPI spec to WebDSL model.")
@click.argument(
    "asyncapi_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
)
@click.argument(
    "output_file",
    required=False,
    default="generated_model.wdsl",
    type=click.Path(file_okay=True, writable=True),
)
def openapi_command(asyncapi_path, output_file):
    """
    Convert AsyncAPI spec to a webdsl model.

    If OUTPUT_FILE is omitted, it defaults to 'generated_model.wdsl'.

    Examples:
      webdsl asyncapi examples/asyncapi_spec.yaml
      webdsl asyncapi examples/asyncapi_spec.yaml ./my_model.wdsl
    """
    try:
        output = os.path.abspath(output_file)

        # Ensure the parent directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)

        console.print(f"Converting AsyncAPI spec: {asyncapi_path}", style="yellow")
        generated_file = transform_asyncapi_to_webdsl(asyncapi_path)

        if generated_file:
            with open(output, "w") as f:
                f.write(generated_file)
            console.print(f"✔ Generated file saved to: {output}", style="green")
        else:
            console.print("✖ No file generated.", style="red")

    except Exception as e:
        console.print(f"✖ Conversion error:\n{e}", style="bold red")
        raise SystemExit(1)


def main():
    cli(prog_name="webdsl")
