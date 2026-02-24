"""Report writer — Rich console output + idempotent tasks/todo.md writing."""

from __future__ import annotations

import json
from pathlib import Path

from rich.table import Table

from matt_stack.auditors.base import AuditFinding, AuditReport, Severity
from matt_stack.utils.console import console

AUDIT_START = "<!-- audit:start -->"
AUDIT_END = "<!-- audit:end -->"

SEVERITY_COLORS = {
    Severity.ERROR: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "blue",
}

SEVERITY_ICONS = {
    Severity.ERROR: "[red]ERR[/red]",
    Severity.WARNING: "[yellow]WRN[/yellow]",
    Severity.INFO: "[blue]INF[/blue]",
}


def print_report(report: AuditReport) -> None:
    """Print audit findings as a Rich table."""
    if not report.findings:
        console.print("\n[green]No issues found.[/green]")
        return

    table = Table(title="Audit Findings", show_header=True, header_style="bold cyan")
    table.add_column("Sev", width=4)
    table.add_column("Category", width=10)
    table.add_column("Location", width=30)
    table.add_column("Message", min_width=40)

    for f in sorted(report.findings, key=lambda x: (x.severity.value, x.category.value)):
        sev = SEVERITY_ICONS[f.severity]
        loc = f"{f.file}:{f.line}" if f.line else str(f.file)
        table.add_row(sev, f.category.value, loc, f.message)

    console.print()
    console.print(table)

    # Summary line
    console.print(
        f"\n[bold]Summary:[/bold] "
        f"[red]{report.error_count} errors[/red], "
        f"[yellow]{report.warning_count} warnings[/yellow], "
        f"[blue]{report.info_count} info[/blue] "
        f"({len(report.findings)} total)"
    )


def print_json(report: AuditReport) -> None:
    """Print audit findings as JSON."""
    console.print_json(json.dumps(report.to_dict(), indent=2))


def write_todo(report: AuditReport, project_path: Path) -> Path | None:
    """Write/update audit findings to tasks/todo.md (idempotent)."""
    # Only write errors and warnings to todo
    actionable = [f for f in report.findings if f.severity in (Severity.ERROR, Severity.WARNING)]
    if not actionable:
        return None

    todo_dir = project_path / "tasks"
    todo_dir.mkdir(parents=True, exist_ok=True)
    todo_path = todo_dir / "todo.md"

    audit_section = _build_audit_section(actionable)

    if todo_path.exists():
        content = todo_path.read_text(encoding="utf-8")
        content = _replace_audit_section(content, audit_section)
    else:
        content = f"# Project TODO\n\n{audit_section}\n"

    todo_path.write_text(content, encoding="utf-8")
    return todo_path


def _build_audit_section(findings: list[AuditFinding]) -> str:
    """Build the markdown audit section."""
    lines = [AUDIT_START, "## Audit Findings", ""]

    # Group by category
    by_category: dict[str, list[AuditFinding]] = {}
    for f in findings:
        by_category.setdefault(f.category.value, []).append(f)

    for category, items in sorted(by_category.items()):
        lines.append(f"### {category.title()}")
        for item in items:
            icon = "x" if item.severity == Severity.ERROR else " "
            loc = f"`{item.file}:{item.line}`" if item.line else f"`{item.file}`"
            lines.append(f"- [{icon}] **{item.severity.value.upper()}** {loc} — {item.message}")
            if item.suggestion:
                lines.append(f"  - {item.suggestion}")
        lines.append("")

    lines.append(AUDIT_END)
    return "\n".join(lines)


def _replace_audit_section(content: str, new_section: str) -> str:
    """Replace existing audit section or append it."""
    if AUDIT_START in content and AUDIT_END in content:
        start = content.index(AUDIT_START)
        end = content.index(AUDIT_END) + len(AUDIT_END)
        return content[:start] + new_section + content[end:]
    else:
        # Append after existing content
        return content.rstrip() + "\n\n" + new_section + "\n"
