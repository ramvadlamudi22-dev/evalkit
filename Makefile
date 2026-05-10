# EvalKit Makefile — thin wrappers around real commands.
# Each target is a one-line invocation; nothing magical lives here.

.PHONY: help install lint format type test cov audit ci docker-build docker-run clean

help:  ## Show this help.
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install dependencies and pre-commit hooks.
	uv sync --extra dev
	uv run pre-commit install

lint:  ## Run ruff lint + format check.
	uv run ruff check .
	uv run ruff format --check .

format:  ## Run ruff format (rewrites files).
	uv run ruff format .
	uv run ruff check --fix .

type:  ## Run mypy.
	uv run mypy

test:  ## Run pytest.
	uv run pytest

cov:  ## Run pytest with coverage report.
	uv run pytest --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

audit:  ## Run pip-audit (skips editable install of evalkit itself).
	uv run pip-audit --skip-editable

ci: lint type test  ## Run the full CI pipeline locally (lint + type + test).

docker-build:  ## Build the Docker image.
	docker build -t evalkit:dev .

docker-run:  ## Run `evalkit --version` from the Docker image.
	docker run --rm evalkit:dev --version

clean:  ## Remove caches and build artifacts.
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov
	rm -rf build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
