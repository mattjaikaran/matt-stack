"""Tests for Pydantic schema parser."""

from __future__ import annotations

from pathlib import Path

from matt_stack.parsers.python_schemas import parse_pydantic_file


def test_parse_basic_schema(tmp_path: Path) -> None:
    f = tmp_path / "schemas.py"
    f.write_text("""\
from ninja import Schema

class UserSchema(Schema):
    name: str
    email: str
    age: int
    is_active: bool = True
""")
    schemas = parse_pydantic_file(f)
    assert len(schemas) == 1
    assert schemas[0].name == "UserSchema"
    assert len(schemas[0].fields) == 4
    names = [field.name for field in schemas[0].fields]
    assert "name" in names
    assert "email" in names
    assert "age" in names
    assert "is_active" in names


def test_parse_optional_fields(tmp_path: Path) -> None:
    f = tmp_path / "schemas.py"
    f.write_text("""\
from typing import Optional
from ninja import Schema

class ProfileSchema(Schema):
    bio: Optional[str]
    avatar: str | None
    website: str
""")
    schemas = parse_pydantic_file(f)
    assert len(schemas) == 1
    fields = {field.name: field for field in schemas[0].fields}
    assert fields["bio"].optional is True
    assert fields["avatar"].optional is True
    assert fields["website"].optional is False


def test_parse_field_constraints(tmp_path: Path) -> None:
    f = tmp_path / "schemas.py"
    f.write_text("""\
from pydantic import BaseModel, Field

class RegisterSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
""")
    schemas = parse_pydantic_file(f)
    assert len(schemas) == 1
    fields = {field.name: field for field in schemas[0].fields}
    assert "min_length" in fields["username"].constraints
    assert "max_length" in fields["username"].constraints
    assert fields["username"].constraints["min_length"] == "3"


def test_parse_multiple_schemas(tmp_path: Path) -> None:
    f = tmp_path / "schemas.py"
    f.write_text("""\
from ninja import Schema

class UserSchema(Schema):
    name: str

class TodoSchema(Schema):
    title: str
    done: bool
""")
    schemas = parse_pydantic_file(f)
    assert len(schemas) == 2
    names = {s.name for s in schemas}
    assert names == {"UserSchema", "TodoSchema"}


def test_parse_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "empty.py"
    f.write_text("# no schemas here\n")
    schemas = parse_pydantic_file(f)
    assert schemas == []
