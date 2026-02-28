"""Root CLAUDE.md template for generated projects."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_claude_md(config: ProjectConfig) -> str:
    """Generate CLAUDE.md for AI assistant context."""
    sections = [_header(config), _structure(config), _tech(config), _commands(config)]

    if config.has_backend:
        sections.append(_backend(config))

    if config.has_frontend:
        sections.append(_frontend(config))

    if config.include_ios:
        sections.append(_ios())

    sections.append(_rules())

    return "\n\n".join(sections) + "\n"


def _header(config: ProjectConfig) -> str:
    variant = " (B2B)" if config.is_b2b else ""
    return f"# {config.display_name}{variant}"


def _structure(config: ProjectConfig) -> str:
    parts = []
    if config.has_backend:
        parts.append("- `backend/` — Django API (django-ninja)")
    if config.has_frontend:
        if config.is_nextjs:
            parts.append("- `frontend/` — Next.js (App Router, TypeScript, Tailwind)")
        else:
            is_tanstack = config.frontend_framework.value == "react-vite"
            fw = "TanStack Router" if is_tanstack else "React Router"
            parts.append(f"- `frontend/` — React + Vite + TypeScript ({fw})")
    if config.include_ios:
        parts.append("- `ios/` — SwiftUI iOS client (iOS 17+)")

    return "## Structure\n\n" + "\n".join(parts)


def _tech(config: ProjectConfig) -> str:
    parts = []
    if config.has_backend:
        parts.append("- Backend: Python 3.12+, Django, django-ninja, PostgreSQL 17")
        if config.use_celery:
            parts.append("- Background: Celery + Redis")
    if config.has_frontend:
        if config.is_nextjs:
            parts.append("- Frontend: Next.js (App Router), TypeScript (strict)")
        else:
            parts.append("- Frontend: React 18, Vite, TypeScript (strict)")
    if config.include_ios:
        parts.append("- iOS: SwiftUI, MVVM, async/await, iOS 17+")

    return "## Tech Stack\n\n" + "\n".join(parts)


def _commands(config: ProjectConfig) -> str:
    lines = [
        "## Commands",
        "",
        "```bash",
        "make setup          # Install all deps",
    ]

    if config.has_backend:
        lines.append("make up             # Start Docker services")
        lines.append("make down           # Stop services")

    lines.append("make test           # Run all tests")
    lines.append("make lint           # Lint all code")
    lines.append("make format         # Format all code")

    if config.has_backend:
        lines.append("make backend-dev    # Django dev server (port 8000)")

    if config.has_frontend:
        label = "Next.js" if config.is_nextjs else "Vite"
        lines.append(f"make frontend-dev   # {label} dev server (port 3000)")

    lines.append("```")
    return "\n".join(lines)


def _backend(config: ProjectConfig) -> str:
    return """\
## Backend

- Package manager: `uv` (NOT pip)
- Linting: `ruff`
- Testing: `pytest`
- API style: django-ninja (type-safe, OpenAPI auto-gen)
- Migrations: `make backend-migrate` / `make backend-makemigrations`"""


def _frontend(config: ProjectConfig) -> str:
    if config.is_nextjs:
        return """\
## Frontend

- Package manager: `bun` (NOT npm/yarn)
- Framework: Next.js (App Router)
- API base: `NEXT_PUBLIC_API_BASE_URL` env var
- Styling: Tailwind CSS
- Routing: App Router (file-based)
- API routes: `app/api/` directory"""

    return """\
## Frontend

- Package manager: `bun` (NOT npm/yarn)
- API base: `VITE_API_BASE_URL` env var
- Styling: Tailwind CSS
- State: TanStack Query for server state"""


def _ios() -> str:
    return """\
## iOS

- SwiftUI with MVVM pattern
- Async/await networking
- iOS 17+ minimum deployment target"""


def _rules() -> str:
    return """\
## Rules

- Never use pip, npm, or yarn — use uv (Python) and bun (JS)
- Always use type hints (Python) and strict TypeScript
- Test before committing
- Keep backend and frontend changes in sync"""
