# AutoDoc Test Suite

This directory contains the comprehensive test suite for the AutoDoc project, designed to achieve ≥70% unit test coverage for analyzers and connectors.

## Test Structure

```
tests/
├── __init__.py                           # Test package initialization
├── conftest.py                           # Pytest configuration and shared fixtures
├── unit/                                 # Unit tests
│   ├── __init__.py
│   ├── test_analyzers.py                 # Code analyzer tests
│   ├── test_connectors.py                # External connector tests
│   ├── test_api.py                       # API endpoint tests
│   ├── test_cli.py                       # CLI interface tests
│   └── test_schemas.py                   # Data schema tests
├── integration/                          # Integration tests
│   ├── __init__.py
│   └── test_analyzer_connector_integration.py
└── README.md                            # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Analyzer Tests**: Tests for code analysis functionality
- **Connector Tests**: Tests for external service connectors (Confluence, Database, etc.)
- **API Tests**: Tests for REST API endpoints
- **CLI Tests**: Tests for command-line interface
- **Schema Tests**: Tests for data validation schemas

### Integration Tests (`tests/integration/`)
- **Analyzer-Connector Integration**: Tests for complete workflows
- **End-to-End Workflows**: Tests for full application flows

## Test Markers

The test suite uses pytest markers for categorization:

- `unit`: Unit tests
- `integration`: Integration tests
- `analyzer`: Analyzer-specific tests
- `connector`: Connector-specific tests
- `api`: API endpoint tests
- `cli`: CLI interface tests
- `database`: Database-related tests
- `external`: Tests requiring external services
- `slow`: Tests that take a long time to run
- `smoke`: Basic functionality tests
- `regression`: Bug fix regression tests

## Running Tests

### Quick Commands
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run with coverage
make coverage

# Run specific test categories
pytest -m "analyzer"
pytest -m "connector"
pytest -m "unit and not slow"
```

### CI Commands
```bash
# Full CI pipeline
make ci

# CI linting only
make ci-lint

# CI tests only
make ci-test

# Direct CI test command (as specified)
pytest -q --maxfail=1 --disable-warnings -q
```

### Custom Test Runs
```bash
# Run tests with specific markers
pytest -m "unit and analyzer"
pytest -m "integration and not external"

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_analyzers.py

# Run with coverage and minimum threshold
pytest --cov=. --cov-fail-under=70
```

## Coverage Requirements

- **Minimum Coverage**: 70% for analyzers and connectors
- **Coverage Reports**: Generated in multiple formats (terminal, HTML, XML)
- **Coverage Scope**: All main modules (`autodoc`, `api`, `cli`, `core`, `db`, `schemas`, `services`)

## Test Fixtures

The `conftest.py` file provides shared fixtures:

- `temp_dir`: Temporary directory for testing
- `mock_settings`: Mock application settings
- `mock_database`: Mock database session
- `mock_confluence_client`: Mock Confluence API client
- `sample_python_code`: Sample Python code for testing
- `sample_ast_tree`: Sample AST tree for testing
- `mock_http_response`: Mock HTTP response
- `mock_file_system`: Mock file system operations

## Development Guidelines

1. **Write Tests First**: Follow TDD principles when implementing features
2. **Mock External Dependencies**: Use mocks for external services and APIs
3. **Use Descriptive Names**: Test names should clearly describe what is being tested
4. **One Assert Per Test**: Keep tests focused on a single behavior
5. **Use Appropriate Markers**: Mark tests with relevant categories
6. **Maintain Coverage**: Ensure new code maintains ≥70% coverage

## Test Data

- Use the provided fixtures for consistent test data
- Create additional fixtures in `conftest.py` for shared test data
- Use descriptive variable names for test data

## Continuous Integration

The test suite is designed to run in CI environments with:

- **Fast Execution**: Unit tests run quickly without external dependencies
- **Reliable**: Tests are deterministic and don't depend on external state
- **Comprehensive**: Covers all critical functionality
- **Maintainable**: Easy to extend and modify

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `pip install -e ".[dev]"`
2. **Coverage Issues**: Check that all source files are included in coverage configuration
3. **Slow Tests**: Use `-m "not slow"` to skip slow tests during development
4. **External Dependencies**: Use `-m "not external"` to skip tests requiring external services

### Getting Help

- Check pytest documentation: https://docs.pytest.org/
- Review coverage documentation: https://coverage.readthedocs.io/
- Check project-specific configuration in `pytest.ini` and `.coveragerc`
