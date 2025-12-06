# AutoDoc Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help setup install lint typecheck test test-unit test-integration test-coverage docker.build docker.run docker.dev docker.ci clean clean-all clean-cache clean-docker clean-everything format pre-commit check-all

# Default target
help: ## Show this help message
	@echo "AutoDoc Development Commands"
	@echo "=============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Development Setup
# =============================================================================

setup: ## One-command local development setup
	@echo "🚀 Setting up AutoDoc development environment..."
	@echo ""
	
	@echo "📦 Installing dependencies..."
	pip3 install -e .
	pip3 install -e ".[dev]"
	
	@echo ""
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	
	@echo ""
	@echo "📝 Creating environment file..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env from env.example"; \
		echo "⚠️  Please update .env with your actual values"; \
	else \
		echo "✅ .env already exists"; \
	fi
	
	@echo ""
	@echo "📁 Creating required directories..."
	mkdir -p logs uploads temp data
	
	@echo ""
	@echo "🧪 Running initial tests..."
	$(MAKE) test
	
	@echo ""
	@echo "🎉 Setup complete! You can now run:"
	@echo "  make dev          # Start development server"
	@echo "  make test         # Run tests"
	@echo "  make lint         # Run linting"
	@echo "  make docker.run   # Run with Docker"

install: ## Install dependencies
	pip3 install -e .
	pip3 install -e ".[dev]"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting checks
	@echo "🔍 Running ruff linting..."
	ruff check . --statistics --exclude src/
	
	@echo ""
	@echo "🎨 Running ruff formatting check..."
	ruff format --check . --exclude src/

format: ## Format code with ruff
	@echo "🎨 Formatting code with ruff..."
	ruff format . --exclude src/
	
	@echo "🔧 Auto-fixing linting issues..."
	ruff check . --fix --exclude src/

typecheck: ## Run type checking with mypy
	@echo "🔍 Running mypy type checking..."
	mypy autodoc/ tests/

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "🧪 Running all tests..."
	@if [ -f .env ]; then \
		set -a && source .env && set +a && pytest -q --maxfail=1 --disable-warnings; \
	else \
		echo "❌ .env file not found. Run 'make setup' first."; \
		exit 1; \
	fi

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	@if [ -f .env ]; then \
		set -a && source .env && set +a && pytest tests/unit/ -q --maxfail=1 --disable-warnings; \
	else \
		echo "❌ .env file not found. Run 'make setup' first."; \
		exit 1; \
	fi

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	@if [ -f .env ]; then \
		set -a && source .env && set +a && pytest tests/integration/ -q --maxfail=1 --disable-warnings; \
	else \
		echo "❌ .env file not found. Run 'make setup' first."; \
		exit 1; \
	fi

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	pytest --cov=autodoc --cov-report=html --cov-report=term-missing --cov-fail-under=70

test-watch: ## Run tests in watch mode
	@echo "🧪 Running tests in watch mode..."
	pytest-watch --runner "pytest -q --maxfail=1 --disable-warnings"

# =============================================================================
# Docker Commands
# =============================================================================

docker.build: ## Build Docker images
	@echo "🐳 Building Docker images..."
	@if command -v docker >/dev/null 2>&1; then \
		docker build --target development -t autodoc:dev .; \
		docker build --target production -t autodoc:prod .; \
		docker build --target ci -t autodoc:ci .; \
	else \
		echo "❌ Docker not installed - skipping Docker build"; \
	fi

docker.run: ## Run AutoDoc with Docker Compose
	@echo "🐳 Starting AutoDoc with Docker Compose..."
	docker compose -f Docker/docker-compose.yml up autodoc-dev

docker.dev: ## Start development environment with Docker
	@echo "🐳 Starting development environment..."
	docker compose -f Docker/docker-compose.yml --profile dev-tools up

docker.ci: ## Run CI pipeline with Docker
	@echo "🐳 Running CI pipeline..."
	docker compose -f Docker/docker-compose.yml run --rm autodoc-ci

docker.stop: ## Stop Docker containers
	@echo "🐳 Stopping Docker containers..."
	docker compose -f Docker/docker-compose.yml down

docker.clean: ## Clean up Docker resources
	@echo "🐳 Cleaning up Docker resources..."
	docker compose -f Docker/docker-compose.yml down -v
	docker system prune -f

# =============================================================================
# Development Server
# =============================================================================

dev: ## Start development server
	@echo "🚀 Starting AutoDoc development server..."
	@echo "📝 Make sure you have set up your .env file"
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

dev-shell: ## Start development shell
	@echo "🐚 Starting development shell..."
	docker compose -f Docker/docker-compose.yml exec autodoc-dev bash

# =============================================================================
# Database
# =============================================================================

db-init: ## Initialize database
	@echo "🗄️  Initializing database..."
	alembic upgrade head

db-migration: ## Create new database migration
	@echo "🗄️  Creating new migration..."
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

db-upgrade: ## Upgrade database to latest migration
	@echo "🗄️  Upgrading database..."
	alembic upgrade head

db-downgrade: ## Downgrade database by one migration
	@echo "🗄️  Downgrading database..."
	alembic downgrade -1

# =============================================================================
# Quality Assurance
# =============================================================================

