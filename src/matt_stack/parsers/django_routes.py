"""Parse Django Ninja route decorators and controller registration."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Route:
    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str
    function_name: str
    file: Path
    line: int
    has_auth: bool = False
    is_stub: bool = False


# Patterns for django-ninja decorators:
# @router.get("/path"), @api.post("/path"), @http_get("/path")
ROUTE_RE = re.compile(
    r"@(?:\w+)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"
    r"(?:.*?auth\s*=\s*(\w+))?"
    r"[^)]*\)",
    re.IGNORECASE | re.DOTALL,
)

# Alternative: @http_get, @http_post etc.
HTTP_DECORATOR_RE = re.compile(
    r"@http_(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# Function def following a route decorator
FUNC_DEF_RE = re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE)

# Router registration: router.add_router("/prefix", module.router)
ROUTER_REG_RE = re.compile(
    r"(?:api|router)\.add_router\s*\(\s*['\"]([^'\"]+)['\"]",
)

# Stub patterns: pass, ..., raise NotImplementedError
STUB_RE = re.compile(
    r"^\s+(pass|\.\.\.|\.\.\.|raise NotImplementedError)\s*$",
    re.MULTILINE,
)


def parse_routes_file(path: Path) -> list[Route]:
    """Parse all route decorators from a Python file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")
    routes: list[Route] = []

    # Find all route decorators
    for pattern in (ROUTE_RE, HTTP_DECORATOR_RE):
        for match in pattern.finditer(text):
            method = match.group(1).upper()
            route_path = match.group(2)
            line_num = text[:match.start()].count("\n") + 1

            # Check for auth parameter
            has_auth = False
            if pattern == ROUTE_RE and match.group(3):
                has_auth = match.group(3).lower() not in ("none", "false")
            elif "auth=" in match.group(0):
                has_auth = True

            # Find the function name (next def after this decorator)
            func_name = "unknown"
            remaining = text[match.end():]
            func_match = FUNC_DEF_RE.search(remaining)
            if func_match:
                func_name = func_match.group(1)

            # Check if function body is a stub
            is_stub = False
            if func_match:
                func_start = match.end() + func_match.end()
                # Look at next few lines for stub patterns
                func_line = text[:func_start].count("\n")
                body_lines = lines[func_line : func_line + 5]
                body_text = "\n".join(body_lines)
                is_stub = bool(STUB_RE.search(body_text))

            routes.append(Route(
                method=method,
                path=route_path,
                function_name=func_name,
                file=path,
                line=line_num,
                has_auth=has_auth,
                is_stub=is_stub,
            ))

    return routes


def find_route_files(project_path: Path) -> list[Path]:
    """Find Python files likely containing route definitions."""
    patterns = [
        "**/api.py", "**/api/*.py",
        "**/routes.py", "**/routes/*.py",
        "**/controllers.py", "**/controllers/*.py",
        "**/endpoints.py", "**/endpoints/*.py",
        "**/views.py", "**/views/*.py",
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
        if any(p in parts for p in (".venv", "venv", "node_modules", ".git", "__pycache__")):
            continue
        seen.add(f)
        result.append(f)
    return sorted(result)
