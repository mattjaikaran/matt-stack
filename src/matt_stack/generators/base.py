"""Base generator with common functionality."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from matt_stack.config import REPO_URLS, ProjectConfig
from matt_stack.utils.console import print_error, print_success
from matt_stack.utils.git import (
    clone_repo,
    create_initial_commit,
    init_repo,
    remove_git_history,
)


class BaseGenerator:
    """Base class for project generators."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.created_files: list[Path] = []

    def create_root_directory(self) -> bool:
        """Create the project root directory."""
        try:
            self.config.path.mkdir(parents=True, exist_ok=False)
            print_success(f"Created directory: {self.config.path}")
            return True
        except FileExistsError:
            print_error(f"Directory already exists: {self.config.path}")
            return False

    def clone_and_strip(self, repo_key: str, dest_name: str) -> bool:
        """Clone a repo and strip its .git history."""
        url = REPO_URLS[repo_key]
        dest = self.config.path / dest_name
        if not clone_repo(url, dest):
            return False
        remove_git_history(dest)
        # Remove the cli/ directory from django boilerplate if present
        cli_dir = dest / "cli"
        if cli_dir.exists():
            shutil.rmtree(cli_dir)
        return True

    def write_file(self, relative_path: str, content: str) -> None:
        """Write a file relative to the project root."""
        file_path = self.config.path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.created_files.append(file_path)

    def update_file(self, file_path: Path, replacements: dict[str, str]) -> None:
        """Apply string replacements to a file."""
        if not file_path.exists():
            print_error(f"File not found: {file_path}")
            return
        content = file_path.read_text()
        for old, new in replacements.items():
            content = content.replace(old, new)
        file_path.write_text(content)

    def update_file_regex(self, file_path: Path, pattern: str, replacement: str) -> None:
        """Apply regex replacement to a file."""
        if not file_path.exists():
            print_error(f"File not found: {file_path}")
            return
        content = file_path.read_text()
        content = re.sub(pattern, replacement, content)
        file_path.write_text(content)

    def update_json_file(self, file_path: Path, updates: dict) -> None:
        """Update fields in a JSON file (e.g., package.json)."""
        if not file_path.exists():
            print_error(f"File not found: {file_path}")
            return
        data = json.loads(file_path.read_text())
        data.update(updates)
        file_path.write_text(json.dumps(data, indent=2) + "\n")

    def init_git_repository(self) -> None:
        """Initialize a fresh git repo with initial commit."""
        if self.config.init_git:
            init_repo(self.config.path)
            create_initial_commit(self.config.path)
            print_success("Initialized git repository")

    def run(self) -> bool:
        """Generate the project. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement run()")
