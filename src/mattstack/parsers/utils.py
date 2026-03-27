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
    """Extract content between matching braces, ignoring braces in strings."""
    depth = 0
    in_string: str | None = None  # None, "'", '"', or "`"
    i = open_pos
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\" and i + 1 < len(text):
                i += 2  # skip escaped character
                continue
            if ch == in_string:
                in_string = None
        else:
            if ch in ("'", '"', "`"):
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[open_pos + 1 : i]
        i += 1
    return text[open_pos + 1 :]
