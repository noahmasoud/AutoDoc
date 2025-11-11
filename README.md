# AutoDoc

**AutoDoc** is a CI/CD code analyzer and Confluence updater that automatically analyzes code changes and updates associated documentation. It runs in CI/CD pipelines to detect API changes and generate documentation updates using configurable templates.

## 🚀 Quick Start (One-Command Setup)

```bash
# Clone and setup everything in one command
git clone <repository-url> && cd AutoDoc && make setup
```

That's it! The `make setup` command will:
- Install all dependencies
- Set up pre-commit hooks
- Create your `.env` file from the template
- Create required directories
- Run initial tests to verify everything works

## 📋 Prerequisites

- **Python 3.11+** (required)
- **Docker** (optional, for containerized development)
- **Git** (for version control)

## 🛠️ Development Setup

### Option 1: One-Command Setup (Recommended)
```bash
make setup
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up pre-commit hooks
pre-commit install

# 3. Create environment file
cp env.example .env
# Edit .env with your actual values

# 4. Create required directories
mkdir -p logs uploads temp data

# 5. Run tests
make test
```

## 🎯 Available Commands

Run `make help` to see all available commands:

```bash
make help
```

### Essential Commands

| Command | Description |
|---------|-------------|
| `make setup` | One-command development setup |
| `make dev` | Start development server |
| `make test` | Run all tests |
| `make lint` | Run linting checks |
| `make typecheck` | Run type checking |
| `make docker.run` | Run with Docker Compose |
| `make check-all` | Run all quality checks |

### Development Workflow

```bash
# Start development
make dev

# Run tests before committing
make test

# Check code quality
make lint
make typecheck

# Format code
make format

# Run everything (CI pipeline locally)
make ci
```

## 🐳 Docker Development

### Quick Start with Docker
```bash
# Build and run with Docker
make docker.build
make docker.run
```

### Docker Commands
```bash
make docker.build    # Build all Docker images
make docker.run      # Run with Docker Compose
make docker.dev      # Start development environment
make docker.ci       # Run CI pipeline in Docker
make docker.stop     # Stop Docker containers
make docker.clean    # Clean up Docker resources
```

## ⚙️ Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

#### Required Variables
```bash
# Security (REQUIRED - must be 32+ characters each)
SECRET_KEY=your-secret-key-here-change-in-production-must-be-32-chars-minimum
JWT_SECRET_KEY=your-jwt-secret-key-here-must-be-32-chars-minimum
```

#### Database Configuration
```bash
# SQLite (default for development)
DATABASE_URL=sqlite:///./autodoc.db

# PostgreSQL (for production)
# DATABASE_URL=postgresql://user:pass@localhost:5432/autodoc
```

#### Confluence Integration (Optional)
```bash
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-username
CONFLUENCE_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=YOUR_SPACE
```

See `env.example` for all available configuration options.

## 🧪 Testing

### Run Tests
```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-coverage     # Tests with coverage report
make test-watch        # Tests in watch mode
```

### Test Structure
```
tests/
├── unit/              # Unit tests (≥70% coverage required)
│   ├── test_analyzers.py
│   ├── test_connectors.py
│   ├── test_api.py
│   └── ...
├── integration/       # Integration tests
│   └── test_analyzer_connector_integration.py
└── conftest.py        # Shared fixtures
```

## 🔍 Code Quality

### Linting and Formatting
```bash
make lint              # Check code style
make format            # Auto-format code
make typecheck         # Type checking with mypy
make pre-commit        # Run pre-commit hooks
```

### Quality Tools
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checking
- **Pre-commit**: Git hooks for quality checks
- **Pytest**: Testing framework with coverage

## 📊 Monitoring and Logging

### Structured Logging
AutoDoc uses structured logging with correlation IDs for tracking:

```python
from autodoc.logging import log_run_context

with log_run_context("autodoc.run", run_id="run_001") as ctx:
    ctx.log_event("run_start", "CI/CD run started")
```

### Log Formats
- **JSON**: Machine-readable for log aggregation
- **Text**: Human-readable for development
- **File + Console**: Configurable output destinations

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
- name: Run AutoDoc
  uses: docker://autodoc:ci
  with:
    args: --commit ${{ github.sha }} --repo ${{ github.repository }}
