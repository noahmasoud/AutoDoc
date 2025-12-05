# AutoDoc

AutoDoc is an intelligent CI/CD tool that automatically analyzes Python code changes and generates documentation updates for Confluence. By integrating directly into your development pipeline, AutoDoc detects API modifications through static analysis and produces structured documentation patches based on configurable templates.

## Project Status

**Current Phase**: Functional Prototype - Sprint 3 (October - December 2025)

AutoDoc is a university capstone project (CS4398 Senior Design) demonstrating end-to-end automated documentation generation. The system currently implements static code analysis for Python and TypeScript, template-based patch generation, and core infrastructure with a focus on code quality and testing rigor.

### Completed Features (Sprint 0-3)

**Sprint 0: Foundation & Infrastructure**
- Docker containerization with optimized multi-stage builds (under 500MB, ~15 second build time)
- GitHub Actions CI/CD pipeline with automated testing and quality checks
- FastAPI backend project structure with SQLite database
- Angular frontend application shell with routing
- Pre-commit hooks and code quality tools (Ruff, MyPy, Pytest)

**Sprint 1: Static Analysis Engine**
- Python AST parser with comprehensive symbol extraction (modules, classes, functions, methods)
- Change detection across git commits with detailed diff analysis
- Docstring extraction for documentation context
- Public symbol identification and signature analysis
- Unit tests with high coverage across analyzers

**Sprint 2: TypeScript Analysis**
- TypeScript AST parser using TypeScript Compiler API
- Export detection and symbol extraction
- Type signature parsing for functions and classes
- JSDoc comment extraction

**Sprint 3: Template Engine & Patch Generation**
- Template rendering system with variable substitution
- Patch generation from detected code changes
- Dry-run mode for preview without persistence
- Test mode for safe experimentation
- Angular UI for template management with full CRUD operations
- Patch preview with side-by-side diff visualization
- CLI interface (in development for MVP integration)

**Quality & Testing**
- Unit and integration test suites achieving >70% coverage target
- Type safety with comprehensive MyPy type hints
- Zero Ruff linting violations in production code
- Pre-commit hooks enforcing quality standards
- Structured logging with correlation IDs

### Future Roadmap

**Confluence Integration** 
- Confluence REST API client for page operations
- Page versioning and conflict resolution
- Retry logic with exponential backoff
- Connections management UI with secure token storage

**Rule Engine & Mapping** 
- Rule-based file-to-page mapping
- Path and module selectors
- Rules CRUD API and UI
- Multiple rules per file support

**Approval Workflow** 
- Patch approval and rejection interface
- Auto-approve flags per rule
- Apply approved patches to Confluence
- PR/MR comment integration

**Advanced Features** 
- Rollback functionality with version history
- Audit trail for all operations
- Read-only viewer role
- Enhanced observability and error handling
- HTTP endpoint detection

## Problem Statement

Modern software teams face a persistent challenge: keeping documentation synchronized with rapidly evolving codebases. Manual documentation updates are time-consuming, error-prone, and often deprioritized under delivery pressure. This leads to outdated documentation that erodes trust and increases onboarding friction.

AutoDoc addresses this by:
1. Automatically detecting API changes through static analysis
2. Generating structured documentation updates using customizable templates
3. Integrating seamlessly into existing CI/CD workflows
4. Providing visibility into what changed and why

## Architecture Overview

### System Design

```
┌─────────────────┐
│   CI/CD Pipeline │
│  (GitHub Actions)│
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           AutoDoc System                │
│                                         │
│  ┌──────────────┐    ┌──────────────┐   │
│  │   CLI Tool   │───▶│  FastAPI     │   │
│  │              │    │  Backend     │   │
│  └──────────────┘    └──────┬───────┘   │
│                              │          │
│  ┌──────────────────────────▼────────┐  │
│  │      Analysis Engine              │  |
│  │  • AST Parser                     │  │
│  │  • Symbol Extractor               │  │
│  │  • Change Detector                │  │
│  │  • Docstring Extractor            │  │
│  └──────────────┬────────────────────┘  │
│                 │                       │
│  ┌──────────────▼────────────────────┐  │
│  │      Template Engine              │  │
│  │  • Rule Evaluation                │  │
│  │  • Patch Generation               │  │
│  │  • Preview Mode                   │  │
│  └──────────────┬────────────────────┘  │
│                 │                       │
└─────────────────┼───────────────────────┘
                  │
         ┌────────▼─────────┐
         │   Angular UI     │
         │ (Template Config)│
         └──────────────────┘
                  │
         ┌────────▼─────────┐
         │   Confluence     │
         │   (Future)       │
         └──────────────────┘
```

