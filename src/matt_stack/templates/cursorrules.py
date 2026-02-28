"""Cursor IDE .cursorrules template for generated projects."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_cursorrules(config: ProjectConfig) -> str:
    """Generate .cursorrules for Cursor IDE agent configuration."""
    sections = [
        _header(),
        _package_managers(),
        _development(config),
        _testing(config),
        _code_style(config),
        _key_files(config),
    ]
    return "\n\n".join(sections) + "\n"


def _header() -> str:
    return "# Project Rules for Cursor"


def _package_managers() -> str:
    return """## Package Managers
- Python: use `uv` (NEVER pip/poetry/conda)
- JavaScript: use `bun` (NEVER npm/yarn/pnpm)"""


def _development(config: ProjectConfig) -> str:
    lines = ["## Development"]
    if config.has_backend:
        lines.append("- Docker Compose runs PostgreSQL and Redis: `docker compose up -d`")
        lines.append("- Backend dev server: `cd backend && uv run python manage.py runserver`")
    if config.has_frontend:
        lines.append("- Frontend dev server: `cd frontend && bun run dev`")
    lines.append("- Or use `matt-stack dev` to start everything at once")
    return "\n".join(lines)


def _testing(config: ProjectConfig) -> str:
    lines = ["## Testing"]
    if config.has_backend:
        lines.append("- Backend: `cd backend && uv run pytest -v`")
    if config.has_frontend:
        lines.append("- Frontend: `cd frontend && bun run test`")
    lines.append("- Or use `matt-stack test` to run all")
    return "\n".join(lines)


def _code_style(config: ProjectConfig) -> str:
    lines = [
        "## Code Style",
        "- Python: type hints required, ruff for linting/formatting",
        "- TypeScript: strict mode, no `any` types",
    ]
    if config.has_backend:
        lines.append("- Backend API: django-ninja (NOT Django REST Framework)")
    return "\n".join(lines)


def _key_files(config: ProjectConfig) -> str:
    lines = [
        "## Key Files",
        "- `CLAUDE.md` — Full project context for AI agents",
    ]
    if config.has_backend:
        lines.append("- `.env.example` — Required environment variables")
    lines.append("- `Makefile` — All available make targets")
    if config.has_backend:
        lines.append("- `docker-compose.yml` — Infrastructure services")
    return "\n".join(lines)
