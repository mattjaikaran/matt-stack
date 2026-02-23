"""Tests for TypeScript interface parser."""

from __future__ import annotations

from pathlib import Path

from matt_stack.parsers.typescript_types import parse_typescript_file


def test_parse_basic_interface(tmp_path: Path) -> None:
    f = tmp_path / "types.ts"
    f.write_text("""\
export interface User {
  name: string;
  email: string;
  age: number;
  isActive: boolean;
}
""")
    interfaces = parse_typescript_file(f)
    assert len(interfaces) == 1
    assert interfaces[0].name == "User"
    assert len(interfaces[0].fields) == 4
    names = [field.name for field in interfaces[0].fields]
    assert "name" in names
    assert "isActive" in names


def test_parse_optional_fields(tmp_path: Path) -> None:
    f = tmp_path / "types.ts"
    f.write_text("""\
interface Profile {
  bio?: string;
  avatar: string | null;
  website: string;
}
""")
    interfaces = parse_typescript_file(f)
    assert len(interfaces) == 1
    fields = {field.name: field for field in interfaces[0].fields}
    assert fields["bio"].optional is True
    assert fields["avatar"].optional is True
    assert fields["website"].optional is False


def test_parse_extends(tmp_path: Path) -> None:
    f = tmp_path / "types.ts"
    f.write_text("""\
interface Base {
  id: number;
}

export interface User extends Base {
  name: string;
}
""")
    interfaces = parse_typescript_file(f)
    assert len(interfaces) == 2
    user = [i for i in interfaces if i.name == "User"][0]
    assert user.extends == "Base"


def test_parse_multiple_interfaces(tmp_path: Path) -> None:
    f = tmp_path / "types.ts"
    f.write_text("""\
export interface User {
  name: string;
}

export interface Todo {
  title: string;
  done: boolean;
}
""")
    interfaces = parse_typescript_file(f)
    assert len(interfaces) == 2
    names = {i.name for i in interfaces}
    assert names == {"User", "Todo"}


def test_parse_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.ts"
    f.write_text("// no interfaces here\n")
    interfaces = parse_typescript_file(f)
    assert interfaces == []
