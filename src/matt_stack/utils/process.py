"""Subprocess execution utilities."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def run_command(
    args: list[str],
    cwd: Path | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=capture,
        text=True,
        check=True,
    )


def command_available(name: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(name) is not None


def check_port_available(port: int) -> bool:
    """Check if a TCP port is available."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def get_command_version(name: str, args: list[str] | None = None) -> str | None:
    """Get version string from a command."""
    if args is None:
        args = [name, "--version"]
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
