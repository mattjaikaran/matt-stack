"""Detected project state from filesystem (for rules command)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DetectedProject:
    """Project state detected from filesystem."""

    name: str
    has_backend: bool = False
    has_frontend: bool = False
    has_docker: bool = False
    has_ios: bool = False
    is_nextjs: bool = False
    is_b2b: bool = False
    use_celery: bool = False
    use_redis: bool = False
    python_pm: str = "uv"
    js_pm: str = "bun"
    backend_framework: str = "django-ninja"
    frontend_framework: str = "react-vite"
    docker_services: list[str] = field(default_factory=list)
    env_files: list[str] = field(default_factory=list)
    makefile_targets: list[str] = field(default_factory=list)

    @property
    def is_fullstack(self) -> bool:
        return self.has_backend and self.has_frontend

    @property
    def display_name(self) -> str:
        return self.name.replace("-", " ").title()
