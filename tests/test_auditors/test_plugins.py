"""Tests for plugin loader."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig, BaseAuditor
from matt_stack.auditors.plugins import discover_plugins

VALID_PLUGIN = '''\
"""A custom auditor plugin."""
from pathlib import Path
from matt_stack.auditors.base import AuditType, BaseAuditor, Severity, AuditFinding


class CustomAuditor(BaseAuditor):
    audit_type = AuditType.QUALITY

    def run(self) -> list[AuditFinding]:
        self.add_finding(
            severity=Severity.INFO,
            file=Path("test.py"),
            line=1,
            message="Plugin finding",
        )
        return self.findings
'''

BROKEN_PLUGIN = '''\
"""A plugin that raises on import."""
raise RuntimeError("Intentional import error")
'''

NO_AUDITOR_PLUGIN = '''\
"""A plugin with no BaseAuditor subclass."""

def some_function():
    return 42
'''


class TestDiscoverPlugins:
    """Tests for discover_plugins."""

    def test_returns_empty_when_no_plugin_dir(self, tmp_path: Path) -> None:
        result = discover_plugins(tmp_path)
        assert result == []

    def test_returns_empty_when_plugin_dir_empty(self, tmp_path: Path) -> None:
        (tmp_path / "matt-stack-plugins").mkdir()
        result = discover_plugins(tmp_path)
        assert result == []

    def test_loads_valid_plugin(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "custom_auditor.py").write_text(VALID_PLUGIN)

        result = discover_plugins(tmp_path)
        assert len(result) == 1
        assert result[0].__name__ == "CustomAuditor"
        assert issubclass(result[0], BaseAuditor)

    def test_plugin_can_run(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "custom_auditor.py").write_text(VALID_PLUGIN)

        classes = discover_plugins(tmp_path)
        assert len(classes) == 1

        config = AuditConfig(project_path=tmp_path)
        auditor = classes[0](config)
        findings = auditor.run()
        assert len(findings) == 1
        assert findings[0].message == "Plugin finding"

    def test_skips_underscore_files(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "_private.py").write_text(VALID_PLUGIN)
        (plugin_dir / "__init__.py").write_text("")

        result = discover_plugins(tmp_path)
        assert result == []

    def test_handles_import_errors_gracefully(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "broken.py").write_text(BROKEN_PLUGIN)

        # Should not raise
        result = discover_plugins(tmp_path)
        assert result == []

    def test_skips_files_without_auditor_class(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "no_auditor.py").write_text(NO_AUDITOR_PLUGIN)

        result = discover_plugins(tmp_path)
        assert result == []

    def test_loads_multiple_plugins(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()

        plugin_a = """\
from pathlib import Path
from matt_stack.auditors.base import AuditType, BaseAuditor, AuditFinding

class AlphaAuditor(BaseAuditor):
    audit_type = AuditType.QUALITY
    def run(self) -> list[AuditFinding]:
        return []
"""
        plugin_b = """\
from pathlib import Path
from matt_stack.auditors.base import AuditType, BaseAuditor, AuditFinding

class BetaAuditor(BaseAuditor):
    audit_type = AuditType.TESTS
    def run(self) -> list[AuditFinding]:
        return []
"""
        (plugin_dir / "alpha.py").write_text(plugin_a)
        (plugin_dir / "beta.py").write_text(plugin_b)

        result = discover_plugins(tmp_path)
        assert len(result) == 2
        names = {cls.__name__ for cls in result}
        assert names == {"AlphaAuditor", "BetaAuditor"}

    def test_mixed_valid_and_broken_plugins(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "matt-stack-plugins"
        plugin_dir.mkdir()
        (plugin_dir / "good.py").write_text(VALID_PLUGIN)
        (plugin_dir / "broken.py").write_text(BROKEN_PLUGIN)

        result = discover_plugins(tmp_path)
        assert len(result) == 1
        assert result[0].__name__ == "CustomAuditor"