### Technology Stack

**Backend**
- Python 3.11+ with type hints
- FastAPI for RESTful API
- Pydantic for data validation
- SQLAlchemy for database ORM
- Alembic for database migrations

**Frontend**
- Angular with TypeScript
- Reactive forms for template configuration
- HttpClient for API integration

**Infrastructure**
- Docker with multi-stage builds
- GitHub Actions for CI/CD
- GitHub Container Registry (GHCR)
- SQLite (development) / PostgreSQL (production-ready)

**Development Tools**
- Pytest for testing framework
- Ruff for linting and formatting
- MyPy for static type checking
- Pre-commit hooks for quality gates

### Core Components

#### Analysis Engine
The analysis engine performs static code analysis using Python's built-in `ast` module:

```python
# Detects changes like:
class UserService:
    def create_user(self, email: str) -> User:  # New method
        pass
    
    def get_user(self, user_id: int) -> Optional[User]:  # Modified signature
        pass
```

Output includes:
- Symbol type (module, class, function, method)
- Signature changes (parameters, return types)
- Docstring extraction for context
- Location information (file, line number)

#### Template System
Templates define how detected changes map to documentation updates:

```json
{
  "name": "API Endpoint Template",
  "rules": [
    {
      "condition": "symbol_type == 'function' AND is_public",
      "template": "## {symbol_name}\n\n{docstring}\n\n**Parameters**: {parameters}"
    }
  ]
}
```

#### Change Detection
Compares git commits to identify:
- New symbols (classes, functions, methods)
- Modified signatures
- Removed or deprecated APIs
- Breaking changes

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git for version control
- Docker (optional, for containerized development)
- Node.js 18+ and npm (for frontend development)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd AutoDoc

# One-command setup (installs dependencies, configures environment, runs tests)
make setup
```

This command will:
1. Install Python dependencies with development extras
2. Set up pre-commit hooks
3. Create `.env` file from template
4. Create required directories (logs, uploads, temp, data)
5. Run initial test suite to verify installation

### Manual Setup

If you prefer step-by-step installation:

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure pre-commit hooks
pre-commit install

# Create environment configuration
cp env.example .env
# Edit .env with your configuration values

# Create required directories
mkdir -p logs uploads temp data

# Verify installation
make test
```

### Configuration

#### Environment Variables

Key configuration in `.env`:

```bash
# Security (Required - minimum 32 characters)
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# Database
DATABASE_URL=sqlite:///./autodoc.db

# Confluence (Optional - for future integration)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=YOUR_SPACE

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Server
HOST=0.0.0.0
PORT=8000
```

See `env.example` for complete configuration options.

## Usage

### Running Locally

Start the development server:

```bash
make dev
```

Access the application:
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json
- Angular UI: http://localhost:4200 (if running frontend separately)

### Running with Docker

```bash
# Build Docker images
make docker.build

# Start services
make docker.run

# View logs
make docker.logs

# Stop services
make docker.stop
```

### CLI Interface (In Development)

The CLI is currently being developed for MVP integration. Planned usage:

```bash
# Analyze current commit (planned)
autodoc analyze --repo /path/to/repo --commit HEAD

# Analyze commit range (planned)
autodoc analyze --repo /path/to/repo --from main --to feature-branch

# Test mode - preview without persisting (planned)
autodoc analyze --repo /path/to/repo --commit HEAD --test-mode
```

### API Endpoints

Current functional endpoints:

```
GET    /api/v1/health           - Health check
POST   /api/v1/templates        - Create documentation template
GET    /api/v1/templates        - List available templates
GET    /api/v1/templates/{id}   - Get specific template
PUT    /api/v1/templates/{id}   - Update template
DELETE /api/v1/templates/{id}   - Delete template
```

Planned endpoints (Sprint 4):
```
POST   /api/v1/analyze          - Trigger code analysis
GET    /api/v1/runs/{run_id}    - Retrieve analysis results
GET    /api/v1/runs/{run_id}/symbols - Get extracted symbols
POST   /api/v1/rules            - Create mapping rule
GET    /api/v1/connections      - Manage Confluence connections
```

### CI/CD Integration (Planned)

AutoDoc is designed to integrate into CI/CD pipelines. Example configurations for Sprint 4:

#### GitHub Actions

```yaml
name: AutoDoc Analysis

on:
  pull_request:
    branches: [main, develop]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Required for git history
      
      - name: Run AutoDoc
        uses: docker://ghcr.io/your-org/autodoc:latest
        with:
          args: analyze --commit ${{ github.sha }} --repo ${{ github.repository }}
```

