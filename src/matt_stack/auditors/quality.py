"""Code quality auditor — TODOs, stubs, mock data, debug statements, credentials."""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

from matt_stack.auditors.base import AuditConfig, AuditFinding, AuditType, BaseAuditor, Severity
from matt_stack.parsers.utils import SKIP_DIRS

# Patterns to scan for, grouped by severity
TODO_RE = re.compile(r"#\s*(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
STUB_RE = re.compile(r"^\s+(pass|\.\.\.|\.\.\.|raise NotImplementedError)\s*$", re.MULTILINE)
MOCK_RE = re.compile(
    r"\b(mock_|fake_|lorem\s*ipsum|placeholder|hardcoded|localhost:\d+)\b",
    re.IGNORECASE,
)
CREDENTIAL_RE = re.compile(
    r"\b(admin[/:]admin|password123|test@test\.com|changeme|secret123|12345)\b"
    r"|(?:sk_live_[a-zA-Z0-9]{20,})"
    r"|(?:AKIA[0-9A-Z]{16})"
    r"|(?:ghp_[a-zA-Z0-9]{36})"
    r"|(?:API_KEY\s*=\s*['\"][^'\"]{8,}['\"])",
    re.IGNORECASE,
)

# Debug statements
PY_DEBUG_RE = re.compile(r"^\s*(print\s*\(|breakpoint\s*\(|import\s+pdb)", re.MULTILINE)
JS_DEBUG_RE = re.compile(r"^\s*(console\.(log|debug|warn|info)\s*\(|debugger\b)", re.MULTILINE)

# File extensions to scan
PY_EXTS = {".py"}
JS_EXTS = {".ts", ".tsx", ".js", ".jsx"}
ALL_EXTS = PY_EXTS | JS_EXTS


class CodeQualityAuditor(BaseAuditor):
    audit_type = AuditType.QUALITY

    def __init__(self, config: AuditConfig) -> None:
        super().__init__(config)
        self._fix_count = 0

    def run(self) -> list[AuditFinding]:
        for path in self._collect_files():
            self._scan_file(path)
        return self.findings

    def _collect_files(self) -> list[Path]:
        """Collect all source files to scan."""
        files: list[Path] = []
        for ext in ALL_EXTS:
            for f in self.config.project_path.rglob(f"*{ext}"):
                if not any(p in f.parts for p in SKIP_DIRS):
                    files.append(f)
        return sorted(files)

    def _scan_file(self, path: Path) -> None:
        """Scan a single file for quality issues."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return

        lines = text.split("\n")
        is_python = path.suffix in PY_EXTS
        is_js = path.suffix in JS_EXTS
        is_test = "test" in path.stem.lower() or "spec" in path.stem.lower()
        rel_path = self._rel(path)
        file_modified = False

        for i, line in enumerate(lines, 1):
            # TODO/FIXME/HACK/XXX
            m = TODO_RE.search(line)
            if m:
                tag = m.group(1).upper()
                self.add_finding(
                    Severity.WARNING if tag in ("TODO", "FIXME") else Severity.INFO,
                    rel_path,
                    i,
                    f"{tag} comment: {line.strip()[:80]}",
                    f"Resolve or track this {tag}",
                )

            # Mock/placeholder data (skip test files)
            if not is_test:
                m = MOCK_RE.search(line)
                if m:
                    self.add_finding(
                        Severity.WARNING,
                        rel_path,
                        i,
                        f"Possible mock/placeholder: '{m.group(0)}'",
                        "Replace with real implementation or configuration",
                    )

            # Credentials
            m = CREDENTIAL_RE.search(line)
            if m:
                self.add_finding(
                    Severity.ERROR,
                    rel_path,
                    i,
                    f"Hardcoded credential: '{m.group(0)}'",
                    "Move to environment variable",
                )

            # Debug statements (skip test files)
            if not is_test:
                if is_python:
                    m = PY_DEBUG_RE.match(line)
                    if m:
                        self._handle_debug(rel_path, i, line, lines, is_python=True)
                        file_modified = True
                elif is_js:
                    m = JS_DEBUG_RE.match(line)
                    if m:
                        self._handle_debug(rel_path, i, line, lines, is_python=False)
                        file_modified = True

        # Write fixed file once after all debug lines collected
        if self.config.fix and file_modified:
            with contextlib.suppress(OSError):
                path.write_text("\n".join(lines), encoding="utf-8")

        # Stub functions (Python only, skip test files)
        if is_python and not is_test:
            for m in STUB_RE.finditer(text):
                line_num = text[: m.start()].count("\n") + 1
                self.add_finding(
                    Severity.WARNING,
                    rel_path,
                    line_num,
                    f"Stub implementation: {m.group(0).strip()}",
                    "Implement the function body",
                )

    def _handle_debug(
        self,
        rel_path: Path,
        line_num: int,
        line: str,
        lines: list[str],
        *,
        is_python: bool,
    ) -> None:
        """Handle a debug statement — report it, and optionally fix."""
        kind = "print()" if is_python else "console.log()"
        self.add_finding(
            Severity.WARNING,
            rel_path,
            line_num,
            f"Debug statement: {line.strip()[:60]}",
            f"Remove {kind} before shipping",
        )

        if self.config.fix:
            lines[line_num - 1] = ""
            self._fix_count += 1

    @property
    def fix_count(self) -> int:
        return self._fix_count
