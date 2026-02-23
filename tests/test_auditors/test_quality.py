"""Tests for code quality auditor."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig, Severity
from matt_stack.auditors.quality import CodeQualityAuditor


def _make_config(path: Path, **kwargs) -> AuditConfig:
    return AuditConfig(project_path=path, **kwargs)


def test_finds_todo_comments(tmp_path: Path) -> None:
    f = tmp_path / "app.py"
    f.write_text("# TODO: fix this later\nx = 1\n# FIXME: broken\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    todo_findings = [f for f in findings if "TODO" in f.message or "FIXME" in f.message]
    assert len(todo_findings) == 2


def test_finds_hardcoded_credentials(tmp_path: Path) -> None:
    f = tmp_path / "config.py"
    f.write_text('USERNAME = "admin/admin"\nPASS = "password123"\n')
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    cred_findings = [f for f in findings if f.severity == Severity.ERROR]
    assert len(cred_findings) >= 1


def test_finds_debug_statements_python(tmp_path: Path) -> None:
    f = tmp_path / "views.py"
    f.write_text("def handler():\n    print('debug')\n    return 42\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    debug_findings = [f for f in findings if "Debug" in f.message or "print" in f.message]
    assert len(debug_findings) >= 1


def test_finds_debug_statements_js(tmp_path: Path) -> None:
    f = tmp_path / "app.tsx"
    f.write_text("export function App() {\n  console.log('test')\n  return null\n}\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    debug_findings = [f for f in findings if "Debug" in f.message or "console" in f.message]
    assert len(debug_findings) >= 1


def test_skips_test_files_for_mock_data(tmp_path: Path) -> None:
    f = tmp_path / "test_views.py"
    f.write_text('mock_user = "test@test.com"\n')
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    # mock_ in test files should not be flagged as quality issue (mock), but credential may
    mock_findings = [
        f for f in findings
        if "mock/placeholder" in f.message.lower()
    ]
    assert len(mock_findings) == 0


def test_finds_stub_functions(tmp_path: Path) -> None:
    f = tmp_path / "handlers.py"
    f.write_text("def create_user():\n    pass\n\ndef delete_user():\n    ...\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    stub_findings = [f for f in findings if "Stub" in f.message]
    assert len(stub_findings) >= 1


def test_fix_removes_print(tmp_path: Path) -> None:
    f = tmp_path / "views.py"
    f.write_text("def handler():\n    print('debug')\n    return 42\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path, fix=True))
    auditor.run()
    content = f.read_text()
    assert "print" not in content


def test_no_findings_on_clean_code(tmp_path: Path) -> None:
    f = tmp_path / "clean.py"
    f.write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert len(findings) == 0


def test_skips_venv_and_node_modules(tmp_path: Path) -> None:
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "bad.py").write_text("# TODO: this should be ignored\n")
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "bad.ts").write_text("console.log('ignored')\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert len(findings) == 0
