"""HTML dashboard report for audit findings."""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from matt_stack.auditors.base import AuditFinding, AuditReport


def generate_html_report(report: AuditReport, project_path: Path) -> str:
    """Generate a standalone HTML audit report."""
    findings_rows = _build_findings_rows(report.findings)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Audit Report — {escape(project_path.name)}</title>
    <style>{_css()}</style>
</head>
<body>
    {_header(project_path)}
    {_summary(report)}
    {_filters()}
    {_table(findings_rows)}
    {_footer()}
    <script>{_js()}</script>
</body>
</html>"""


def _css() -> str:
    """Return inline CSS styles."""
    return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f6fa; color: #2d3436; line-height: 1.6; }
        header { background: #2d3436; color: #fff; padding: 2rem; }
        header h1 { font-size: 1.5rem; font-weight: 600; }
        header p { color: #b2bec3; margin-top: 0.25rem; font-size: 0.9rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
        .cards { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
        .card { background: #fff; border-radius: 8px; padding: 1.25rem 1.5rem;
                flex: 1; min-width: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .card .label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em;
                       color: #636e72; margin-bottom: 0.25rem; }
        .card .value { font-size: 1.75rem; font-weight: 700; }
        .card.total .value { color: #2d3436; }
        .card.error .value { color: #d63031; }
        .card.warning .value { color: #fdcb6e; }
        .card.info .value { color: #0984e3; }
        .filters { margin-bottom: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }
        .filters button { padding: 0.4rem 1rem; border: 1px solid #dfe6e9; border-radius: 4px;
                          background: #fff; cursor: pointer;
                          font-size: 0.85rem; transition: all 0.15s; }
        .filters button:hover { background: #dfe6e9; }
        .filters button.active { background: #2d3436; color: #fff; border-color: #2d3436; }
        table { width: 100%; border-collapse: collapse; background: #fff;
                border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th { background: #dfe6e9; text-align: left; padding: 0.75rem 1rem; font-size: 0.8rem;
             text-transform: uppercase; letter-spacing: 0.05em; cursor: pointer;
             user-select: none; position: relative; }
        th:hover { background: #b2bec3; }
        th::after { content: ''; display: inline-block; margin-left: 0.4rem; }
        th.sort-asc::after { content: ' ^'; }
        th.sort-desc::after { content: ' v'; }
        td { padding: 0.65rem 1rem; border-top: 1px solid #f1f2f6; font-size: 0.9rem; }
        tr:hover td { background: #fafafa; }
        .badge { display: inline-block; padding: 0.15rem 0.6rem; border-radius: 3px;
                 font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-error { background: #ffeaa7; color: #d63031; background: #fab1a0; }
        .badge-warning { background: #ffeaa7; color: #e17055; }
        .badge-info { background: #81ecec; color: #00707a; }
        .empty-state { text-align: center; padding: 3rem; color: #636e72; }
        footer { text-align: center; padding: 2rem; color: #b2bec3; font-size: 0.8rem; }
    """


def _header(project_path: Path) -> str:
    """Build the page header."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<header>
    <div class="container">
        <h1>Audit Report &mdash; {escape(project_path.name)}</h1>
        <p>{escape(str(project_path))} &middot; {escape(now)}</p>
    </div>
</header>"""


def _summary(report: AuditReport) -> str:
    """Build summary cards."""
    return f"""<div class="container">
    <div class="cards">
        <div class="card total">
            <div class="label">Total Findings</div>
            <div class="value">{len(report.findings)}</div>
        </div>
        <div class="card error">
            <div class="label">Errors</div>
            <div class="value">{report.error_count}</div>
        </div>
        <div class="card warning">
            <div class="label">Warnings</div>
            <div class="value">{report.warning_count}</div>
        </div>
        <div class="card info">
            <div class="label">Info</div>
            <div class="value">{report.info_count}</div>
        </div>
    </div>"""


def _filters() -> str:
    """Build filter buttons."""
    return """<div class="filters">
        <button class="active" data-filter="all">All</button>
        <button data-filter="error">Errors</button>
        <button data-filter="warning">Warnings</button>
        <button data-filter="info">Info</button>
    </div>"""


def _build_findings_rows(findings: list[AuditFinding]) -> str:
    """Build HTML table rows for findings."""
    if not findings:
        return ""
    rows: list[str] = []
    for f in sorted(findings, key=lambda x: (x.severity.value, x.category.value)):
        badge_cls = f"badge-{f.severity.value}"
        loc = f"{escape(str(f.file))}:{f.line}" if f.line else escape(str(f.file))
        rows.append(
            f'<tr data-severity="{escape(f.severity.value)}" '
            f'data-category="{escape(f.category.value)}">'
            f'<td><span class="badge {badge_cls}">{escape(f.severity.value)}</span></td>'
            f"<td>{escape(f.category.value)}</td>"
            f"<td>{loc}</td>"
            f"<td>{escape(f.message)}</td>"
            f"<td>{escape(f.suggestion)}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _table(rows: str) -> str:
    """Build findings table."""
    if not rows:
        return '<div class="empty-state"><p>No findings. Project looks clean!</p></div></div>'
    return f"""<table id="findings-table">
        <thead>
            <tr>
                <th data-col="0">Severity</th>
                <th data-col="1">Category</th>
                <th data-col="2">Location</th>
                <th data-col="3">Message</th>
                <th data-col="4">Suggestion</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</div>"""


def _footer() -> str:
    """Build page footer."""
    return "<footer>Generated by matt-stack audit</footer>"


def _js() -> str:
    """Return inline JavaScript for filtering and sorting."""
    return """
    (function() {
        // --- Filtering ---
        var buttons = document.querySelectorAll('.filters button');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                buttons.forEach(function(b) { b.classList.remove('active'); });
                btn.classList.add('active');
                var filter = btn.getAttribute('data-filter');
                var rows = document.querySelectorAll('#findings-table tbody tr');
                rows.forEach(function(row) {
                    if (filter === 'all' || row.getAttribute('data-severity') === filter) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });

        // --- Sorting ---
        var headers = document.querySelectorAll('#findings-table th');
        var sortState = {};
        headers.forEach(function(th) {
            th.addEventListener('click', function() {
                var col = parseInt(th.getAttribute('data-col'));
                var tbody = document.querySelector('#findings-table tbody');
                if (!tbody) return;
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var asc = sortState[col] !== 'asc';
                sortState = {};
                sortState[col] = asc ? 'asc' : 'desc';
                headers.forEach(function(h) { h.classList.remove('sort-asc', 'sort-desc'); });
                th.classList.add(asc ? 'sort-asc' : 'sort-desc');
                rows.sort(function(a, b) {
                    var aText = a.children[col].textContent.toLowerCase();
                    var bText = b.children[col].textContent.toLowerCase();
                    if (aText < bText) return asc ? -1 : 1;
                    if (aText > bText) return asc ? 1 : -1;
                    return 0;
                });
                rows.forEach(function(row) { tbody.appendChild(row); });
            });
        });
    })();
    """
