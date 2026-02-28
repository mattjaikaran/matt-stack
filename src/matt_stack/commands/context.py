"""Context command: dump project context for AI agents."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from matt_stack.utils.console import console
from matt_stack.utils.package_manager import detect_package_manager
from matt_stack.utils.process import command_available, get_command_version


def _detect_components(path: Path) -> dict[str, bool]:
    """Detect which components exist in the project."""
    return {
        "backend": (path / "backend" / "pyproject.toml").exists(),
        "frontend": (path / "frontend" / "package.json").exists(),
        "ios": (path / "ios").is_dir() and any((path / "ios").glob("*.xcodeproj")),
        "docker": (path / "docker-compose.yml").exists(),
        "makefile": (path / "Makefile").exists(),
        "claude_md": (path / "CLAUDE.md").exists(),
    }


def _detect_backend_stack(path: Path) -> dict:
    """Extract backend stack details."""
    backend_dir = path / "backend"
    if not (backend_dir / "pyproject.toml").exists():
        return {}

    info: dict = {"language": "python", "package_manager": "uv"}

    pyproject = backend_dir / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    if "django" in content.lower():
        info["framework"] = "django"
    if "django-ninja" in content.lower():
        info["api"] = "django-ninja"
    if "celery" in content.lower():
        info["task_queue"] = "celery"

    return info


def _detect_frontend_stack(path: Path) -> dict:
    """Extract frontend stack details."""
    frontend_dir = path / "frontend"
    pkg_json = frontend_dir / "package.json"
    if not pkg_json.exists():
        return {}

    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    pm = detect_package_manager(path)

    info: dict = {"language": "typescript", "package_manager": pm.value}

    if "next" in deps:
        info["framework"] = "next.js"
    elif "vite" in deps:
        info["framework"] = "vite"

    if "react" in deps:
        info["ui_library"] = "react"
    if "tailwindcss" in deps or "@tailwindcss/vite" in deps:
        info["styling"] = "tailwind"

    scripts = pkg.get("scripts", {})
    if scripts:
        info["scripts"] = list(scripts.keys())

    return info


def _detect_env_vars(path: Path) -> list[str]:
    """Extract env var names from .env.example."""
    env_example = path / ".env.example"
    if not env_example.exists():
        return []

    names = []
    for line in env_example.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.append(line.split("=", 1)[0].strip())
    return names


def _detect_makefile_targets(path: Path) -> list[str]:
    """Extract Makefile target names."""
    makefile = path / "Makefile"
    if not makefile.exists():
        return []

    targets = []
    for line in makefile.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("\t") and not line.startswith("#") and ":" in line:
            target = line.split(":")[0].strip()
            if target and not target.startswith("."):
                targets.append(target)
    return targets


def _tool_versions() -> dict[str, str | None]:
    """Get versions of relevant dev tools."""
    tools = ["git", "uv", "bun", "node", "python", "docker", "make"]
    versions = {}
    for tool in tools:
        if command_available(tool):
            ver = get_command_version(tool)
            versions[tool] = ver.split("\n")[0] if ver else "installed"
    return versions


def build_context(path: Path) -> dict:
    """Build a complete project context dictionary."""
    components = _detect_components(path)
    ctx: dict = {
        "project_name": path.name,
        "project_path": str(path.resolve()),
        "components": components,
    }

    if components["backend"]:
        ctx["backend"] = _detect_backend_stack(path)
    if components["frontend"]:
        ctx["frontend"] = _detect_frontend_stack(path)

    env_vars = _detect_env_vars(path)
    if env_vars:
        ctx["env_vars"] = env_vars

    targets = _detect_makefile_targets(path)
    if targets:
        ctx["makefile_targets"] = targets

    ctx["tools"] = _tool_versions()
    return ctx


def format_context_markdown(ctx: dict) -> str:
    """Format project context as markdown for AI agents."""
    lines = [f"# Project: {ctx['project_name']}", ""]

    comps = ctx.get("components", {})
    active = [k for k, v in comps.items() if v]
    if active:
        lines.append(f"**Components:** {', '.join(active)}")
        lines.append("")

    if "backend" in ctx:
        be = ctx["backend"]
        lines.append("## Backend")
        for k, v in be.items():
            lines.append(f"- **{k}:** {v}")
        lines.append("")

    if "frontend" in ctx:
        fe = ctx["frontend"]
        lines.append("## Frontend")
        for k, v in fe.items():
            if k == "scripts":
                lines.append(f"- **scripts:** {', '.join(v)}")
            else:
                lines.append(f"- **{k}:** {v}")
        lines.append("")

    if "env_vars" in ctx:
        lines.append("## Environment Variables")
        lines.append(f"`{', '.join(ctx['env_vars'])}`")
        lines.append("")

    if "makefile_targets" in ctx:
        lines.append("## Makefile Targets")
        lines.append(f"`{', '.join(ctx['makefile_targets'])}`")
        lines.append("")

    if "tools" in ctx:
        lines.append("## Dev Tools")
        for tool, ver in ctx["tools"].items():
            lines.append(f"- **{tool}:** {ver}")
        lines.append("")

    return "\n".join(lines)


def run_context(
    path: Path,
    json_output: bool = False,
    output_file: str | None = None,
) -> None:
    """Dump project context for AI agent consumption."""
    if not path.is_dir():
        from matt_stack.utils.console import print_error

        print_error(f"Directory not found: {path}")
        raise typer.Exit(code=1)

    ctx = build_context(path)

    text = json.dumps(ctx, indent=2) if json_output else format_context_markdown(ctx)

    if output_file:
        out = Path(output_file)
        out.write_text(text, encoding="utf-8")
        from matt_stack.utils.console import print_success

        print_success(f"Context written to {out}")
    else:
        console.print(text)
