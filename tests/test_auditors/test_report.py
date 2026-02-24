"""Tests for audit report writer."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditFinding, AuditReport, AuditType, Severity
from matt_stack.auditors.report import AUDIT_END, AUDIT_START, write_todo


def _make_report(findings: list[AuditFinding]) -> AuditReport:
    return AuditReport(findings=findings, auditors_run=["quality"])


def _finding(
    severity: Severity = Severity.WARNING,
    category: AuditType = AuditType.QUALITY,
    message: str = "Test finding",
) -> AuditFinding:
    return AuditFinding(
        category=category,
        severity=severity,
        file=Path("app.py"),
        line=10,
        message=message,
        suggestion="Fix it",
    )


def test_write_todo_creates_file(tmp_path: Path) -> None:
    report = _make_report([_finding()])
    result = write_todo(report, tmp_path)
    assert result is not None
    assert result.exists()
    content = result.read_text()
    assert AUDIT_START in content
    assert AUDIT_END in content
    assert "Test finding" in content


def test_write_todo_idempotent(tmp_path: Path) -> None:
    report = _make_report([_finding(message="First run")])
    write_todo(report, tmp_path)

    report2 = _make_report([_finding(message="Second run")])
    write_todo(report2, tmp_path)

    content = (tmp_path / "tasks" / "todo.md").read_text()
    assert content.count(AUDIT_START) == 1
    assert content.count(AUDIT_END) == 1
    assert "Second run" in content
    assert "First run" not in content


def test_write_todo_preserves_existing_content(tmp_path: Path) -> None:
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    todo = tasks_dir / "todo.md"
    todo.write_text("# My Project\n\n- [x] Setup done\n")

    report = _make_report([_finding()])
    write_todo(report, tmp_path)

    content = todo.read_text()
    assert "# My Project" in content
    assert "Setup done" in content
    assert AUDIT_START in content


def test_write_todo_skips_info_only(tmp_path: Path) -> None:
    report = _make_report([_finding(severity=Severity.INFO)])
    result = write_todo(report, tmp_path)
    assert result is None


def test_write_todo_errors_get_x_marker(tmp_path: Path) -> None:
    report = _make_report([_finding(severity=Severity.ERROR, message="Critical bug")])
    write_todo(report, tmp_path)
    content = (tmp_path / "tasks" / "todo.md").read_text()
    assert "[x]" in content
    assert "Critical bug" in content


def test_report_summary_counts() -> None:
    report = _make_report(
        [
            _finding(severity=Severity.ERROR),
            _finding(severity=Severity.WARNING),
            _finding(severity=Severity.WARNING),
            _finding(severity=Severity.INFO),
        ]
    )
    assert report.error_count == 1
    assert report.warning_count == 2
    assert report.info_count == 1


def test_report_to_dict() -> None:
    report = _make_report([_finding()])
    d = report.to_dict()
    assert "summary" in d
    assert "findings" in d
    assert d["summary"]["total"] == 1
