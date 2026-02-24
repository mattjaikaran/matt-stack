"""Tests for the audit command orchestrator."""

from __future__ import annotations

from pathlib import Path

from matt_stack.commands.audit import run_audit


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal project with known issues."""
    proj = tmp_path / "test-proj"
    proj.mkdir()
    # Python file with debug statement and TODO
    (proj / "views.py").write_text(
        "# TODO: clean up\ndef handler():\n    print('debug')\n    return 42\n"
    )
    # JS file with console.log
    (proj / "app.tsx").write_text(
        "export function App() {\n  console.log('debug')\n  return null\n}\n"
    )
    return proj


def test_audit_finds_issues(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    # Should not raise
    run_audit(proj, no_todo=True)


def test_audit_json_output(tmp_path: Path, capsys) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, json_output=True, no_todo=True)
    # JSON output goes through Rich, so check capsys for structure
    # (Rich prints to its own console, but we can verify no crash)


def test_audit_single_type(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, audit_types=["quality"], no_todo=True)


def test_audit_fix_removes_debug(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, audit_types=["quality"], fix=True, no_todo=True)
    content = (proj / "views.py").read_text()
    assert "print" not in content


def test_audit_fix_multiple_debug_in_one_file(tmp_path: Path) -> None:
    """Regression: fix mode used to write after each line, losing intermediate fixes."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "views.py").write_text(
        "def handler():\n    print('one')\n    print('two')\n    print('three')\n    return 42\n"
    )
    run_audit(proj, audit_types=["quality"], fix=True, no_todo=True)
    content = (proj / "views.py").read_text()
    assert "print" not in content
    # All 3 should be gone, not just the last one
    assert content.count("print") == 0


def test_audit_writes_todo(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, audit_types=["quality"])
    todo = proj / "tasks" / "todo.md"
    assert todo.exists()
    content = todo.read_text()
    assert "<!-- audit:start -->" in content
    assert "<!-- audit:end -->" in content


def test_audit_idempotent_todo(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, audit_types=["quality"])
    run_audit(proj, audit_types=["quality"])
    todo = proj / "tasks" / "todo.md"
    content = todo.read_text()
    # Should have exactly one audit section
    assert content.count("<!-- audit:start -->") == 1


def test_audit_clean_project(tmp_path: Path) -> None:
    proj = tmp_path / "clean"
    proj.mkdir()
    (proj / "clean.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
    run_audit(proj, audit_types=["quality"], no_todo=True)


def test_audit_all_types(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    # Should run all 4 auditors without crashing
    run_audit(proj, no_todo=True)


def test_audit_no_todo_flag(tmp_path: Path) -> None:
    proj = _make_project(tmp_path)
    run_audit(proj, no_todo=True)
    assert not (proj / "tasks" / "todo.md").exists()
