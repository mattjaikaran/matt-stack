"""Tests for iOS generator add-on."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from matt_stack.config import ProjectConfig, ProjectType, Variant
from matt_stack.generators.ios import add_ios_to_project


def _make_config(tmp_path: Path, **kwargs) -> ProjectConfig:
    defaults = {
        "name": "test-proj",
        "path": tmp_path / "test-proj",
        "project_type": ProjectType.FULLSTACK,
        "variant": Variant.STARTER,
        "include_ios": True,
    }
    defaults.update(kwargs)
    return ProjectConfig(**defaults)


@patch("matt_stack.generators.ios.remove_git_history")
@patch("matt_stack.generators.ios.clone_repo", return_value=True)
def test_add_ios_clones_and_removes_git(mock_clone, mock_rm_git, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config.path.mkdir(parents=True)

    result = add_ios_to_project(config)

    assert result is True
    mock_clone.assert_called_once()
    # Verify the destination is the ios directory
    call_args = mock_clone.call_args
    assert call_args[0][1] == config.ios_dir
    mock_rm_git.assert_called_once_with(config.ios_dir)


@patch("matt_stack.generators.ios.remove_git_history")
@patch("matt_stack.generators.ios.clone_repo", return_value=True)
def test_add_ios_skips_if_dir_exists(mock_clone, mock_rm_git, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config.ios_dir.mkdir(parents=True)

    result = add_ios_to_project(config)

    assert result is True
    mock_clone.assert_not_called()
    mock_rm_git.assert_not_called()


@patch("matt_stack.generators.ios.remove_git_history")
@patch("matt_stack.generators.ios.clone_repo", return_value=False)
def test_add_ios_returns_false_on_clone_failure(mock_clone, mock_rm_git, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config.path.mkdir(parents=True)

    result = add_ios_to_project(config)

    assert result is False
    mock_clone.assert_called_once()
    mock_rm_git.assert_not_called()


@patch("matt_stack.generators.ios.remove_git_history")
@patch("matt_stack.generators.ios.clone_repo", return_value=True)
def test_add_ios_uses_swift_ios_repo_url(mock_clone, mock_rm_git, tmp_path: Path) -> None:
    config = _make_config(tmp_path)
    config.path.mkdir(parents=True)

    add_ios_to_project(config)

    call_args = mock_clone.call_args
    url = call_args[0][0]
    assert "swift-ios" in url
