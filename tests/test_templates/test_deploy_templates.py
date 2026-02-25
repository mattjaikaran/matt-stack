"""Tests for deployment config templates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from matt_stack.config import DeploymentTarget, ProjectConfig, ProjectType, Variant
from matt_stack.templates.deploy_railway import generate_railway_json, generate_railway_toml
from matt_stack.templates.deploy_render import generate_render_yaml
from matt_stack.templates.deploy_vercel import generate_vercel_json

# --- Fixtures for deployment-specific configs ---


@pytest.fixture
def railway_fullstack_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-app",
        path=tmp_path / "my-app",
        project_type=ProjectType.FULLSTACK,
        variant=Variant.STARTER,
        deployment=DeploymentTarget.RAILWAY,
    )


@pytest.fixture
def railway_backend_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-api",
        path=tmp_path / "my-api",
        project_type=ProjectType.BACKEND_ONLY,
        variant=Variant.STARTER,
        deployment=DeploymentTarget.RAILWAY,
    )


@pytest.fixture
def render_fullstack_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-app",
        path=tmp_path / "my-app",
        project_type=ProjectType.FULLSTACK,
        variant=Variant.STARTER,
        deployment=DeploymentTarget.RENDER,
    )


@pytest.fixture
def render_backend_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-api",
        path=tmp_path / "my-api",
        project_type=ProjectType.BACKEND_ONLY,
        variant=Variant.STARTER,
        deployment=DeploymentTarget.RENDER,
    )


@pytest.fixture
def render_backend_no_redis_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-api",
        path=tmp_path / "my-api",
        project_type=ProjectType.BACKEND_ONLY,
        variant=Variant.STARTER,
        deployment=DeploymentTarget.RENDER,
        use_celery=False,
        use_redis=False,
    )


@pytest.fixture
def vercel_fullstack_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-app",
        path=tmp_path / "my-app",
        project_type=ProjectType.FULLSTACK,
        variant=Variant.STARTER,
    )


@pytest.fixture
def vercel_frontend_config(tmp_path: Path) -> ProjectConfig:
    return ProjectConfig(
        name="my-frontend",
        path=tmp_path / "my-frontend",
        project_type=ProjectType.FRONTEND_ONLY,
        variant=Variant.STARTER,
    )


# --- Railway JSON tests ---


def test_railway_json_fullstack(railway_fullstack_config: ProjectConfig) -> None:
    content = generate_railway_json(railway_fullstack_config)
    data = json.loads(content)
    assert data["build"]["builder"] == "NIXPACKS"
    assert "uv" in data["build"]["buildCommand"]
    assert "runserver" in data["deploy"]["startCommand"]
    assert data["deploy"]["healthcheckPath"] == "/api/health/"


def test_railway_json_backend_only(railway_backend_config: ProjectConfig) -> None:
    content = generate_railway_json(railway_backend_config)
    data = json.loads(content)
    assert data["build"]["builder"] == "NIXPACKS"
    assert data["deploy"]["healthcheckPath"] == "/api/health/"
    assert data["deploy"]["restartPolicyType"] == "ON_FAILURE"


def test_railway_json_is_valid_json(railway_fullstack_config: ProjectConfig) -> None:
    content = generate_railway_json(railway_fullstack_config)
    # Should not raise
    data = json.loads(content)
    assert "$schema" in data


# --- Railway TOML tests ---


def test_railway_toml_fullstack(railway_fullstack_config: ProjectConfig) -> None:
    content = generate_railway_toml(railway_fullstack_config)
    assert "[build]" in content
    assert "[deploy]" in content
    assert "gunicorn" in content
    assert "my_app" in content  # python_package_name
    assert "healthcheckPath" in content


def test_railway_toml_backend_only(railway_backend_config: ProjectConfig) -> None:
    content = generate_railway_toml(railway_backend_config)
    assert "[build]" in content
    assert "gunicorn" in content
    assert "my_api" in content  # python_package_name


def test_railway_toml_project_name_substitution(
    railway_fullstack_config: ProjectConfig,
) -> None:
    content = generate_railway_toml(railway_fullstack_config)
    assert "my_app.wsgi:application" in content


# --- Render YAML tests ---


def test_render_yaml_fullstack(render_fullstack_config: ProjectConfig) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "services:" in content
    assert "databases:" in content
    assert "my-app-api" in content
    assert "my-app-frontend" in content
    assert "my-app-db" in content
    assert "gunicorn" in content
    assert "healthCheckPath: /api/health/" in content


def test_render_yaml_backend_only(render_backend_config: ProjectConfig) -> None:
    content = generate_render_yaml(render_backend_config)
    assert "my-api-api" in content
    assert "my-api-db" in content
    assert "my-api-frontend" not in content


def test_render_yaml_has_redis_when_configured(
    render_fullstack_config: ProjectConfig,
) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "my-app-redis" in content
    assert "type: redis" in content


def test_render_yaml_no_redis_when_disabled(
    render_backend_no_redis_config: ProjectConfig,
) -> None:
    content = generate_render_yaml(render_backend_no_redis_config)
    assert "redis" not in content.lower()


def test_render_yaml_has_celery_when_configured(
    render_fullstack_config: ProjectConfig,
) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "my-app-celery-worker" in content
    assert "my-app-celery-beat" in content
    assert "celery -A my_app worker" in content
    assert "celery -A my_app beat" in content


def test_render_yaml_no_celery_when_disabled(
    render_backend_no_redis_config: ProjectConfig,
) -> None:
    content = generate_render_yaml(render_backend_no_redis_config)
    assert "celery" not in content.lower()


def test_render_yaml_project_name_substitution(
    render_fullstack_config: ProjectConfig,
) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "my_app.wsgi:application" in content
    assert "my_app.settings" in content


def test_render_yaml_frontend_static_site(render_fullstack_config: ProjectConfig) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "runtime: static" in content
    assert "frontend/dist" in content
    assert "bun install && bun run build" in content


def test_render_yaml_env_groups(render_fullstack_config: ProjectConfig) -> None:
    content = generate_render_yaml(render_fullstack_config)
    assert "envGroups:" in content
    assert "shared-env" in content


# --- Vercel JSON tests ---


def test_vercel_json_fullstack(vercel_fullstack_config: ProjectConfig) -> None:
    content = generate_vercel_json(vercel_fullstack_config)
    data = json.loads(content)
    assert data["framework"] == "vite"
    assert data["outputDirectory"] == "dist"
    assert data["buildCommand"] == "bun install && bun run build"
    # Should have API proxy rewrite for fullstack
    sources = [r["source"] for r in data["rewrites"]]
    assert "/api/:path*" in sources


def test_vercel_json_frontend_only(vercel_frontend_config: ProjectConfig) -> None:
    content = generate_vercel_json(vercel_frontend_config)
    data = json.loads(content)
    assert data["framework"] == "vite"
    # Should NOT have API proxy rewrite for frontend-only
    sources = [r["source"] for r in data["rewrites"]]
    assert "/api/:path*" not in sources


def test_vercel_json_spa_rewrite(vercel_fullstack_config: ProjectConfig) -> None:
    content = generate_vercel_json(vercel_fullstack_config)
    data = json.loads(content)
    # SPA fallback should always be present
    destinations = [r["destination"] for r in data["rewrites"]]
    assert "/index.html" in destinations


def test_vercel_json_is_valid_json(vercel_frontend_config: ProjectConfig) -> None:
    content = generate_vercel_json(vercel_frontend_config)
    data = json.loads(content)
    assert "$schema" in data


def test_vercel_json_security_headers(vercel_fullstack_config: ProjectConfig) -> None:
    content = generate_vercel_json(vercel_fullstack_config)
    data = json.loads(content)
    assert "headers" in data
    header_keys = [h["key"] for h in data["headers"][0]["headers"]]
    assert "X-Frame-Options" in header_keys
    assert "X-Content-Type-Options" in header_keys
