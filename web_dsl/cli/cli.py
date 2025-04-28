import click
import os
from web_dsl.language import build_model
from web_dsl.generate import generate


@click.group()
def cli():
    """A CLI for local code generation and model validation."""
    pass


@cli.command(name="generate")
@click.option(
    "--model",
    required=True,
    type=click.Path(exists=True),
    help="Path to the model file",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Path to generate the project files",
)
def generate_command(model, output):
    """Generate project files from a model file."""
    try:
        output = os.path.abspath(output)

        if os.path.exists(output) and not os.path.isdir(output):
            raise ValueError(
                f"The output path '{output}' exists and is not a directory."
            )

        click.echo(f"Generating project into: {output}")

        os.makedirs(output, exist_ok=True)

        generate(model, output)

        click.echo(f"Generation successful. Project generated at {output}")

    except Exception as e:
        click.echo(f"Generation error: {e}", err=True)


@cli.command()
@click.option(
    "--model",
    required=True,
    type=click.Path(exists=True),
    help="Path to the model file",
)
def validate(model):
    """Validate a model file."""
    try:
        build_model(model)
        click.echo("Model validation success")
    except Exception as e:
        click.echo(f"Validation error: {e}", err=True)


if __name__ == "__main__":
    cli()


# Example usage:
# ╰─ python -m web_dsl.cli.cli generate --model web_dsl/examples/entity_test.wdsl --output ~/Desktop/test_dir_output
# ╰─ python -m web_dsl.cli.cli validate --model web_dsl/examples/entity_test.wdsl
