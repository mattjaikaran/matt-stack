"""Doctor command: validate development environment."""

from __future__ import annotations

import sys

from matt_stack.utils.console import console, create_table
from matt_stack.utils.docker import docker_available, docker_compose_available, docker_running
from matt_stack.utils.process import check_port_available, command_available, get_command_version

INSTALL_HINTS: dict[str, str] = {
    "git": "brew install git",
    "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
    "bun": "curl -fsSL https://bun.sh/install | bash",
    "make": "xcode-select --install",
}


def run_doctor() -> None:
    """Check all required tools and ports."""
    console.print()
    console.print("[bold cyan]matt-stack doctor[/bold cyan]")
    console.print()

    all_ok = True
    table = create_table("Environment Check", ["Check", "Status", "Details"])

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 12)
    table.add_row(
        "Python >= 3.12",
        _status(py_ok),
        py_version,
    )
    all_ok &= py_ok

    # Required tools
    tools = [
        ("git", "git"),
        ("uv", "uv"),
        ("bun", "bun"),
        ("make", "make"),
    ]
    for label, cmd in tools:
        available = command_available(cmd)
        version = get_command_version(cmd) or "not found"
        # Take just the first line of version output
        version_short = version.split("\n")[0] if version else "not found"
        if available:
            detail = version_short
        else:
            hint = INSTALL_HINTS.get(cmd, "")
            detail = f"not installed — install: {hint}" if hint else "not installed"
        table.add_row(label, _status(available), detail)
        all_ok &= available

    # Docker
    dk_available = docker_available()
    table.add_row("docker", _status(dk_available), "installed" if dk_available else "not installed")
    all_ok &= dk_available

    dc_available = docker_compose_available()
    table.add_row(
        "docker compose",
        _status(dc_available),
        "available" if dc_available else "not available",
    )
    all_ok &= dc_available

    dk_running = docker_running() if dk_available else False
    table.add_row(
        "Docker daemon",
        _status(dk_running),
        "running" if dk_running else "not running",
    )

    # Ports
    ports = [
        (5432, "PostgreSQL"),
        (6379, "Redis"),
        (8000, "Django API"),
        (3000, "Vite frontend"),
    ]
    for port, label in ports:
        available = check_port_available(port)
        table.add_row(
            f"Port {port} ({label})",
            _status(available),
            "available" if available else "in use",
        )

    console.print(table)
    console.print()

    if all_ok:
        console.print("[bold green]All checks passed![/bold green]")
    else:
        msg = "Some checks failed. Install missing tools before using matt-stack."
        console.print(f"[bold yellow]{msg}[/bold yellow]")


def _status(ok: bool) -> str:
    return "[green]OK[/green]" if ok else "[red]FAIL[/red]"
