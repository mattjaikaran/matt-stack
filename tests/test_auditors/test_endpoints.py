"""Tests for endpoint auditor."""

from __future__ import annotations

import urllib.error
from pathlib import Path
from unittest.mock import patch

from matt_stack.auditors.base import AuditConfig, Severity
from matt_stack.auditors.endpoints import EndpointAuditor


def _make_config(path: Path, **kwargs) -> AuditConfig:
    return AuditConfig(project_path=path, **kwargs)


def test_finds_no_routes(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("x = 1\n")
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    assert any("No route definitions" in f.message for f in findings)


def test_finds_duplicate_routes(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text(
        "from ninja import Router\n"
        "router = Router()\n\n"
        '@router.get("/users")\n'
        "def list_users(request): return []\n\n"
        '@router.get("/users")\n'
        "def list_users_v2(request): return []\n"
    )
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    dup_findings = [f for f in findings if "Duplicate" in f.message]
    assert len(dup_findings) >= 1


def test_finds_stub_endpoints(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text(
        "from ninja import Router\n"
        "router = Router()\n\n"
        '@router.get("/stub")\n'
        "def stub_endpoint(request):\n"
        "    pass\n"
    )
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    stub_findings = [f for f in findings if "Stub" in f.message]
    assert len(stub_findings) >= 1


def test_finds_missing_auth(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text(
        "from ninja import Router\n"
        "router = Router()\n\n"
        '@router.post("/users")\n'
        "def create_user(request): return {}\n"
    )
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    auth_findings = [f for f in findings if "No auth" in f.message]
    assert len(auth_findings) >= 1


def test_auth_endpoint_no_warning(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text(
        "from ninja import Router\n"
        "router = Router()\n\n"
        '@router.post("/users", auth=Bearer)\n'
        "def create_user(request): return {}\n"
    )
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    auth_findings = [f for f in findings if "No auth" in f.message]
    assert len(auth_findings) == 0


def test_trailing_slash_warning(tmp_path: Path) -> None:
    (tmp_path / "api.py").write_text(
        "from ninja import Router\n"
        "router = Router()\n\n"
        '@router.get("/users/")\n'
        "def list_users(request): return []\n"
    )
    auditor = EndpointAuditor(_make_config(tmp_path))
    findings = auditor.run()
    slash_findings = [f for f in findings if "Trailing slash" in f.message]
    assert len(slash_findings) >= 1


def test_configurable_base_url(tmp_path: Path) -> None:
    """Verify base_url is configurable."""
    config = _make_config(tmp_path, base_url="http://localhost:9000")
    assert config.base_url == "http://localhost:9000"


# ---------------------------------------------------------------------------
# _live_probe tests
# ---------------------------------------------------------------------------

_GET_ROUTE_FILE = (
    "from ninja import Router\n"
    "router = Router()\n\n"
    '@router.get("/health")\n'
    'def health_check(request): return {"ok": True}\n'
)

_POST_ROUTE_FILE = (
    "from ninja import Router\n"
    "router = Router()\n\n"
    '@router.post("/users")\n'
    "def create_user(request): return {}\n"
)

_PARAM_ROUTE_FILE = (
    "from ninja import Router\n"
    "router = Router()\n\n"
    '@router.get("/users/{id}")\n'
    "def get_user(request, id: int): return {}\n"
)


def test_live_probe_500_error(tmp_path: Path) -> None:
    """Live probe reports ERROR when server returns 500."""
    (tmp_path / "api.py").write_text(_GET_ROUTE_FILE)
    config = _make_config(tmp_path, live=True)
    auditor = EndpointAuditor(config)

    err = urllib.error.HTTPError("http://localhost:8000/health", 500, "Server Error", {}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        findings = auditor.run()

    probe_findings = [f for f in findings if "returned 500" in f.message]
    assert len(probe_findings) == 1
    assert probe_findings[0].severity == Severity.ERROR


def test_live_probe_404(tmp_path: Path) -> None:
    """Live probe reports WARNING when server returns 404."""
    (tmp_path / "api.py").write_text(_GET_ROUTE_FILE)
    config = _make_config(tmp_path, live=True)
    auditor = EndpointAuditor(config)

    err = urllib.error.HTTPError("http://localhost:8000/health", 404, "Not Found", {}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        findings = auditor.run()

    probe_findings = [f for f in findings if "returned 404" in f.message]
    assert len(probe_findings) == 1
    assert probe_findings[0].severity == Severity.WARNING


def test_live_probe_server_unreachable(tmp_path: Path) -> None:
    """Live probe reports INFO when server is not reachable."""
    (tmp_path / "api.py").write_text(_GET_ROUTE_FILE)
    config = _make_config(tmp_path, live=True)
    auditor = EndpointAuditor(config)

    err = urllib.error.URLError("Connection refused")
    with patch("urllib.request.urlopen", side_effect=err):
        findings = auditor.run()

    probe_findings = [f for f in findings if "Could not reach" in f.message]
    assert len(probe_findings) == 1
    assert probe_findings[0].severity == Severity.INFO


def test_live_probe_skips_non_get(tmp_path: Path) -> None:
    """Live probe skips non-GET routes (only probes GET for safety)."""
    (tmp_path / "api.py").write_text(_POST_ROUTE_FILE)
    config = _make_config(tmp_path, live=True)
    auditor = EndpointAuditor(config)

    with patch("urllib.request.urlopen") as mock_urlopen:
        auditor.run()

    mock_urlopen.assert_not_called()


def test_live_probe_skips_parameterized(tmp_path: Path) -> None:
    """Live probe skips parameterized routes like /users/{id}."""
    (tmp_path / "api.py").write_text(_PARAM_ROUTE_FILE)
    config = _make_config(tmp_path, live=True)
    auditor = EndpointAuditor(config)

    with patch("urllib.request.urlopen") as mock_urlopen:
        auditor.run()

    mock_urlopen.assert_not_called()
