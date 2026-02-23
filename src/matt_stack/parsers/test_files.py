"""Parse pytest and vitest test structures."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TestCase:
    name: str
    file: Path
    line: int
    class_name: str | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass
class TestSuite:
    file: Path
    framework: str  # "pytest" or "vitest"
    test_cases: list[TestCase] = field(default_factory=list)


# pytest: def test_xxx or async def test_xxx
PYTEST_FUNC_RE = re.compile(r"^(?:async\s+)?def\s+(test_\w+)\s*\(", re.MULTILINE)

# pytest: class TestXxx:
PYTEST_CLASS_RE = re.compile(r"^class\s+(Test\w+)\s*[:(]", re.MULTILINE)

# pytest: method inside class
PYTEST_METHOD_RE = re.compile(
    r"^\s{4}(?:async\s+)?def\s+(test_\w+)\s*\(", re.MULTILINE
)

# vitest/jest: describe("xxx", () => {
VITEST_DESCRIBE_RE = re.compile(
    r"describe\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE
)

# vitest/jest: it("xxx", or test("xxx",
VITEST_TEST_RE = re.compile(
    r"(?:it|test)\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE
)

# Keywords for feature mapping
FEATURE_KEYWORDS = [
    "auth", "login", "register", "signup", "user", "profile",
    "todo", "task", "item", "list",
    "org", "organization", "team", "member", "role", "permission",
    "api", "endpoint", "route",
    "create", "read", "update", "delete", "crud",
]


def parse_pytest_file(path: Path) -> TestSuite:
    """Parse test cases from a pytest file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    cases: list[TestCase] = []

    # Find standalone test functions
    for match in PYTEST_FUNC_RE.finditer(text):
        name = match.group(1)
        line = text[:match.start()].count("\n") + 1
        # Check it's not inside a class (not indented)
        line_start = text.rfind("\n", 0, match.start()) + 1
        if match.start() - line_start < 2:  # top-level
            cases.append(TestCase(
                name=name,
                file=path,
                line=line,
                keywords=_extract_keywords(name),
            ))

    # Find test classes and their methods
    for class_match in PYTEST_CLASS_RE.finditer(text):
        class_name = class_match.group(1)
        class_end = text.find("\nclass ", class_match.end())
        if class_end == -1:
            class_end = len(text)
        class_body = text[class_match.end():class_end]

        for method_match in PYTEST_METHOD_RE.finditer(class_body):
            method_name = method_match.group(1)
            line = text[:class_match.end() + method_match.start()].count("\n") + 1
            cases.append(TestCase(
                name=method_name,
                file=path,
                line=line,
                class_name=class_name,
                keywords=_extract_keywords(f"{class_name}_{method_name}"),
            ))

    return TestSuite(file=path, framework="pytest", test_cases=cases)


def parse_vitest_file(path: Path) -> TestSuite:
    """Parse test cases from a vitest/jest file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    cases: list[TestCase] = []

    # Find describe blocks as context
    describes: list[tuple[str, int, int]] = []
    for match in VITEST_DESCRIBE_RE.finditer(text):
        name = match.group(1)
        start = match.start()
        describes.append((name, start, 0))  # end computed lazily

    # Find individual test cases
    for match in VITEST_TEST_RE.finditer(text):
        name = match.group(1)
        line = text[:match.start()].count("\n") + 1

        # Find parent describe
        parent = None
        for desc_name, desc_start, _ in describes:
            if desc_start < match.start():
                parent = desc_name

        cases.append(TestCase(
            name=name,
            file=path,
            line=line,
            class_name=parent,
            keywords=_extract_keywords(name),
        ))

    return TestSuite(file=path, framework="vitest", test_cases=cases)


def _extract_keywords(name: str) -> list[str]:
    """Extract feature keywords from a test name."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")
    return [kw for kw in FEATURE_KEYWORDS if kw in name_lower]


def find_test_files(project_path: Path) -> list[Path]:
    """Find all test files in a project."""
    patterns = [
        # Python tests
        "**/test_*.py", "**/*_test.py", "**/tests.py",
        # JS/TS tests
        "**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx",
        "**/*.test.js", "**/*.test.jsx", "**/*.spec.js", "**/*.spec.jsx",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(project_path.glob(pattern))
    seen: set[Path] = set()
    result: list[Path] = []
    for f in files:
        if f in seen:
            continue
        parts = f.parts
        if any(p in parts for p in (".venv", "venv", "node_modules", ".git", "__pycache__")):
            continue
        seen.add(f)
        result.append(f)
    return sorted(result)
