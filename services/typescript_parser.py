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
        Extract all exported entities from AST and return uniform JSON structure.

        Traverses AST to collect exported entities including:
        - ExportNamedDeclaration (export class X, export function Y, export const Z)
        - ExportDefaultDeclaration (export default ...)
        - Re-exports (export { X } from './file', export * from './file')
        - Nested exports (exports inside namespaces/modules)

        Args:
            ast: AST dictionary from parser

        Returns:
            List of exported symbols with uniform JSON format:
            [{
                'symbol': str,      # Symbol name
                'type': str,        # Declaration type (class, function, interface, etc.)
                'signature': dict,  # Function/class signature details
                'location': dict,   # Line/column information
                'isDefault': bool   # Whether it's a default export
            }]

        All returned dictionaries are JSON-serializable and follow the same structure.
        """
        exports = []

        if "body" not in ast:
            return exports

        for node in ast["body"]:
            # Extract direct exports
            export_info = self._extract_export_info(node)
            if export_info:
                exports.extend(export_info)

            # Check for nested exports inside modules/namespaces
            nested_exports = self._extract_nested_exports(node)
            if nested_exports:
                exports.extend(nested_exports)

        # Validate and normalize all exports for JSON serialization
        return self._normalize_exports_for_json(exports)

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
            source = node.get("source")

            if declaration:
                # Single declaration export: export class X { }
                info = self._extract_declaration_export(declaration, is_default=False)
                if info:
                    exports.append(info)
            elif node.get("specifiers"):
                # Multiple named exports: export { a, b, c }
                # OR re-exports: export { a, b } from './file'
                source_path = (
                    source.get("value", "") if isinstance(source, dict) else None
                )
                for specifier in node.get("specifiers", []):
                    info = self._extract_named_specifier(specifier, source_path)
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
        source_path: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Extract export information from a named export specifier.

        Handles:
        - Direct exports: export { a, b, c }
        - Re-exports: export { a, b } from './file'
        - Re-exports with renaming: export { oldName as newName } from './file'

        Args:
            specifier: ExportSpecifier node
            source_path: Optional source file path for re-exports

        Returns:
            Export information dictionary or None
        """
        exported = specifier.get("exported", {})
        local = specifier.get("local", {})

        symbol_name = exported.get("name") if isinstance(exported, dict) else None
        original_name = local.get("name") if isinstance(local, dict) else None

        if not symbol_name:
            return None

        # Build signature with re-export information
        signature = {}
        if original_name and original_name != symbol_name:
            signature["originalName"] = original_name
        if source_path:
            signature["source"] = source_path
            signature["isReExport"] = True

        return {
            "symbol": symbol_name,
            "type": "named",
            "signature": signature,
            "location": self._extract_location(specifier),
            "isDefault": False,
            "exportType": "specifier" if not source_path else "re-export",
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

    def _extract_nested_exports(
        self,
        node: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """
        Extract nested exports from modules/namespaces.

        Handles exports inside:
        - TSModuleDeclaration (namespace/module declarations)
        - ClassDeclaration (static exports, though less common)

        Args:
            node: AST node to examine for nested exports

        Returns:
            List of nested export information dictionaries
        """
        nested_exports = []
        node_type = node.get("type")

        # Handle TSModuleDeclaration (namespace X { ... } or module X { ... })
        if node_type == "TSModuleDeclaration":
            body = node.get("body", {})
            # TSModuleBlock contains the body
            if isinstance(body, dict) and body.get("type") == "TSModuleBlock":
                module_body = body.get("body", [])
                module_id = node.get("id", {})
                module_name = (
                    module_id.get("name") if isinstance(module_id, dict) else None
                )

                # Recursively extract exports from module body
                for nested_node in module_body:
                    export_info = self._extract_export_info(nested_node)
                    if export_info:
                        # Prefix nested exports with module name for clarity
                        for exp in export_info:
                            exp["signature"] = exp.get("signature", {})
                            exp["signature"]["nestedIn"] = module_name
                            exp["signature"]["isNested"] = True
                        nested_exports.extend(export_info)

                    # Handle nested modules (nested namespaces)
                    deeper_nested = self._extract_nested_exports(nested_node)
                    if deeper_nested:
                        nested_exports.extend(deeper_nested)

        # Handle ClassDeclaration for static exports (if any)
        elif node_type == "ClassDeclaration":
            # Check for static class members that are exports
            # This is less common but some frameworks use this pattern
            body = node.get("body", {})
            if isinstance(body, dict) and body.get("type") == "ClassBody":
                class_body = body.get("body", [])
                class_id = node.get("id", {})
                class_name = (
                    class_id.get("name") if isinstance(class_id, dict) else None
                )

                for member in class_body:
                    # Look for static members that might be considered exports
                    if member.get("static") and member.get("type") in (
                        "MethodDefinition",
                        "PropertyDefinition",
                    ):
                        # These are class members, not module exports
                        # but we can track them if needed for documentation
                        pass

        return nested_exports

    def _normalize_exports_for_json(
        self,
        exports: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Normalize and validate exports for JSON serialization.

        Ensures all exports follow the uniform structure {symbol, type, signature, location}.
        Handles None values and ensures all fields are JSON-serializable.

        Args:
            exports: List of export dictionaries

        Returns:
            Normalized list of exports ready for JSON serialization
        """
        normalized = []

        for export in exports:
            # Ensure all required fields exist with proper defaults
            normalized_export = {
                "symbol": export.get("symbol", ""),
                "type": export.get("type", "unknown"),
                "signature": export.get("signature", {}),
                "location": export.get("location", {"line": None, "column": None}),
                "isDefault": export.get("isDefault", False),
            }

            # Add any additional fields (like exportType for all exports, etc.)
            for key, value in export.items():
                if key not in normalized_export:
                    normalized_export[key] = value

            # Ensure nested dicts are properly structured
            if not isinstance(normalized_export["signature"], dict):
                normalized_export["signature"] = {}

            if not isinstance(normalized_export["location"], dict):
                normalized_export["location"] = {"line": None, "column": None}

            normalized.append(normalized_export)

        return normalized

    def serialize_exports_to_json(self, exports: list[dict[str, Any]]) -> str:
        """
        Serialize exported symbols to JSON string.

        Args:
            exports: List of export dictionaries

        Returns:
            JSON string representation of exports

        Raises:
            TypeError: If exports contain non-serializable data
        """
        return json.dumps(exports, indent=2, default=str)
