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


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-essential output"),
    ] = False,
) -> None:
    """Scaffold fullstack monorepos from battle-tested boilerplates."""
    if verbose:
        from matt_stack.utils.console import set_verbose

        set_verbose(True)
    if quiet:
        from matt_stack.utils.console import set_quiet

        set_quiet(True)


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
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview what would be generated without creating files"),
    ] = False,
) -> None:
    """Create a new project from boilerplates."""
    from matt_stack.commands.init import run_init

    run_init(
        name=name,
        preset=preset,
        config_file=config,
        ios=ios,
        output_dir=output_dir,
        dry_run=dry_run,
    )


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


@app.command(hidden=True)
def presets() -> None:
    """List available presets (alias for info)."""
    from matt_stack.commands.info import run_info

    run_info()


@app.command()
def audit(
    path: Annotated[
        Path | None,
        typer.Argument(help="Project path to audit (default: current directory)"),
    ] = None,
    audit_type: Annotated[
        list[str] | None,
        typer.Option("--type", "-t", help="Audit type: types, quality, endpoints, tests"),
    ] = None,
    live: Annotated[
        bool,
        typer.Option("--live", help="Enable live endpoint probing (GET only)"),
    ] = False,
    no_todo: Annotated[
        bool,
        typer.Option("--no-todo", help="Skip writing to tasks/todo.md"),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Output as JSON"),
    ] = False,
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Auto-remove debug statements"),
    ] = False,
    base_url: Annotated[
        str,
        typer.Option("--base-url", help="Base URL for live endpoint probing"),
    ] = "http://localhost:8000",
    severity: Annotated[
        str | None,
        typer.Option("--severity", "-s", help="Minimum severity: error, warning, info"),
    ] = None,
) -> None:
    """Run static analysis on a generated project."""
    from matt_stack.commands.audit import run_audit

    run_audit(
        path=path or Path.cwd(),
        audit_types=audit_type,
        live=live,
        no_todo=no_todo,
        json_output=json_output,
        fix=fix,
        base_url=base_url,
        min_severity=severity,
    )


@app.command()
def version() -> None:
    """Show matt-stack version."""
    typer.echo(f"matt-stack {__version__}")


if __name__ == "__main__":
    app()
