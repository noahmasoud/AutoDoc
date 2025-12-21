"""
JavaScript Parser Service

This module provides JavaScript AST parsing using the TypeScript parser
(since TypeScript is a superset of JavaScript and can parse JS files).
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class JavaScriptParserError(Exception):
    """Base exception for JavaScript parser errors."""

    pass


class ParseError(JavaScriptParserError):
    """Raised when parsing fails."""

    pass


class NodeJSNotFoundError(JavaScriptParserError):
    """Raised when Node.js is not found on the system."""

    pass


class JavaScriptParser:
    """
    Python wrapper for JavaScript AST parser using Node.js bridge.

    This class reuses the TypeScript parser script since TypeScript
    can parse JavaScript files (TypeScript is a superset of JavaScript).
    """

    def __init__(self, parser_script: str | None = None) -> None:
        """
        Initialize the JavaScript parser.

        Args:
            parser_script: Path to the Node.js parser script.
                          Defaults to 'scripts/parse-typescript.js'
        """
        if parser_script is None:
            # Reuse TypeScript parser script
            script_path = (
                Path(__file__).parent.parent / "scripts" / "parse-typescript.js"
            )
        else:
            script_path = Path(parser_script)

        self.parser_script = script_path

        if not self.parser_script.exists():
            raise FileNotFoundError(
                f"Parser script not found: {self.parser_script}",
            )

        # Verify Node.js is available
        self._check_nodejs()

    def _check_nodejs(self) -> None:
        """Check if Node.js is installed and available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise NodeJSNotFoundError("Node.js check failed")

            version = result.stdout.strip()
            logger.info(f"Node.js version: {version}")
        except FileNotFoundError:
            raise NodeJSNotFoundError(
                "Node.js is not installed. "
                "Please install Node.js >= 18.0.0 to use the JavaScript parser.",
            ) from None
        except subprocess.TimeoutExpired:
            raise NodeJSNotFoundError("Node.js version check timed out") from None

    def parse_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse a JavaScript file and return its AST.

        Args:
            file_path: Path to the JavaScript file to parse

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing JavaScript file: {file_path}")

        try:
            # Use temp file to avoid pipe buffer limits for large JSON outputs
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_out:
                tmp_out_path = tmp_out.name
            
            try:
                result = subprocess.run(
                    ["node", str(self.parser_script), str(file_path)],
                    check=False,
                    stdout=open(tmp_out_path, 'w'),
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                
                # Read the full output from temp file
                with open(tmp_out_path, 'r') as f:
                    stdout = f.read()
                
                if result.returncode != 0:
                    # Try to parse error from stderr
                    error_data = self._parse_error_output(result.stderr)
                    raise ParseError(
                        f"Parsing failed: {error_data.get('message', 'Unknown error')}",
                    )

                # Parse JSON output
                ast_data = json.loads(stdout)
            finally:
                # Clean up temp file
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)

            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}",
                )

            logger.info("Successfully parsed JavaScript file")
            return ast_data["ast"]

        except subprocess.TimeoutExpired:
            raise ParseError("Parser timed out after 30 seconds") from None
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON output: {e}") from e
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Parser script not found: {self.parser_script}",
            ) from None

    def parse_string(self, source_code: str) -> dict[str, Any]:
        """
        Parse JavaScript source code from a string and return its AST.

        Args:
            source_code: JavaScript source code as a string

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
        """
        if not source_code or not source_code.strip():
            raise ValueError("Source code cannot be empty")

        logger.info("Parsing JavaScript source code from string")

        try:
            # Use temp files to avoid pipe buffer limits for large JSON outputs
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp_in:
                tmp_in_path = tmp_in.name
                tmp_in.write(source_code)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_out:
                tmp_out_path = tmp_out.name
            
            try:
                result = subprocess.run(
                    ["node", str(self.parser_script), tmp_in_path],
                    check=False,
                    stdout=open(tmp_out_path, 'w'),
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
                
                # Read the full output from temp file
                with open(tmp_out_path, 'r') as f:
                    stdout = f.read()
                
                if result.returncode != 0:
                    error_data = self._parse_error_output(result.stderr)
                    raise ParseError(
                        f"Parsing failed: {error_data.get('message', 'Unknown error')}",
                    )

                ast_data = json.loads(stdout)
            finally:
                # Clean up temp files
                for tmp_file in [tmp_in_path, tmp_out_path]:
                    if os.path.exists(tmp_file):
                        os.unlink(tmp_file)

            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}",
                )

            logger.info("Successfully parsed JavaScript source code")
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
        Extract public symbols (classes, functions, interfaces) from AST.

        Args:
            ast: AST dictionary from parser

        Returns:
            Dictionary with extracted symbols by type
        """
        symbols: dict[str, list[dict[str, Any]]] = {
            "classes": [],
            "functions": [],
            "interfaces": [],
            "types": [],
            "enums": [],
        }

        if "body" not in ast:
            return symbols

        for node in ast["body"]:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type")
            node_id = node.get("id", {})

            # Extract class declarations
            if node_type == "ClassDeclaration":
                if node_id.get("name"):
                    symbols["classes"].append(
                        {
                            "name": node_id["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                            "decorators": len(node.get("decorators", [])),
                        },
                    )

            # Extract function declarations
            elif node_type == "FunctionDeclaration":
                if node_id.get("name"):
                    symbols["functions"].append(
                        {
                            "name": node_id["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                            "async": node.get("async", False),
                            "generator": node.get("generator", False),
                        },
                    )

            # Extract interface declarations (TypeScript, but may appear in JS with TS parser)
            elif node_type == "TSInterfaceDeclaration":
                if node_id.get("name"):
                    symbols["interfaces"].append(
                        {
                            "name": node_id["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

            # Extract type aliases (TypeScript)
            elif node_type == "TSTypeAliasDeclaration":
                if node_id.get("name"):
                    symbols["types"].append(
                        {
                            "name": node_id["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

            # Extract enum declarations (TypeScript)
            elif node_type == "TSEnumDeclaration":
                if node_id.get("name"):
                    symbols["enums"].append(
                        {
                            "name": node_id["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

            # Extract variable declarations that might be functions (arrow functions, etc.)
            elif node_type == "VariableDeclaration":
                for decl in node.get("declarations", []):
                    init = decl.get("init", {})
                    if init.get("type") in ("ArrowFunctionExpression", "FunctionExpression"):
                        var_id = decl.get("id", {})
                        if var_id.get("name"):
                            symbols["functions"].append(
                                {
                                    "name": var_id["name"],
                                    "line": node.get("loc", {}).get("start", {}).get("line"),
                                    "async": init.get("async", False),
                                    "generator": init.get("generator", False),
                                },
                            )

        return symbols

    def _is_javascript_file(self, file_path: str | Path) -> bool:
        """
        Check if a file is a JavaScript file.

        Args:
            file_path: Path to check

        Returns:
            True if file is JavaScript (.js or .jsx)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        return suffix in {".js", ".jsx"}

