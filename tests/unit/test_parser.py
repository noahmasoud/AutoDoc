import ast
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.analyzer.parser import PythonParser, ParseResult, parse_python_file


class TestParseResult:
    """Tests for ParseResult dataclass"""

    def test_parse_result_success(self):
        """Test creating a successful ParseResult"""
        tree = ast.parse("x = 1")
        result = ParseResult(
            success=True,
            file_path="/path/to/file.py",
            ast_tree=tree,
        )

        assert result.success is True
        assert result.file_path == "/path/to/file.py"
        assert result.ast_tree is tree
        assert result.error is None
        assert result.error_line is None

    def test_parse_result_failure(self):
        """Test creating a failed ParseResult"""
        result = ParseResult(
            success=False,
            file_path="/path/to/file.py",
            error="Syntax error",
            error_line=10,
        )

        assert result.success is False
        assert result.file_path == "/path/to/file.py"
        assert result.ast_tree is None
        assert result.error == "Syntax error"
        assert result.error_line == 10


class TestPythonParser:
    """Tests for PythonParser class"""

    @pytest.fixture
    def parser(self):
        """Create a parser instance with a mock logger"""
        logger = Mock(spec=logging.Logger)
        return PythonParser(logger=logger)

    @pytest.fixture
    def temp_python_file(self):
        """Create a temporary Python file for testing"""
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write('def hello():\n    return "world"\n')
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    # ==========================================
    # Tests for valid Python files
    # ==========================================

    def test_parse_simple_function(self, parser, temp_python_file):
        """Test parsing a simple Python function"""
        result = parser.parse(temp_python_file)

        assert result.success is True
        assert result.ast_tree is not None
        assert isinstance(result.ast_tree, ast.Module)
        assert result.error is None

        # Verify logger was called
        parser.logger.info.assert_called_once()

    def test_parse_with_class(self, parser):
        """Test parsing a file with a class definition"""
        code = """
class MyClass:
    def __init__(self, value):
        self.value = value
    
    def get_value(self):
        return self.value
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True
            assert result.ast_tree is not None

            # Verify class is in the AST
            classes = [node for node in ast.walk(
                result.ast_tree) if isinstance(node, ast.ClassDef)]
            assert len(classes) == 1
            assert classes[0].name == "MyClass"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_with_python_311_features(self, parser):
        """Test parsing Python 3.11+ syntax (match statement)"""
        code = """
def process_command(command):
    match command:
        case "start":
            return "Starting..."
        case "stop":
            return "Stopping..."
        case _:
            return "Unknown command"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True
            assert result.ast_tree is not None

            # Verify match statement is in the AST
            matches = [node for node in ast.walk(
                result.ast_tree) if isinstance(node, ast.Match)]
            assert len(matches) == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_with_type_hints(self, parser):
        """Test parsing file with type hints"""
        code = """
from typing import List, Optional

def process_items(items: List[str], default: Optional[str] = None) -> str:
    if not items:
        return default or "empty"
    return items[0]
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_empty_file(self, parser):
        """Test parsing an empty Python file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Write nothing - empty file
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True
            assert result.ast_tree is not None
            assert isinstance(result.ast_tree, ast.Module)
            assert len(result.ast_tree.body) == 0
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_file_with_only_comments(self, parser):
        """Test parsing a file with only comments"""
        code = """
# This is a comment
# Another comment
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_with_docstring(self, parser):
        """Test parsing file with module docstring"""
        code = '''"""This is a module docstring."""

def my_function():
    """Function docstring"""
    pass
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result.success is True

            # Verify docstring is accessible
            module_docstring = ast.get_docstring(result.ast_tree)
            assert module_docstring == "This is a module docstring."
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # ==========================================
    # Tests for syntax errors
    # ==========================================

    def test_parse_syntax_error(self, parser):
        """Test parsing file with syntax error"""
        code = """
