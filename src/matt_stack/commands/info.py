"""Info command: show presets, repos, and config options."""

from __future__ import annotations

from matt_stack.config import REPO_URLS
from matt_stack.presets import list_presets
from matt_stack.utils.console import console, create_table


def run_info() -> None:
    """Display all available presets and source repos."""
    console.print()
    _show_presets()
    console.print()
    _show_repos()
    console.print()
    _show_usage()
    console.print()


def _show_presets() -> None:
    table = create_table("Available Presets", ["Name", "Type", "Variant", "Description"])
    for preset in list_presets():
        table.add_row(
            f"[cyan]{preset.name}[/cyan]",
            preset.project_type.value,
            preset.variant.value,
            preset.description,
        )
    console.print(table)


def _show_repos() -> None:
    table = create_table("Source Repositories", ["Key", "URL"])
    for key, url in REPO_URLS.items():
        table.add_row(f"[cyan]{key}[/cyan]", url)
    console.print(table)


def _show_usage() -> None:
    console.print("[bold]Usage Examples:[/bold]")
    console.print()
    examples = [
        ("matt-stack init", "Interactive wizard"),
        ("matt-stack init my-app --preset starter-fullstack", "Preset mode"),
        ("matt-stack init my-app --preset b2b-fullstack --ios", "With iOS"),
        ("matt-stack init --config stack.yaml", "Config file"),
        ("matt-stack doctor", "Check environment"),
    ]
    for cmd, desc in examples:
        console.print(f"  [cyan]{cmd}[/cyan]  {desc}")
