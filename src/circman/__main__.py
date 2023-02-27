"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Manager for CircuitPython deployment."""


if __name__ == "__main__":
    main(prog_name="circman")  # pragma: no cover
