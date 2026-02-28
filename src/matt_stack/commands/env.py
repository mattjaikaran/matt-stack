"""Env command: environment variable management for .env files."""

from __future__ import annotations

import re
from pathlib import Path

import typer

from matt_stack.utils.console import console, create_table, print_error, print_info, print_success

# Common locations for .env files
ENV_PATHS = [
    ".env.example",
    ".env",
    "backend/.env.example",
    "backend/.env",
    "frontend/.env.example",
    "frontend/.env.local",
]


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse .env file into key -> value dict. Uses regex, no new deps."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            # Strip surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            result[key] = value
    return result


def _find_env_pairs(path: Path) -> list[tuple[Path, Path]]:
    """Find (example, actual) pairs: .env.example -> .env, etc."""
    pairs: list[tuple[Path, Path]] = []
    candidates = [
        (path / ".env.example", path / ".env"),
        (path / "backend" / ".env.example", path / "backend" / ".env"),
        (path / "frontend" / ".env.example", path / "frontend" / ".env.local"),
        (path / "frontend" / ".env.example", path / "frontend" / ".env"),
    ]
    for example_path, actual_path in candidates:
        if example_path.exists():
            pairs.append((example_path, actual_path))
    return pairs


def _mask_value(value: str) -> str:
    """Mask value: show first 3 chars + ***."""
    if not value:
        return "***"
    if len(value) <= 3:
        return "*" * len(value)
    return value[:3] + "***"


def run_env_check(path: Path) -> None:
    """Compare .env.example vs .env, report missing and extra vars."""
    path = path.resolve()
    if not path.is_dir():
        print_error(f"Directory not found: {path}")
        raise typer.Exit(code=1)

    pairs = _find_env_pairs(path)
    if not pairs:
        print_info("No .env.example files found.")
        return

    console.print()
    console.print("[bold cyan]matt-stack env check[/bold cyan]")
    console.print()

    any_issues = False
    for example_path, actual_path in pairs:
        rel_ex = example_path.relative_to(path)
        rel_act = actual_path.relative_to(path)
        example_vars = _parse_env_file(example_path)
        actual_vars = _parse_env_file(actual_path)

        missing = [k for k in example_vars if k not in actual_vars]
        extra = [k for k in actual_vars if k not in example_vars]

        if not missing and not extra:
            print_success(f"{rel_ex} ↔ {rel_act}: OK (all vars present, no extras)")
            continue

        any_issues = True
        table = create_table(f"{rel_ex} vs {rel_act}", ["Type", "Variables"])
        if missing:
            table.add_row("[yellow]Missing in .env[/yellow]", ", ".join(missing))
        if extra:
            table.add_row("[dim]Extra in .env[/dim]", ", ".join(extra))
        console.print(table)
        console.print()

    if any_issues:
        print_info("Run 'matt-stack env sync' to copy missing vars from .env.example")
    else:
        print_success("All .env files are in sync")


def run_env_sync(path: Path) -> None:
    """Copy missing vars from .env.example to .env with empty values."""
    path = path.resolve()
    if not path.is_dir():
        print_error(f"Directory not found: {path}")
        raise typer.Exit(code=1)

    pairs = _find_env_pairs(path)
    if not pairs:
        print_info("No .env.example files found.")
        return

    console.print()
    console.print("[bold cyan]matt-stack env sync[/bold cyan]")
    console.print()

    for example_path, actual_path in pairs:
        example_vars = _parse_env_file(example_path)
        actual_vars = _parse_env_file(actual_path)
        missing = [k for k in example_vars if k not in actual_vars]

        if not missing:
            print_info(f"{actual_path.relative_to(path)}: already in sync")
            continue

        # Build new content: keep existing, add missing with default/empty
        lines: list[str] = (
            actual_path.read_text(encoding="utf-8").splitlines() if actual_path.exists() else []
        )

        # Add missing vars
        for key in missing:
            default = example_vars.get(key, "")
            lines.append(f"{key}={default}")

        actual_path.parent.mkdir(parents=True, exist_ok=True)
        actual_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print_success(f"{actual_path.relative_to(path)}: added {len(missing)} vars")


def run_env_show(path: Path) -> None:
    """Show current .env vars with values masked."""
    path = path.resolve()
    if not path.is_dir():
        print_error(f"Directory not found: {path}")
        raise typer.Exit(code=1)

    env_files = [
        path / ".env",
        path / "backend" / ".env",
        path / "frontend" / ".env.local",
        path / "frontend" / ".env",
    ]

    console.print()
    console.print("[bold cyan]matt-stack env show[/bold cyan]")
    console.print()

    found_any = False
    for env_path in env_files:
        if not env_path.exists():
            continue
        found_any = True
        vars_dict = _parse_env_file(env_path)
        table = create_table(str(env_path.relative_to(path)), ["Variable", "Value (masked)"])
        for k, v in sorted(vars_dict.items()):
            table.add_row(k, _mask_value(v))
        console.print(table)
        console.print()

    if not found_any:
        print_info("No .env files found.")


def run_env(
    action: str,
    path: Path,
) -> None:
    """Dispatch to check, sync, or show."""
    action = action.lower().strip()
    if action == "check":
        run_env_check(path)
    elif action == "sync":
        run_env_sync(path)
    elif action == "show":
        run_env_show(path)
    else:
        print_error(f"Unknown action: {action}. Use: check, sync, show")
        raise typer.Exit(code=1)
