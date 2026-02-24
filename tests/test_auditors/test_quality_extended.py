"""Extended tests for code quality auditor — credential patterns, fix mode."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig, Severity
from matt_stack.auditors.quality import CodeQualityAuditor


def _make_config(path: Path, **kwargs) -> AuditConfig:
    return AuditConfig(project_path=path, **kwargs)


def test_detects_stripe_key(tmp_path: Path) -> None:
    f = tmp_path / "config.py"
    f.write_text('STRIPE_KEY = "sk_live_abcdefghijklmnopqrst"\n')
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    cred = [f for f in findings if f.severity == Severity.ERROR]
    assert len(cred) >= 1


def test_detects_aws_key(tmp_path: Path) -> None:
    f = tmp_path / "config.py"
    f.write_text('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n')
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    cred = [f for f in findings if f.severity == Severity.ERROR]
    assert len(cred) >= 1


def test_detects_github_token(tmp_path: Path) -> None:
    f = tmp_path / "config.py"
    f.write_text('GH_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"\n')
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    cred = [f for f in findings if f.severity == Severity.ERROR]
    assert len(cred) >= 1


def test_detects_api_key_assignment(tmp_path: Path) -> None:
    f = tmp_path / "config.py"
    f.write_text("API_KEY = 'my-secret-api-key-here'\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    cred = [f for f in findings if f.severity == Severity.ERROR]
    assert len(cred) >= 1


def test_fix_count_tracks_correctly(tmp_path: Path) -> None:
    f = tmp_path / "views.py"
    f.write_text("def handler():\n    print('one')\n    print('two')\n    return 42\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path, fix=True))
    auditor.run()
    assert auditor.fix_count == 2


def test_fix_js_debug(tmp_path: Path) -> None:
    f = tmp_path / "app.tsx"
    f.write_text(
        "export function App() {\n"
        "  console.log('debug1')\n"
        "  console.warn('debug2')\n"
        "  return null\n"
        "}\n"
    )
    auditor = CodeQualityAuditor(_make_config(tmp_path, fix=True))
    auditor.run()
    content = f.read_text()
    assert "console.log" not in content
    assert "console.warn" not in content
    assert auditor.fix_count == 2


def test_breakpoint_detected(tmp_path: Path) -> None:
    f = tmp_path / "views.py"
    f.write_text("def handler():\n    breakpoint()\n    return 42\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    debug = [f for f in findings if "Debug" in f.message]
    assert len(debug) >= 1


def test_hack_and_xxx_are_info(tmp_path: Path) -> None:
    f = tmp_path / "views.py"
    f.write_text("# HACK: workaround\n# XXX: review this\n")
    auditor = CodeQualityAuditor(_make_config(tmp_path))
    findings = auditor.run()
    info = [f for f in findings if f.severity == Severity.INFO]
    assert len(info) >= 2