def broken_function(
    # Missing closing parenthesis
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is False
            assert result.ast_tree is None
            assert result.error is not None
            assert "Syntax error" in result.error
            assert result.error_line is not None

            # Verify logger was called
            parser.logger.exception.assert_called()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_indentation_error(self, parser):
        """Test parsing file with indentation error"""
        code = """
def my_function():
print("This is not indented correctly")
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is False
            assert result.error is not None
            assert result.error_line is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_invalid_syntax(self, parser):
        """Test parsing file with invalid Python syntax"""
        code = "def for while class import"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is False
            assert result.error is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # ==========================================
    # Tests for path handling
    # ==========================================

    def test_parse_nonexistent_file(self, parser):
        """Test parsing a file that doesn't exist"""
        result = parser.parse("/path/to/nonexistent/file.py")

        assert result.success is False
        assert result.error is not None
        assert "File not found" in result.error
        assert result.ast_tree is None

        # Verify logger was called
        parser.logger.exception.assert_called()

    def test_parse_directory_instead_of_file(self, parser):
        """Test parsing a directory path instead of a file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = parser.parse(temp_dir)

            assert result.success is False
            assert result.error is not None
            assert "Path is not a file" in result.error
            assert result.ast_tree is None

            parser.logger.exception.assert_called()

    def test_parse_relative_path(self, parser):
        """Test parsing with relative path"""
        code = "x = 1"

        # Create file in current directory
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            dir=".",
        ) as f:
            f.write(code)
            temp_name = Path(f.name).name

        try:
            # Parse using just the filename (relative path)
            result = parser.parse(temp_name)

            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_name).unlink(missing_ok=True)

    def test_parse_absolute_path(self, parser, temp_python_file):
        """Test parsing with absolute path"""
        absolute_path = str(Path(temp_python_file).resolve())
        result = parser.parse(absolute_path)

        assert result.success is True
        assert result.ast_tree is not None

    # ==========================================
    # Tests for error handling
    # ==========================================

    def test_parse_invalid_encoding(self, parser):
        """Test parsing file with invalid UTF-8 encoding"""
        # Create a file with invalid UTF-8 bytes
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".py", delete=False) as f:
            f.write(b'def test():\n    x = "\xff\xfe"\n')  # Invalid UTF-8
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            # Should fail gracefully with encoding error
            assert result.success is False
            assert result.error is not None
            assert "Encoding error" in result.error or "decode" in result.error.lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_with_custom_logger(self):
        """Test parser with custom logger"""
        custom_logger = Mock(spec=logging.Logger)
        parser = PythonParser(logger=custom_logger)

        code = "x = 1"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            # Verify custom logger was used
            custom_logger.info.assert_called_once()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # ==========================================
    # Tests for internal methods
    # ==========================================

    def test_resolve_path_absolute(self, parser):
        """Test _resolve_path with absolute path"""
        absolute_path = "/home/user/project/main.py"
        resolved = parser._resolve_path(absolute_path)

        assert resolved.is_absolute()
        assert "home/user/project/main.py" in str(resolved)

    def test_resolve_path_relative(self, parser):
        """Test _resolve_path with relative path"""
        relative_path = "./src/main.py"
        resolved = parser._resolve_path(relative_path)

        assert resolved.is_absolute()

    def test_resolve_path_home_directory(self, parser):
        """Test _resolve_path with home directory expansion"""
        home_path = "~/project/main.py"
        resolved = parser._resolve_path(home_path)

        assert resolved.is_absolute()
        assert "~" not in str(resolved)

    def test_read_file_content(self, parser, temp_python_file):
        """Test _read_file_content method"""
        path = Path(temp_python_file)
        content = parser._read_file_content(path)

        assert isinstance(content, str)
        assert "def hello" in content
        assert 'return "world"' in content


class TestConvenienceFunction:
    """Tests for parse_python_file convenience function"""

    def test_parse_python_file_success(self):
        """Test convenience function with valid file"""
        code = "x = 1"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parse_python_file(temp_path)

            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_python_file_with_error(self):
        """Test convenience function with invalid file"""
        result = parse_python_file("/nonexistent/file.py")

        assert result.success is False
        assert result.error is not None


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    @pytest.fixture
    def parser(self):
        return PythonParser()

    def test_parse_very_large_file(self, parser):
        """Test parsing a large Python file"""
        # Generate a large but valid Python file
        code = "# Large file\n" + \
            "\n".join([f"x{i} = {i}" for i in range(1000)])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_file_with_unicode(self, parser):
        """Test parsing file with Unicode characters"""
        code = '''
def greet():
    """Say hello in different languages"""
    return "Hello 👋 Bonjour 🇫🇷 こんにちは 🇯🇵"
'''
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert result.ast_tree is not None
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_parse_file_with_async_functions(self, parser):
        """Test parsing file with async/await syntax"""
        code = """
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "data"

async def main():
    result = await fetch_data()
    return result
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True

            # Verify async functions are in the AST
            async_funcs = [
                node for node in ast.walk(result.ast_tree)
                if isinstance(node, ast.AsyncFunctionDef)
            ]
            assert len(async_funcs) == 2
        finally:
            Path(temp_path).unlink(missing_ok=True)
