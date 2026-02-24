"""Tests for type safety auditor."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig
from matt_stack.auditors.types import TypeSafetyAuditor


def _make_config(path: Path) -> AuditConfig:
    return AuditConfig(project_path=path)


def test_no_schemas_info(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("x = 1\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert any("No Pydantic schemas" in f.message for f in findings)


def test_missing_ts_interface(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "schemas.py").write_text(
        "from pydantic import BaseModel\n\n"
        "class UserSchema(BaseModel):\n"
        "    name: str\n"
        "    email: str\n"
    )
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    missing = [f for f in findings if "no matching TS interface" in f.message]
    assert len(missing) >= 1


def test_matching_ts_interface(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass UserSchema(BaseModel):\n    name: str\n"
    )
    types_dir = tmp_path / "types"
    types_dir.mkdir()
    (types_dir / "types.ts").write_text("export interface UserSchema {\n  name: string;\n}\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    missing = [f for f in findings if "no matching TS interface" in f.message]
    assert len(missing) == 0


def test_type_mismatch(tmp_path: Path) -> None:
    schemas = tmp_path / "schemas"
    schemas.mkdir()
    (schemas / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass ItemSchema(BaseModel):\n    count: int\n"
    )
    types_dir = tmp_path / "types"
    types_dir.mkdir()
    (types_dir / "types.ts").write_text("export interface ItemSchema {\n  count: string;\n}\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    mismatch = [f for f in findings if "Type mismatch" in f.message]
    assert len(mismatch) >= 1
