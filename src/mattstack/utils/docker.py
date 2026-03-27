"""Docker detection utilities."""

from __future__ import annotations

import shutil
import subprocess


def docker_available() -> bool:
    return shutil.which("docker") is not None


def docker_compose_available() -> bool:
    """Check if docker compose (v2 plugin) is available."""
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def docker_running() -> bool:
    """Check if Docker daemon is running."""
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
