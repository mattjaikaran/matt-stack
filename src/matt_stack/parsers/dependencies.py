"""Dependency file parser — pyproject.toml and package.json."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from matt_stack.parsers.utils import SKIP_DIRS


@dataclass
class Dependency:
    name: str
    version_constraint: str
    source_file: Path
    line: int
    dev: bool = False


@dataclass
class DependencyManifest:
    file: Path
    dependencies: list[Dependency] = field(default_factory=list)
    python_version: str = ""
    node_version: str = ""


_SECTION_RE = re.compile(r"^\[.*\]\s*$", re.MULTILINE)
_PROJECT_DEPS_RE = re.compile(r"^\[project\]\s*$", re.MULTILINE)
_OPT_DEPS_RE = re.compile(r"^\[project\.optional-dependencies\]\s*$", re.MULTILINE)
_UV_DEV_RE = re.compile(r"^\[tool\.uv\.dev-dependencies\]\s*$", re.MULTILINE)
_UV_SECTION_RE = re.compile(r"^\[tool\.uv\]\s*$", re.MULTILINE)
_DEPS_KEY_RE = re.compile(r"^dependencies\s*=\s*\[", re.MULTILINE)
_DEV_DEPS_KEY_RE = re.compile(r"^dev-dependencies\s*=\s*\[", re.MULTILINE)
_PYTHON_REQ_RE = re.compile(r"requires-python\s*=\s*\"(.+?)\"")


def _extract_list_block(text: str, start: int) -> tuple[str, int]:
    """Extract content of a [...] list starting from the opening bracket."""
    bracket_pos = text.find("[", start)
    if bracket_pos == -1:
        return "", start
    depth = 0
    for i in range(bracket_pos, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[bracket_pos + 1 : i], bracket_pos
    return text[bracket_pos + 1 :], bracket_pos


def _get_section_text(text: str, section_match: re.Match) -> str:  # type: ignore[type-arg]
    """Get text from a section header to the next section header."""
    start = section_match.end()
    next_section = _SECTION_RE.search(text, start)
    if next_section:
        return text[start : next_section.start()]
    return text[start:]


def _line_number_at_offset(text: str, offset: int) -> int:
    """Return 1-based line number for a character offset."""
    return text[:offset].count("\n") + 1


def _parse_dep_line(
    line: str, source_file: Path, line_num: int, *, dev: bool = False
) -> Dependency | None:
    """Parse a single dependency line like '"django>=5.0"' or '"requests"'."""
    line = line.strip().rstrip(",")
    if line.startswith('"') and line.endswith('"') or line.startswith("'") and line.endswith("'"):
        line = line[1:-1]
    else:
        return None

    if not line:
        return None

    m = re.match(r"([a-zA-Z0-9][a-zA-Z0-9_.\\-]*)(.*)", line)
    if not m:
        return None

    name = m.group(1).strip()
    constraint = m.group(2).strip()

    # Handle extras like "package[extra]>=1.0"
    if "[" in name:
        name = name.split("[")[0]

    return Dependency(
        name=name,
        version_constraint=constraint,
        source_file=source_file,
        line=line_num,
        dev=dev,
    )


def _parse_deps_from_section(
    text: str,
    section_match: re.Match,  # type: ignore[type-arg]
    key_re: re.Pattern,  # type: ignore[type-arg]
    source_file: Path,
    full_text: str,
    *,
    dev: bool = False,
) -> list[Dependency]:
    """Parse dependencies from a TOML section using a key regex."""
    deps: list[Dependency] = []
    section_text = _get_section_text(full_text, section_match)
    key_match = key_re.search(section_text)
    if not key_match:
        return deps

    list_content, bracket_pos = _extract_list_block(section_text, key_match.start())
    abs_offset = section_match.end() + bracket_pos
    base_line = _line_number_at_offset(full_text, abs_offset)

    for i, dep_line in enumerate(list_content.split("\n")):
        dep_line_stripped = dep_line.strip()
        if not dep_line_stripped or dep_line_stripped.startswith("#"):
            continue
        dep = _parse_dep_line(dep_line_stripped, source_file, base_line + i + 1, dev=dev)
        if dep:
            deps.append(dep)

    return deps


def parse_pyproject_toml(path: Path) -> DependencyManifest:
    """Parse pyproject.toml for dependencies (regex-based, no toml lib)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    manifest = DependencyManifest(file=path)

    # Extract python version requirement
    py_req = _PYTHON_REQ_RE.search(text)
    if py_req:
        manifest.python_version = py_req.group(1)

    # [project] dependencies = [...]
    project_match = _PROJECT_DEPS_RE.search(text)
    if project_match:
        manifest.dependencies.extend(
            _parse_deps_from_section(text, project_match, _DEPS_KEY_RE, path, text, dev=False)
        )

    # [project.optional-dependencies]
    opt_match = _OPT_DEPS_RE.search(text)
    if opt_match:
        section_text = _get_section_text(text, opt_match)
        for key_match in re.finditer(r"^(\w+)\s*=\s*\[", section_text, re.MULTILINE):
            list_content, bracket_pos = _extract_list_block(section_text, key_match.start())
            abs_offset = opt_match.end() + bracket_pos
            base_line = _line_number_at_offset(text, abs_offset)

            for i, dep_line in enumerate(list_content.split("\n")):
                dep_line_stripped = dep_line.strip()
                if not dep_line_stripped or dep_line_stripped.startswith("#"):
                    continue
                dep = _parse_dep_line(dep_line_stripped, path, base_line + i + 1, dev=True)
                if dep:
                    manifest.dependencies.append(dep)

    # [tool.uv.dev-dependencies] dependencies = [...]
    uv_dev_match = _UV_DEV_RE.search(text)
    if uv_dev_match:
        manifest.dependencies.extend(
            _parse_deps_from_section(text, uv_dev_match, _DEPS_KEY_RE, path, text, dev=True)
        )

    # [tool.uv] dev-dependencies = [...]
    uv_match = _UV_SECTION_RE.search(text)
    if uv_match:
        manifest.dependencies.extend(
            _parse_deps_from_section(text, uv_match, _DEV_DEPS_KEY_RE, path, text, dev=True)
        )

    return manifest


