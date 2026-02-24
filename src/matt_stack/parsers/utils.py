"""Shared parser utilities."""

from __future__ import annotations

from pathlib import Path

SKIP_DIRS = frozenset(
    {
        ".venv",
        "venv",
        "node_modules",
        ".git",
        "__pycache__",
        "dist",
        "build",
        ".next",
    }
)


def find_files(project_path: Path, patterns: list[str]) -> list[Path]:
    """Find files matching patterns, deduplicating and skipping ignored dirs."""
    files: list[Path] = []
    for pattern in patterns:
        files.extend(project_path.glob(pattern))
    seen: set[Path] = set()
    result: list[Path] = []
    for f in files:
        if f in seen:
            continue
        if any(p in f.parts for p in SKIP_DIRS):
            continue
        seen.add(f)
        result.append(f)
    return sorted(result)


def extract_block(text: str, open_pos: int) -> str:
    """Extract content between matching braces."""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_pos + 1 : i]
    return text[open_pos + 1 :]
