"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_settings() -> Mock:
    """Mock application settings."""
    settings = Mock()
    settings.debug = False
    settings.log_level = "INFO"
    settings.database_url = "sqlite:///:memory:"
    settings.confluence_url = "https://example.atlassian.net"
    settings.confluence_token = "mock_token"
    return settings


@pytest.fixture
def mock_database() -> Mock:
    """Mock database session."""
    session = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.add = Mock()
    session.delete = Mock()
    session.query = Mock()
    session.execute = Mock()
    return session


@pytest.fixture
def mock_confluence_client() -> Mock:
    """Mock Confluence API client."""
    client = Mock()
    client.get_page = Mock(return_value={"id": "123", "title": "Test Page"})
    client.create_page = Mock(return_value={"id": "456", "title": "New Page"})
    client.update_page = Mock(return_value={"id": "123", "title": "Updated Page"})
    client.delete_page = Mock(return_value=True)
    client.search_pages = Mock(return_value=[{"id": "123", "title": "Test Page"}])
    return client


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing analyzers."""
    return '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of a and b
    """
    return a + b


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value: int = 0):
        """Initialize calculator with initial value.

        Args:
            initial_value: Starting value for calculations
        """
        self.value = initial_value

    def add(self, number: int) -> int:
        """Add a number to the current value.

        Args:
            number: Number to add

        Returns:
            New value after addition
        """
        self.value += number
        return self.value


if __name__ == "__main__":
    calc = Calculator(10)
    result = calc.add(5)
    print(f"Result: {result}")
'''


@pytest.fixture
def sample_ast_tree() -> Any:
    """Sample AST tree for testing."""
    import ast

    # Parse the sample code into an AST
    code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, World!")


class MyClass:
    """A simple class."""

    def method(self):
        """A simple method."""
        return "Hello from method"
'''

    return ast.parse(code)


@pytest.fixture
def mock_http_response() -> Mock:
    """Mock HTTP response for testing."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"success": True, "data": []}
    response.text = '{"success": true, "data": []}'
    response.headers = {"Content-Type": "application/json"}
    return response


@pytest.fixture
def mock_file_system() -> Mock:
    """Mock file system operations."""
    fs = Mock()
    fs.exists.return_value = True
    fs.read_text.return_value = "file content"
    fs.write_text.return_value = None
    fs.mkdir.return_value = None
    fs.rmdir.return_value = None
    fs.unlink.return_value = None
    return fs


# Markers for different test types
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "analyzer: Analyzer tests")
    config.addinivalue_line("markers", "connector: Connector tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "cli: CLI tests")
    config.addinivalue_line("markers", "database: Database tests")
    config.addinivalue_line("markers", "external: External service tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")
    config.addinivalue_line("markers", "regression: Regression tests")
