"""YAML config file parser for matt-stack init --config."""

from __future__ import annotations

from pathlib import Path

import yaml

from matt_stack.config import (
    DeploymentTarget,
    FrontendFramework,
    ProjectConfig,
    ProjectType,
    Variant,
)
from matt_stack.utils.console import print_error


def load_config_file(config_path: Path, output_path: Path) -> ProjectConfig | None:
    """Parse a YAML config file into a ProjectConfig."""
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        return None

    try:
        data = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as e:
        print_error(f"Invalid YAML: {e}")
        return None

    if not isinstance(data, dict):
        print_error("Config file must be a YAML mapping")
        return None

    name = data.get("name")
    if not name:
        print_error("Config file must include 'name'")
        return None

    project_type = ProjectType(data.get("type", "fullstack"))
    variant = Variant(data.get("variant", "starter"))

    backend = data.get("backend", {})
    frontend = data.get("frontend", {})
    author = data.get("author", {})

    frontend_fw = FrontendFramework(frontend.get("framework", "react-vite"))
    deployment = DeploymentTarget(data.get("deployment", "docker"))

    return ProjectConfig(
        name=name,
        path=output_path / name,
        project_type=project_type,
        variant=variant,
        frontend_framework=frontend_fw,
        include_ios=data.get("ios", False),
        use_celery=backend.get("celery", True),
        use_redis=backend.get("redis", True),
        deployment=deployment,
        author_name=author.get("name", "Matt Jaikaran"),
        author_email=author.get("email", "info@mattjaikaran.com"),
    )
