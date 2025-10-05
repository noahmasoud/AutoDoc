# Makefile for AutoDoc project
# Provides convenient commands for development and CI

.PHONY: help install install-dev test test-unit test-integration test-analyzer test-connector lint format type-check coverage clean ci ci-lint ci-test docs serve-docs

# Default target
help:
	@echo "AutoDoc Development Commands"
	@echo "============================"
	@echo ""
	@echo "Installation:"
	@echo "  install          Install package in development mode"
	@echo "  install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-analyzer    Run analyzer tests only"
	@echo "  test-connector   Run connector tests only"
	@echo "  coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code with ruff"
	@echo "  type-check       Run type checking with mypy"
	@echo ""
	@echo "CI:"
	@echo "  ci               Run full CI pipeline"
	@echo "  ci-lint          Run CI linting checks"
	@echo "  ci-test          Run CI tests"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation"
	@echo "  serve-docs       Serve documentation locally"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean build artifacts and caches"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,lint,docs]"

# Testing
test:
	pytest -q --maxfail=1 --disable-warnings

test-unit:
	pytest -q --maxfail=1 --disable-warnings -m "unit and not slow"

test-integration:
	pytest -q --maxfail=1 --disable-warnings -m "integration and not slow"

test-analyzer:
	pytest -q --maxfail=1 --disable-warnings -m "analyzer"

test-connector:
	pytest -q --maxfail=1 --disable-warnings -m "connector and not external"

coverage:
	pytest --cov=autodoc --cov=api --cov=cli --cov=core --cov=db --cov=schemas --cov=services \
		--cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml \
		--cov-fail-under=70

# Code Quality
lint:
	ruff check .
	mypy .

format:
	ruff format .

type-check:
	mypy .

# CI Commands
ci: ci-lint ci-test

ci-lint:
	./scripts/ci-lint.sh

ci-test:
	./scripts/ci-test.sh

# Documentation
docs:
	mkdocs build

serve-docs:
	mkdocs serve

# Utilities
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f coverage.json
	rm -f coverage.lcov
	rm -f bandit-report.json
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development helpers
dev-setup: install-dev
	@echo "Setting up development environment..."
	pre-commit install

quick-test:
	pytest -q --maxfail=1 --disable-warnings -m "unit and not slow" --tb=short

# CI-specific commands (matching your requirements)
ci-quick:
	pytest -q --maxfail=1 --disable-warnings -q --cov-fail-under=70 --tb=short

# Test specific categories with coverage
test-with-coverage:
	pytest -q --maxfail=1 --disable-warnings \
		--cov=autodoc --cov=api --cov=cli --cov=core --cov=db --cov=schemas --cov=services \
		--cov-report=term-missing --cov-fail-under=70 \
		-m "unit and analyzer and connector"
