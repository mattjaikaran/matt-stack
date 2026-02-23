"""Parse Pydantic Schema/BaseModel classes from Python files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PydanticField:
    name: str
    type_str: str
    optional: bool = False
    default: str | None = None
    constraints: dict[str, str] = field(default_factory=dict)


@dataclass
class PydanticSchema:
    name: str
    file: Path
    line: int
    fields: list[PydanticField] = field(default_factory=list)
    parent: str | None = None


# Pattern: class Name(Schema): or class Name(BaseModel):
CLASS_RE = re.compile(
    r"^class\s+(\w+)\s*\(\s*(Schema|BaseModel|ModelSchema)\s*\)\s*:", re.MULTILINE
)

# Pattern: field_name: type = default or Field(...)
FIELD_RE = re.compile(
    r"^\s{4}(\w+)\s*:\s*(.+?)(?:\s*=\s*(.+))?\s*$", re.MULTILINE
)

# Pattern: Field(min_length=X, max_length=Y, ...) constraints
CONSTRAINT_RE = re.compile(r"(\w+)\s*=\s*([^,\)]+)")

# Type patterns for optionality
OPTIONAL_RE = re.compile(r"Optional\[(.+)\]|(\w+)\s*\|\s*None|None\s*\|\s*(\w+)")


def parse_pydantic_file(path: Path) -> list[PydanticSchema]:
    """Parse all Pydantic schema classes from a Python file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    schemas: list[PydanticSchema] = []

    for match in CLASS_RE.finditer(text):
        class_name = match.group(1)
        parent = match.group(2)
        class_start = text[:match.start()].count("\n") + 1

        # Find the class body (indented lines after class declaration)
        body_lines: list[str] = []
        for line in lines[class_start:]:
            if line.strip() == "" or line.startswith("    ") or line.strip().startswith("#"):
                body_lines.append(line)
            elif body_lines:  # Non-indented non-empty line = end of class
                break

        body_text = "\n".join(body_lines)
        fields = _parse_fields(body_text)

        schemas.append(PydanticSchema(
            name=class_name,
            file=path,
            line=class_start,
            fields=fields,
            parent=parent,
        ))

    return schemas


def _parse_fields(body: str) -> list[PydanticField]:
    """Extract fields from a class body."""
    fields: list[PydanticField] = []

    for match in FIELD_RE.finditer(body):
        name = match.group(1)
        type_str = match.group(2).strip()
        default_val = match.group(3)

        # Skip class Meta, Config, methods, private attrs
        if name.startswith("_") or name in ("class", "def", "Meta", "Config"):
            continue

        optional = bool(OPTIONAL_RE.search(type_str))

        # Parse constraints from Field(...)
        constraints: dict[str, str] = {}
        if default_val and "Field(" in default_val:
            for cm in CONSTRAINT_RE.finditer(default_val):
                key, val = cm.group(1).strip(), cm.group(2).strip()
                if key not in ("default", "default_factory"):
                    constraints[key] = val

        fields.append(PydanticField(
            name=name,
            type_str=_normalize_type(type_str),
            optional=optional,
            default=default_val.strip() if default_val else None,
            constraints=constraints,
        ))

    return fields


def _normalize_type(t: str) -> str:
    """Normalize Python type to a canonical form."""
    t = t.strip()
    # Remove Optional wrapper
    m = OPTIONAL_RE.match(t)
    if m:
        inner = m.group(1) or m.group(2) or m.group(3)
        if inner:
            t = inner.strip()
    return t


def find_schema_files(project_path: Path) -> list[Path]:
    """Find Python files likely containing Pydantic schemas."""
    patterns = ["**/schemas.py", "**/schemas/*.py", "**/schema.py", "**/models.py"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(project_path.glob(pattern))
    # Deduplicate and filter out venvs/node_modules
    seen: set[Path] = set()
    result: list[Path] = []
    for f in files:
        if f in seen:
            continue
        parts = f.parts
        if any(p in parts for p in (".venv", "venv", "node_modules", ".git", "__pycache__")):
            continue
        seen.add(f)
        result.append(f)
    return sorted(result)
