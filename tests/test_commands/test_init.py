"""Tests for the init command — preset mode, config mode, error handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import click.exceptions
import pytest

from matt_stack.commands.init import _generate, _run_from_preset, run_init
from matt_stack.config import ProjectConfig, ProjectType, Variant


def test_preset_creates_config(tmp_path: Path) -> None:
    """Preset mode should create a valid ProjectConfig."""
    with patch("matt_stack.commands.init._generate") as mock_gen:
        mock_gen.return_value = True
        _run_from_preset("my-app", "starter-fullstack", False, tmp_path)
        config = mock_gen.call_args[0][0]
        assert config.name == "my-app"
        assert config.project_type == ProjectType.FULLSTACK
        assert config.variant == Variant.STARTER


def test_preset_with_ios(tmp_path: Path) -> None:
    with patch("matt_stack.commands.init._generate") as mock_gen:
        mock_gen.return_value = True
        _run_from_preset("my-app", "starter-fullstack", True, tmp_path)
        config = mock_gen.call_args[0][0]
        assert config.include_ios is True


def test_bad_preset_exits(tmp_path: Path) -> None:
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        _run_from_preset("test", "nonexistent-preset", False, tmp_path)


def test_yaml_config_mode(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("name: my-app\ntype: backend-only\nvariant: starter\n")
    with patch("matt_stack.commands.init._generate") as mock_gen:
        mock_gen.return_value = True
        run_init(config_file=str(cfg_file), output_dir=tmp_path)
        config = mock_gen.call_args[0][0]
        assert config.name == "my-app"
        assert config.project_type == ProjectType.BACKEND_ONLY


def test_yaml_config_bad_type(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("name: my-app\ntype: invalid-type\n")
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        run_init(config_file=str(cfg_file), output_dir=tmp_path)


def test_yaml_config_missing_name(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("type: fullstack\nvariant: starter\n")
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        run_init(config_file=str(cfg_file), output_dir=tmp_path)


def test_yaml_config_nonexistent_file(tmp_path: Path) -> None:
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        run_init(config_file=str(tmp_path / "missing.yaml"), output_dir=tmp_path)


def test_generate_existing_dir_exits(tmp_path: Path) -> None:
    proj_dir = tmp_path / "existing"
    proj_dir.mkdir()
    config = ProjectConfig(
        name="existing",
        path=proj_dir,
        project_type=ProjectType.FULLSTACK,
    )
    with pytest.raises((SystemExit, click.exceptions.Exit)):
        _generate(config)


def test_generate_dry_run_skips_dir_check(tmp_path: Path) -> None:
    proj_dir = tmp_path / "existing"
    proj_dir.mkdir()
    config = ProjectConfig(
        name="existing",
        path=proj_dir,
        project_type=ProjectType.FULLSTACK,
        dry_run=True,
        init_git=False,
    )
    with patch("matt_stack.generators.fullstack.FullstackGenerator.run", return_value=True):
        result = _generate(config)
    assert result is True


def test_keyboard_interrupt_handling(tmp_path: Path) -> None:
    with (
        patch("matt_stack.commands.init._run_interactive", side_effect=KeyboardInterrupt),
        pytest.raises((SystemExit, click.exceptions.Exit)),
    ):
        run_init(output_dir=tmp_path)
