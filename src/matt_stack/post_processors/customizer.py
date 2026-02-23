"""Post-processor to customize cloned repos (rename, rebrand)."""

from __future__ import annotations

import json

from matt_stack.config import ProjectConfig
from matt_stack.utils.console import print_info


def customize_backend(config: ProjectConfig) -> None:
    """Rename the backend project to match the project name."""
    pyproject = config.backend_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        # Update project name
        content = content.replace(
            'name = "django-ninja-boilerplate"',
            f'name = "{config.name}-backend"',
        )
        content = content.replace(
            'name = "django_ninja_boilerplate"',
            f'name = "{config.python_package_name}_backend"',
        )
        pyproject.write_text(content)
        print_info(f"Renamed backend to {config.name}-backend")

    # Remove boilerplate cli/ dir if somehow still present
    cli_dir = config.backend_dir / "cli"
    if cli_dir.exists():
        import shutil

        shutil.rmtree(cli_dir)


def customize_frontend(config: ProjectConfig) -> None:
    """Rename the frontend project to match the project name."""
    package_json = config.frontend_dir / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text())
        data["name"] = f"{config.name}-frontend"
        package_json.write_text(json.dumps(data, indent=2) + "\n")
        print_info(f"Renamed frontend to {config.name}-frontend")
