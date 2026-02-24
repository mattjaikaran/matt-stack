"""Test coverage auditor — coverage gaps, naming, feature mapping."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditFinding, AuditType, BaseAuditor, Severity
from matt_stack.parsers.python_schemas import find_schema_files, parse_pydantic_file
from matt_stack.parsers.test_files import (
    TestSuite,
    find_test_files,
    parse_pytest_file,
    parse_vitest_file,
)

# Feature areas to check for test coverage
FEATURE_AREAS = {
    "auth": ["auth", "login", "register", "signup", "token", "password"],
    "user": ["user", "profile", "account"],
    "crud": ["create", "read", "update", "delete", "list", "get", "post", "put"],
    "org": ["org", "organization", "team", "member", "role", "permission"],
}


class CoverageAuditor(BaseAuditor):
    audit_type = AuditType.TESTS

    def run(self) -> list[AuditFinding]:
        project = self.config.project_path
        test_files = find_test_files(project)

        if not test_files:
            self.add_finding(
                Severity.WARNING,
                Path("."),
                0,
                "No test files found",
                "Add tests in tests/ (pytest) or __tests__/ (vitest)",
            )
            return self.findings

        # Parse all test files
        suites = self._parse_suites(test_files)
        all_keywords = self._collect_keywords(suites)

        # Check coverage
        self._check_schema_coverage(project, suites)
        self._check_feature_coverage(all_keywords)
        self._check_naming(suites)
        self._check_empty_suites(suites)

        return self.findings

    def _parse_suites(self, test_files: list[Path]) -> list[TestSuite]:
        suites: list[TestSuite] = []
        for f in test_files:
            if f.suffix == ".py":
                suites.append(parse_pytest_file(f))
            elif f.suffix in (".ts", ".tsx", ".js", ".jsx"):
                suites.append(parse_vitest_file(f))
        return suites

    def _collect_keywords(self, suites: list[TestSuite]) -> set[str]:
        keywords: set[str] = set()
        for suite in suites:
            for tc in suite.test_cases:
                keywords.update(tc.keywords)
        return keywords

    def _check_schema_coverage(
        self,
        project: Path,
        suites: list[TestSuite],
    ) -> None:
        """Check if Pydantic schemas have corresponding tests."""
        schemas = []
        for f in find_schema_files(project):
            schemas.extend(parse_pydantic_file(f))

        if not schemas:
            return

        # Collect all test names
        test_names = set()
        for suite in suites:
            for tc in suite.test_cases:
                test_names.add(tc.name.lower())
                if tc.class_name:
                    test_names.add(tc.class_name.lower())

        for schema in schemas:
            name_lower = schema.name.lower().replace("schema", "")
            # Check if any test references this schema
            has_test = any(name_lower in tn for tn in test_names)
            if not has_test:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(schema.file),
                    schema.line,
                    f"No tests found for schema '{schema.name}'",
                    f"Add tests for {schema.name} CRUD and validation",
                )

    def _check_feature_coverage(self, tested_keywords: set[str]) -> None:
        """Check if major feature areas have test coverage."""
        for area, keywords in FEATURE_AREAS.items():
            covered = any(kw in tested_keywords for kw in keywords)
            if not covered:
                self.add_finding(
                    Severity.INFO,
                    Path("."),
                    0,
                    f"No tests cover the '{area}' feature area",
                    f"Add tests for: {', '.join(keywords[:3])}",
                )

    def _check_naming(self, suites: list[TestSuite]) -> None:
        """Check test naming conventions."""
        for suite in suites:
            for tc in suite.test_cases:
                if suite.framework == "pytest" and not tc.name.startswith("test_"):
                    self.add_finding(
                        Severity.INFO,
                        self._rel(tc.file),
                        tc.line,
                        f"Pytest function '{tc.name}' doesn't start with 'test_'",
                        "Prefix test functions with 'test_' for pytest discovery",
                    )

    def _check_empty_suites(self, suites: list[TestSuite]) -> None:
        """Find test files with no test cases."""
        for suite in suites:
            if not suite.test_cases:
                self.add_finding(
                    Severity.WARNING,
                    self._rel(suite.file),
                    1,
                    f"Empty test file: {self._rel(suite.file)}",
                    "Add test cases or remove the file",
                )
