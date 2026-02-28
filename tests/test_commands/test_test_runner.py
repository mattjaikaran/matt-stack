"""Tests for matt-stack test command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from matt_stack.commands.test import _has_backend, _has_frontend, run_test


class TestHasBackend:
    def test_has_backend_when_pyproject_exists(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text('[project]\nname = "test"\n')
        assert _has_backend(tmp_path) is True

    def test_no_backend_when_pyproject_missing(self, tmp_path: Path) -> None:
        assert _has_backend(tmp_path) is False


class TestHasFrontend:
    def test_has_frontend_when_test_script_exists(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"test": "vitest run"}})
        )
        assert _has_frontend(tmp_path) is True

    def test_has_frontend_when_test_coverage_script_exists(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"test:coverage": "vitest run --coverage"}})
        )
        assert _has_frontend(tmp_path) is True

    def test_no_frontend_when_no_test_script(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"dev": "vite"}})
        )
        assert _has_frontend(tmp_path) is False

    def test_no_frontend_when_no_package_json(self, tmp_path: Path) -> None:
        assert _has_frontend(tmp_path) is False


class TestRunTest:
    def test_no_backend_or_frontend_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            run_test(tmp_path)
        assert exc_info.value.exit_code == 1

    def test_backend_only_with_no_backend_exits_1(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text(
            json.dumps({"scripts": {"test": "vitest run"}})
        )
        with pytest.raises(typer.Exit) as exc_info:
            run_test(tmp_path, backend_only=True)
        assert exc_info.value.exit_code == 1

    def test_frontend_only_with_no_frontend_exits_1(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text('[project]\nname = "test"\n')
        with pytest.raises(typer.Exit) as exc_info:
            run_test(tmp_path, frontend_only=True)
        assert exc_info.value.exit_code == 1

    def test_nonexistent_path_exits_1(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit) as exc_info:
            run_test(tmp_path / "nonexistent")
        assert exc_info.value.exit_code == 1

    def test_backend_tests_run_when_backend_exists(self, tmp_path: Path) -> None:
        backend = tmp_path / "backend"
        backend.mkdir()
        (backend / "pyproject.toml").write_text('[project]\nname = "test"\n')
        with patch("matt_stack.commands.test.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            run_test(tmp_path)
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "pytest" in call_args