def parse_package_json(path: Path) -> DependencyManifest:
    """Parse package.json for dependencies."""
    text = path.read_text(encoding="utf-8", errors="replace")
    manifest = DependencyManifest(file=path)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return manifest

    engines = data.get("engines", {})
    if isinstance(engines, dict):
        manifest.node_version = engines.get("node", "")

    lines = text.split("\n")

    def _find_line(key: str) -> int:
        for i, line in enumerate(lines, 1):
            if f'"{key}"' in line:
                return i
        return 1

    deps = data.get("dependencies", {})
    if isinstance(deps, dict):
        for name, version in deps.items():
            manifest.dependencies.append(
                Dependency(
                    name=name,
                    version_constraint=str(version),
                    source_file=path,
                    line=_find_line(name),
                    dev=False,
                )
            )

    dev_deps = data.get("devDependencies", {})
    if isinstance(dev_deps, dict):
        for name, version in dev_deps.items():
            manifest.dependencies.append(
                Dependency(
                    name=name,
                    version_constraint=str(version),
                    source_file=path,
                    line=_find_line(name),
                    dev=True,
                )
            )

    return manifest


def find_dependency_files(project_path: Path) -> list[Path]:
    """Find pyproject.toml and package.json files up to 2 levels deep."""
    results: list[Path] = []
    seen: set[Path] = set()

    # Check root
    for name in ("pyproject.toml", "package.json"):
        candidate = project_path / name
        if candidate.is_file() and candidate not in seen:
            seen.add(candidate)
            results.append(candidate)

    # Check 1 and 2 levels deep
    for pattern in (
        "*/pyproject.toml",
        "*/package.json",
        "*/*/pyproject.toml",
        "*/*/package.json",
    ):
        for f in project_path.glob(pattern):
            if f in seen:
                continue
            if any(p in f.parts for p in SKIP_DIRS):
                continue
            seen.add(f)
            results.append(f)

    return sorted(results)
