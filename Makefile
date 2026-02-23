.PHONY: help setup dev test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies
	uv sync

dev: ## Install in editable mode
	uv pip install -e ".[dev]"

test: ## Run tests
	uv run pytest -v

lint: ## Run linter
	uv run ruff check src/ tests/

format: ## Format code
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
