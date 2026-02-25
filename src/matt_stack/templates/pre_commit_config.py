"""Pre-commit configuration template."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_pre_commit_config(config: ProjectConfig) -> str:
    """Generate .pre-commit-config.yaml content."""
    repos: list[str] = []

    # Common hooks
    repos.append("""\
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files""")

    if config.has_backend:
        repos.append("""\
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format""")

    if config.has_frontend:
        repos.append("""\
  - repo: local
    hooks:
      - id: prettier
        name: prettier
        entry: bash -c 'cd frontend && bun run prettier --check .'
        language: system
        types_or: [javascript, jsx, ts, tsx, css, json, markdown]
        pass_filenames: false""")

    repos_block = "\n".join(repos)
    return f"repos:\n{repos_block}\n"
