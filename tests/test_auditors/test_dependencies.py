"""Tests for dependency auditor."""

from __future__ import annotations

import json
from pathlib import Path

from matt_stack.auditors.base import AuditConfig, Severity
from matt_stack.auditors.dependencies import DependencyAuditor


def _make_config(path: Path, **kwargs) -> AuditConfig:
    return AuditConfig(project_path=path, **kwargs)


def _write_pyproject(path: Path, deps_toml: str) -> Path:
    """Write a pyproject.toml with given content."""
    f = path / "pyproject.toml"
    f.write_text(deps_toml)
    return f


def _write_package_json(path: Path, data: dict) -> Path:
    """Write a package.json with given data."""
    f = path / "package.json"
    f.write_text(json.dumps(data, indent=4))
    return f


def test_unpinned_dependency_warning(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """[project]
name = "myapp"
dependencies = [
    "requests",
    "django>=5.0,<6.0",
]
""",
    )
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    unpinned = [f for f in findings if "Unpinned" in f.message]
    assert len(unpinned) == 1
    assert "requests" in unpinned[0].message


def test_deprecated_package_warning_python(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """[project]
name = "myapp"
dependencies = [
    "nose>=1.0",
    "six>=1.0",
]
""",
    )
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    deprecated = [f for f in findings if "Deprecated" in f.message]
    assert len(deprecated) == 2


def test_deprecated_package_warning_js(tmp_path: Path) -> None:
    data = {
        "name": "myapp",
        "dependencies": {"moment": "^2.29.0", "react": "^18.0.0"},
    }
    _write_package_json(tmp_path, data)
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    deprecated = [f for f in findings if "Deprecated" in f.message]
    assert len(deprecated) == 1
    assert "moment" in deprecated[0].message


def test_duplicate_dependency_error(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """[project]
name = "myapp"
dependencies = [
    "requests>=2.0",
]

[project.optional-dependencies]
dev = [
    "requests>=2.0",
]
""",
    )
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    dupes = [f for f in findings if f.severity == Severity.ERROR and "Duplicate" in f.message]
    assert len(dupes) == 1


def test_overly_broad_constraint(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """[project]
name = "myapp"
dependencies = [
    "django>=5.0",
]
""",
    )
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    broad = [f for f in findings if "Overly broad" in f.message]
    assert len(broad) == 1


def test_clean_project_no_errors(tmp_path: Path) -> None:
    _write_pyproject(
        tmp_path,
        """[project]
name = "myapp"
dependencies = [
    "django>=5.0,<6.0",
    "pydantic>=2.0,<3.0",
]
""",
    )
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 0


def test_js_unpinned_dependency(tmp_path: Path) -> None:
    data = {"name": "myapp", "dependencies": {"react": "*"}}
    _write_package_json(tmp_path, data)
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    unpinned = [f for f in findings if "Unpinned" in f.message]
    assert len(unpinned) == 1


def test_js_duplicate_dependency(tmp_path: Path) -> None:
    data = {
        "name": "myapp",
        "dependencies": {"lodash": "^4.0.0"},
        "devDependencies": {"lodash": "^4.0.0"},
    }
    _write_package_json(tmp_path, data)
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    dupes = [f for f in findings if f.severity == Severity.ERROR and "Duplicate" in f.message]
    assert len(dupes) == 1


def test_no_dependency_files(tmp_path: Path) -> None:
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert len(findings) == 0


def test_typescript_version_conflict(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    admin = tmp_path / "admin"
    admin.mkdir()
    fe_data = {
        "name": "frontend",
        "devDependencies": {"typescript": "^5.0.0"},
    }
    admin_data = {
        "name": "admin",
        "devDependencies": {"typescript": "^4.9.0"},
    }
    _write_package_json(frontend, fe_data)
    _write_package_json(admin, admin_data)
    auditor = DependencyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    conflicts = [f for f in findings if "conflict" in f.message.lower()]
    assert len(conflicts) == 2