#### GitLab CI

```yaml
autodoc:
  image: ghcr.io/your-org/autodoc:latest
  script:
    - autodoc analyze --commit $CI_COMMIT_SHA --repo $CI_PROJECT_PATH
  only:
    - merge_requests
```

## Development Guide

### Development Workflow

```bash
# Start development server with auto-reload
make dev

# Run tests continuously during development
make test-watch

# Check code quality before committing
make check-all  # Runs tests, linting, type checking
```

### Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests only

# Run specific test file
pytest tests/unit/test_analyzers.py -v

# Run specific test
pytest tests/unit/test_analyzers.py::TestPythonAnalyzer::test_function_detection -v
```

Test organization:
```
tests/
├── unit/              # Unit tests (>70% coverage target)
│   ├── test_analyzers.py
│   ├── test_detectors.py
│   ├── test_extractors.py
│   └── test_api.py
├── integration/       # Integration tests
│   └── test_analyzer_pipeline.py
└── conftest.py        # Shared fixtures and configuration
```

### Code Quality

```bash
# Lint code
make lint

# Auto-format code
make format

# Type checking
make typecheck

# Run pre-commit hooks manually
make pre-commit

# Run all quality checks (CI equivalent)
make ci
```

Quality standards:
- PEP 8 compliance enforced by Ruff
- Type hints required for all functions (MyPy strict mode)
- Minimum 70% test coverage
- Pre-commit hooks for automatic checks
- Structured logging with correlation IDs

### Git Branching Strategy

The project uses a simplified Git Flow workflow:

```
main (protected)
  ├── develop (integration branch)
      ├── infrastructure/SCRUM-X-feature-name
      ├── backend/SCRUM-X-feature-name
      └── frontend/SCRUM-X-feature-name
```

**Workflow**:

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b infrastructure/SCRUM-42-docker-optimization

# Work on feature with meaningful commits
git add .
git commit -m "feat(infra): optimize Docker multi-stage build"

# Push and create PR to develop
git push origin infrastructure/SCRUM-42-docker-optimization
```

**Pull Request Requirements**:
- At least 1 review from another team member
- All CI checks must pass (tests, linting, type checking)
- No merge conflicts with target branch
- Sprint completion: PRs from develop to main require all team member reviews

### Project Structure

```
AutoDoc/
├── src/
│   └── autodoc/
│       ├── analyzers/       # Code analysis (AST parsing, symbol extraction)
│       ├── detectors/       # Change detection logic
│       ├── extractors/      # Docstring and metadata extraction
│       ├── connectors/      # External service integration (Confluence, Git)
│       ├── templates/       # Template engine and rules
│       ├── api/            # FastAPI routes and models
│       ├── cli/            # Command-line interface
│       ├── models/         # Database models
│       └── logging/        # Structured logging utilities
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── frontend/              # Angular application
│   ├── src/
│   │   ├── app/
│   │   └── environments/
│   └── angular.json
├── docker/               # Docker configurations
│   ├── Dockerfile
│   └── docker-compose.yml
├── .github/
│   └── workflows/        # CI/CD pipelines
├── scripts/              # Utility scripts
└── docs/                # Additional documentation
```

## Technical Achievements

### Sprint Accomplishments (Sprint 0-3)

**Static Code Analysis**
- Dual language support: Python and TypeScript AST parsing
- Comprehensive symbol extraction for modules, classes, functions, and methods
- Accurate change detection across git commits with diff analysis
- Docstring and JSDoc extraction for contextual documentation
- Test coverage exceeding 70% target across analyzer components

**Infrastructure Excellence**
- Docker multi-stage builds reducing image size from 1.2GB to under 500MB
- Build time optimization from 2+ minutes to approximately 15 seconds
- GitHub Actions CI/CD pipeline with parallel test execution
- GitHub Container Registry integration for automated image publishing
- Complete pipeline execution in ~15 seconds

**Full-Stack Implementation**
- FastAPI backend with type-safe Pydantic models
- SQLAlchemy ORM with Alembic migrations for schema management
- Angular frontend with reactive forms and component-based architecture
- RESTful API design following OpenAPI 3.0 specification
- Structured JSON output for downstream consumption

**Template Engine**
- Variable substitution system for dynamic documentation generation
- Support for Markdown and Confluence Storage Format
- Dry-run mode for safe preview without side effects
- Test mode for template experimentation
- CRUD interface for template management

**Code Quality & Testing**
- Unit tests for individual components with mocked dependencies
- Integration tests for end-to-end pipeline validation
- MyPy strict mode type checking eliminating type-related bugs
- Ruff linting with zero violations in production code
- Pre-commit hooks enforcing quality gates before commits

