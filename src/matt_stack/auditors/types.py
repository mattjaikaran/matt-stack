"""Type safety auditor — Pydantic schema ↔ TS interface / Zod schema comparison."""

from __future__ import annotations

import re
from pathlib import Path

from matt_stack.auditors.base import AuditFinding, AuditType, BaseAuditor, Severity
from matt_stack.parsers.python_schemas import PydanticSchema, find_schema_files, parse_pydantic_file
from matt_stack.parsers.typescript_types import (
    TSInterface,
    find_typescript_type_files,
    parse_typescript_file,
)
from matt_stack.parsers.zod_schemas import ZodSchema, find_zod_files, parse_zod_file

# Python → TypeScript type mapping
TYPE_MAP: dict[str, set[str]] = {
    "str": {"string"},
    "int": {"number"},
    "float": {"number"},
    "bool": {"boolean"},
    "list": {"array", "Array"},
    "dict": {"object", "Record"},
    "datetime": {"string", "Date"},
    "date": {"string", "Date"},
    "uuid": {"string"},
    "UUID": {"string"},
    "Decimal": {"number", "string"},
}

# snake_case → camelCase conversion
SNAKE_RE = re.compile(r"_([a-z])")


def snake_to_camel(name: str) -> str:
    return SNAKE_RE.sub(lambda m: m.group(1).upper(), name)


def camel_to_snake(name: str) -> str:
    s = re.sub(r"([A-Z])", r"_\1", name)
    return s.lower().lstrip("_")