pre-commit: ## Run pre-commit hooks
	@echo "🔧 Running pre-commit hooks..."
	pre-commit run --all-files

check-all: ## Run all quality checks
	@echo "🔍 Running all quality checks..."
	@echo ""
	@echo "1️⃣  Linting..."
	$(MAKE) lint
	@echo ""
	@echo "2️⃣  Type checking..."
	$(MAKE) typecheck
	@echo ""
	@echo "3️⃣  Tests..."
	$(MAKE) test
	@echo ""
	@echo "✅ All quality checks passed!"

# =============================================================================
# CI/CD
# =============================================================================

ci: ## Run CI pipeline locally
	@echo "🔄 Running CI pipeline..."
	@echo ""
	@echo "1️⃣  Code quality checks..."
	$(MAKE) lint
	$(MAKE) typecheck
	@echo ""
	@echo "2️⃣  Running tests..."
	$(MAKE) test-coverage
	@echo ""
	@echo "3️⃣  Docker build test..."
	$(MAKE) docker.build
	@echo ""
	@echo "✅ CI pipeline completed successfully!"

ci-test: ## Run CI test script
	@echo "🧪 Running CI test script..."
	./scripts/ci-test.sh

ci-lint: ## Run CI lint script
	@echo "🔍 Running CI lint script..."
	./scripts/ci-lint.sh

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	mkdocs build

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	mkdocs serve

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean up temporary files and caches
	@echo "🧹 Cleaning up temporary files and caches..."
	@echo "  Removing Python cache files..."
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "  Removing package build artifacts..."
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	@echo "  Removing test and coverage artifacts..."
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf .coverage.* 2>/dev/null || true
	rm -rf coverage.xml 2>/dev/null || true
	@echo "  Removing linter and type checker caches..."
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".dmypy.json" -delete 2>/dev/null || true
	@echo "  Removing temporary directories..."
	rm -rf temp/* 2>/dev/null || true
	rm -rf tmp/* 2>/dev/null || true
	@echo "✅ Cleanup complete!"

clean-all: clean logs-clean ## Deep clean: remove all temporary files and logs
	@echo "🧹 Deep cleaning workspace..."
	@echo "  Removing uploads and data..."
	rm -rf uploads/* 2>/dev/null || true
	rm -rf data/* 2>/dev/null || true
	@echo "  Removing IDE and editor files..."
	find . -name "*.swp" -delete 2>/dev/null || true
	find . -name "*.swo" -delete 2>/dev/null || true
	find . -name "*~" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Deep cleanup complete!"

clean-docker: ## Clean Docker resources (requires Docker)
	@echo "🐳 Cleaning Docker resources..."
	@if command -v docker >/dev/null 2>&1; then \
		docker compose -f Docker/docker-compose.yml down -v; \
		docker system prune -f; \
		echo "✅ Docker cleanup complete!"; \
	else \
		echo "❌ Docker not installed - skipping Docker cleanup"; \
	fi

clean-everything: clean-all clean-docker ## Complete clean: everything including Docker
	@echo "🧹 Complete workspace cleanup finished!"

clean-cache: ## Clean only cache directories (fast)
	@echo "🧹 Cleaning cache directories..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache cleanup complete!"

logs: ## Show recent logs
	@echo "📋 Recent logs:"
	tail -f logs/autodoc.log

logs-clean: ## Clean log files
	@echo "🧹 Cleaning log files..."
	rm -rf logs/*.log

# =============================================================================
# Release
# =============================================================================

version: ## Show current version
	@python3 -c "import autodoc; print(autodoc.__version__)"

release-check: ## Check if ready for release
	@echo "🔍 Checking release readiness..."
	$(MAKE) check-all
	@echo "✅ Ready for release!"

# =============================================================================
# Environment
# =============================================================================

env-check: ## Check environment setup
	@echo "🔍 Checking environment setup..."
	@echo ""
	@echo "Python version:"
	@python3 --version
	@echo ""
	@echo "Docker version:"
	@if command -v docker >/dev/null 2>&1; then docker --version; else echo "❌ Docker not installed (optional)"; fi
	@echo ""
	@echo "Environment file:"
	@if [ -f .env ]; then echo "✅ .env exists"; else echo "❌ .env missing - run 'make setup'"; fi
	@echo ""
	@echo "Required directories:"
	@for dir in logs uploads temp data; do \
		if [ -d $$dir ]; then echo "✅ $$dir/ exists"; else echo "❌ $$dir/ missing"; fi; \
	done

# =============================================================================
# Helpers
# =============================================================================

.PHONY: install-dev
install-dev: ## Install development dependencies
	pip3 install -e ".[dev]"

.PHONY: update-deps
update-deps: ## Update dependencies
	pip3 install --upgrade -e ".[dev]"

.PHONY: shell
shell: ## Start Python shell with AutoDoc loaded
	python3 -c "import autodoc; print('AutoDoc loaded successfully')"

# =============================================================================
# Shortcuts
# =============================================================================

# Common development workflow shortcuts
dev-setup: setup ## Alias for setup
test-fast: test-unit ## Quick unit tests only
build: docker.build ## Alias for docker.build
run: docker.run ## Alias for docker.run
check: check-all ## Alias for check-all