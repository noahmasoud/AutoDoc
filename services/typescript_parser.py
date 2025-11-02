"""
TypeScript AST Parser Service

This module provides a Python interface to the Node.js TypeScript parser.
It executes the Node.js parser via subprocess and parses the JSON AST output.

Usage:
    parser = TypeScriptParser()
    ast = parser.parse_file('path/to/file.ts')
    # Or parse from string
    ast = parser.parse_string(typescript_code)
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TypeScriptParserError(Exception):
    """Base exception for TypeScript parser errors."""


class ParseError(TypeScriptParserError):
    """Raised when TypeScript parsing fails."""


class NodeJSNotFoundError(TypeScriptParserError):
    """Raised when Node.js is not found on the system."""


class TypeScriptParser:
    """
    Python wrapper for TypeScript AST parser using Node.js bridge.

    This class executes the Node.js parser script and converts the JSON
    output into Python data structures.
    """

    def __init__(self, parser_script: str | None = None) -> None:
        """
        Initialize the TypeScript parser.

        Args:
            parser_script: Path to the Node.js parser script.
                          Defaults to 'scripts/parse-typescript.js'
        """
        if parser_script is None:
            # Assume we're running from project root
            parser_script = (
                Path(__file__).parent.parent / "scripts" / "parse-typescript.js"
            )

        self.parser_script = Path(parser_script)

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
                "Please install Node.js >= 18.0.0 to use the TypeScript parser.",
            ) from None
        except subprocess.TimeoutExpired:
            raise NodeJSNotFoundError("Node.js version check timed out") from None

    def parse_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse a TypeScript file and return its AST.

        Args:
            file_path: Path to the TypeScript file to parse

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
            FileNotFoundError: If the file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing TypeScript file: {file_path}")

        try:
            result = subprocess.run(
                ["node", str(self.parser_script), str(file_path)],
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

            logger.info("Successfully parsed TypeScript file")
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
        Parse TypeScript source code from a string and return its AST.

        Args:
            source_code: TypeScript source code as a string

        Returns:
            Dictionary containing the AST and metadata

        Raises:
            ParseError: If parsing fails
        """
        if not source_code or not source_code.strip():
            raise ValueError("Source code cannot be empty")

        logger.info("Parsing TypeScript source code from string")

        try:
            result = subprocess.run(
                ["node", str(self.parser_script)],
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

            logger.info("Successfully parsed TypeScript source code")
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
        symbols = {
            "classes": [],
            "functions": [],
            "interfaces": [],
            "types": [],
            "enums": [],
        }

        if "body" not in ast:
            return symbols

        for node in ast["body"]:
            if node.get("type") == "ClassDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["classes"].append(
                        {
                            "name": node["id"]["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                            "decorators": len(node.get("decorators", [])),
                        },
                    )

            elif node.get("type") == "FunctionDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["functions"].append(
                        {
                            "name": node["id"]["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                            "async": node.get("async", False),
                        },
                    )

            elif node.get("type") == "TSInterfaceDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["interfaces"].append(
                        {
                            "name": node["id"]["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

            elif node.get("type") == "TSTypeAliasDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["types"].append(
                        {
                            "name": node["id"]["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

            elif node.get("type") == "TSEnumDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["enums"].append(
                        {
                            "name": node["id"]["name"],
                            "line": node.get("loc", {}).get("start", {}).get("line"),
                        },
                    )

        return symbols

    def extract_exported_symbols(
        self,
        ast: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract all exported entities from AST.

        Traverses AST to collect exported entities including:
        - ExportNamedDeclaration (export class X, export function Y, export const Z)
        - ExportDefaultDeclaration (export default ...)
        - Re-exports (export * from './file')

        Args:
            ast: AST dictionary from parser

        Returns:
            List of exported symbols with format:
            [{
                'symbol': str,      # Symbol name
                'type': str,        # Declaration type (class, function, interface, etc.)
                'signature': dict,  # Function/class signature details
                'location': dict,   # Line/column information
                'isDefault': bool   # Whether it's a default export
            }]
        """
        exports = []

        if "body" not in ast:
            return exports

        for node in ast["body"]:
            export_info = self._extract_export_info(node)
            if export_info:
                exports.extend(export_info)

        return exports

    def _extract_export_info(
        self,
        node: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract export information from a single AST node.

        Args:
            node: AST node to examine

        Returns:
            List of export information dictionaries (empty if not an export)
        """
        exports = []
        node_type = node.get("type")

        # Handle ExportNamedDeclaration: export class, export function, export const, etc.
        if node_type == "ExportNamedDeclaration":
            declaration = node.get("declaration")

            if declaration:
                # Single declaration export: export class X { }
                info = self._extract_declaration_export(declaration, is_default=False)
                if info:
                    exports.append(info)
            elif node.get("specifiers"):
                # Multiple named exports: export { a, b, c }
                for specifier in node.get("specifiers", []):
                    info = self._extract_named_specifier(specifier)
                    if info:
                        exports.append(info)

        # Handle ExportDefaultDeclaration: export default ...
        elif node_type == "ExportDefaultDeclaration":
            declaration = node.get("declaration")

            if declaration:
                info = self._extract_declaration_export(declaration, is_default=True)
                if info:
                    exports.append(info)

        # Handle ExportAllDeclaration: export * from './file'
        elif node_type == "ExportAllDeclaration":
            source = node.get("source", {}).get("value", "")
            if source:
                exports.append(
                    {
                        "symbol": "*",
                        "type": "namespace",
                        "signature": {"source": source},
                        "location": self._extract_location(node),
                        "isDefault": False,
                        "exportType": "all",
                    },
                )

        return exports

    def _extract_declaration_export(
        self,
        declaration: dict[str, Any],
        is_default: bool,
    ) -> dict[str, Any] | None:
        """
        Extract export information from a declaration node.

        Args:
            declaration: Declaration node (ClassDeclaration, FunctionDeclaration, etc.)
            is_default: Whether this is a default export

        Returns:
            Export information dictionary or None if not extractable
        """
        decl_type = declaration.get("type")
        node_id = declaration.get("id", {})
        name = node_id.get("name") if isinstance(node_id, dict) else None

        if not name:
            return None

        # Map declaration types to our symbol types
        type_mapping = {
            "ClassDeclaration": "class",
            "FunctionDeclaration": "function",
            "TSInterfaceDeclaration": "interface",
            "TSTypeAliasDeclaration": "type",
            "TSEnumDeclaration": "enum",
            "VariableDeclaration": "variable",
        }

        symbol_type = type_mapping.get(decl_type, "unknown")

        # Extract signature details based on type
        signature = self._extract_signature(declaration, symbol_type)

        return {
            "symbol": name,
            "type": symbol_type,
            "signature": signature,
            "location": self._extract_location(declaration),
            "isDefault": is_default,
        }

    def _extract_named_specifier(
        self,
        specifier: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Extract export information from a named export specifier.

        Handles: export { a, b, c } style exports

        Args:
            specifier: ExportSpecifier node

        Returns:
            Export information dictionary or None
        """
        exported = specifier.get("exported", {})
        local = specifier.get("local", {})

        symbol_name = exported.get("name") if isinstance(exported, dict) else None
        original_name = local.get("name") if isinstance(local, dict) else None

        if not symbol_name:
            return None

        return {
            "symbol": symbol_name,
            "type": "named",
            "signature": {"originalName": original_name}
            if original_name != symbol_name
            else {},
            "location": self._extract_location(specifier),
            "isDefault": False,
            "exportType": "specifier",
        }

    def _extract_signature(
        self,
        declaration: dict[str, Any],
        symbol_type: str,
    ) -> dict[str, Any]:
        """
        Extract signature details based on symbol type.

        Args:
            declaration: Declaration node
            symbol_type: Type of symbol (class, function, etc.)

        Returns:
            Signature information dictionary
        """
        signature = {}

        if symbol_type == "function":
            signature = {
                "params": self._extract_function_params(declaration),
                "returnType": self._extract_return_type(declaration),
                "async": declaration.get("async", False),
                "generator": declaration.get("generator", False),
            }
        elif symbol_type == "class":
            signature = {
                "superClass": self._extract_superclass(declaration),
                "decorators": len(declaration.get("decorators", [])),
                "superTypeParams": declaration.get("superTypeParameters", []),
            }

        return signature

    def _extract_function_params(
        self,
        func_declaration: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract function parameters.

        Args:
            func_declaration: FunctionDeclaration node

        Returns:
            List of parameter information
        """
        params = []
        for param in func_declaration.get("params", []):
            param_info = self._extract_parameter_info(param)
            if param_info:
                params.append(param_info)
        return params

    def _extract_parameter_info(
        self,
        param: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Extract information from a single parameter.

        Args:
            param: Parameter node

        Returns:
            Parameter information dictionary or None
        """
        param_type = param.get("type")

        # Handle different parameter types
        if param_type == "Identifier":
            name = param.get("name")
            return {"name": name, "type": None}
        if param_type in ("AssignmentPattern", "ObjectPattern", "ArrayPattern"):
            # Complex parameter patterns - extract what we can
            left = param.get("left", {})
            name = left.get("name") if isinstance(left, dict) else str(param_type)
            return {"name": name, "type": param_type}

        return None

    def _extract_return_type(
        self,
        func_declaration: dict[str, Any],
    ) -> str | None:
        """
        Extract return type annotation.

        Args:
            func_declaration: FunctionDeclaration node

        Returns:
            Return type string or None
        """
        return_type = func_declaration.get("returnType", {})
        if return_type and isinstance(return_type, dict):
            type_annotation = return_type.get("typeAnnotation", {})
            if isinstance(type_annotation, dict):
                # Try to extract a readable type
                return (
                    type_annotation.get("typeName", {}).get("name")
                    if isinstance(type_annotation.get("typeName"), dict)
                    else type_annotation.get("type")
                )
        return None

    def _extract_superclass(
        self,
        class_declaration: dict[str, Any],
    ) -> str | None:
        """
        Extract superclass name.

        Args:
            class_declaration: ClassDeclaration node

        Returns:
            Superclass name or None
        """
        superclass = class_declaration.get("superClass", {})
        if isinstance(superclass, dict):
            return superclass.get("name")
        return None

    def _extract_location(
        self,
        node: dict[str, Any],
    ) -> dict[str, int | None]:
        """
        Extract location information from a node.

        Args:
            node: Any AST node with location information

        Returns:
            Location dictionary with line and column
        """
        loc = node.get("loc", {})
        if not isinstance(loc, dict):
            return {"line": None, "column": None}

        start = loc.get("start", {})
        if isinstance(start, dict):
            return {
                "line": start.get("line"),
                "column": start.get("column"),
            }

        return {"line": None, "column": None}
