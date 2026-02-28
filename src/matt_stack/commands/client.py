"""Client command: unified frontend package manager wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from matt_stack.utils.console import console, print_error, print_info, print_success
from matt_stack.utils.package_manager import (
    PackageManager,
    build_add_cmd,
    build_exec_cmd,
    build_install_cmd,
    build_remove_cmd,
    build_run_cmd,
    resolve_package_manager,
    run_pm_command,
)

client_app = typer.Typer(
    name="client",
    help="Frontend package manager commands (bun/npm/yarn/pnpm).",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _resolve(path: Path, pm_override: str | None) -> tuple[Path, PackageManager]:
    """Resolve working directory and package manager."""
    work_dir = path.resolve()

    frontend_dir = work_dir / "frontend"
    if frontend_dir.is_dir() and (frontend_dir / "package.json").exists():
        work_dir = frontend_dir

    if not (work_dir / "package.json").exists():
        print_error(f"No package.json found in {work_dir}")
        raise typer.Exit(code=1)

    pm = resolve_package_manager(work_dir, override=pm_override)
    return work_dir, pm


@client_app.command("add")
def add(
    packages: Annotated[list[str], typer.Argument(help="Packages to install")],
    dev: Annotated[bool, typer.Option("--dev", "-D", help="Install as dev dependency")] = False,
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Add packages to the frontend project."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_add_cmd(resolved_pm, packages, dev=dev)
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    if result.returncode == 0:
        print_success(f"Installed: {', '.join(packages)}")
    else:
        print_error(f"Failed with exit code {result.returncode}")
        raise typer.Exit(code=result.returncode)


@client_app.command("remove")
def remove(
    packages: Annotated[list[str], typer.Argument(help="Packages to remove")],
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Remove packages from the frontend project."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_remove_cmd(resolved_pm, packages)
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    if result.returncode == 0:
        print_success(f"Removed: {', '.join(packages)}")
    else:
        print_error(f"Failed with exit code {result.returncode}")
        raise typer.Exit(code=result.returncode)


@client_app.command("install")
def install(
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Install all frontend dependencies."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_install_cmd(resolved_pm)
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    if result.returncode == 0:
        print_success("Dependencies installed")
    else:
        print_error(f"Failed with exit code {result.returncode}")
        raise typer.Exit(code=result.returncode)


@client_app.command("run")
def run_script(
    script: Annotated[str, typer.Argument(help="Script name from package.json")],
    extra: Annotated[list[str] | None, typer.Argument(help="Extra arguments")] = None,
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Run a package.json script."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_run_cmd(resolved_pm, script, extra)
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    raise typer.Exit(code=result.returncode)


@client_app.command("dev")
def dev(
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Start the frontend dev server (runs 'dev' script)."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_run_cmd(resolved_pm, "dev")
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    raise typer.Exit(code=result.returncode)


@client_app.command("build")
def build(
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Build the frontend for production (runs 'build' script)."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_run_cmd(resolved_pm, "build")
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    if result.returncode == 0:
        print_success("Build complete")
    else:
        print_error(f"Build failed with exit code {result.returncode}")
        raise typer.Exit(code=result.returncode)


@client_app.command("exec")
def exec_bin(
    binary: Annotated[str, typer.Argument(help="Binary to execute (bunx/npx/pnpm dlx)")],
    extra: Annotated[list[str] | None, typer.Argument(help="Extra arguments")] = None,
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
    pm: Annotated[
        str | None, typer.Option("--pm", help="Package manager: bun, npm, yarn, pnpm")
    ] = None,
) -> None:
    """Execute a package binary (like bunx/npx)."""
    work_dir, resolved_pm = _resolve(path or Path.cwd(), pm)
    cmd = build_exec_cmd(resolved_pm, binary, extra)
    print_info(f"[{resolved_pm.value}] {cmd}")
    result = run_pm_command(cmd, cwd=work_dir)
    raise typer.Exit(code=result.returncode)


@client_app.command("which")
def which_pm(
    path: Annotated[Path | None, typer.Option("--path", "-p", help="Project path")] = None,
) -> None:
    """Show which package manager would be used and why."""
    work_dir = (path or Path.cwd()).resolve()
    pm = resolve_package_manager(work_dir)

    console.print(f"[bold cyan]Package manager:[/bold cyan] {pm.value}")

    for lockfile in ["bun.lockb", "bun.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]:
        for d in [work_dir, work_dir / "frontend"]:
            if (d / lockfile).exists():
                console.print(f"[dim]Detected from:[/dim] {d / lockfile}")
                return

    console.print("[dim]Source: default (bun)[/dim]")