```

### GitLab CI
```yaml
autodoc:
  image: autodoc:ci
  script:
    - autodoc --commit $CI_COMMIT_SHA --repo $CI_PROJECT_PATH
```

### Local CI Testing
```bash
make ci                # Run full CI pipeline locally
make ci-test          # Run CI test script
make ci-lint          # Run CI lint script
```

## 📚 API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json
- **Python symbol metadata**: `GET /api/v1/runs/{run_id}/python-symbols` returns persisted module/class/function docstrings and signatures for a run.

## 🏗️ Architecture

### Core Components
- **Analyzers**: Static code analysis for Python/TypeScript
- **Connectors**: External service integration (Confluence, Git)
- **Templates**: Configurable documentation generation
- **API**: RESTful interface for configuration and monitoring
- **CLI**: Command-line interface for CI/CD integration

### Key Features
- **Static Analysis**: Detects API changes and breaking changes
- **Template Engine**: Generates documentation from templates
- **Approval Workflow**: Review and approve changes before applying
- **Version Control**: Track and rollback documentation changes
- **Observability**: Comprehensive logging and monitoring
- **Docstring Persistence**: Stores Python module/class/function/method docstrings during analysis and exposes them through the API for downstream documentation patches

## 🔧 Troubleshooting

### Common Issues

#### Environment Setup
```bash
# Check environment setup
make env-check

# Clean and reinstall
make clean
make install
```

#### Docker Issues
```bash
# Clean Docker resources
make docker.clean

# Rebuild images
make docker.build
```

#### Test Failures
```bash
# Run tests with verbose output
pytest -v

# Run specific test
pytest tests/unit/test_analyzers.py::TestPythonAnalyzer::test_function_detection
```

### Getting Help
- Check the logs: `make logs`
- Run diagnostics: `make env-check`
- Verify setup: `make check-all`

## 📈 Performance

### Benchmarks
- **Analysis**: ≤5 minutes for ≤500 LOC changes on ≤10k LOC repos
- **Confluence Updates**: ≤10 seconds per page (network permitting)
- **API Response**: ≤100ms for typical requests

### Optimization
- Structured logging with correlation IDs
- Efficient AST parsing and caching
- Async operations for I/O
- Connection pooling for databases

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Make** your changes
4. **Add** tests for new functionality
5. **Run** quality checks: `make check-all`
6. **Commit** your changes: `git commit -m 'Add amazing feature'`
7. **Push** to your branch: `git push origin feature/amazing-feature`
8. **Open** a Pull Request

### Code Standards
- Follow PEP 8 style guidelines (enforced by Ruff)
- Add type hints for all functions (checked by MyPy)
- Maintain ≥70% test coverage
- Write clear docstrings and comments
- Use structured logging with correlation IDs

### Pull Request Process
1. Ensure all tests pass: `make test`
2. Run quality checks: `make check-all`
3. Update documentation if needed
4. Add changelog entry
5. Request review from maintainers

## 📄 License

[License information will be added here]

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the API
- Uses [Pydantic](https://pydantic.dev/) for data validation
- Integrated with [Confluence](https://www.atlassian.com/software/confluence) for documentation
- CI/CD support for [GitHub Actions](https://github.com/features/actions) and [GitLab CI](https://docs.gitlab.com/ee/ci/)

---

## 📋 Git Branching Strategy

For the 3-person team working on infrastructure, backend, and frontend:

### Recommended Strategy: Simplified Git Flow
```
main (protected)
├── develop (integration branch)
    ├── infrastructure/feature-name (Noah's branches)
    ├── backend/feature-name (Ryan's branches)
    └── frontend/feature-name (Logan's branches)
```

### Workflow
```bash
# Starting a new feature
git checkout develop
git pull origin develop
git checkout -b backend/feature-name

# Work on feature...
git add .
git commit -m "feat(backend): add feature description"
git push origin backend/feature-name

# Create PR: backend/feature-name → develop
```

### Pull Request Rules
- All PRs merge to develop first
- Require at least 1 review from another team member
- CI must pass (tests, linting) before merge
- At end of sprint: Create PR from develop → main