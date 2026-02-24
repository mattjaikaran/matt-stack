"""Rich console utilities."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

_verbose = False


def set_verbose(enabled: bool) -> None:
    global _verbose
    _verbose = enabled


def print_verbose(message: str) -> None:
    if _verbose:
        console.print(f"[dim][VERBOSE][/dim] {message}")


def print_info(message: str) -> None:
    console.print(f"[blue][INFO][/blue] {message}")


def print_success(message: str) -> None:
    console.print(f"[green][SUCCESS][/green] {message}")


def print_warning(message: str) -> None:
    console.print(f"[yellow][WARNING][/yellow] {message}")


def print_error(message: str) -> None:
    console.print(f"[red][ERROR][/red] {message}")


def print_step(step: int, total: int, message: str) -> None:
    console.print(f"[cyan][{step}/{total}][/cyan] {message}")


def print_header(title: str) -> None:
    console.print(Panel(title, border_style="cyan", expand=False))


def create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def create_table(title: str, columns: list[str]) -> Table:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    return table