### Engineering Practices

**SOLID Principles**
- Single Responsibility: Separate detector classes for each analysis type (function, class, module)
- Open/Closed: Extensible analyzer interface for adding new languages
- Dependency Inversion: Abstract base classes for analyzers and connectors

**Performance Optimization**
- Efficient AST parsing for repositories up to 10,000 lines of code
- Change detection handles up to 500 LOC changes efficiently
- Structured dataclass output minimizing serialization overhead
- Layer caching in Docker builds preventing redundant operations

**Security & Best Practices**
- Non-root user execution in Docker containers
- Secure secret management with environment variables
- Token masking in logs and UI (planned for Sprint 4)
- Input validation using Pydantic schemas
- Comprehensive error handling with structured logging

## Known Limitations

**Current Implementation Scope:**
- Analysis supports Python and TypeScript only (additional languages planned)
- CLI interface in development for MVP (API functional)
- Template engine supports basic variable substitution (advanced conditionals planned)
- Single repository analysis per run (multi-repo support planned)
- Patch generation and preview functional; Confluence publishing pending integration

**Deferred Features:**
- Confluence API integration for live documentation updates
- Rule-based mapping of files to documentation pages
- Approval workflow for patch review
- Rollback functionality with version history
- Audit trail and compliance logging

## Future Roadmap

**Sprint 4: Approval Workflow & Integration** (December 2025)
- Complete CLI interface for CI/CD integration
- Implement Confluence API client with retry logic
- Build rule engine for file-to-page mapping
- Create approval workflow for patch review
- Add auto-approve flags per rule
- Implement rollback functionality

**Phase 2: Production Readiness**
- Enhanced observability with comprehensive audit trails
- Read-only viewer role for documentation consumers
- PR/MR comment integration for GitHub/GitLab
- Performance optimization for large repositories
- Multi-repository analysis support

**Phase 3: Extended Language Support**
- Java analyzer for Spring Boot applications
- Go analyzer for microservices
- C# analyzer for .NET projects
- Plugin architecture for custom analyzers

**Phase 4: Advanced Features**
- Breaking change detection with impact analysis
- Dependency graph visualization
- Real-time collaboration on templates
- Webhook integrations for custom workflows
- AI-assisted documentation suggestions

## Contributing

### For Contributors

We welcome contributions from developers interested in automated documentation, static analysis, or CI/CD tooling.

**Getting Started**:
1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Set up development environment: `make setup`
4. Create a feature branch: `git checkout -b feature/your-feature-name`
5. Make your changes with tests
6. Run quality checks: `make check-all`
7. Submit a pull request

**Contribution Guidelines**:
- Write tests for new functionality (maintain >70% coverage)
- Follow existing code style (enforced by Ruff)
- Add type hints to all functions
- Update documentation for user-facing changes
- Use structured logging with correlation IDs
- Write clear commit messages following conventional commits

**Areas for Contribution**:
- Additional language analyzers (TypeScript, Java, Go)
- Template engine enhancements
- UI/UX improvements for frontend
- Documentation and examples
- Performance optimizations
- Bug fixes and testing

### Pull Request Process

1. Ensure all tests pass: `make test`
2. Verify code quality: `make check-all`
3. Update relevant documentation
4. Add entry to CHANGELOG.md
5. Request review from at least one maintainer
6. Address review feedback
7. Squash commits if requested

## Team

AutoDoc is developed by a three-person team as part of CS4398 Senior Design:

- **Noah**: Infrastructure & CI/CD Lead - Docker, CI/CD pipelines, AST parsing, system architecture
- **Ryan**: Backend Developer - Python/FastAPI, database, API endpoints
- **Logan**: Frontend Developer - Angular/TypeScript, UI components, template management

## License

[License information to be determined]

## Acknowledgments

**Technologies**:
- FastAPI for modern Python web framework
- Pydantic for data validation and settings management
- Angular for frontend framework
- Docker for containerization
- GitHub Actions for CI/CD automation

**Inspiration**:
- Automated documentation tools like Sphinx and MkDocs
- Static analysis frameworks like Pylint and MyPy
- CI/CD best practices from industry leaders

## Contact

For questions, feedback, or collaboration opportunities:
- Create an issue in the repository
- Contact the development team through university channels
- Review the documentation at `/docs`

---

**Project Timeline**: October 2025 - December 2025  
**Institution**: University Capstone Project (CS4398 Senior Design)  
**Status**: Active Development - Functional Prototype
