"""Post-processor for B2B features (organizations, teams, RBAC)."""

from __future__ import annotations

from matt_stack.config import ProjectConfig
from matt_stack.utils.console import console


def print_b2b_instructions(config: ProjectConfig) -> None:
    """Print instructions for generating B2B features.

    Feature generators require deps to be installed first (uv sync),
    so we print instructions rather than running them directly.
    """
    console.print()
    console.print("[bold yellow]B2B Feature Setup[/bold yellow]")
    console.print()
    console.print("After running [cyan]make setup[/cyan] and [cyan]make backend-migrate[/cyan],")
    console.print("generate B2B features:")
    console.print()
    console.print("[dim]cd backend[/dim]")
    console.print("[cyan]uv run python manage.py generate_feature organizations[/cyan]")
    console.print("[cyan]uv run python manage.py generate_feature teams[/cyan]")
    console.print("[cyan]uv run python manage.py generate_feature rbac[/cyan]")
    console.print("[cyan]uv run python manage.py makemigrations[/cyan]")
    console.print("[cyan]uv run python manage.py migrate[/cyan]")
    console.print()
