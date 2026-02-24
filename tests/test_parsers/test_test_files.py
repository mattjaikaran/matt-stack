"""Tests for test file parser."""

from __future__ import annotations

from pathlib import Path

from matt_stack.parsers.test_files import parse_pytest_file, parse_vitest_file


def test_pytest_functions(tmp_path: Path) -> None:
    f = tmp_path / "test_auth.py"
    f.write_text(
        "def test_login():\n    assert True\n\n"
        "def test_register():\n    assert True\n\n"
        "def helper_func():\n    pass\n"
    )
    suite = parse_pytest_file(f)
    assert suite.framework == "pytest"
    # Only test_ prefixed functions counted
    assert len(suite.test_cases) == 2


def test_pytest_class(tmp_path: Path) -> None:
    f = tmp_path / "test_user.py"
    f.write_text(
        "class TestUser:\n"
        "    def test_create(self):\n        pass\n"
        "    def test_delete(self):\n        pass\n"
    )
    suite = parse_pytest_file(f)
    assert len(suite.test_cases) == 2
    assert all(tc.class_name == "TestUser" for tc in suite.test_cases)


def test_pytest_keywords(tmp_path: Path) -> None:
    f = tmp_path / "test_auth.py"
    f.write_text("def test_user_login():\n    assert True\n")
    suite = parse_pytest_file(f)
    assert "user" in suite.test_cases[0].keywords
    assert "login" in suite.test_cases[0].keywords


def test_pytest_async(tmp_path: Path) -> None:
    f = tmp_path / "test_async.py"
    f.write_text("async def test_async_handler():\n    assert True\n")
    suite = parse_pytest_file(f)
    assert len(suite.test_cases) == 1


def test_vitest_basic(tmp_path: Path) -> None:
    f = tmp_path / "app.test.ts"
    f.write_text(
        "describe('App', () => {\n"
        "  it('should render', () => {\n    expect(true).toBe(true)\n  })\n"
        "  test('should handle click', () => {\n    expect(1).toBe(1)\n  })\n"
        "})\n"
    )
    suite = parse_vitest_file(f)
    assert suite.framework == "vitest"
    assert len(suite.test_cases) == 2


def test_vitest_parent_describe(tmp_path: Path) -> None:
    f = tmp_path / "auth.test.tsx"
    f.write_text(
        "describe('Auth', () => {\n  it('logs in', () => { expect(true).toBe(true) })\n})\n"
    )
    suite = parse_vitest_file(f)
    assert suite.test_cases[0].class_name == "Auth"


def test_empty_test_file(tmp_path: Path) -> None:
    f = tmp_path / "test_empty.py"
    f.write_text("# empty test file\n")
    suite = parse_pytest_file(f)
    assert len(suite.test_cases) == 0
