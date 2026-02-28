"""Tests for matt-stack lint command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from matt_stack.commands.lint import _has_backend, _has_frontend, run_lint


class TestHasBackend:
    def test_has_backend_when_pyproject_exists(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text('[project]\nname = "test"\n')
        assert _has_backend(tmp_path) is True

    def test_no_backend_when_pyproject_missing(self, tmp_path: Path) -> None:
        assert _has_backend(tmp_path) is False


class TestHasFrontend:
    def test_has_frontend_when_lint_script_exists(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"lint": "eslint ."}})
        )
        assert _has_frontend(tmp_path) is True

    def test_has_frontend_when_lint_fix_script_exists(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"lint:fix": "eslint . --fix"}})
        )
        assert _has_frontend(tmp_path) is True

    def test_no_frontend_when_no_lint_script(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"dev": "vite"}})
        )
        assert _has_frontend(tmp_path) is False

    def test_no_frontend_when_no_package_json(self, tmp_path: Path) -> None:
        assert _has_frontend(tmp_path) is False


class TestRunLint:
    def test_no_backend_or_frontend_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            run_lint(tmp_path)
        assert exc_info.value.exit_code == 1

    def test_nonexistent_path_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            run_lint(tmp_path / "nonexistent")
        assert exc_info.value.exit_code == 1

    def test_backend_lint_runs_when_backend_exists(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text('[project]\nname = "test"\n')
        with patch("matt_stack.commands.lint.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            run_lint(tmp_path)
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "ruff" in call_args
