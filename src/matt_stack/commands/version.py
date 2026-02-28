"""Version command with update check."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from matt_stack import __version__
from matt_stack.utils.console import console


def check_pypi_version(package: str = "matt-stack") -> str | None:
    """Check PyPI for the latest version. Returns None on any failure."""
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("info", {}).get("version")
    except (urllib.error.URLError, json.JSONDecodeError, OSError, KeyError, TimeoutError):
        return None


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a version string like '0.1.0' into a tuple of ints."""
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


def run_version() -> None:
    """Show version with optional update check."""
    console.print(f"matt-stack [bold]{__version__}[/bold]")

    latest = check_pypi_version()
    if latest and latest != __version__:
        current = _parse_version(__version__)
        remote = _parse_version(latest)
        if remote > current:
            console.print()
            console.print(
                f"[yellow]Update available:[/yellow] "
                f"{__version__} → [bold green]{latest}[/bold green]"
            )
            console.print("[dim]Run: uv tool upgrade matt-stack[/dim]")

    console.print("[dim]Tip: matt-stack completions --install for shell completions[/dim]")
