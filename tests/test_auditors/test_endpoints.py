"""Tests for endpoint auditor."""

from __future__ import annotations

from pathlib import Path

from matt_stack.auditors.base import AuditConfig
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
