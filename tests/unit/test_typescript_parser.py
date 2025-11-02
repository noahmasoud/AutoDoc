"""Unit tests for TypeScript parser service."""

import json
import subprocess
from unittest.mock import Mock

import pytest

from services.typescript_parser import (
    NodeJSNotFoundError,
    ParseError,
    TypeScriptParser,
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
        # Initialization calls _check_nodejs, no need to call separately
        assert parser is not None

    @pytest.mark.unit
    def test_check_nodejs_not_found(self, mock_nodejs):
        """Test Node.js availability check fails when Node.js not installed."""
        mock_nodejs.side_effect = FileNotFoundError("node: command not found")

        with pytest.raises(NodeJSNotFoundError):
            TypeScriptParser()

    @pytest.mark.unit
    def test_parse_file_success(self, mock_nodejs, tmp_path):
        """Test successful file parsing."""
        mock_ast = {
            "type": "Program",
            "body": [
                {
                    "type": "ClassDeclaration",
                    "id": {"name": "MyClass"},
                    "loc": {"start": {"line": 1}},
                },
            ],
        }

        # Create a temporary test file
        test_file = tmp_path / "test.ts"
        test_file.write_text("export class MyClass {}")

        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"success": True, "ast": mock_ast}),
            stderr="",
        )

        parser = TypeScriptParser()
        result = parser.parse_file(str(test_file))

        assert result == mock_ast
        mock_nodejs.assert_called()

    @pytest.mark.unit
    def test_parse_file_parse_error(self, mock_nodejs, tmp_path):
        """Test file parsing with syntax error."""
        # Create a temporary test file
        test_file = tmp_path / "test.ts"
        test_file.write_text("invalid syntax here")

        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                {
                    "success": False,
                    "error": {"message": "Syntax error"},
                },
            ),
            stderr="",
        )

        parser = TypeScriptParser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse_file(str(test_file))

        assert "Syntax error" in str(exc_info.value)

    @pytest.mark.unit
    def test_parse_file_subprocess_error(self, mock_nodejs, tmp_path):
        """Test file parsing with subprocess error."""
        # Create a temporary test file
        test_file = tmp_path / "test.ts"
        test_file.write_text("export class Test {}")

        # First call for Node.js check succeeds, second call for parsing fails
        mock_nodejs.side_effect = [
            Mock(returncode=0, stdout="v18.0.0\n"),  # Node.js check
            Mock(
                returncode=1,
                stdout="",
                stderr=json.dumps({"error": "Subprocess failed"}),
            ),  # Parse fails
        ]

        parser = TypeScriptParser()

        with pytest.raises(ParseError):
            parser.parse_file(str(test_file))

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
                    "loc": {"start": {"line": 1}},
                },
            ],
        }

        mock_nodejs.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"success": True, "ast": mock_ast}),
            stderr="",
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
        # First call for Node.js check succeeds, second call for parsing times out
        mock_nodejs.side_effect = [
            Mock(returncode=0, stdout="v18.0.0\n"),  # Node.js check
            subprocess.TimeoutExpired("node", 30),  # Parse times out
        ]

        parser = TypeScriptParser()

        with pytest.raises(ParseError) as exc_info:
            parser.parse_string("const x = 1;")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_extract_public_symbols_classes(self, mock_nodejs):
        """Test extracting class symbols from AST."""
        ast = {
            "body": [
                {
                    "type": "ClassDeclaration",
                    "id": {"name": "MyClass"},
                    "loc": {"start": {"line": 1}},
                    "decorators": [{"type": "_kind"}],
                },
            ],
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
                    "async": True,
                },
            ],
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
                    "loc": {"start": {"line": 5}},
                },
            ],
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

    @pytest.mark.unit
    def test_extract_exported_symbols_named_export_class(self, mock_nodejs):
        """Test extracting named exported class."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "MyClass"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "decorators": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "MyClass"
        assert exports[0]["type"] == "class"
        assert exports[0]["isDefault"] is False

    @pytest.mark.unit
    def test_extract_exported_symbols_default_export_function(self, mock_nodejs):
        """Test extracting default exported function."""
        ast = {
            "body": [
                {
                    "type": "ExportDefaultDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "myFunction"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "myFunction"
        assert exports[0]["type"] == "function"
        assert exports[0]["isDefault"] is True

    @pytest.mark.unit
    def test_extract_exported_symbols_multiple_named_exports(self, mock_nodejs):
        """Test extracting multiple named exports in one statement."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "specifiers": [
                        {
                            "type": "ExportSpecifier",
                            "exported": {"name": "exportA"},
                            "local": {"name": "localA"},
                            "loc": {"start": {"line": 1, "column": 0}},
                        },
                        {
                            "type": "ExportSpecifier",
                            "exported": {"name": "exportB"},
                            "local": {"name": "localB"},
                            "loc": {"start": {"line": 1, "column": 15}},
                        },
                    ],
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 2
        assert exports[0]["symbol"] == "exportA"
        assert exports[1]["symbol"] == "exportB"
        assert all(exp["type"] == "named" for exp in exports)

    @pytest.mark.unit
    def test_extract_exported_symbols_all_export(self, mock_nodejs):
        """Test extracting export all declaration."""
        ast = {
            "body": [
                {
                    "type": "ExportAllDeclaration",
                    "source": {"value": "./other-file"},
                    "loc": {"start": {"line": 1, "column": 0}},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "*"
        assert exports[0]["type"] == "namespace"
        assert exports[0]["exportType"] == "all"
        assert "./other-file" in str(exports[0]["signature"])

    @pytest.mark.unit
    def test_extract_exported_symbols_empty_ast(self, mock_nodejs):
        """Test extracting exports from empty AST."""
        ast = {}

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 0

    @pytest.mark.unit
    def test_extract_exported_symbols_no_exports(self, mock_nodejs):
        """Test extracting exports when no exports exist."""
        ast = {
            "body": [
                {"type": "VariableDeclaration", "declarations": []},
                {"type": "ImportDeclaration", "source": {"value": "./file"}},
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 0

    @pytest.mark.unit
    def test_extract_function_signature_with_params(self, mock_nodejs):
        """Test extracting function signature with parameters."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "calculate"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [
                            {
                                "type": "Identifier",
                                "name": "a",
                            },
                            {
                                "type": "Identifier",
                                "name": "b",
                            },
                        ],
                        "returnType": {
                            "type": "TSTypeAnnotation",
                            "typeAnnotation": {
                                "type": "TSNumberKeyword",
                            },
                        },
                        "async": False,
                        "generator": False,
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "calculate"
        assert "signature" in exports[0]
        assert len(exports[0]["signature"]["params"]) == 2
        assert exports[0]["signature"]["params"][0]["name"] == "a"
        assert exports[0]["signature"]["params"][1]["name"] == "b"
        assert exports[0]["signature"]["async"] is False

    @pytest.mark.unit
    def test_extract_async_function_signature(self, mock_nodejs):
        """Test extracting async function signature."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "fetchData"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [],
                        "async": True,
                        "generator": False,
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "fetchData"
        assert exports[0]["signature"]["async"] is True

    @pytest.mark.unit
    def test_extract_class_with_superclass(self, mock_nodejs):
        """Test extracting class signature with superclass."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "ChildClass"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "superClass": {
                            "type": "Identifier",
                            "name": "BaseClass",
                        },
                        "decorators": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "ChildClass"
        assert "signature" in exports[0]
        assert exports[0]["signature"]["superClass"] == "BaseClass"

    @pytest.mark.unit
    def test_extract_class_with_decorators(self, mock_nodejs):
        """Test extracting class with decorators."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "Component"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "decorators": [
                            {"type": "Decorator", "expression": {"name": "Injectable"}},
                            {
                                "type": "Decorator",
                                "expression": {"name": "AppComponent"},
                            },
                        ],
                        "superClass": None,
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "Component"
        assert exports[0]["signature"]["decorators"] == 2

    @pytest.mark.unit
    def test_extract_complex_parameter_types(self, mock_nodejs):
        """Test extracting function with complex parameter types."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "processData"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [
                            {
                                "type": "AssignmentPattern",
                                "left": {"type": "Identifier", "name": "options"},
                            },
                            {
                                "type": "ObjectPattern",
                                "left": {},
                            },
                        ],
                        "async": False,
                        "generator": False,
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert len(exports[0]["signature"]["params"]) == 2
        assert exports[0]["signature"]["params"][0]["name"] == "options"
        assert exports[0]["signature"]["params"][0]["type"] == "AssignmentPattern"

    @pytest.mark.unit
    def test_extract_interface_signature(self, mock_nodejs):
        """Test extracting interface signature."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "User"},
                        "loc": {"start": {"line": 1, "column": 0}},
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "User"
        assert exports[0]["type"] == "interface"

    @pytest.mark.unit
    def test_exports_uniform_json_structure(self, mock_nodejs):
        """Test that all exports follow uniform JSON structure."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "func"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "MyClass"},
                        "loc": {"start": {"line": 2, "column": 0}},
                        "decorators": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        # Check uniform structure for all exports
        for export in exports:
            assert "symbol" in export
            assert "type" in export
            assert "signature" in export
            assert "location" in export
            assert "isDefault" in export

            # Verify types
            assert isinstance(export["symbol"], str)
            assert isinstance(export["type"], str)
            assert isinstance(export["signature"], dict)
            assert isinstance(export["location"], dict)
            assert isinstance(export["isDefault"], bool)

            # Verify location structure
            assert "line" in export["location"]
            assert "column" in export["location"]

    @pytest.mark.unit
    def test_serialize_exports_to_json(self, mock_nodejs):
        """Test JSON serialization of exports."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "TestClass"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "decorators": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        # Serialize to JSON
        json_str = parser.serialize_exports_to_json(exports)

        # Verify valid JSON
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["symbol"] == "TestClass"

    @pytest.mark.unit
    def test_json_structure_handles_none_values(self, mock_nodejs):
        """Test that JSON structure handles None values gracefully."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "test"},
                        "loc": {"start": {"line": 1, "column": None}},
                        "params": [],
                    },
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        # Should handle None values without errors
        json_str = parser.serialize_exports_to_json(exports)
        parsed = json.loads(json_str)

        assert len(parsed) == 1
        assert parsed[0]["location"]["column"] is None

    @pytest.mark.unit
    def test_extract_re_export_from_file(self, mock_nodejs):
        """Test extracting re-exports from another file."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "specifiers": [
                        {
                            "type": "ExportSpecifier",
                            "exported": {"name": "MyClass"},
                            "local": {"name": "MyClass"},
                            "loc": {"start": {"line": 1, "column": 0}},
                        },
                    ],
                    "source": {"value": "./other-file"},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "MyClass"
        assert exports[0]["exportType"] == "re-export"
        assert exports[0]["signature"]["source"] == "./other-file"
        assert exports[0]["signature"]["isReExport"] is True

    @pytest.mark.unit
    def test_extract_re_export_with_renaming(self, mock_nodejs):
        """Test extracting re-exports with renaming."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "specifiers": [
                        {
                            "type": "ExportSpecifier",
                            "exported": {"name": "NewName"},
                            "local": {"name": "OldName"},
                            "loc": {"start": {"line": 1, "column": 0}},
                        },
                    ],
                    "source": {"value": "./source-file"},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "NewName"
        assert exports[0]["signature"]["originalName"] == "OldName"
        assert exports[0]["signature"]["source"] == "./source-file"
        assert exports[0]["exportType"] == "re-export"

    @pytest.mark.unit
    def test_extract_nested_exports_in_namespace(self, mock_nodejs):
        """Test extracting exports nested inside a namespace."""
        ast = {
            "body": [
                {
                    "type": "TSModuleDeclaration",
                    "id": {"name": "MyNamespace"},
                    "body": {
                        "type": "TSModuleBlock",
                        "body": [
                            {
                                "type": "ExportNamedDeclaration",
                                "declaration": {
                                    "type": "FunctionDeclaration",
                                    "id": {"name": "nestedFunction"},
                                    "loc": {"start": {"line": 2, "column": 2}},
                                    "params": [],
                                },
                            },
                        ],
                    },
                    "loc": {"start": {"line": 1, "column": 0}},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "nestedFunction"
        assert exports[0]["type"] == "function"
        assert exports[0]["signature"]["nestedIn"] == "MyNamespace"
        assert exports[0]["signature"]["isNested"] is True

    @pytest.mark.unit
    def test_extract_nested_exports_multiple_levels(self, mock_nodejs):
        """Test extracting exports from nested namespaces."""
        ast = {
            "body": [
                {
                    "type": "TSModuleDeclaration",
                    "id": {"name": "Outer"},
                    "body": {
                        "type": "TSModuleBlock",
                        "body": [
                            {
                                "type": "TSModuleDeclaration",
                                "id": {"name": "Inner"},
                                "body": {
                                    "type": "TSModuleBlock",
                                    "body": [
                                        {
                                            "type": "ExportNamedDeclaration",
                                            "declaration": {
                                                "type": "ClassDeclaration",
                                                "id": {"name": "DeepClass"},
                                                "loc": {
                                                    "start": {"line": 3, "column": 4},
                                                },
                                                "decorators": [],
                                            },
                                        },
                                    ],
                                },
                                "loc": {"start": {"line": 2, "column": 2}},
                            },
                        ],
                    },
                    "loc": {"start": {"line": 1, "column": 0}},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 1
        assert exports[0]["symbol"] == "DeepClass"
        assert exports[0]["type"] == "class"
        assert exports[0]["signature"]["nestedIn"] == "Inner"
        assert exports[0]["signature"]["isNested"] is True

    @pytest.mark.unit
    def test_extract_mixed_exports_and_re_exports(self, mock_nodejs):
        """Test extracting mixed direct exports and re-exports."""
        ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "localFunction"},
                        "loc": {"start": {"line": 1, "column": 0}},
                        "params": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "specifiers": [
                        {
                            "type": "ExportSpecifier",
                            "exported": {"name": "ExternalClass"},
                            "local": {"name": "ExternalClass"},
                            "loc": {"start": {"line": 2, "column": 0}},
                        },
                    ],
                    "source": {"value": "./external-module"},
                },
            ],
        }

        parser = TypeScriptParser()
        exports = parser.extract_exported_symbols(ast)

        assert len(exports) == 2
        # First export should be local (direct declaration export)
        local_export = next(
            (e for e in exports if e["symbol"] == "localFunction"),
            None,
        )
        assert local_export is not None
        assert local_export["type"] == "function"
        # Direct declaration exports don't have exportType set

        # Second export should be re-export
        re_export = next(
            (e for e in exports if e["symbol"] == "ExternalClass"),
            None,
        )
        assert re_export is not None
        assert re_export["exportType"] == "re-export"
        assert re_export["signature"]["source"] == "./external-module"
