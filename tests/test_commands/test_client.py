"""Tests for the client command: frontend package manager wrapper."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from matt_stack.commands.client import _resolve
from matt_stack.utils.package_manager import PackageManager


class TestResolve:
    def test_resolve_from_root_with_frontend(self, tmp_path: Path) -> None:
        frontend = tmp_path / "frontend"
        frontend.mkdir()
        (frontend / "package.json").write_text("{}")
        (frontend / "bun.lockb").write_text("")
        work_dir, pm = _resolve(tmp_path, None)
        assert work_dir == frontend
        assert pm == PackageManager.BUN

    def test_resolve_from_root_without_frontend(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text("{}")
        (tmp_path / "yarn.lock").write_text("")
        work_dir, pm = _resolve(tmp_path, None)
        assert work_dir == tmp_path.resolve()
        assert pm == PackageManager.YARN

    def test_resolve_missing_package_json(self, tmp_path: Path) -> None:
        with pytest.raises(typer.Exit):
            _resolve(tmp_path, None)

    def test_resolve_with_pm_override(self, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text("{}")
        work_dir, pm = _resolve(tmp_path, "pnpm")
        assert pm == PackageManager.PNPM


class TestClientCommands:
    """Test client subcommands via the Typer test runner."""

    def _setup_project(self, tmp_path: Path) -> Path:
        """Create a minimal project with package.json."""
        (tmp_path / "package.json").write_text(
            json.dumps({"name": "test", "scripts": {"dev": "vite", "build": "vite build"}})
        )
        (tmp_path / "bun.lockb").write_text("")
        return tmp_path

    @patch("matt_stack.commands.client.run_pm_command")
    def test_which_shows_pm(self, mock_run, tmp_path: Path) -> None:
        proj = self._setup_project(tmp_path)
        from matt_stack.commands.client import which_pm

        which_pm(path=proj)
