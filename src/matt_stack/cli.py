"""Typer CLI app for matt-stack."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from matt_stack import __version__

app = typer.Typer(
    name="matt-stack",
    help="Scaffold fullstack monorepos from battle-tested boilerplates.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command()
def init(
    name: Annotated[
        str | None,
        typer.Argument(help="Project name"),
    ] = None,
    preset: Annotated[
        str | None,
        typer.Option("--preset", "-p", help="Use a preset (e.g. starter-fullstack, b2b-api)"),
    ] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Path to YAML config file"),
    ] = None,
    ios: Annotated[
        bool,
        typer.Option("--ios", help="Include iOS client"),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output directory (default: current)"),
    ] = None,
) -> None:
    """Create a new project from boilerplates."""
    from matt_stack.commands.init import run_init

    run_init(name=name, preset=preset, config_file=config, ios=ios, output_dir=output_dir)


@app.command()
def doctor() -> None:
    """Check your development environment."""
    from matt_stack.commands.doctor import run_doctor

    run_doctor()


@app.command()
def info() -> None:
    """Show available presets, repos, and usage."""
    from matt_stack.commands.info import run_info

    run_info()


@app.command()
def presets() -> None:
    """List available presets (alias for info)."""
    from matt_stack.commands.info import run_info

    run_info()


@app.command()
def version() -> None:
    """Show matt-stack version."""
    typer.echo(f"matt-stack {__version__}")


if __name__ == "__main__":
    app()
