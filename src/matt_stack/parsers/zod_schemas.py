"""Parse Zod z.object() schemas from TypeScript/TSX files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ZodField:
    name: str
    type_str: str
    optional: bool = False
    constraints: dict[str, str] = field(default_factory=dict)


@dataclass
class ZodSchema:
    name: str
    file: Path
    line: int
    fields: list[ZodField] = field(default_factory=list)


# Pattern: const/export const Name = z.object({
ZOD_SCHEMA_RE = re.compile(
    r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*z\.object\(\s*\{",
    re.MULTILINE,
)

# Pattern:   fieldName: z.string().min(3), or z.number().optional(),
ZOD_FIELD_RE = re.compile(
    r"^\s+(\w+)\s*:\s*(z\..+?)\s*,?\s*$",
    re.MULTILINE,
)

# Zod type extractors
ZOD_TYPE_RE = re.compile(r"z\.(\w+)\(\)")

# Constraint patterns: .min(N), .max(N), .email(), .url(), .length(N)
ZOD_CONSTRAINT_RE = re.compile(r"\.(\w+)\(([^)]*)\)")


def parse_zod_file(path: Path) -> list[ZodSchema]:
    """Parse all z.object() schemas from a TypeScript file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    schemas: list[ZodSchema] = []

    for match in ZOD_SCHEMA_RE.finditer(text):
        name = match.group(1)
        line_num = text[:match.start()].count("\n") + 1

        # Find the opening brace of z.object({
        brace_pos = text.index("{", match.start() + len(match.group(0)) - 1)
        body = _extract_block(text, brace_pos)

        fields = _parse_zod_fields(body)
        schemas.append(ZodSchema(
            name=name,
            file=path,
            line=line_num,
            fields=fields,
        ))

    return schemas


def _extract_block(text: str, open_pos: int) -> str:
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


def _parse_zod_fields(body: str) -> list[ZodField]:
    """Extract fields from a z.object body."""
    fields: list[ZodField] = []
    for match in ZOD_FIELD_RE.finditer(body):
        name = match.group(1)
        chain = match.group(2).strip().rstrip(",")

        # Extract base type
        type_match = ZOD_TYPE_RE.search(chain)
        type_str = type_match.group(1) if type_match else "unknown"

        # Check optional
        optional = ".optional()" in chain or ".nullable()" in chain

        # Extract constraints
        constraints: dict[str, str] = {}
        for cm in ZOD_CONSTRAINT_RE.finditer(chain):
            method = cm.group(1)
            arg = cm.group(2).strip().strip("'\"")
            if method in ("min", "max", "length", "email", "url", "regex", "uuid"):
                constraints[method] = arg if arg else "true"
            elif method in ("optional", "nullable"):
                pass  # Already handled
            elif method not in (type_str,):  # Skip the base type call
                constraints[method] = arg if arg else "true"

        fields.append(ZodField(
            name=name,
            type_str=type_str,
            optional=optional,
            constraints=constraints,
        ))
    return fields


def find_zod_files(project_path: Path) -> list[Path]:
    """Find TypeScript files likely containing Zod schemas."""
    patterns = [
        "**/schemas.ts", "**/schemas/*.ts",
        "**/forms/**/*.tsx", "**/forms/**/*.ts",
        "**/validation.ts", "**/validators.ts",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(project_path.glob(pattern))
    seen: set[Path] = set()
    result: list[Path] = []
    for f in files:
        if f in seen:
            continue
        parts = f.parts
        if any(p in parts for p in ("node_modules", ".git", "dist", "build")):
            continue
        seen.add(f)
        result.append(f)
    return sorted(result)
