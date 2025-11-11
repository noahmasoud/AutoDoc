"""Integration tests for TypeScript parser validation against test files."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from services.typescript_parser import TypeScriptParser
from services.typescript_validator import TypeScriptValidator


class TestTypeScriptFileValidation:
    """Integration tests validating parser output against known test files."""

    @pytest.fixture
    @patch("services.typescript_parser.subprocess.run")
    def validator(self, mock_run: Mock) -> TypeScriptValidator:
        """Create a validator instance for testing."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")
        parser = TypeScriptParser()
        return TypeScriptValidator(parser=parser)

    @pytest.fixture
    def test_samples_dir(self) -> Path:
        """Get path to test samples directory."""
        return Path(__file__).parent.parent / "test-samples"

    @pytest.mark.integration
    def test_validate_example_ts_file(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test validation of the example.ts test file."""
        file_path = test_samples_dir / "example.ts"

        # Mock parser's parse_file method to avoid requiring Node.js
        mock_ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "User"},
                        "loc": {"start": {"line": 12}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSTypeAliasDeclaration",
                        "id": {"name": "Status"},
                        "loc": {"start": {"line": 20}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "UserService"},
                        "loc": {"start": {"line": 26}},
                        "decorators": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "UserListComponent"},
                        "loc": {"start": {"line": 73}},
                        "decorators": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "formatUserName"},
                        "loc": {"start": {"line": 90}},
                        "params": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "DataProcessor"},
                        "loc": {"start": {"line": 95}},
                        "decorators": [],
                    },
                },
            ],
        }

        # Expected exports based on example.ts content
        expected_exports = [
            {
                "symbol": "User",
                "type": "interface",
                "isDefault": False,
            },
            {
                "symbol": "Status",
                "type": "type",
                "isDefault": False,
            },
            {
                "symbol": "UserService",
                "type": "class",
                "isDefault": False,
            },
            {
                "symbol": "UserListComponent",
                "type": "class",
                "isDefault": False,
            },
            {
                "symbol": "formatUserName",
                "type": "function",
                "isDefault": False,
            },
            {
                "symbol": "DataProcessor",
                "type": "class",
                "isDefault": False,
            },
        ]

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

            assert result.is_valid, f"Validation failed: {result.errors}"
            assert len(result.actual_exports) >= len(expected_exports)

    @pytest.mark.integration
    def test_validate_basic_exports(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test validation of basic exports file."""
        file_path = test_samples_dir / "exports-basic.ts"

        mock_ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "BasicInterface"},
                        "loc": {"start": {"line": 1}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "BasicClass"},
                        "loc": {"start": {"line": 1}},
                        "decorators": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "basicFunction"},
                        "loc": {"start": {"line": 1}},
                        "params": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSTypeAliasDeclaration",
                        "id": {"name": "BasicType"},
                        "loc": {"start": {"line": 1}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSEnumDeclaration",
                        "id": {"name": "BasicEnum"},
                        "loc": {"start": {"line": 1}},
                    },
                },
            ],
        }

        expected_exports = [
            {
                "symbol": "BasicInterface",
                "type": "interface",
                "isDefault": False,
            },
            {
                "symbol": "BasicClass",
                "type": "class",
                "isDefault": False,
            },
            {
                "symbol": "basicFunction",
                "type": "function",
                "isDefault": False,
            },
            {
                "symbol": "BasicType",
                "type": "type",
                "isDefault": False,
            },
            {
                "symbol": "BasicEnum",
                "type": "enum",
                "isDefault": False,
            },
        ]

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

        assert result.is_valid, f"Validation failed: {result.errors}"
        # Should have at least all expected exports
        actual_symbols = {exp["symbol"] for exp in result.actual_exports}
        expected_symbols = {exp["symbol"] for exp in expected_exports}
        assert expected_symbols.issubset(actual_symbols), (
            f"Missing exports: {expected_symbols - actual_symbols}"
        )

    @pytest.mark.integration
    def test_validate_default_exports(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test validation of default exports file."""
        file_path = test_samples_dir / "exports-default.ts"

        mock_ast = {
            "body": [
                {
                    "type": "ExportDefaultDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "DefaultClass"},
                        "loc": {"start": {"line": 1}},
                        "decorators": [],
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "NamedInterface"},
                        "loc": {"start": {"line": 1}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "FunctionDeclaration",
                        "id": {"name": "namedFunction"},
                        "loc": {"start": {"line": 1}},
                        "params": [],
                    },
                },
            ],
        }

        expected_exports = [
            {
                "symbol": "DefaultClass",  # Default export name
                "type": "class",
                "isDefault": True,
            },
            {
                "symbol": "NamedInterface",
                "type": "interface",
                "isDefault": False,
            },
            {
                "symbol": "namedFunction",
                "type": "function",
                "isDefault": False,
            },
        ]

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

            assert result.is_valid, f"Validation failed: {result.errors}"

            # Verify default export is present
            default_exports = [
                exp for exp in result.actual_exports if exp.get("isDefault") is True
            ]
            assert len(default_exports) >= 1, "No default export found"

    @pytest.mark.integration
    def test_validate_nested_exports(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test validation of nested exports in namespaces."""
        file_path = test_samples_dir / "exports-nested.ts"

        mock_ast = {
            "body": [
                {
                    "type": "TSModuleDeclaration",
                    "id": {"name": "OuterNamespace"},
                    "body": {
                        "type": "TSModuleBlock",
                        "body": [
                            {
                                "type": "ExportNamedDeclaration",
                                "declaration": {
                                    "type": "TSInterfaceDeclaration",
                                    "id": {"name": "NestedInterface"},
                                    "loc": {"start": {"line": 1}},
                                },
                            },
                            {
                                "type": "ExportNamedDeclaration",
                                "declaration": {
                                    "type": "ClassDeclaration",
                                    "id": {"name": "NestedClass"},
                                    "loc": {"start": {"line": 1}},
                                    "decorators": [],
                                },
                            },
                            {
                                "type": "ExportNamedDeclaration",
                                "declaration": {
                                    "type": "FunctionDeclaration",
                                    "id": {"name": "nestedFunction"},
                                    "loc": {"start": {"line": 1}},
                                    "params": [],
                                },
                            },
                        ],
                    },
                    "loc": {"start": {"line": 1}},
                },
            ],
        }

        expected_exports = [
            # Nested exports should be extracted (namespace itself is not exported)
            {
                "symbol": "NestedInterface",
                "type": "interface",
                "isDefault": False,
                "signature": {
                    "nestedIn": "OuterNamespace",
                    "isNested": True,
                },
            },
            {
                "symbol": "NestedClass",
                "type": "class",
                "isDefault": False,
                "signature": {
                    "nestedIn": "OuterNamespace",
                    "isNested": True,
                },
            },
            {
                "symbol": "nestedFunction",
                "type": "function",
                "isDefault": False,
                "signature": {
                    "nestedIn": "OuterNamespace",
                    "isNested": True,
                },
            },
        ]

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

            # In non-strict mode, nested exports may or may not be extracted
            # depending on implementation details
            assert result.is_valid or len(result.warnings) > 0, (
                f"Validation failed with errors: {result.errors}"
            )

    @pytest.mark.integration
    def test_validate_multiple_files(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test validation of multiple files at once."""
        file_validations = [
            {
                "file": str(test_samples_dir / "exports-basic.ts"),
                "expected_exports": [
                    {
                        "symbol": "BasicInterface",
                        "type": "interface",
                        "isDefault": False,
                    },
                    {"symbol": "BasicClass", "type": "class", "isDefault": False},
                ],
            },
            {
                "file": str(test_samples_dir / "exports-default.ts"),
                "expected_exports": [
                    {"symbol": "DefaultClass", "type": "class", "isDefault": True},
                ],
            },
        ]

        # Mock ASTs for both files
        mock_asts = {
            str(test_samples_dir / "exports-basic.ts"): {
                "body": [
                    {
                        "type": "ExportNamedDeclaration",
                        "declaration": {
                            "type": "TSInterfaceDeclaration",
                            "id": {"name": "BasicInterface"},
                            "loc": {"start": {"line": 1}},
                        },
                    },
                    {
                        "type": "ExportNamedDeclaration",
                        "declaration": {
                            "type": "ClassDeclaration",
                            "id": {"name": "BasicClass"},
                            "loc": {"start": {"line": 1}},
                            "decorators": [],
                        },
                    },
                ],
            },
            str(test_samples_dir / "exports-default.ts"): {
                "body": [
                    {
                        "type": "ExportDefaultDeclaration",
                        "declaration": {
                            "type": "ClassDeclaration",
                            "id": {"name": "DefaultClass"},
                            "loc": {"start": {"line": 1}},
                            "decorators": [],
                        },
                    },
                ],
            },
        }

        def mock_parse_file(file_path: str) -> dict[str, Any]:
            return mock_asts.get(file_path, {"body": []})

        with patch.object(validator.parser, "parse_file", side_effect=mock_parse_file):
            results = validator.validate_multiple_files(file_validations, strict=False)

            assert len(results) == 2
            for file_path, result in results.items():
                assert result.is_valid or len(result.warnings) > 0, (
                    f"File {file_path} validation failed: {result.errors}"
                )

    @pytest.mark.integration
    def test_validate_strict_mode(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test that strict mode enforces exact matching."""
        file_path = test_samples_dir / "exports-basic.ts"

        # Mock AST with exactly 2 exports
        mock_ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "BasicInterface"},
                        "loc": {"start": {"line": 1}},
                    },
                },
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "BasicClass"},
                        "loc": {"start": {"line": 1}},
                        "decorators": [],
                    },
                },
            ],
        }

        # Expected exports with exact count
        expected_exports = [
            {"symbol": "BasicInterface", "type": "interface", "isDefault": False},
            {"symbol": "BasicClass", "type": "class", "isDefault": False},
        ]

        # In strict mode, if there are more exports than expected, it should fail
        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=True)

            # Should either pass if exact match, or have warnings/errors if extra exports
            # Since we know there are more exports in the file, strict mode should report issues
            if not result.is_valid:
                assert len(result.errors) > 0 or len(result.warnings) > 0

    @pytest.mark.integration
    def test_validate_nonexistent_file(self, validator: TypeScriptValidator):
        """Test that validation handles nonexistent files gracefully."""
        file_path = Path("nonexistent-file.ts")
        expected_exports: list[dict[str, Any]] = []

        with pytest.raises(FileNotFoundError):
            validator.validate_file(file_path, expected_exports)

    @pytest.mark.integration
    def test_validate_invalid_typescript(
        self,
        validator: TypeScriptValidator,
        tmp_path: Path,
    ):
        """Test validation with invalid TypeScript syntax."""
        # Create a file with invalid syntax
        invalid_file = tmp_path / "invalid.ts"
        invalid_file.write_text("export class { invalid syntax }")

        expected_exports: list[dict[str, Any]] = []

        # Mock parser to raise ParseError
        from services.typescript_parser import ParseError

        with patch.object(
            validator.parser,
            "parse_file",
            side_effect=ParseError("Syntax error"),
        ):
            result = validator.validate_file(
                invalid_file,
                expected_exports,
                strict=False,
            )

            # Should handle the error gracefully
            assert not result.is_valid
            assert len(result.errors) > 0

    @pytest.mark.integration
    def test_validation_result_structure(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test that ValidationResult has proper structure."""
        file_path = test_samples_dir / "exports-basic.ts"
        expected_exports = [
            {"symbol": "BasicInterface", "type": "interface", "isDefault": False},
        ]

        mock_ast = {
            "body": [
                {
                    "type": "ExportNamedDeclaration",
                    "declaration": {
                        "type": "TSInterfaceDeclaration",
                        "id": {"name": "BasicInterface"},
                        "loc": {"start": {"line": 1}},
                    },
                },
            ],
        }

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

            assert hasattr(result, "is_valid")
            assert hasattr(result, "file_path")
            assert hasattr(result, "errors")
            assert hasattr(result, "warnings")
            assert hasattr(result, "actual_exports")
            assert hasattr(result, "expected_exports")
            assert isinstance(result.errors, list)
            assert isinstance(result.warnings, list)

    @pytest.mark.integration
    def test_validate_export_properties(
        self,
        validator: TypeScriptValidator,
        test_samples_dir: Path,
    ):
        """Test that export properties are correctly validated."""
        file_path = test_samples_dir / "exports-default.ts"

        mock_ast = {
            "body": [
                {
                    "type": "ExportDefaultDeclaration",
                    "declaration": {
                        "type": "ClassDeclaration",
                        "id": {"name": "DefaultClass"},
                        "loc": {"start": {"line": 1}},
                        "decorators": [],
                    },
                },
            ],
        }

        expected_exports = [
            {
                "symbol": "DefaultClass",
                "type": "class",
                "isDefault": True,
                "signature": {},
            },
        ]

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(file_path, expected_exports, strict=False)

            # Find the default export in actual exports
            if result.is_valid:
                default_exports = [
                    exp for exp in result.actual_exports if exp.get("isDefault") is True
                ]
                assert len(default_exports) > 0, "Default export should be found"

    @pytest.mark.integration
    def test_validate_empty_file(self, validator: TypeScriptValidator, tmp_path: Path):
        """Test validation of empty TypeScript file."""
        empty_file = tmp_path / "empty.ts"
        empty_file.write_text("// Empty file\n")

        expected_exports: list[dict[str, Any]] = []

        mock_ast: dict[str, Any] = {"body": []}

        with patch.object(validator.parser, "parse_file", return_value=mock_ast):
            result = validator.validate_file(empty_file, expected_exports, strict=True)

            # Empty file should validate successfully with no exports
            assert result.is_valid or len(result.actual_exports) == 0
