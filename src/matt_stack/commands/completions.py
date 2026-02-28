"""Shell completion installer."""

from __future__ import annotations

import os
import subprocess
import sys

import typer

from matt_stack.utils.console import console, print_error, print_info, print_success


def run_completions(install: bool = False, show: bool = False) -> None:
    """Install or show shell completions."""
    if show:
        # Show what shell is detected and the completion script
        shell = _detect_shell()
        if not shell:
            print_error("Could not detect shell. Set SHELL env var.")
            raise typer.Exit(code=1)
        print_info(f"Detected shell: {shell}")
        # Use typer's built-in completion generation
        result = subprocess.run(
            [sys.executable, "-m", "matt_stack.cli", "--show-completion"],
            capture_output=True,
            text=True,
        )
        if result.stdout:
            console.print(result.stdout)
        return

    if install:
        shell = _detect_shell()
        if not shell:
            print_error("Could not detect shell. Set SHELL env var.")
            raise typer.Exit(code=1)

        print_info(f"Installing completions for {shell}...")
        result = subprocess.run(
            [sys.executable, "-m", "matt_stack.cli", "--install-completion"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print_success(f"Completions installed for {shell}")
            print_info("Restart your shell or source your profile to activate.")
        else:
            output = result.stderr or result.stdout
            if output:
                console.print(output)
            print_error("Failed to install completions")
            raise typer.Exit(code=1)
        return

    # Default: show instructions
    shell = _detect_shell() or "your shell"
    console.print()
    console.print("[bold cyan]Shell Completions[/bold cyan]")
    console.print()
    console.print(f"  Detected shell: [bold]{shell}[/bold]")
    console.print()
    console.print("  [bold]Install:[/bold]")
    console.print("    matt-stack completions --install")
    console.print()
    console.print("  [bold]Show completion script:[/bold]")
    console.print("    matt-stack completions --show")
    console.print()


def _detect_shell() -> str | None:
    """Detect the current shell."""
    shell_path = os.environ.get("SHELL", "")
    if "zsh" in shell_path:
        return "zsh"
    if "bash" in shell_path:
        return "bash"
    if "fish" in shell_path:
        return "fish"
    if shell_path:
        return shell_path.split("/")[-1]
    return None
