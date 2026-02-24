"""Tests for the init command — preset mode, config mode, error handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import click.exceptions
import pytest

from matt_stack.commands.init import _generate, _run_from_preset, _run_interactive, run_init
from matt_stack.config import FrontendFramework, ProjectConfig, ProjectType, Variant


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


# ---------------------------------------------------------------------------
# Interactive wizard mode tests
# ---------------------------------------------------------------------------


def _mock_questionary_for_wizard(
    mock_q: object,
    *,
    name: str | None = "wizard-app",
    project_type: str = "fullstack",
    variant: str = "starter",
    framework: str | None = "react-vite",
    ios: bool | None = False,
    celery: bool | None = True,
    confirm: bool | None = True,
) -> None:
    """Configure a mock questionary object for _run_interactive.

    The wizard calls questionary methods in this order:
    1. text() — project name
    2. select() — project type
    3. select() — variant
    4. select() — frontend framework (only for fullstack / frontend-only)
    5. confirm() — include iOS (only for fullstack)
    6. confirm() — include Celery (only for fullstack / backend-only)
    7. confirm() — "Generate project?" final confirmation

    We use side_effect lists on the .ask() return to handle the ordering.
    """
    # text().ask() — project name
    mock_q.text.return_value.ask.return_value = name

    # select().ask() — called 2 or 3 times depending on project type
    select_answers: list[str | None] = [project_type, variant]
    if framework is not None:
        select_answers.append(framework)
    mock_q.select.return_value.ask.side_effect = select_answers

    # confirm().ask() — 1-3 calls depending on project type
    confirm_answers: list[bool | None] = []
    if project_type == "fullstack":
        confirm_answers.append(ios if ios is not None else False)
    if project_type in ("fullstack", "backend-only"):
        confirm_answers.append(celery if celery is not None else True)
    if confirm is not None:
        confirm_answers.append(confirm)
    mock_q.confirm.return_value.ask.side_effect = confirm_answers

    # questionary.Choice needs to be passthrough so the select() calls work
    mock_q.Choice = lambda title, value: value  # noqa: ARG005


def test_wizard_creates_fullstack(tmp_path: Path) -> None:
    """Interactive wizard should build a fullstack config with the chosen options."""
    with (
        patch("matt_stack.commands.init._generate") as mock_gen,
        patch("matt_stack.commands.init.questionary") as mock_q,
        patch(
            "matt_stack.commands.init.get_git_user",
            return_value=("Test Author", "test@test.com"),
        ),
    ):
        mock_gen.return_value = True
        _mock_questionary_for_wizard(
            mock_q,
            name="wizard-app",
            project_type="fullstack",
            variant="starter",
            framework="react-vite",
            ios=False,
            celery=True,
            confirm=True,
        )

        _run_interactive(tmp_path)

        mock_gen.assert_called_once()
        config: ProjectConfig = mock_gen.call_args[0][0]
        assert config.name == "wizard-app"
        assert config.project_type == ProjectType.FULLSTACK
        assert config.variant == Variant.STARTER
        assert config.frontend_framework == FrontendFramework.REACT_VITE
        assert config.include_ios is False
        assert config.use_celery is True
        assert config.author_name == "Test Author"
        assert config.author_email == "test@test.com"


def test_wizard_creates_backend_only(tmp_path: Path) -> None:
    """Interactive wizard should create a backend-only project when selected."""
    with (
        patch("matt_stack.commands.init._generate") as mock_gen,
        patch("matt_stack.commands.init.questionary") as mock_q,
        patch(
            "matt_stack.commands.init.get_git_user",
            return_value=("Test Author", "test@test.com"),
        ),
    ):
        mock_gen.return_value = True
        _mock_questionary_for_wizard(
            mock_q,
            name="backend-app",
            project_type="backend-only",
            variant="starter",
            framework=None,  # no framework prompt for backend-only
            ios=None,  # no iOS prompt for backend-only
            celery=True,
            confirm=True,
        )

        _run_interactive(tmp_path)

        mock_gen.assert_called_once()
        config: ProjectConfig = mock_gen.call_args[0][0]
        assert config.name == "backend-app"
        assert config.project_type == ProjectType.BACKEND_ONLY
        assert config.variant == Variant.STARTER
        assert config.use_celery is True


def test_wizard_cancel_on_name(tmp_path: Path) -> None:
    """Returning None from the name prompt should raise KeyboardInterrupt (caught by run_init)."""
    with (
        patch("matt_stack.commands.init._generate") as mock_gen,
        patch("matt_stack.commands.init.questionary") as mock_q,
        patch(
            "matt_stack.commands.init.get_git_user",
            return_value=("Test Author", "test@test.com"),
        ),
        pytest.raises((SystemExit, click.exceptions.Exit)),
    ):
        mock_q.text.return_value.ask.return_value = None
        # run_init wraps KeyboardInterrupt into typer.Exit
        run_init(output_dir=tmp_path)
        mock_gen.assert_not_called()


def test_wizard_cancel_on_confirm(tmp_path: Path) -> None:
    """Declining the final confirmation should skip generation."""
    with (
        patch("matt_stack.commands.init._generate") as mock_gen,
        patch("matt_stack.commands.init.questionary") as mock_q,
        patch(
            "matt_stack.commands.init.get_git_user",
            return_value=("Test Author", "test@test.com"),
        ),
    ):
        _mock_questionary_for_wizard(
            mock_q,
            name="wizard-app",
            project_type="fullstack",
            variant="starter",
            framework="react-vite",
            ios=False,
            celery=True,
            confirm=False,
        )

        _run_interactive(tmp_path)

        mock_gen.assert_not_called()


def test_wizard_default_name_skips_prompt(tmp_path: Path) -> None:
    """Passing default_name should skip the name prompt and use the provided name."""
    with (
        patch("matt_stack.commands.init._generate") as mock_gen,
        patch("matt_stack.commands.init.questionary") as mock_q,
        patch(
            "matt_stack.commands.init.get_git_user",
            return_value=("Test Author", "test@test.com"),
        ),
    ):
        mock_gen.return_value = True
        # Only need select + confirm answers since name prompt is skipped
        select_answers: list[str] = ["fullstack", "starter", "react-vite"]
        mock_q.select.return_value.ask.side_effect = select_answers
        mock_q.confirm.return_value.ask.side_effect = [False, True, True]  # ios, celery, confirm
        mock_q.Choice = lambda title, value: value  # noqa: ARG005

        _run_interactive(tmp_path, default_name="prenamed")

        # text() should never have been called
        mock_q.text.return_value.ask.assert_not_called()

        mock_gen.assert_called_once()
        config: ProjectConfig = mock_gen.call_args[0][0]
        assert config.name == "prenamed"
