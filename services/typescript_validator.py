"""
TypeScript Parser Output Validator

This module provides validation functionality to compare parser output
against expected results from known TypeScript test files.

Usage:
    validator = TypeScriptValidator()
    result = validator.validate_file('path/to/test.ts', expected_exports)
    assert result.is_valid
"""

import logging
from pathlib import Path
from typing import Any

from services.typescript_parser import ParseError, TypeScriptParser

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""


class ValidationResult:
    """Result of a validation operation."""

    def __init__(
        self,
        is_valid: bool,
        file_path: str,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
        actual_exports: list[dict[str, Any]] | None = None,
        expected_exports: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed
            file_path: Path to the file that was validated
            errors: List of validation errors
            warnings: List of validation warnings
            actual_exports: Actual exports found by parser
            expected_exports: Expected exports structure
        """
        self.is_valid = is_valid
        self.file_path = file_path
        self.errors = errors or []
        self.warnings = warnings or []
        self.actual_exports = actual_exports or []
        self.expected_exports = expected_exports or []

    def __repr__(self) -> str:
        """String representation of validation result."""
        status = "VALID" if self.is_valid else "INVALID"
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        return (
            f"ValidationResult({status}, errors={error_count}, "
            f"warnings={warning_count}, file={self.file_path})"
        )


class TypeScriptValidator:
    """
    Validator for TypeScript parser output against expected results.

    Compares actual parser output with expected export structures
    to ensure correctness.
    """

    def __init__(self, parser: TypeScriptParser | None = None) -> None:
        """Initialize the validator.

        Args:
            parser: Optional TypeScriptParser instance. Creates new one if not provided.
        """
        self.parser = parser or TypeScriptParser()

    def validate_file(
        self,
        file_path: str | Path,
        expected_exports: list[dict[str, Any]],
        strict: bool = True,
    ) -> ValidationResult:
        """
        Validate parser output against expected exports for a file.

        Args:
            file_path: Path to TypeScript file to validate
            expected_exports: List of expected export dictionaries
            strict: If True, all exports must match exactly. If False, allows extra exports.

        Returns:
            ValidationResult with validation status and details

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If validation fails and strict mode is enabled
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Test file not found: {file_path}")

        logger.info(f"Validating TypeScript file: {file_path}")

        errors: list[str] = []
        warnings: list[str] = []

        try:
            # Parse the file
            ast = self.parser.parse_file(str(file_path))
            actual_exports = self.parser.extract_exported_symbols(ast)

            # Validate exports
            validation_result = self._validate_exports(
                actual_exports,
                expected_exports,
                strict=strict,
            )

            errors.extend(validation_result.errors)
            warnings.extend(validation_result.warnings)

            is_valid = len(errors) == 0

            result = ValidationResult(
                is_valid=is_valid,
                file_path=str(file_path),
                errors=errors,
                warnings=warnings,
                actual_exports=actual_exports,
                expected_exports=expected_exports,
            )

            if is_valid:
                logger.info(f"Validation passed for {file_path}")
            else:
                logger.warning(
                    f"Validation failed for {file_path}: {len(errors)} errors",
                )
                if strict:
                    raise ValidationError(
                        f"Validation failed: {'; '.join(errors[:3])}",
                    )

            return result

        except ParseError as e:
            error_msg = f"Failed to parse file: {e}"
            logger.exception("Failed to parse file")
            return ValidationResult(
                is_valid=False,
                file_path=str(file_path),
                errors=[error_msg],
                warnings=warnings,
            )

    def _validate_exports(
        self,
        actual: list[dict[str, Any]],
        expected: list[dict[str, Any]],
        strict: bool = True,
    ) -> ValidationResult:
        """
        Validate actual exports against expected exports.

        Args:
            actual: Actual exports from parser
            expected: Expected exports structure
            strict: Whether to enforce strict matching

        Returns:
            ValidationResult with comparison results
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Normalize exports for comparison (by symbol name)
        actual_by_symbol = {exp["symbol"]: exp for exp in actual if "symbol" in exp}
        expected_by_symbol = {exp["symbol"]: exp for exp in expected if "symbol" in exp}

        # Check for missing exports
        missing_exports = set(expected_by_symbol.keys()) - set(
            actual_by_symbol.keys(),
        )
        if missing_exports:
            errors.append(
                f"Missing expected exports: {', '.join(sorted(missing_exports))}",
            )

        # Check for unexpected exports (only in strict mode)
        if strict:
            unexpected_exports = set(actual_by_symbol.keys()) - set(
                expected_by_symbol.keys(),
            )
            if unexpected_exports:
                errors.append(
                    f"Unexpected exports found: {', '.join(sorted(unexpected_exports))}",
                )
        else:
            unexpected_exports = set(actual_by_symbol.keys()) - set(
                expected_by_symbol.keys(),
            )
            if unexpected_exports:
                warnings.append(
                    f"Extra exports found (allowed in non-strict mode): "
                    f"{', '.join(sorted(unexpected_exports))}",
                )

        # Validate each export's properties
        for symbol_name, expected_export in expected_by_symbol.items():
            if symbol_name not in actual_by_symbol:
                continue  # Already reported as missing

            actual_export = actual_by_symbol[symbol_name]
            export_errors = self._validate_export_properties(
                actual_export,
                expected_export,
                symbol_name,
            )
            errors.extend(export_errors)

        is_valid = len(errors) == 0

        # Create a temporary result for internal validation
        return ValidationResult(
            is_valid=is_valid,
            file_path="internal",
            errors=errors,
            warnings=warnings,
        )

    def _validate_export_properties(
        self,
        actual: dict[str, Any],
        expected: dict[str, Any],
        symbol_name: str,
    ) -> list[str]:
        """
        Validate properties of a single export.

        Args:
            actual: Actual export dictionary
            expected: Expected export dictionary
            symbol_name: Name of the symbol being validated

        Returns:
            List of error messages (empty if validation passes)
        """
        errors: list[str] = []

        # Required fields to check
        required_fields = ["symbol", "type", "isDefault"]

        for field in required_fields:
            if field in expected:
                actual_value = actual.get(field)
                expected_value = expected.get(field)

                if actual_value != expected_value:
                    errors.append(
                        f"Export '{symbol_name}': {field} mismatch - "
                        f"expected '{expected_value}', got '{actual_value}'",
                    )

        # Validate signature if present in expected
        if "signature" in expected:
            actual_sig = actual.get("signature", {})
            expected_sig = expected.get("signature", {})

            # Check source for re-exports
            if "source" in expected_sig:
                if "source" not in actual_sig:
                    errors.append(
                        f"Export '{symbol_name}': missing 'source' in signature",
                    )
                elif actual_sig.get("source") != expected_sig.get("source"):
                    errors.append(
                        f"Export '{symbol_name}': source mismatch - "
                        f"expected '{expected_sig.get('source')}', "
                        f"got '{actual_sig.get('source')}'",
                    )

            # Check nestedIn for nested exports
            if "nestedIn" in expected_sig:
                if "nestedIn" not in actual_sig:
                    errors.append(
                        f"Export '{symbol_name}': missing 'nestedIn' in signature",
                    )
                elif actual_sig.get("nestedIn") != expected_sig.get("nestedIn"):
                    errors.append(
                        f"Export '{symbol_name}': nestedIn mismatch - "
                        f"expected '{expected_sig.get('nestedIn')}', "
                        f"got '{actual_sig.get('nestedIn')}'",
                    )

        return errors

    def validate_multiple_files(
        self,
        file_validations: list[dict[str, Any]],
        strict: bool = True,
    ) -> dict[str, ValidationResult]:
        """
        Validate multiple files at once.

        Args:
            file_validations: List of dicts with 'file' and 'expected_exports' keys
            strict: Whether to enforce strict matching

        Returns:
            Dictionary mapping file paths to ValidationResult objects

        Example:
            validations = [
                {
                    'file': 'test1.ts',
                    'expected_exports': [{'symbol': 'TestClass', 'type': 'class'}]
                },
                {
                    'file': 'test2.ts',
                    'expected_exports': [{'symbol': 'TestFunc', 'type': 'function'}]
                }
            ]
            results = validator.validate_multiple_files(validations)
        """
        results: dict[str, ValidationResult] = {}

        for validation in file_validations:
            file_path = validation.get("file")
            expected_exports = validation.get("expected_exports", [])

            if not file_path:
                continue

            try:
                result = self.validate_file(file_path, expected_exports, strict=strict)
                results[str(file_path)] = result
            except Exception as e:
                logger.exception(f"Error validating {file_path}")
                results[str(file_path)] = ValidationResult(
                    is_valid=False,
                    file_path=str(file_path),
                    errors=[str(e)],
                )

        return results
