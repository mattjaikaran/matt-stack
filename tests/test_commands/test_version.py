"""Tests for matt-stack version command."""

from __future__ import annotations

from unittest.mock import patch

from matt_stack.commands.version import (
    _parse_version,
    check_pypi_version,
)


class TestParseVersion:
    def test_parses_semver(self) -> None:
        assert _parse_version("0.1.0") == (0, 1, 0)
        assert _parse_version("1.2.3") == (1, 2, 3)

    def test_parses_single_part(self) -> None:
        assert _parse_version("5") == (5,)

    def test_parses_two_parts(self) -> None:
        assert _parse_version("2.1") == (2, 1)

    def test_stops_at_non_numeric(self) -> None:
        # Stops at first part that can't be parsed as int
        assert _parse_version("1.2.3a1") == (1, 2)
        assert _parse_version("1.0-dev") == (1,)


class TestCheckPypiVersion:
    def test_returns_none_on_network_failure(self) -> None:
        with patch("matt_stack.commands.version.urllib.request.urlopen") as mock_urlopen:
            import urllib.error

            mock_urlopen.side_effect = urllib.error.URLError("connection refused")
            assert check_pypi_version() is None

    def test_returns_none_on_timeout(self) -> None:
        with patch("matt_stack.commands.version.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError("timeout")
            assert check_pypi_version() is None

    def test_returns_version_on_success(self) -> None:
        with patch("matt_stack.commands.version.urllib.request.urlopen") as mock_urlopen:
            mock_resp = mock_urlopen.return_value.__enter__.return_value
            mock_resp.read.return_value = b'{"info": {"version": "1.2.3"}}'
            assert check_pypi_version() == "1.2.3"


class TestRunVersion:
    def test_outputs_version_string(self) -> None:
        from typer.testing import CliRunner

        from matt_stack.cli import app

        with patch("matt_stack.commands.version.check_pypi_version", return_value=None):
            runner = CliRunner()
            result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "matt-stack" in result.output
