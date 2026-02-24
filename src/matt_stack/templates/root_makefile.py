"""Root Makefile template for generated projects."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_makefile(config: ProjectConfig) -> str:
    """Generate root Makefile content."""
    sections = [_header(), _help_target()]

    if config.is_fullstack:
        sections.append(_setup_fullstack(config))
        sections.append(_docker_targets(config))
        sections.append(_backend_targets())
        sections.append(_frontend_targets())
        if config.include_ios:
            sections.append(_ios_targets())
        sections.append(_combined_targets(config))
        sections.append(_prod_targets())
    elif config.has_backend:
        sections.append(_setup_backend())
        sections.append(_docker_targets(config))
        sections.append(_backend_targets())
        sections.append(_prod_targets())
    elif config.has_frontend:
        sections.append(_setup_frontend())
        sections.append(_frontend_targets())

    return "\n".join(sections)


def _header() -> str:
    return """\
.DEFAULT_GOAL := help
SHELL := /bin/bash"""


def _help_target() -> str:
    # Long awk line is required for Makefile help target
    grep_cmd = (
        "@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort"
        ' | awk \'BEGIN {FS = ":.*?## "}; '
        '{printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}\''
    )
    return f"""
.PHONY: help
help: ## Show this help
\t{grep_cmd}"""


def _setup_fullstack(config: ProjectConfig) -> str:
    ios_setup = "\n\t@echo 'iOS setup: open ios/ in Xcode'" if config.include_ios else ""
    return f"""
.PHONY: setup
setup: ## Install all dependencies
\t@echo 'Setting up backend...'
\tcd backend && uv sync
\t@echo 'Setting up frontend...'
\tcd frontend && bun install{ios_setup}
\t@echo 'Copying .env.example to .env (if needed)...'
\t@test -f .env || cp .env.example .env
\t@echo 'Setup complete!'"""


def _setup_backend() -> str:
    return """
.PHONY: setup
setup: ## Install backend dependencies
\t@echo 'Setting up backend...'
\tcd backend && uv sync
\t@test -f .env || cp .env.example .env
\t@echo 'Setup complete!'"""


def _setup_frontend() -> str:
    return """
.PHONY: setup
setup: ## Install frontend dependencies
\t@echo 'Setting up frontend...'
\tcd frontend && bun install
\t@echo 'Setup complete!'"""


def _docker_targets(config: ProjectConfig) -> str:
    return """
.PHONY: up down logs restart
up: ## Start all services (Docker)
\tdocker compose up -d

down: ## Stop all services
\tdocker compose down

logs: ## Tail service logs
\tdocker compose logs -f

restart: ## Restart all services
\tdocker compose restart"""


def _backend_targets() -> str:
    return """
.PHONY: backend-setup backend-dev backend-test backend-lint
.PHONY: backend-migrate backend-shell backend-makemigrations backend-superuser
backend-setup: ## Install backend deps
\tcd backend && uv sync

backend-dev: ## Run backend dev server
\tcd backend && uv run python manage.py runserver

backend-test: ## Run backend tests
\tcd backend && uv run pytest -v

backend-lint: ## Lint backend
\tcd backend && uv run ruff check .

backend-migrate: ## Run Django migrations
\tcd backend && uv run python manage.py migrate

backend-makemigrations: ## Create Django migrations
\tcd backend && uv run python manage.py makemigrations

backend-shell: ## Django shell
\tcd backend && uv run python manage.py shell

backend-superuser: ## Create Django superuser
\tcd backend && uv run python manage.py createsuperuser"""


def _frontend_targets() -> str:
    return """
.PHONY: frontend-setup frontend-dev frontend-build frontend-test frontend-lint
frontend-setup: ## Install frontend deps
\tcd frontend && bun install

frontend-dev: ## Run frontend dev server
\tcd frontend && bun run dev

frontend-build: ## Build frontend
\tcd frontend && bun run build

frontend-test: ## Run frontend type check
\tcd frontend && bun run typecheck

frontend-lint: ## Lint frontend
\tcd frontend && bun run lint"""


def _ios_targets() -> str:
    return """
.PHONY: ios-build ios-test
ios-build: ## Build iOS project
\tcd ios && xcodebuild -scheme MyApp -sdk iphonesimulator build

ios-test: ## Run iOS tests
\tcd ios && xcodebuild -scheme MyApp -sdk iphonesimulator test"""


def _combined_targets(config: ProjectConfig) -> str:
    return """
.PHONY: test lint format sync-types clean
test: ## Run all tests
\t@echo 'Running backend tests...'
\tcd backend && uv run pytest -v
\t@echo 'Running frontend type check...'
\tcd frontend && bun run typecheck

lint: ## Lint all code
\tcd backend && uv run ruff check . && uv run ruff format --check .
\tcd frontend && bun run lint

format: ## Format all code
\tcd backend && uv run ruff format .
\tcd frontend && bun run format

sync-types: ## Sync backend types to frontend TypeScript
\tcd backend && uv run python manage.py sync_types \
\t\t--target typescript --output ../frontend/src/types

clean: ## Clean all build artifacts
\tdocker compose down -v
\trm -rf backend/.pytest_cache backend/__pycache__
\trm -rf frontend/node_modules frontend/dist"""


def _prod_targets() -> str:
    return """
.PHONY: prod-build prod-up prod-down
prod-build: ## Build production images
\tdocker compose -f docker-compose.prod.yml build

prod-up: ## Start production
\tdocker compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production
\tdocker compose -f docker-compose.prod.yml down"""
