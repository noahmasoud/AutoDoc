"""Unit tests for TypeScript parser service."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services.typescript_parser import (
    NodeJSNotFoundError,
    ParseError,
    TypeScriptParser,
    TypeScriptParserError,
)


class TestTypeScriptParser:
    """Test suite for TypeScriptParser."""

    @pytest.mark.unit
    def test_init_with_default_script(self, mock_nodejs):
        """Test parser initialization with default script path."""
        parser = TypeScriptParser()
        assert parser.parser_script.exists()

    @pytest.mark.unit
    def test_init_with_custom_script(self, mock_nodejs, tmp_path):
        """Test parser initialization with custom script path."""
        custom_script = tmp_path / "custom-parser.js"
        custom_script.write_text("console.log('test');")
        
        parser = TypeScriptParser(str(custom_script))
        assert parser.parser_script == custom_script

    @pytest.mark.unit
    def test_init_with_nonexistent_script(self, mock_nodejs, tmp_path):
        """Test parser initialization with non-existent script."""
        nonexistent = tmp_path / "does-not-exist.js"
        
        with pytest.raises(FileNotFoundError):
            TypeScriptParser(str(nonexistent))

    @pytest.mark.unit
    def test_check_nodejs_success(self, mock_nodejs):
        """Test Node.js availability check succeeds."""
        parser = TypeScriptParser()
        parser._check_nodejs()  # Should not raise

    @pytest.mark.unit
     
    def test_check_nodejs_not_found(self, mock_nodejs):
        """Test Node.js availability check fails when Node.js not installed."""
        mock_nodejs.side_effect = FileNotFoundError("node: command not found")
        
        with pytest.raises(NodeJSNotFoundError):
            TypeScriptParser()

    @pytest.mark.unit
    def test_parse_file_success(self, mock_nodejs):
        """Test successful file parsing."""
        mock_ast = {
            "type": "Program",
            "body": [
                {
                    "type": "ClassDeclaration",
                    "id": {"name": "MyClass"},
                    "loc": {"start": {"line": 1}}
                }
            ]
        }
        
        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"success": True, "ast": mock_ast}),
            stderr=""
        )
        
        parser = TypeScriptParser()
        result = parser.parse_file("test.ts")
        
        assert result == mock_ast
        mock_nodejs.assert_called()

    @pytest.mark.unit
     
    def test_parse_file_parse_error(self, mock_nodejs):
        """Test file parsing with syntax error."""
        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps({
                "success": False,
                "error": {"message": "Syntax error"}
            }),
            stderr=""
        )
        
        parser = TypeScriptParser()
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_file("test.ts")
        
        assert "Syntax error" in str(exc_info.value)

    @pytest.mark.unit
     
    def test_parse_file_subprocess_error(self, mock_nodejs):
        """Test file parsing with subprocess error."""
        mock_nodejs.return_value = Mock(
            returncode=1,
            stdout="",
            stderr=json.dumps({"error": "Subprocess failed"})
        )
        
        parser = TypeScriptParser()
        
        with pytest.raises(ParseError):
            parser.parse_file("test.ts")

    @pytest.mark.unit
    def test_parse_file_nonexistent(self, mock_nodejs):
        """Test parsing non-existent file."""
        parser = TypeScriptParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent.ts")

    @pytest.mark.unit
     
    def test_parse_string_success(self, mock_nodejs):
        """Test successful string parsing."""
        mock_ast = {
            "type": "Program",
            "body": [
                {
                    "type": "FunctionDeclaration",
                    "id": {"name": "myFunction"},
                    "loc": {"start": {"line": 1}}
                }
            ]
        }
        
        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"success": True, "ast": mock_ast}),
            stderr=""
        )
        
        parser = TypeScriptParser()
        source_code = "function myFunction() {}"
        result = parser.parse_string(source_code)
        
        assert result == mock_ast

    @pytest.mark.unit
    def test_parse_string_empty(self, mock_nodejs):
        """Test parsing empty string."""
        parser = TypeScriptParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse_string("")
        
        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.unit
     
    def test_parse_string_timeout(self, mock_nodejs):
        """Test string parsing timeout."""
        mock_nodejs.side_effect = subprocess.TimeoutExpired("node", 30)
        
        parser = TypeScriptParser()
        
        with pytest.raises(ParseError) as exc_info:
            parser.parse_string("const x = 1;")
        
        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_extract_public_symbols_classes(self, mock_nodejs):
        """Test extracting class symbols from AST."""
        ast = {
            "body": [
                {
                    "type": "ClassDeclaration",
                    "id": {"name": "MyClass"},
                    "loc": {"start": {"line": 1}},
                    "decorators": [{"type": "_kind"}]
                }
            ]
        }
        
        parser = TypeScriptParser()
        symbols = parser.extract_public_symbols(ast)
        
        assert len(symbols["classes"]) == 1
        assert symbols["classes"][0]["name"] == "MyClass"
        assert symbols["classes"][0]["decorators"] == 1

    @pytest.mark.unit
    def test_extract_public_symbols_functions(self, mock_nodejs):
        """Test extracting function symbols from AST."""
        ast = {
            "body": [
                {
                    "type": "FunctionDeclaration",
                    "id": {"name": "myFunction"},
                    "loc": {"start": {"line": 10}},
                    "async": True
                }
            ]
        }
        
        parser = TypeScriptParser()
        symbols = parser.extract_public_symbols(ast)
        
        assert len(symbols["functions"]) == 1
        assert symbols["functions"][0]["name"] == "myFunction"
        assert symbols["functions"][0]["async"] is True

    @pytest.mark.unit
    def test_extract_public_symbols_interfaces(self, mock_nodejs):
        """Test extracting interface symbols from AST."""
        ast = {
            "body": [
                {
                    "type": "TSInterfaceDeclaration",
                    "id": {"name": "MyInterface"},
                    "loc": {"start": {"line": 5}}
                }
            ]
        }
        
        parser = TypeScriptParser()
        symbols = parser.extract_public_symbols(ast)
        
        assert len(symbols["interfaces"]) == 1
        assert symbols["interfaces"][0]["name"] == "MyInterface"

    @pytest.mark.unit
    def test_extract_public_symbols_empty(self, mock_nodejs):
        """Test extracting symbols from empty AST."""
        ast = {"body": []}
        
        parser = TypeScriptParser()
        symbols = parser.extract_public_symbols(ast)
        
        assert all(len(symbols[key]) == 0 for key in symbols)

    @pytest.mark.unit
    def test_extract_public_symbols_no_body(self, mock_nodejs):
        """Test extracting symbols from AST without body."""
        ast = {}
        
        parser = TypeScriptParser()
        symbols = parser.extract_public_symbols(ast)
        
        assert all(len(symbols[key]) == 0 for key in symbols)

