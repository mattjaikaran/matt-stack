"""Tests for matt-stack completions command."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from matt_stack.cli import app
from matt_stack.commands.completions import _detect_shell, run_completions


class TestDetectShell:
    def test_detects_zsh(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"}):
            assert _detect_shell() == "zsh"

    def test_detects_bash(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert _detect_shell() == "bash"

    def test_detects_fish(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/usr/local/bin/fish"}):
            assert _detect_shell() == "fish"

    def test_returns_none_when_empty(self) -> None:
        with patch.dict(os.environ, {"SHELL": ""}, clear=False):
            # SHELL might be unset in test env; patch to empty
            orig = os.environ.get("SHELL")
            try:
                os.environ["SHELL"] = ""
                assert _detect_shell() is None
            finally:
                if orig is not None:
                    os.environ["SHELL"] = orig

    def test_fallback_to_basename(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/usr/bin/ksh"}):
            assert _detect_shell() == "ksh"


class TestRunCompletions:
    def test_default_shows_instructions(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            run_completions()
        # Should not raise; default shows instructions

    def test_show_without_shell_exits_1(self) -> None:
        import typer

        with patch("matt_stack.commands.completions._detect_shell", return_value=None):
            with pytest.raises(typer.Exit) as exc_info:
                run_completions(show=True)
            assert exc_info.value.exit_code == 1


class TestCompletionsCliIntegration:
    def test_completions_command_default(self) -> None:
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}):
            runner = CliRunner()
            result = runner.invoke(app, ["completions"])
            assert result.exit_code == 0
            assert "Install" in result.output or "install" in result.output.lower()
            assert "matt-stack completions" in result.output
