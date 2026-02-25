"""Plugin loader for custom auditors."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from matt_stack.auditors.base import BaseAuditor
from matt_stack.utils.console import print_info, print_warning


def discover_plugins(project_path: Path) -> list[type[BaseAuditor]]:
    """Discover and load custom auditor plugins from matt-stack-plugins/ directory."""
    plugin_dir = project_path / "matt-stack-plugins"
    if not plugin_dir.is_dir():
        return []

    plugins: list[type[BaseAuditor]] = []
    for py_file in sorted(plugin_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            auditor_cls = _load_plugin(py_file)
            if auditor_cls:
                plugins.append(auditor_cls)
                print_info(f"Loaded plugin: {py_file.name}")
        except Exception as e:
            print_warning(f"Failed to load plugin {py_file.name}: {e}")

    return plugins


def _load_plugin(path: Path) -> type[BaseAuditor] | None:
    """Load a single plugin file and find the BaseAuditor subclass."""
    module_name = f"matt_stack_plugin_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    # Find BaseAuditor subclass in the module
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, BaseAuditor) and attr is not BaseAuditor:
            return attr

    return None
