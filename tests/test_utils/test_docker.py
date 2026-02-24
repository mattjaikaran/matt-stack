"""Tests for Docker utility functions."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from matt_stack.utils.docker import docker_available, docker_compose_available, docker_running

# --- docker_available ---


@patch("matt_stack.utils.docker.shutil.which", return_value="/usr/local/bin/docker")
def test_docker_available_found(mock_which) -> None:
    assert docker_available() is True
    mock_which.assert_called_once_with("docker")


@patch("matt_stack.utils.docker.shutil.which", return_value=None)
def test_docker_available_not_found(mock_which) -> None:
    assert docker_available() is False
    mock_which.assert_called_once_with("docker")


# --- docker_compose_available ---


@patch("matt_stack.utils.docker.subprocess.run")
def test_docker_compose_available_success(mock_run) -> None:
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    assert docker_compose_available() is True
    mock_run.assert_called_once_with(
        ["docker", "compose", "version"],
        check=True,
        capture_output=True,
        text=True,
    )


@patch("matt_stack.utils.docker.subprocess.run", side_effect=subprocess.CalledProcessError(1, ""))
def test_docker_compose_available_called_process_error(mock_run) -> None:
    assert docker_compose_available() is False


@patch("matt_stack.utils.docker.subprocess.run", side_effect=FileNotFoundError)
def test_docker_compose_available_file_not_found(mock_run) -> None:
    assert docker_compose_available() is False


# --- docker_running ---


@patch("matt_stack.utils.docker.subprocess.run")
def test_docker_running_success(mock_run) -> None:
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
    assert docker_running() is True
    mock_run.assert_called_once_with(
        ["docker", "info"],
        check=True,
        capture_output=True,
        text=True,
    )


@patch("matt_stack.utils.docker.subprocess.run", side_effect=subprocess.CalledProcessError(1, ""))
def test_docker_running_called_process_error(mock_run) -> None:
    assert docker_running() is False


@patch("matt_stack.utils.docker.subprocess.run", side_effect=FileNotFoundError)
def test_docker_running_file_not_found(mock_run) -> None:
    assert docker_running() is False
