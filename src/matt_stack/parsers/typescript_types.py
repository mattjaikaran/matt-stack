"""Parse TypeScript interface blocks from .ts/.tsx files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from matt_stack.parsers.utils import extract_block as _extract_block


@dataclass
class TSField:
    name: str
    type_str: str
    optional: bool = False


@dataclass
class TSInterface:
    name: str
    file: Path
    line: int
    fields: list[TSField] = field(default_factory=list)
    extends: str | None = None


# Pattern: export interface Name { or interface Name extends Base {
INTERFACE_RE = re.compile(
    r"^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{",
    re.MULTILINE,
)

# Pattern:   fieldName: type; or fieldName?: type;
TS_FIELD_RE = re.compile(
    r"^\s+(\w+)(\?)?:\s*(.+?)\s*;?\s*$",
    re.MULTILINE,
)


def parse_typescript_file(path: Path) -> list[TSInterface]:
    """Parse all interface declarations from a TypeScript file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    interfaces: list[TSInterface] = []

    for match in INTERFACE_RE.finditer(text):
        name = match.group(1)
        extends = match.group(2)
        line_num = text[: match.start()].count("\n") + 1

        # Find matching closing brace
        brace_start = text.index("{", match.start())
        body = _extract_block(text, brace_start)

        fields = _parse_ts_fields(body)
        interfaces.append(
            TSInterface(
                name=name,
                file=path,
                line=line_num,
                fields=fields,
                extends=extends,
            )
        )

    return interfaces


def _parse_ts_fields(body: str) -> list[TSField]:
    """Extract fields from an interface body."""
    fields: list[TSField] = []
    for match in TS_FIELD_RE.finditer(body):
        name = match.group(1)
        optional = match.group(2) == "?"
        type_str = match.group(3).strip().rstrip(";")

        # Also optional if type ends with | null or | undefined
        if re.search(r"\|\s*(null|undefined)\s*$", type_str):
            optional = True

        fields.append(TSField(name=name, type_str=type_str, optional=optional))
    return fields


def find_typescript_type_files(project_path: Path) -> list[Path]:
    """Find TypeScript files likely containing type definitions."""
    from matt_stack.parsers.utils import find_files

    patterns = [
        "**/types.ts",
        "**/types/*.ts",
        "**/types.tsx",
        "**/interfaces.ts",
        "**/interfaces/*.ts",
    ]
    return find_files(project_path, patterns)
