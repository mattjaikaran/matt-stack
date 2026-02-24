"""Tests for CLI commands via typer.testing.CliRunner."""

from __future__ import annotations

from typer.testing import CliRunner

from matt_stack.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "matt-stack" in result.output


def test_info_command() -> None:
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "starter-fullstack" in result.output


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "Python" in result.output or "python" in result.output.lower()


def test_audit_bad_type() -> None:
    result = runner.invoke(app, ["audit", "--type", "nonexistent"])
    assert result.exit_code == 1
    assert "Unknown audit type" in result.output


def test_audit_did_you_mean() -> None:
    result = runner.invoke(app, ["audit", "--type", "qualiy"])
    assert result.exit_code == 1
    assert "Did you mean" in result.output
    assert "quality" in result.output


def test_audit_bad_path() -> None:
    result = runner.invoke(app, ["audit", "/nonexistent/path"])
    assert result.exit_code == 1
    assert "Not a directory" in result.output


def test_init_bad_preset() -> None:
    result = runner.invoke(app, ["init", "test", "--preset", "nonexistent", "-o", "/tmp"])
    assert result.exit_code == 1
    assert "Unknown preset" in result.output


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    # no_args_is_help=True causes exit code 0 or 2 depending on Typer version
    assert result.exit_code in (0, 2)
    assert "Usage" in result.output or "matt-stack" in result.output


def test_verbose_flag() -> None:
    result = runner.invoke(app, ["-v", "version"])
    assert result.exit_code == 0
    assert "matt-stack" in result.output


def test_presets_command_hidden_but_works() -> None:
    result = runner.invoke(app, ["presets"])
    assert result.exit_code == 0
    assert "starter-fullstack" in result.output
