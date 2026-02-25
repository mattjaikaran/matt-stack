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


def test_type_mismatch_detected(tmp_path: Path) -> None:
    """int should map to number, not string — expect WARNING about type mismatch."""
    schemas_dir = tmp_path / "backend" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass User(BaseModel):\n    age: int\n"
    )
    types_dir = tmp_path / "frontend" / "types"
    types_dir.mkdir(parents=True)
    (types_dir / "types.ts").write_text("export interface User {\n  age: string;\n}\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    mismatch = [
        f for f in findings if "Type mismatch" in f.message and f.severity.value == "warning"
    ]
    assert len(mismatch) == 1
    assert "int" in mismatch[0].message
    assert "string" in mismatch[0].message


def test_optionality_mismatch(tmp_path: Path) -> None:
    """Optional Python field paired with required TS field — expect INFO finding."""
    schemas_dir = tmp_path / "backend" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass Profile(BaseModel):\n    name: str | None = None\n"
    )
    types_dir = tmp_path / "frontend" / "types"
    types_dir.mkdir(parents=True)
    (types_dir / "types.ts").write_text("export interface Profile {\n  name: string;\n}\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    opt_mismatch = [
        f for f in findings if "Optionality mismatch" in f.message and f.severity.value == "info"
    ]
    assert len(opt_mismatch) == 1
    assert "optional" in opt_mismatch[0].message.lower()


def test_snake_to_camel_field_matching(tmp_path: Path) -> None:
    """Pydantic first_name should match TS firstName — no missing field warning."""
    schemas_dir = tmp_path / "backend" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass Contact(BaseModel):\n    first_name: str\n"
    )
    types_dir = tmp_path / "frontend" / "types"
    types_dir.mkdir(parents=True)
    (types_dir / "types.ts").write_text("export interface Contact {\n  firstName: string;\n}\n")
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    missing = [f for f in findings if "missing field" in f.message]
    assert len(missing) == 0


def test_zod_constraint_sync(tmp_path: Path) -> None:
    """Pydantic min_length without matching Zod .min() — expect INFO finding."""
    schemas_dir = tmp_path / "backend" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "schemas.py").write_text(
        "from pydantic import BaseModel, Field\n\n"
        "class UserSchema(BaseModel):\n"
        "    name: str = Field(min_length=3)\n"
    )
    zod_dir = tmp_path / "frontend" / "schemas"
    zod_dir.mkdir(parents=True)
    (zod_dir / "schemas.ts").write_text(
        "import { z } from 'zod';\nexport const userSchema = z.object({\n  name: z.string(),\n});\n"
    )
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    constraint = [
        f
        for f in findings
        if "min_length" in f.message and "no .min()" in f.message and f.severity.value == "info"
    ]
    assert len(constraint) == 1
    assert "3" in constraint[0].message


def test_zod_matching_by_name_variants(tmp_path: Path) -> None:
    """Pydantic UserSchema should match Zod userSchema (camelCase) — no missing warning."""
    schemas_dir = tmp_path / "backend" / "schemas"
    schemas_dir.mkdir(parents=True)
    (schemas_dir / "schemas.py").write_text(
        "from pydantic import BaseModel\n\nclass UserSchema(BaseModel):\n    email: str\n"
    )
    zod_dir = tmp_path / "frontend" / "schemas"
    zod_dir.mkdir(parents=True)
    (zod_dir / "schemas.ts").write_text(
        "import { z } from 'zod';\n"
        "export const userSchema = z.object({\n"
        "  email: z.string(),\n"
        "});\n"
    )
    auditor = TypeSafetyAuditor(_make_config(tmp_path))
    findings = auditor.run()
    # Should NOT have any "missing field" warnings for the Zod comparison
    zod_missing = [
        f for f in findings if "Zod schema" in f.message and "missing field" in f.message
    ]
    assert len(zod_missing) == 0


def test_type_compatibility_structure() -> None:
    """TYPE_COMPATIBILITY should have python-typescript pair with expected types."""
    from matt_stack.auditors.types import TYPE_COMPATIBILITY

    py_ts = TYPE_COMPATIBILITY[("python", "typescript")]
    assert py_ts["str"] == {"string"}
    assert py_ts["int"] == {"number"}
    assert py_ts["bool"] == {"boolean"}
    assert py_ts["list"] == {"array", "Array"}
    assert py_ts["datetime"] == {"string", "Date"}


def test_type_map_backward_compat() -> None:
    """TYPE_MAP should still work as alias for python-typescript pair."""
    from matt_stack.auditors.types import TYPE_COMPATIBILITY, TYPE_MAP

    assert TYPE_MAP is TYPE_COMPATIBILITY[("python", "typescript")]
    assert TYPE_MAP["str"] == {"string"}


def test_snake_to_pascal() -> None:
    """snake_to_pascal should convert to PascalCase."""
    from matt_stack.auditors.types import snake_to_pascal

    assert snake_to_pascal("first_name") == "FirstName"
    assert snake_to_pascal("user_id") == "UserId"
    assert snake_to_pascal("name") == "Name"


def test_name_converters() -> None:
    """NAME_CONVERTERS should have python-typescript and python-csharp pairs."""
    from matt_stack.auditors.types import NAME_CONVERTERS

    assert ("python", "typescript") in NAME_CONVERTERS
    assert ("python", "csharp") in NAME_CONVERTERS
    assert NAME_CONVERTERS[("python", "typescript")]("first_name") == "firstName"
    assert NAME_CONVERTERS[("python", "csharp")]("first_name") == "FirstName"
