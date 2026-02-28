"""Tests for the add command: expand existing projects with new layers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from matt_stack.commands.add import (
    VALID_COMPONENTS,
    _build_config,
    _detect_project,
    run_add,
)
from matt_stack.config import FrontendFramework, ProjectType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_backend_project(path: Path) -> Path:
    """Create a minimal backend-only project structure."""
    path.mkdir(parents=True, exist_ok=True)
    backend = path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text('[project]\nname = "test-backend"\n')
    (backend / "manage.py").write_text("#!/usr/bin/env python\n")
    (path / "Makefile").write_text(".DEFAULT_GOAL := help\n")
    return path


def _make_frontend_project(path: Path) -> Path:
    """Create a minimal frontend-only project structure."""
    path.mkdir(parents=True, exist_ok=True)
    frontend = path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"name": "test-frontend"}\n')
    (frontend / "src").mkdir()
    (path / "Makefile").write_text(".DEFAULT_GOAL := help\n")
    return path


def _make_fullstack_project(path: Path) -> Path:
    """Create a minimal fullstack project structure."""
    path.mkdir(parents=True, exist_ok=True)
    backend = path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text('[project]\nname = "test-backend"\n')
    frontend = path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"name": "test-frontend"}\n')
    (path / "Makefile").write_text(".DEFAULT_GOAL := help\n")
    return path


def _mock_clone(url: str, dest: Path, branch: str = "main", depth: int = 1) -> bool:
    """Simulate a git clone by creating the directory with expected files."""
    dest.mkdir(parents=True, exist_ok=True)
    if "django" in url:
        (dest / "pyproject.toml").write_text('[project]\nname = "test"\n')
        (dest / "manage.py").write_text("#!/usr/bin/env python\n")
    elif "react" in url:
        (dest / "package.json").write_text('{"name": "test"}\n')
        (dest / "src").mkdir(exist_ok=True)
    elif "swift" in url:
        (dest / "Package.swift").write_text("// swift\n")
    return True


# ---------------------------------------------------------------------------
# Tests: _detect_project
# ---------------------------------------------------------------------------


class TestDetectProject:
    def test_detect_backend_only(self, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-api")
        detected = _detect_project(proj)
        assert detected["has_backend"] is True
        assert detected["has_frontend"] is False
        assert detected["has_ios"] is False
        assert detected["name"] == "my-api"

    def test_detect_frontend_only(self, tmp_path: Path) -> None:
        proj = _make_frontend_project(tmp_path / "my-spa")
        detected = _detect_project(proj)
        assert detected["has_backend"] is False
        assert detected["has_frontend"] is True
        assert detected["has_ios"] is False
        assert detected["name"] == "my-spa"

    def test_detect_fullstack(self, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        detected = _detect_project(proj)
        assert detected["has_backend"] is True
        assert detected["has_frontend"] is True
        assert detected["has_ios"] is False

    def test_detect_with_ios(self, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        (proj / "ios").mkdir()
        detected = _detect_project(proj)
        assert detected["has_ios"] is True

    def test_detect_empty_project(self, tmp_path: Path) -> None:
        proj = tmp_path / "empty"
        proj.mkdir()
        detected = _detect_project(proj)
        assert detected["has_backend"] is False
        assert detected["has_frontend"] is False
        assert detected["has_ios"] is False


# ---------------------------------------------------------------------------
# Tests: _build_config
# ---------------------------------------------------------------------------


class TestBuildConfig:
    def test_adding_frontend_to_backend_produces_fullstack(self, tmp_path: Path) -> None:
        detected = {"has_backend": True, "has_frontend": False, "has_ios": False, "name": "proj"}
        config = _build_config(tmp_path, detected, "frontend", None)
        assert config.project_type == ProjectType.FULLSTACK
        assert config.has_backend is True
        assert config.has_frontend is True
        assert config.init_git is False

    def test_adding_backend_to_frontend_produces_fullstack(self, tmp_path: Path) -> None:
        detected = {"has_backend": False, "has_frontend": True, "has_ios": False, "name": "proj"}
        config = _build_config(tmp_path, detected, "backend", None)
        assert config.project_type == ProjectType.FULLSTACK

    def test_adding_ios_keeps_project_type(self, tmp_path: Path) -> None:
        detected = {"has_backend": True, "has_frontend": True, "has_ios": False, "name": "proj"}
        config = _build_config(tmp_path, detected, "ios", None)
        assert config.project_type == ProjectType.FULLSTACK
        assert config.include_ios is True

    def test_adding_backend_only(self, tmp_path: Path) -> None:
        detected = {"has_backend": False, "has_frontend": False, "has_ios": False, "name": "proj"}
        config = _build_config(tmp_path, detected, "backend", None)
        assert config.project_type == ProjectType.BACKEND_ONLY

    def test_custom_framework(self, tmp_path: Path) -> None:
        detected = {"has_backend": True, "has_frontend": False, "has_ios": False, "name": "proj"}
        config = _build_config(tmp_path, detected, "frontend", "react-vite-starter")
        assert config.frontend_framework == FrontendFramework.REACT_VITE_STARTER


# ---------------------------------------------------------------------------
# Tests: run_add (integration with mocks)
# ---------------------------------------------------------------------------


class TestRunAdd:
    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_frontend_to_backend(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        run_add("frontend", proj)
        # Frontend directory should now exist (created by mock clone)
        assert (proj / "frontend" / "package.json").exists()
        # Root files should be regenerated
        makefile = (proj / "Makefile").read_text()
        assert "frontend" in makefile.lower()
        mock_clone.assert_called_once()
        mock_rm_git.assert_called_once()

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_backend_to_frontend(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_frontend_project(tmp_path / "my-app")
        run_add("backend", proj)
        assert (proj / "backend" / "pyproject.toml").exists()
        makefile = (proj / "Makefile").read_text()
        assert "backend" in makefile.lower()

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_ios_to_fullstack(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        run_add("ios", proj)
        assert (proj / "ios" / "Package.swift").exists()
        makefile = (proj / "Makefile").read_text()
        assert "ios" in makefile.lower()

    def test_reject_add_existing_frontend(self, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        with pytest.raises(typer.Exit):
            run_add("frontend", proj)

    def test_reject_add_existing_backend(self, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        with pytest.raises(typer.Exit):
            run_add("backend", proj)

    def test_reject_add_existing_ios(self, tmp_path: Path) -> None:
        proj = _make_fullstack_project(tmp_path / "my-app")
        (proj / "ios").mkdir()
        with pytest.raises(typer.Exit):
            run_add("ios", proj)

    def test_reject_invalid_component(self, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        with pytest.raises(typer.Exit):
            run_add("database", proj)

    def test_reject_nonexistent_path(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit):
            run_add("frontend", tmp_path / "does-not-exist")

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_dry_run_does_not_clone(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        original_makefile = (proj / "Makefile").read_text()
        run_add("frontend", proj, dry_run=True)
        # Clone should not be called in dry-run mode
        mock_clone.assert_not_called()
        mock_rm_git.assert_not_called()
        # Makefile should not be changed
        assert (proj / "Makefile").read_text() == original_makefile

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", return_value=False)
    def test_clone_failure_raises_exit(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        with pytest.raises(typer.Exit):
            run_add("frontend", proj)

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_frontend_with_custom_framework(
        self, mock_clone, mock_rm_git, tmp_path: Path
    ) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        run_add("frontend", proj, framework="react-vite-starter")
        mock_clone.assert_called_once()
        url = mock_clone.call_args[0][0]
        assert "react-vite-starter" in url

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_backend_generates_docker_compose(
        self, mock_clone, mock_rm_git, tmp_path: Path
    ) -> None:
        proj = _make_frontend_project(tmp_path / "my-app")
        run_add("backend", proj)
        assert (proj / "docker-compose.yml").exists()
        dc_content = (proj / "docker-compose.yml").read_text()
        assert "postgres" in dc_content.lower()

    @patch("matt_stack.commands.add.remove_git_history")
    @patch("matt_stack.commands.add.clone_repo", side_effect=_mock_clone)
    def test_add_generates_env_example(self, mock_clone, mock_rm_git, tmp_path: Path) -> None:
        proj = _make_backend_project(tmp_path / "my-app")
        run_add("frontend", proj)
        assert (proj / ".env.example").exists()
        env_content = (proj / ".env.example").read_text()
        assert "VITE_" in env_content  # Frontend env vars present

    def test_valid_components_constant(self) -> None:
        assert "frontend" in VALID_COMPONENTS
        assert "backend" in VALID_COMPONENTS
        assert "ios" in VALID_COMPONENTS
