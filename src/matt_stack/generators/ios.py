"""iOS add-on generator."""

from __future__ import annotations

from matt_stack.config import REPO_URLS, ProjectConfig
from matt_stack.utils.console import print_info, print_success
from matt_stack.utils.git import clone_repo, remove_git_history


def add_ios_to_project(config: ProjectConfig) -> bool:
    """Clone the iOS starter into an existing project."""
    ios_dir = config.ios_dir
    if ios_dir.exists():
        print_info("iOS directory already exists, skipping")
        return True

    url = REPO_URLS["swift-ios"]
    if not clone_repo(url, ios_dir):
        return False

    remove_git_history(ios_dir)
    print_success("Added iOS client to project")
    return True
