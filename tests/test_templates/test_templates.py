"""Tests for template generation."""

from matt_stack.config import ProjectConfig
from matt_stack.templates.docker_compose import generate_docker_compose
from matt_stack.templates.root_env import generate_env_example
from matt_stack.templates.root_gitignore import generate_gitignore
from matt_stack.templates.root_makefile import generate_makefile
from matt_stack.templates.root_readme import generate_readme


def test_makefile_fullstack(starter_fullstack_config: ProjectConfig):
    content = generate_makefile(starter_fullstack_config)
    assert "setup:" in content
    assert "backend-dev:" in content
    assert "frontend-dev:" in content
    assert "prod-build:" in content


def test_makefile_backend_only(backend_only_config: ProjectConfig):
    content = generate_makefile(backend_only_config)
    assert "backend-dev:" in content
    assert "frontend-dev:" not in content


def test_makefile_frontend_only(frontend_only_config: ProjectConfig):
    content = generate_makefile(frontend_only_config)
    assert "frontend-dev:" in content
    assert "backend-dev:" not in content


def test_docker_compose_fullstack(starter_fullstack_config: ProjectConfig):
    content = generate_docker_compose(starter_fullstack_config)
    assert "db:" in content
    assert "redis:" in content
    assert "api-dev:" in content
    assert "frontend-dev:" in content
    assert "test_project" in content  # python_package_name


def test_docker_compose_no_celery(starter_fullstack_config: ProjectConfig):
    starter_fullstack_config.use_celery = False
    content = generate_docker_compose(starter_fullstack_config)
    assert "celery-worker:" not in content


def test_env_example(starter_fullstack_config: ProjectConfig):
    content = generate_env_example(starter_fullstack_config)
    assert "DJANGO_SECRET_KEY" in content
    assert "VITE_API_BASE_URL" in content
    assert "POSTGRES_DB=test_project" in content


def test_gitignore_fullstack(starter_fullstack_config: ProjectConfig):
    content = generate_gitignore(starter_fullstack_config)
    assert "__pycache__" in content
    assert "node_modules" in content


def test_gitignore_frontend_only(frontend_only_config: ProjectConfig):
    content = generate_gitignore(frontend_only_config)
    assert "node_modules" in content
    assert "__pycache__" not in content


def test_readme(starter_fullstack_config: ProjectConfig):
    content = generate_readme(starter_fullstack_config)
    assert "# Test Project" in content
    assert "Django" in content
    assert "React" in content


def test_readme_b2b(b2b_config: ProjectConfig):
    content = generate_readme(b2b_config)
    assert "B2B" in content
    assert "generate_feature" in content
