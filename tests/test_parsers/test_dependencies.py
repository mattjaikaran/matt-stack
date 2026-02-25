"""Tests for dependency file parser."""

from __future__ import annotations

import json
from pathlib import Path

from matt_stack.parsers.dependencies import (
    find_dependency_files,
    parse_package_json,
    parse_pyproject_toml,
)


def test_parse_pyproject_pinned_deps(tmp_path: Path) -> None:
    f = tmp_path / "pyproject.toml"
    f.write_text(
        """[project]
name = "myapp"
dependencies = [
    "django>=5.0,<6.0",
    "pydantic>=2.0,<3.0",
]
"""
    )
    manifest = parse_pyproject_toml(f)
    assert len(manifest.dependencies) == 2
    names = {d.name for d in manifest.dependencies}
    assert names == {"django", "pydantic"}
    django_dep = next(d for d in manifest.dependencies if d.name == "django")
    assert ">=5.0" in django_dep.version_constraint
    assert "<6.0" in django_dep.version_constraint
    assert django_dep.dev is False


def test_parse_pyproject_unpinned_deps(tmp_path: Path) -> None:
    f = tmp_path / "pyproject.toml"
    f.write_text(
        """[project]
name = "myapp"
dependencies = [
    "requests",
    "flask",
]
"""
    )
    manifest = parse_pyproject_toml(f)
    assert len(manifest.dependencies) == 2
    for dep in manifest.dependencies:
        assert dep.version_constraint == ""


def test_parse_pyproject_dev_deps(tmp_path: Path) -> None:
    f = tmp_path / "pyproject.toml"
    f.write_text(
        """[project]
name = "myapp"
dependencies = [
    "django>=5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff",
]
"""
    )
    manifest = parse_pyproject_toml(f)
    assert len(manifest.dependencies) == 3
    dev_deps = [d for d in manifest.dependencies if d.dev]
    assert len(dev_deps) == 2
    regular = [d for d in manifest.dependencies if not d.dev]
    assert len(regular) == 1


def test_parse_pyproject_python_version(tmp_path: Path) -> None:
    f = tmp_path / "pyproject.toml"
    f.write_text(
        """[project]
name = "myapp"
requires-python = ">=3.12"
dependencies = []
"""
    )
    manifest = parse_pyproject_toml(f)
    assert manifest.python_version == ">=3.12"


def test_parse_package_json(tmp_path: Path) -> None:
    f = tmp_path / "package.json"
    data = {
        "name": "myapp",
        "dependencies": {"react": "^18.2.0", "next": "^14.0.0"},
        "devDependencies": {
            "typescript": "^5.0.0",
            "eslint": "^8.0.0",
        },
    }
    f.write_text(json.dumps(data, indent=4))
    manifest = parse_package_json(f)
    assert len(manifest.dependencies) == 4
    regular = [d for d in manifest.dependencies if not d.dev]
    assert len(regular) == 2
    dev = [d for d in manifest.dependencies if d.dev]
    assert len(dev) == 2
    react_dep = next(d for d in manifest.dependencies if d.name == "react")
    assert react_dep.version_constraint == "^18.2.0"


def test_parse_package_json_with_engines(tmp_path: Path) -> None:
    f = tmp_path / "package.json"
    data = {
        "name": "myapp",
        "engines": {"node": ">=18"},
        "dependencies": {},
    }
    f.write_text(json.dumps(data, indent=4))
    manifest = parse_package_json(f)
    assert manifest.node_version == ">=18"


def test_find_dependency_files(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """[project]
name = "x"
"""
    )
    (tmp_path / "package.json").write_text("{}")
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text(
        """[project]
name = "b"
"""
    )
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text("{}")
    files = find_dependency_files(tmp_path)
    assert len(files) == 3
    assert not any("node_modules" in str(f) for f in files)


def test_find_no_dependency_files(tmp_path: Path) -> None:
    files = find_dependency_files(tmp_path)
    assert files == []


def test_parse_empty_pyproject(tmp_path: Path) -> None:
    f = tmp_path / "pyproject.toml"
    f.write_text(
        """[build-system]
requires = ["hatchling"]
"""
    )
    manifest = parse_pyproject_toml(f)
    assert manifest.dependencies == []


def test_parse_invalid_json(tmp_path: Path) -> None:
    f = tmp_path / "package.json"
    f.write_text("not valid json {{{")
    manifest = parse_package_json(f)
    assert manifest.dependencies == []
