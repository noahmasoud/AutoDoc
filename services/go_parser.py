"""
Go Parser Service

This module provides Go AST parsing using Go's built-in go/ast package
via a subprocess bridge.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GoParserError(Exception):
    """Base exception for Go parser errors."""

    pass


class ParseError(GoParserError):
    """Raised when parsing fails."""

    pass


class GoNotFoundError(GoParserError):
    """Raised when Go is not found on the system."""

    pass


class GoParser:
    """
    Python wrapper for Go AST parser using Go's go/ast package via subprocess.

    This class executes a Go program that uses go/ast to parse Go files
    and outputs JSON AST for consumption by the Python backend.
    """

    def __init__(self, parser_binary: str | None = None) -> None:
        """
        Initialize the Go parser.

        Args:
            parser_binary: Path to the compiled Go parser binary.
                          Defaults to 'scripts/parse-go' (compiled from parse-go.go)
        """
        if parser_binary is None:
            # Look for compiled binary
            script_path = Path(__file__).parent.parent / "scripts" / "parse-go"
            if not script_path.exists():
                # Try with .exe extension (Windows)
                script_path = Path(__file__).parent.parent / "scripts" / "parse-go.exe"
            if not script_path.exists():
                # Try to compile if source exists
                source_path = Path(__file__).parent.parent / "scripts" / "parse-go.go"
                if source_path.exists():
                    self._compile_parser(source_path, script_path)
        else:
            script_path = Path(parser_binary)

        self.parser_binary = script_path

        if not self.parser_binary.exists():
            raise FileNotFoundError(
                f"Parser binary not found: {self.parser_binary}. "
                "Please compile parse-go.go first: go build -o scripts/parse-go scripts/parse-go.go",
            )

        # Verify Go is available (for compilation, not runtime)
        self._check_go()

    def _check_go(self) -> None:
        """Check if Go is installed and available."""
        try:
            result = subprocess.run(
                ["go", "version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise GoNotFoundError("Go check failed")

            version = result.stdout.strip()
            logger.info(f"Go version: {version}")
        except FileNotFoundError:
            raise GoNotFoundError(
                "Go is not installed. "
                "Please install Go >= 1.18 to use the Go parser.",
            ) from None
        except subprocess.TimeoutExpired:
            raise GoNotFoundError("Go version check timed out") from None

    def _compile_parser(self, source_path: Path, binary_path: Path) -> None:
        """Compile the Go parser script."""
        try:
            logger.info(f"Compiling Go parser from {source_path}")
            result = subprocess.run(
                [
                    "go",
                    "build",
                    "-o",
                    str(binary_path),
                    str(source_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise GoParserError(
                    f"Failed to compile Go parser: {result.stderr}",
                )
            logger.info(f"Successfully compiled Go parser to {binary_path}")
        except subprocess.TimeoutExpired:
            raise GoParserError("Go compilation timed out") from None
        except FileNotFoundError:
            raise GoNotFoundError(
                "Go compiler not found. Please install Go >= 1.18.",
            ) from None

    def parse_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse a Go file and return its AST.

        Args:
            file_path: Path to the Go file to parse

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing Go file: {file_path}")

        try:
            result = subprocess.run(
                [str(self.parser_binary), str(file_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )

            if result.returncode != 0:
                # Try to parse error from stderr
                error_data = self._parse_error_output(result.stderr)
                raise ParseError(
                    f"Parsing failed: {error_data.get('message', 'Unknown error')}",
                )

            # Parse JSON output
            ast_data = json.loads(result.stdout)

            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}",
                )

            logger.info("Successfully parsed Go file")
            return ast_data["ast"]

        except subprocess.TimeoutExpired:
            raise ParseError("Parser timed out after 30 seconds") from None
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON output: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Parser binary not found: {self.parser_binary}",
            ) from None

    def parse_string(self, source_code: str) -> dict[str, Any]:
        """
        Parse Go source code from a string and return its AST.

        Args:
            source_code: Go source code as a string

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
        """
        if not source_code or not source_code.strip():
            raise ValueError("Source code cannot be empty")

        logger.info("Parsing Go source code from string")

        try:
            result = subprocess.run(
                [str(self.parser_binary)],
                check=False,
                input=source_code,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_data = self._parse_error_output(result.stderr)
                raise ParseError(
                    f"Parsing failed: {error_data.get('message', 'Unknown error')}",
                )

            ast_data = json.loads(result.stdout)

            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}",
                )

            logger.info("Successfully parsed Go source code")
            return ast_data["ast"]

        except subprocess.TimeoutExpired:
            raise ParseError("Parser timed out after 30 seconds") from None
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON output: {e}") from e

    def _parse_error_output(self, stderr: str) -> dict[str, Any]:
        """
        Try to parse error output from stderr as JSON.

        Args:
            stderr: Standard error output from subprocess

        Returns:
            Dictionary with error information
        """
        try:
            return json.loads(stderr)
        except json.JSONDecodeError:
            return {"message": stderr}

    def extract_public_symbols(
        self,
        ast: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract public symbols (functions, types, interfaces, structs) from AST.

        Args:
            ast: AST dictionary from parser

        Returns:
            Dictionary with extracted symbols by type
        """
        # The Go parser already extracts symbols, so we can use them directly
        # if available, otherwise extract from AST body
        symbols: dict[str, list[dict[str, Any]]] = {
            "functions": [],
            "types": [],
            "interfaces": [],
            "structs": [],
            "consts": [],
            "vars": [],
        }

        # If the parser output includes symbols, use them
        # Otherwise, extract from AST body
        if "body" in ast:
            for node in ast.get("body", []):
                if not isinstance(node, dict):
                    continue

                node_type = node.get("type")
                node_name = node.get("name")
                node_line = node.get("line")

                if not node_name:
                    continue

                # Map node types to symbol types
                if node_type == "FunctionDeclaration":
                    symbols["functions"].append(
                        {
                            "name": node_name,
                            "line": node_line,
                            "exported": node.get("data", {}).get("exported", False),
                        },
                    )
                elif node_type == "MethodDeclaration":
                    symbols["functions"].append(
                        {
                            "name": node_name,
                            "line": node_line,
                            "exported": node.get("data", {}).get("exported", False),
                            "is_method": True,
                        },
                    )
                elif node_type == "TypeDeclaration":
                    symbols["types"].append(
                        {
                            "name": node_name,
                            "line": node_line,
                            "exported": node.get("data", {}).get("exported", False),
                        },
                    )
                elif node_type == "ConstDeclaration":
                    symbols["consts"].append(
                        {
                            "name": node_name,
                            "line": node_line,
                            "exported": node.get("data", {}).get("exported", False),
                        },
                    )
                elif node_type == "VarDeclaration":
                    symbols["vars"].append(
                        {
                            "name": node_name,
                            "line": node_line,
                            "exported": node.get("data", {}).get("exported", False),
                        },
                    )

        return symbols

    def _is_go_file(self, file_path: str | Path) -> bool:
        """
        Check if a file is a Go file.

        Args:
            file_path: Path to check

        Returns:
            True if file is Go (.go)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        return suffix == ".go"