class TypeSafetyAuditor(BaseAuditor):
    audit_type = AuditType.TYPES

    def run(self) -> list[AuditFinding]:
        project = self.config.project_path

        # Parse all sources
        py_schemas = self._parse_python(project)
        ts_interfaces = self._parse_typescript(project)
        zod_schemas = self._parse_zod(project)

        if not py_schemas:
            self.add_finding(
                Severity.INFO,
                Path("."),
                0,
                "No Pydantic schemas found",
                "Define schemas in */schemas/*.py",
            )
            return self.findings

        # Compare Pydantic ↔ TS interfaces
        self._compare_with_ts(py_schemas, ts_interfaces)

        # Compare Pydantic ↔ Zod schemas
        self._compare_with_zod(py_schemas, zod_schemas)

        return self.findings

    def _parse_python(self, project: Path) -> list[PydanticSchema]:
        schemas: list[PydanticSchema] = []
        for f in find_schema_files(project):
            schemas.extend(parse_pydantic_file(f))
        return schemas

    def _parse_typescript(self, project: Path) -> list[TSInterface]:
        interfaces: list[TSInterface] = []
        for f in find_typescript_type_files(project):
            interfaces.extend(parse_typescript_file(f))
        return interfaces

    def _parse_zod(self, project: Path) -> list[ZodSchema]:
        schemas: list[ZodSchema] = []
        for f in find_zod_files(project):
            schemas.extend(parse_zod_file(f))
        return schemas

    def _compare_with_ts(
        self,
        py_schemas: list[PydanticSchema],
        ts_interfaces: list[TSInterface],
    ) -> None:
        ts_by_name: dict[str, TSInterface] = {i.name: i for i in ts_interfaces}

        for schema in py_schemas:
            ts = ts_by_name.get(schema.name)
            if not ts:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(schema.file),
                    schema.line,
                    f"Pydantic '{schema.name}' has no matching TS interface",
                    f"Create 'interface {schema.name}' in frontend types",
                )
                continue

            self._compare_fields_ts(schema, ts)

    def _compare_fields_ts(self, py: PydanticSchema, ts: TSInterface) -> None:
        ts_fields = {f.name: f for f in ts.fields}

        for pf in py.fields:
            # Try exact name or camelCase
            camel = snake_to_camel(pf.name)
            tf = ts_fields.get(pf.name) or ts_fields.get(camel)

            if not tf:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(ts.file),
                    ts.line,
                    f"TS interface '{ts.name}' missing field '{camel}' (from Python '{pf.name}')",
                    f"Add '{camel}: {self._py_to_frontend_type(pf.type_str)}' to {ts.name}",
                )
                continue

            # Check type compatibility
            expected_ts_types = TYPE_MAP.get(pf.type_str, set())
            if expected_ts_types and not any(t in tf.type_str for t in expected_ts_types):
                self.add_finding(
                    Severity.WARNING,
                    self._rel(ts.file),
                    ts.line,
                    f"Type mismatch: Python '{py.name}.{pf.name}' is '{pf.type_str}' "
                    f"but TS '{ts.name}.{tf.name}' is '{tf.type_str}'",
                    f"Expected TS type containing one of: {expected_ts_types}",
                )

            # Check optionality
            if pf.optional and not tf.optional:
                self.add_finding(
                    Severity.INFO,
                    self._rel(ts.file),
                    ts.line,
                    f"Optionality mismatch: '{py.name}.{pf.name}' is optional in Python "
                    f"but required in TS '{ts.name}.{tf.name}'",
                    f"Consider making '{tf.name}' optional with '?'",
                )

    def _compare_with_zod(
        self,
        py_schemas: list[PydanticSchema],
        zod_schemas: list[ZodSchema],
    ) -> None:
        # Try matching by name (e.g., UserSchema → userSchema, UserFormSchema, etc.)
        zod_by_name: dict[str, ZodSchema] = {}
        for z in zod_schemas:
            # Store both exact and lowered versions
            zod_by_name[z.name] = z
            zod_by_name[z.name.lower()] = z

        for schema in py_schemas:
            # Try various naming conventions
            candidates = [
                schema.name,
                schema.name.lower(),
                schema.name.replace("Schema", ""),
                f"{schema.name[0].lower()}{schema.name[1:]}",  # camelCase
            ]
            zod = None
            for c in candidates:
                zod = zod_by_name.get(c)
                if zod:
                    break

            if not zod:
                continue  # No matching Zod schema found (not necessarily an error)

            self._compare_fields_zod(schema, zod)

    def _compare_fields_zod(self, py: PydanticSchema, zod: ZodSchema) -> None:
        zod_fields = {f.name: f for f in zod.fields}

        for pf in py.fields:
            camel = snake_to_camel(pf.name)
            zf = zod_fields.get(pf.name) or zod_fields.get(camel)

            if not zf:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(zod.file),
                    zod.line,
                    f"Zod schema '{zod.name}' missing field '{camel}' (from Python '{pf.name}')",
                    f"Add '{camel}: z.{self._py_to_frontend_type(pf.type_str)}()' to {zod.name}",
                )
                continue

            # Check constraint sync (min_length ↔ .min())
            if "min_length" in pf.constraints and "min" not in zf.constraints:
                self.add_finding(
                    Severity.INFO,
                    self._rel(zod.file),
                    zod.line,
                    f"Python '{py.name}.{pf.name}' has min_length={pf.constraints['min_length']} "
                    f"but Zod '{zod.name}.{zf.name}' has no .min() constraint",
                    f"Add .min({pf.constraints['min_length']}) to match backend validation",
                )

            if "max_length" in pf.constraints and "max" not in zf.constraints:
                self.add_finding(
                    Severity.INFO,
                    self._rel(zod.file),
                    zod.line,
                    f"Python '{py.name}.{pf.name}' has max_length={pf.constraints['max_length']} "
                    f"but Zod '{zod.name}.{zf.name}' has no .max() constraint",
                    f"Add .max({pf.constraints['max_length']}) to match backend validation",
                )

    @staticmethod
    def _py_to_frontend_type(py_type: str) -> str:
        mapping = {"str": "string", "int": "number", "float": "number", "bool": "boolean"}
        return mapping.get(py_type, py_type)
