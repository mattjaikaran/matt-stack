"""Tests for iOS generator add-on."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from matt_stack.config import ProjectConfig, ProjectType, Variant
from matt_stack.generators.ios import (
    _customize_ios_project,
    _rename_ios_directories,
    add_ios_to_project,
)


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


# ---------------------------------------------------------------------------
# _customize_ios_project tests
# ---------------------------------------------------------------------------


def test_customize_replaces_myapp_in_swift_files(tmp_path: Path) -> None:
    """_customize_ios_project should replace MyApp references in .swift files."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    swift_file = ios_dir / "ContentView.swift"
    swift_file.write_text("import SwiftUI\nstruct MyApp: App {\n    // MyApp body\n}\n")

    count = _customize_ios_project(config)

    assert count == 1
    content = swift_file.read_text()
    # config name is "test-proj" -> display_name is "Test Proj" -> no spaces = "TestProj"
    assert "TestProj" in content
    assert "MyApp" not in content


def test_customize_replaces_in_pbxproj(tmp_path: Path) -> None:
    """_customize_ios_project should replace MyApp references in .pbxproj files."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    pbxproj = ios_dir / "MyApp.xcodeproj" / "project.pbxproj"
    pbxproj.parent.mkdir(parents=True)
    pbxproj.write_text('PRODUCT_NAME = "MyApp";\nTARGET_NAME = myapp;\n')

    count = _customize_ios_project(config)

    assert count == 1
    content = pbxproj.read_text()
    assert "TestProj" in content
    assert "test-proj" in content


def test_customize_replaces_in_plist(tmp_path: Path) -> None:
    """_customize_ios_project should replace MyApp references in .plist files."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    plist = ios_dir / "Info.plist"
    plist.write_text("<string>MyApp</string>\n<string>myapp</string>\n")

    count = _customize_ios_project(config)

    assert count == 1
    content = plist.read_text()
    assert "TestProj" in content
    assert "MyApp" not in content


def test_customize_skips_non_matching_extensions(tmp_path: Path) -> None:
    """Files with non-iOS extensions should be left untouched."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    txt_file = ios_dir / "notes.txt"
    txt_file.write_text("MyApp notes\n")

    py_file = ios_dir / "script.py"
    py_file.write_text("name = 'MyApp'\n")

    count = _customize_ios_project(config)

    assert count == 0
    assert txt_file.read_text() == "MyApp notes\n"
    assert py_file.read_text() == "name = 'MyApp'\n"


def test_customize_skips_hidden_directories(tmp_path: Path) -> None:
    """Files inside hidden directories (e.g. .git) should be skipped."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    hidden_dir = ios_dir / ".build"
    hidden_dir.mkdir()
    hidden_file = hidden_dir / "cache.swift"
    hidden_file.write_text("MyApp cached\n")

    count = _customize_ios_project(config)

    assert count == 0
    assert hidden_file.read_text() == "MyApp cached\n"


def test_customize_skips_files_without_myapp(tmp_path: Path) -> None:
    """Swift files that don't contain MyApp should not be counted as modified."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    swift_file = ios_dir / "Utils.swift"
    swift_file.write_text('func helper() -> String { return "ok" }\n')

    count = _customize_ios_project(config)

    assert count == 0


def test_customize_returns_zero_when_ios_dir_missing(tmp_path: Path) -> None:
    """Should return 0 when the iOS directory doesn't exist."""
    config = _make_config(tmp_path)

    count = _customize_ios_project(config)

    assert count == 0


def test_customize_skips_binary_files(tmp_path: Path) -> None:
    """Binary files with a matching extension should be skipped gracefully."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    # Create a binary file with a .swift extension
    binary_file = ios_dir / "binary.swift"
    binary_file.write_bytes(b"\x00\x01\x02MyApp\xff\xfe")

    # Should not raise, just skip the undecodable file
    count = _customize_ios_project(config)
    assert count == 0


# ---------------------------------------------------------------------------
# _rename_ios_directories tests
# ---------------------------------------------------------------------------


def test_rename_directories_renames_myapp(tmp_path: Path) -> None:
    """_rename_ios_directories should rename directories containing MyApp."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    myapp_dir = ios_dir / "MyApp"
    myapp_dir.mkdir()
    (myapp_dir / "ContentView.swift").write_text("placeholder")

    myapp_tests = ios_dir / "MyAppTests"
    myapp_tests.mkdir()
    (myapp_tests / "Tests.swift").write_text("placeholder")

    _rename_ios_directories(config)

    # "test-proj" -> display_name "Test Proj" -> no spaces "TestProj"
    assert (ios_dir / "TestProj").is_dir()
    assert (ios_dir / "TestProjTests").is_dir()
    assert not (ios_dir / "MyApp").exists()
    assert not (ios_dir / "MyAppTests").exists()
    # Files should have been moved with the directory
    assert (ios_dir / "TestProj" / "ContentView.swift").is_file()


def test_rename_directories_handles_nested(tmp_path: Path) -> None:
    """Nested MyApp directories should be renamed deepest-first."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    parent = ios_dir / "MyApp"
    child = parent / "MyAppCore"
    child.mkdir(parents=True)
    (child / "Core.swift").write_text("placeholder")

    _rename_ios_directories(config)

    # Child renamed first, then parent
    assert (ios_dir / "TestProj" / "TestProjCore").is_dir()
    assert (ios_dir / "TestProj" / "TestProjCore" / "Core.swift").is_file()


def test_rename_directories_skips_existing_target(tmp_path: Path) -> None:
    """If the target directory already exists, the rename should be skipped."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    myapp_dir = ios_dir / "MyApp"
    myapp_dir.mkdir()
    (myapp_dir / "Original.swift").write_text("original")

    # Pre-create the target so rename is skipped
    target_dir = ios_dir / "TestProj"
    target_dir.mkdir()
    (target_dir / "Existing.swift").write_text("existing")

    _rename_ios_directories(config)

    # MyApp should still exist since target was taken
    assert (ios_dir / "MyApp").is_dir()
    assert (ios_dir / "TestProj" / "Existing.swift").read_text() == "existing"


def test_rename_directories_no_myapp_dirs(tmp_path: Path) -> None:
    """When no directories contain MyApp, nothing should happen."""
    config = _make_config(tmp_path)
    ios_dir = config.ios_dir
    ios_dir.mkdir(parents=True)

    other_dir = ios_dir / "Sources"
    other_dir.mkdir()

    _rename_ios_directories(config)

    assert (ios_dir / "Sources").is_dir()
