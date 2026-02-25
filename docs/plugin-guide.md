# matt-stack Plugin Guide

Write custom audit rules by dropping Python files into `matt-stack-plugins/` in your project root.

## Quick Start

1. Create `matt-stack-plugins/` in your project root
2. Add a `.py` file with a `BaseAuditor` subclass
3. Run `matt-stack audit` -- your plugin runs automatically

## Basic Plugin

```python
"""Check for hardcoded API keys."""
from pathlib import Path
from matt_stack.auditors.base import AuditType, BaseAuditor, Severity

class ApiKeyAuditor(BaseAuditor):
    audit_type = AuditType.QUALITY

    def run(self):
        project = self.config.project_path
        for py_file in project.rglob("*.py"):
            text = py_file.read_text(errors="replace")
            for i, line in enumerate(text.split("\n"), 1):
                if "sk-" in line or "api_key" in line.lower():
                    self.add_finding(
                        Severity.ERROR,
                        self._rel(py_file),
                        i,
                        "Possible hardcoded API key",
                        "Use environment variables instead",
                    )
        return self.findings
```

## Plugin Metadata (Optional)

Add a `PLUGIN_META` dict for richer display:

```python
PLUGIN_META = {
    "name": "API Key Scanner",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "Scans for hardcoded API keys and secrets",
}
```

## Available AuditTypes

| Value | Description |
|-------|-------------|
| `AuditType.TYPES` | Type safety checks |
| `AuditType.QUALITY` | Code quality |
| `AuditType.ENDPOINTS` | Route/endpoint analysis |
| `AuditType.TESTS` | Test coverage |
| `AuditType.DEPENDENCIES` | Dependency checks |
| `AuditType.VULNERABILITIES` | Security vulnerabilities |

## Available Severity Levels

| Level | When to Use |
|-------|-------------|
| `Severity.ERROR` | Must fix before production |
| `Severity.WARNING` | Should fix, potential issue |
| `Severity.INFO` | Suggestion or informational |

## Tips

- Use `self._rel(path)` to convert absolute paths to relative
- Use `self.add_finding()` instead of appending to `self.findings` directly
- Keep plugins focused -- one concern per plugin
- Plugins are sorted alphabetically by filename
- Files starting with `_` are skipped
