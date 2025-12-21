"""Unit tests for Go parser."""

from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from services.go_parser import (
    GoParser,
    GoParserError,
    GoNotFoundError,
    ParseError,
)


class TestGoParser:
    """Unit tests for GoParser."""

    def test_init_with_default_binary(self):
        """Test parser initialization with default binary path."""
        with patch("services.go_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")
            with patch.object(Path, "exists", return_value=True):
                parser = GoParser()
                assert "parse-go" in str(parser.parser_binary)

    def test_check_go_not_found(self):
        """Test error when Go is not found."""
        with patch("services.go_parser.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            with pytest.raises(GoNotFoundError):
                GoParser()

    def test_parse_file_success(self):
        """Test successful file parsing."""
        with patch("services.go_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")
            parser = GoParser()
            
            mock_ast = {
                "package": "main",
                "body": [
                    {
                        "type": "FunctionDeclaration",
                        "name": "main",
                        "line": 1,
                    }
                ]
            }
            
            with patch.object(Path, "exists", return_value=True):
                with patch("services.go_parser.subprocess.run") as mock_parse:
                    import json
                    mock_parse.return_value = Mock(
                        returncode=0,
                        stdout=json.dumps({"success": True, "ast": mock_ast}),
                        stderr="",
                    )
                    result = parser.parse_file("test.go")
                    assert "body" in result

    def test_extract_public_symbols(self):
        """Test symbol extraction from AST."""
        with patch("services.go_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")
            with patch.object(Path, "exists", return_value=True):
                parser = GoParser()
                
                ast = {
                    "body": [
                        {
                            "type": "FunctionDeclaration",
                            "name": "testFunc",
                            "line": 1,
                            "data": {"exported": True},
                        },
                        {
                            "type": "TypeDeclaration",
                            "name": "TestType",
                            "line": 5,
                            "data": {"exported": True},
                        },
                    ]
                }
                
                symbols = parser.extract_public_symbols(ast)
                assert len(symbols["functions"]) == 1
                assert len(symbols["types"]) == 1
                assert symbols["functions"][0]["name"] == "testFunc"
                assert symbols["types"][0]["name"] == "TestType"

    def test_is_go_file(self):
        """Test Go file detection."""
        with patch("services.go_parser.subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")
            with patch.object(Path, "exists", return_value=True):
                parser = GoParser()
                assert parser._is_go_file("test.go") is True
                assert parser._is_go_file("test.js") is False
                assert parser._is_go_file("test.py") is False

