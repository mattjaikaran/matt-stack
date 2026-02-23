"""Audit command orchestrator."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig, AuditReport, AuditType, BaseAuditor
from matt_stack.auditors.endpoints import EndpointAuditor
from matt_stack.auditors.quality import CodeQualityAuditor
from matt_stack.auditors.report import print_json, print_report, write_todo
from matt_stack.auditors.tests import TestCoverageAuditor
from matt_stack.auditors.types import TypeSafetyAuditor
from matt_stack.utils.console import console, print_error, print_info, print_success, print_warning

AUDITOR_CLASSES: dict[AuditType, type[BaseAuditor]] = {
    AuditType.TYPES: TypeSafetyAuditor,
    AuditType.QUALITY: CodeQualityAuditor,
    AuditType.ENDPOINTS: EndpointAuditor,
    AuditType.TESTS: TestCoverageAuditor,
}


def run_audit(
    path: Path,
    *,
    audit_types: list[str] | None = None,
    live: bool = False,
    no_todo: bool = False,
    json_output: bool = False,
    fix: bool = False,
) -> None:
    """Run audit on a project directory."""
    project_path = path.resolve()

    if not project_path.is_dir():
        print_error(f"Not a directory: {project_path}")
        raise SystemExit(1)

    # Parse audit type strings
    types: list[AuditType] | None = None
    if audit_types:
        types = []
        for t in audit_types:
            try:
                types.append(AuditType(t))
            except ValueError:
                valid = ", ".join(at.value for at in AuditType)
                print_error(f"Unknown audit type: '{t}'. Valid: {valid}")
                raise SystemExit(1) from None

    config = AuditConfig(
        project_path=project_path,
        audit_types=types,
        live=live,
        write_todo=not no_todo,
        json_output=json_output,
        fix=fix,
    )

    if not json_output:
        console.print(f"\n[bold cyan]Auditing:[/bold cyan] {project_path}\n")

    report = AuditReport()

    # Run each applicable auditor
    for audit_type, auditor_cls in AUDITOR_CLASSES.items():
        if not config.should_run(audit_type):
            continue

        if not json_output:
            print_info(f"Running {audit_type.value} audit...")

        auditor = auditor_cls(config)
        findings = auditor.run()
        report.findings.extend(findings)
        report.auditors_run.append(audit_type.value)

        if not json_output and findings:
            console.print(f"  Found {len(findings)} issues")

    # Output results
    if json_output:
        print_json(report)
    else:
        print_report(report)

        # Auto-fix summary
        if fix:
            for audit_type, auditor_cls in AUDITOR_CLASSES.items():
                if auditor_cls == CodeQualityAuditor and config.should_run(audit_type):
                    # Re-check the fix_count from the quality auditor instance
                    # (we already ran it, so count was tracked)
                    pass
            print_info("Auto-fix applied where possible (debug statements removed)")

        # Write to todo.md
        if config.write_todo:
            todo_path = write_todo(report, project_path)
            if todo_path:
                print_success(f"Wrote findings to {todo_path}")
            elif report.findings:
                print_info("No actionable findings to write to todo.md")

        # Exit summary
        if report.error_count:
            print_warning(f"{report.error_count} errors need attention")
        elif report.warning_count:
            print_info(f"{report.warning_count} warnings to review")
        else:
            print_success("Project looks clean!")
