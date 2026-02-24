"""Tests for FullstackGenerator — mocked git clone."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from matt_stack.config import ProjectConfig, ProjectType, Variant
from matt_stack.generators.fullstack import FullstackGenerator


def _make_config(tmp_path: Path, **kwargs) -> ProjectConfig:
    defaults = {
        "name": "test-proj",
        "path": tmp_path / "test-proj",
        "project_type": ProjectType.FULLSTACK,
        "variant": Variant.STARTER,
        "init_git": False,
    }
    defaults.update(kwargs)
    return ProjectConfig(**defaults)


def _mock_clone(url: str, dest: Path, branch: str = "main", depth: int = 1) -> bool:
    """Simulate a git clone by creating directory with expected files."""
    dest.mkdir(parents=True, exist_ok=True)
    if "django" in url:
        (dest / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (dest / "manage.py").write_text("#!/usr/bin/env python\n")
    elif "react" in url:
        (dest / "package.json").write_text('{"name": "test"}\n')
        (dest / "src").mkdir()
    elif "swift" in url:
        (dest / "Package.swift").write_text("// swift\n")
    return True


@patch("matt_stack.generators.base.clone_repo", side_effect=_mock_clone)
def test_fullstack_generates_all_files(mock_clone, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is True
    assert config.path.exists()
    assert (config.path / "Makefile").exists()
    assert (config.path / "docker-compose.yml").exists()
    assert (config.path / "README.md").exists()
    assert (config.path / ".gitignore").exists()
    assert (config.path / "tasks" / "todo.md").exists()


@patch("matt_stack.generators.base.clone_repo", side_effect=_mock_clone)
def test_fullstack_with_ios(mock_clone, tmp_path: Path) -> None:
    config = _make_config(tmp_path, include_ios=True)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is True
    assert (config.path / "ios").exists()


@patch("matt_stack.generators.base.clone_repo", return_value=False)
def test_fullstack_clone_failure_returns_false(mock_clone, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is False


@patch("matt_stack.generators.base.clone_repo", return_value=False)
def test_fullstack_clone_failure_cleans_up(mock_clone, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    gen = FullstackGenerator(config)
    gen.run()
    # Cleanup should remove the directory
    assert not config.path.exists()


@patch("matt_stack.generators.base.clone_repo", side_effect=_mock_clone)
def test_fullstack_b2b(mock_clone, tmp_path: Path) -> None:
    config = _make_config(tmp_path, variant=Variant.B2B)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is True


@patch("matt_stack.generators.fullstack.setup_frontend_monorepo")
@patch("matt_stack.generators.fullstack.customize_frontend")
@patch("matt_stack.generators.fullstack.customize_backend")
@patch("matt_stack.generators.base.clone_repo", side_effect=_mock_clone)
def test_fullstack_dry_run(mock_clone, mock_be, mock_fe, mock_setup, tmp_path: Path) -> None:
    config = _make_config(tmp_path, dry_run=True)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is True
    # In dry-run, clone_repo should NOT be called
    mock_clone.assert_not_called()


def test_fullstack_existing_dir_fails(tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config.path.mkdir(parents=True)
    gen = FullstackGenerator(config)
    result = gen.run()
    assert result is False
