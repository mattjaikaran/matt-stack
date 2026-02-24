"""Tests for test coverage auditor."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig
from matt_stack.auditors.tests import TestCoverageAuditor


def _make_config(path: Path) -> AuditConfig:
    return AuditConfig(project_path=path)


def test_no_test_files(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("x = 1\n")
    auditor = TestCoverageAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert any("No test files" in f.message for f in findings)


def test_empty_test_file(tmp_path: Path) -> None:
    (tmp_path / "test_empty.py").write_text("# empty\n")
    auditor = TestCoverageAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert any("Empty test file" in f.message for f in findings)


def test_finds_schema_without_tests(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass UserSchema(BaseModel):\n    name: str\n"
    )
    (tmp_path / "test_app.py").write_text("def test_something():\n    assert True\n")
    auditor = TestCoverageAuditor(_make_config(tmp_path))
    findings = auditor.run()
    missing = [f for f in findings if "No tests found for schema" in f.message]
    assert len(missing) >= 1


def test_feature_coverage(tmp_path: Path) -> None:
    (tmp_path / "test_misc.py").write_text("def test_math():\n    assert 1 + 1 == 2\n")
    auditor = TestCoverageAuditor(_make_config(tmp_path))
    findings = auditor.run()
    # Should report missing auth, user, etc. feature areas
    feature_gaps = [f for f in findings if "feature area" in f.message]
    assert len(feature_gaps) >= 1
