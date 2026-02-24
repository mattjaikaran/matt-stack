"""Tests for shared parser utilities."""

from __future__ import annotations

from pathlib import Path

from matt_stack.parsers.utils import SKIP_DIRS, extract_block, find_files


def test_skip_dirs_is_frozenset() -> None:
    assert isinstance(SKIP_DIRS, frozenset)
    assert ".venv" in SKIP_DIRS
    assert "node_modules" in SKIP_DIRS


def test_find_files_basic(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("")
    (tmp_path / "b.py").write_text("")
    (tmp_path / "c.txt").write_text("")
    result = find_files(tmp_path, ["*.py"])
    assert len(result) == 2


def test_find_files_skips_venv(tmp_path: Path) -> None:
    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)
    (venv / "pkg.py").write_text("")
    (tmp_path / "app.py").write_text("")
    result = find_files(tmp_path, ["**/*.py"])
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_find_files_skips_node_modules(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "index.ts").write_text("")
    (tmp_path / "app.ts").write_text("")
    result = find_files(tmp_path, ["**/*.ts"])
    assert len(result) == 1


def test_find_files_deduplicates(tmp_path: Path) -> None:
    sub = tmp_path / "schemas"
    sub.mkdir()
    (sub / "user.py").write_text("")
    # Both patterns match the same file
    result = find_files(tmp_path, ["**/schemas/*.py", "**/user.py"])
    # Should have no duplicates
    assert len(result) == len(set(result))


def test_extract_block_simple() -> None:
    text = "{ a { b } c }"
    result = extract_block(text, 0)
    assert result == " a { b } c "


def test_extract_block_nested() -> None:
    text = "x { a { b { c } } d } y"
    result = extract_block(text, 2)
    assert "a" in result
    assert "d" in result


def test_extract_block_unclosed() -> None:
    text = "{ hello world"
    result = extract_block(text, 0)
    assert "hello world" in result
