"""Unit tests for JavaScript parser."""

from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from services.javascript_parser import (
    JavaScriptParser,
    JavaScriptParserError,
    NodeJSNotFoundError,
    ParseError,
)


class TestJavaScriptParser:
    """Unit tests for JavaScriptParser."""

    def test_init_with_default_script(self):
        """Test parser initialization with default script path."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            parser = JavaScriptParser()
            assert parser.parser_script.name == "parse-typescript.js"

    def test_init_with_custom_script(self):
        """Test parser initialization with custom script path."""
        custom_script = Path("/custom/path/parser.js")
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            with patch.object(Path, "exists", return_value=True):
                parser = JavaScriptParser(parser_script=str(custom_script))
                assert parser.parser_script == custom_script

    def test_check_nodejs_not_found(self):
        """Test error when Node.js is not found."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(NodeJSNotFoundError):
                JavaScriptParser()

    def test_check_nodejs_timeout(self):
        """Test error when Node.js check times out."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("node", 5)
            with pytest.raises(NodeJSNotFoundError):
                JavaScriptParser()

    def test_parse_file_success(self):
        """Test successful file parsing."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            parser = JavaScriptParser()
            
            mock_ast = {
                "success": True,
                "ast": {
                    "body": [
                        {
                            "type": "FunctionDeclaration",
                            "id": {"name": "testFunc"},
                            "loc": {"start": {"line": 1}},
                        }
                    ]
                }
            }
            
            with patch.object(Path, "exists", return_value=True):
                with patch("services.javascript_parser.subprocess.run") as mock_parse:
                    mock_parse.return_value = Mock(
                        returncode=0,
                        stdout='{"success": true, "ast": {"body": [{"type": "FunctionDeclaration", "id": {"name": "testFunc"}, "loc": {"start": {"line": 1}}}]}}',
                        stderr="",
                    )
                    result = parser.parse_file("test.js")
                    assert "body" in result

    def test_parse_file_not_found(self):
        """Test error when file doesn't exist."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            parser = JavaScriptParser()
            with pytest.raises(FileNotFoundError):
                parser.parse_file("nonexistent.js")

    def test_extract_public_symbols(self):
        """Test symbol extraction from AST."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            parser = JavaScriptParser()
            
            ast = {
                "body": [
                    {
                        "type": "FunctionDeclaration",
                        "id": {"name": "testFunc"},
                        "loc": {"start": {"line": 1}},
                        "async": False,
                    },
                    {
                        "type": "ClassDeclaration",
                        "id": {"name": "TestClass"},
                        "loc": {"start": {"line": 5}},
                        "decorators": [],
                    },
                ]
            }
            
            symbols = parser.extract_public_symbols(ast)
            assert len(symbols["functions"]) == 1
            assert len(symbols["classes"]) == 1
            assert symbols["functions"][0]["name"] == "testFunc"
            assert symbols["classes"][0]["name"] == "TestClass"

    def test_is_javascript_file(self):
        """Test JavaScript file detection."""
        with patch("services.javascript_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
            parser = JavaScriptParser()
            assert parser._is_javascript_file("test.js") is True
            assert parser._is_javascript_file("test.jsx") is True
            assert parser._is_javascript_file("test.ts") is False
            assert parser._is_javascript_file("test.py") is False

