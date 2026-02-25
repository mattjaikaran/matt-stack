"""iOS add-on generator."""

from __future__ import annotations

from pathlib import Path

from matt_stack.config import REPO_URLS, ProjectConfig
from matt_stack.utils.console import print_info, print_success
from matt_stack.utils.git import clone_repo, remove_git_history

# File extensions that may contain MyApp references to replace
_IOS_TEXT_EXTENSIONS: set[str] = {
    ".swift",
    ".pbxproj",
    ".plist",
    ".xcscheme",
    ".storyboard",
    ".xib",
    ".entitlements",
}


def _rename_ios_directories(config: ProjectConfig) -> None:
    """Rename directories containing MyApp to the actual project name."""
    ios_dir = config.ios_dir
    # Sort deepest-first so child dirs are renamed before parents
    dirs_to_rename: list[Path] = sorted(
        [d for d in ios_dir.rglob("*") if d.is_dir() and "MyApp" in d.name],
        key=lambda d: len(d.parts),
        reverse=True,
    )
    for dir_path in dirs_to_rename:
        new_name = dir_path.name.replace("MyApp", config.display_name.replace(" ", ""))
        new_path = dir_path.parent / new_name
        if not new_path.exists():
            dir_path.rename(new_path)


def _customize_ios_project(config: ProjectConfig) -> int:
    """Replace MyApp references with the actual project name in iOS source files."""
    ios_dir = config.ios_dir
    if not ios_dir.exists():
        return 0

    replacements: dict[str, str] = {
        "MyApp": config.display_name.replace(" ", ""),
        "myapp": config.name,
        "my_app": config.python_package_name,
    }

    modified = 0

    for file_path in ios_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in _IOS_TEXT_EXTENSIONS:
            continue
        if any(part.startswith(".") for part in file_path.parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                modified += 1
        except (UnicodeDecodeError, PermissionError):
            continue

    return modified


def add_ios_to_project(config: ProjectConfig) -> bool:
    """Clone the iOS starter into an existing project and customize it."""
    ios_dir = config.ios_dir
    if ios_dir.exists():
        print_info("iOS directory already exists, skipping")
        return True

    url = REPO_URLS["swift-ios"]
    if not clone_repo(url, ios_dir):
        return False

    remove_git_history(ios_dir)
    _rename_ios_directories(config)
    count = _customize_ios_project(config)
    if count:
        print_info(f"Customized {count} iOS files")
    print_success("Added iOS client to project")
    return True
