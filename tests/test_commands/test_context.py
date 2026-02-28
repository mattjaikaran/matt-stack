"""Tests for the context command: AI agent context dumper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer

from matt_stack.commands.context import (
    _detect_components,
    _detect_env_vars,
    _detect_frontend_stack,
    _detect_makefile_targets,
    build_context,
    format_context_markdown,
    run_context,
)


def _make_fullstack(path: Path) -> Path:
    """Create a minimal fullstack project."""
    path.mkdir(parents=True, exist_ok=True)
    backend = path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text(
        '[project]\nname = "test"\ndependencies = ["django", "django-ninja", "celery"]\n'
    )
    frontend = path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "name": "test-frontend",
                "dependencies": {"react": "^18", "next": "^14", "tailwindcss": "^3"},
                "devDependencies": {},
                "scripts": {"dev": "next dev", "build": "next build", "lint": "eslint ."},
            }
        )
    )
    (path / "Makefile").write_text("setup:\n\techo setup\ntest:\n\techo test\n")
    (path / ".env.example").write_text(
        "DATABASE_URL=postgres://localhost/db\nSECRET_KEY=changeme\n"
    )
    (path / "docker-compose.yml").write_text("version: '3'\n")
    (path / "CLAUDE.md").write_text("# test\n")
    return path


class TestDetectComponents:
    def test_fullstack(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        comps = _detect_components(proj)
        assert comps["backend"] is True
        assert comps["frontend"] is True
        assert comps["docker"] is True
        assert comps["makefile"] is True
        assert comps["claude_md"] is True

    def test_empty(self, tmp_path: Path) -> None:
        comps = _detect_components(tmp_path)
        assert all(v is False for v in comps.values())


class TestDetectFrontendStack:
    def test_nextjs_detected(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        stack = _detect_frontend_stack(proj)
        assert stack["framework"] == "next.js"
        assert stack["ui_library"] == "react"
        assert stack["styling"] == "tailwind"
        assert "dev" in stack["scripts"]

    def test_no_frontend(self, tmp_path: Path) -> None:
        assert _detect_frontend_stack(tmp_path) == {}


class TestDetectEnvVars:
    def test_parses_env_example(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        env_vars = _detect_env_vars(proj)
        assert "DATABASE_URL" in env_vars
        assert "SECRET_KEY" in env_vars

    def test_empty(self, tmp_path: Path) -> None:
        assert _detect_env_vars(tmp_path) == []


class TestDetectMakefileTargets:
    def test_parses_targets(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        targets = _detect_makefile_targets(proj)
        assert "setup" in targets
        assert "test" in targets

    def test_no_makefile(self, tmp_path: Path) -> None:
        assert _detect_makefile_targets(tmp_path) == []


class TestBuildContext:
    def test_fullstack_context(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        ctx = build_context(proj)
        assert ctx["project_name"] == "app"
        assert ctx["components"]["backend"] is True
        assert "backend" in ctx
        assert "frontend" in ctx
        assert "env_vars" in ctx
        assert "makefile_targets" in ctx
        assert "tools" in ctx


class TestFormatContextMarkdown:
    def test_produces_markdown(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        ctx = build_context(proj)
        md = format_context_markdown(ctx)
        assert "# Project: app" in md
        assert "## Backend" in md
        assert "## Frontend" in md
        assert "## Environment Variables" in md
        assert "## Makefile Targets" in md


class TestRunContext:
    def test_json_output(self, tmp_path: Path, capsys) -> None:
        proj = _make_fullstack(tmp_path / "app")
        run_context(proj, json_output=True, output_file=str(tmp_path / "out.json"))
        content = (tmp_path / "out.json").read_text()
        data = json.loads(content)
        assert data["project_name"] == "app"

    def test_markdown_output_to_file(self, tmp_path: Path) -> None:
        proj = _make_fullstack(tmp_path / "app")
        run_context(proj, json_output=False, output_file=str(tmp_path / "out.md"))
        content = (tmp_path / "out.md").read_text()
        assert "# Project: app" in content

    def test_nonexistent_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit):
            run_context(tmp_path / "nope")
