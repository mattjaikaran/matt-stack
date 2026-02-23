"""Preset configurations for common project types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from matt_stack.config import (
    FrontendFramework,
    ProjectConfig,
    ProjectType,
    Variant,
)


@dataclass
class Preset:
    """A named preset configuration."""

    name: str
    description: str
    project_type: ProjectType
    variant: Variant
    frontend_framework: FrontendFramework = FrontendFramework.REACT_VITE
    include_ios: bool = False
    use_celery: bool = True

    def to_config(self, project_name: str, path: Path) -> ProjectConfig:
        return ProjectConfig(
            name=project_name,
            path=path,
            project_type=self.project_type,
            variant=self.variant,
            frontend_framework=self.frontend_framework,
            include_ios=self.include_ios,
            use_celery=self.use_celery,
        )


PRESETS: dict[str, Preset] = {
    "starter-fullstack": Preset(
        name="starter-fullstack",
        description="Standard fullstack monorepo (Django + React Vite TanStack)",
        project_type=ProjectType.FULLSTACK,
        variant=Variant.STARTER,
    ),
    "b2b-fullstack": Preset(
        name="b2b-fullstack",
        description="B2B fullstack with orgs/teams/roles (Django + React Vite)",
        project_type=ProjectType.FULLSTACK,
        variant=Variant.B2B,
    ),
    "starter-api": Preset(
        name="starter-api",
        description="Django API only (no frontend)",
        project_type=ProjectType.BACKEND_ONLY,
        variant=Variant.STARTER,
    ),
    "b2b-api": Preset(
        name="b2b-api",
        description="B2B Django API with orgs/teams/roles",
        project_type=ProjectType.BACKEND_ONLY,
        variant=Variant.B2B,
    ),
    "starter-frontend": Preset(
        name="starter-frontend",
        description="React Vite SPA with TanStack Router",
        project_type=ProjectType.FRONTEND_ONLY,
        variant=Variant.STARTER,
        use_celery=False,
    ),
    "simple-frontend": Preset(
        name="simple-frontend",
        description="Simpler React Vite SPA with React Router",
        project_type=ProjectType.FRONTEND_ONLY,
        variant=Variant.STARTER,
        frontend_framework=FrontendFramework.REACT_VITE_STARTER,
        use_celery=False,
    ),
}


def get_preset(name: str) -> Preset | None:
    return PRESETS.get(name)


def list_presets() -> list[Preset]:
    return list(PRESETS.values())
