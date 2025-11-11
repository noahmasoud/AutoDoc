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
        Extract exported symbols from the AST in a flattened list format.

        Args:
            ast: AST dictionary from parser

        Returns:
            List of export dictionaries with symbol metadata
        """
        exports: list[dict[str, Any]] = []

        body = ast.get("body", [])
        if not isinstance(body, list):
            return exports

        self._extract_exports_from_nodes(body, namespace_stack=[], exports=exports)

        return exports

    def _extract_exports_from_nodes(
        self,
        nodes: list[dict[str, Any]],
        namespace_stack: list[str],
        exports: list[dict[str, Any]],
    ) -> None:
        for node in nodes:
            node_type = node.get("type")

            if node_type in {"ExportNamedDeclaration", "ExportDefaultDeclaration"}:
                self._handle_export_declaration(
                    node,
                    namespace_stack=namespace_stack,
                    exports=exports,
                )
            elif node_type == "ExportAllDeclaration":
                self._handle_export_all_declaration(
                    node,
                    namespace_stack=namespace_stack,
                    exports=exports,
                )
            elif node_type == "TSModuleDeclaration":
                module_name = node.get("id", {}).get("name")
                body = node.get("body", {})
                if (
                    isinstance(module_name, str)
                    and isinstance(body, dict)
                    and body.get("type") == "TSModuleBlock"
                ):
                    nested_nodes = body.get("body", [])
                    if isinstance(nested_nodes, list):
                        self._extract_exports_from_nodes(
                            nested_nodes,
                            namespace_stack=[*namespace_stack, module_name],
                            exports=exports,
                        )

    def _handle_export_declaration(
        self,
        node: dict[str, Any],
        namespace_stack: list[str],
        exports: list[dict[str, Any]],
    ) -> None:
        declaration = node.get("declaration")
        specifiers = node.get("specifiers", [])
        source = node.get("source")
        source_dict = source if isinstance(source, dict) else None
        node_type = node.get("type")

        is_default = node_type == "ExportDefaultDeclaration"

        if isinstance(declaration, dict):
            export_entry = self._build_export_entry_from_declaration(
                declaration,
                is_default=is_default,
            )
            if export_entry:
                self._apply_namespace_metadata(export_entry, namespace_stack)
                exports.append(export_entry)

        for specifier in specifiers or []:
            if not isinstance(specifier, dict):
                continue

            exported = specifier.get("exported")
            if not isinstance(exported, dict) or not exported.get("name"):
                exported = specifier.get("local")
            if not isinstance(exported, dict):
                continue

            name = exported.get("name")
            if not name:
                continue

            entry: dict[str, Any] = {
                "symbol": name,
                "type": self._infer_export_type_from_specifier(specifier),
                "isDefault": is_default
                or (
                    specifier.get("exportKind") == "value"
                    and isinstance(specifier.get("local"), dict)
                    and specifier.get("local", {}).get("name") == "default"
                ),
                "signature": {
                    "source": source_dict.get("value") if source_dict else None,
                },
            }
            self._apply_namespace_metadata(entry, namespace_stack)
            exports.append(entry)

    def _handle_export_all_declaration(
        self,
        node: dict[str, Any],
        namespace_stack: list[str],
        exports: list[dict[str, Any]],
    ) -> None:
        source = node.get("source")
        source_dict = source if isinstance(source, dict) else None

        entry: dict[str, Any] = {
            "symbol": "*",
            "type": "all",
            "isDefault": False,
            "signature": {
                "source": source_dict.get("value") if source_dict else None,
            },
        }
        self._apply_namespace_metadata(entry, namespace_stack)
        exports.append(entry)

    @staticmethod
    def _build_export_entry_from_declaration(
        declaration: dict[str, Any],
        is_default: bool = False,
    ) -> dict[str, Any] | None:
        decl_type = declaration.get("type")
        identifier = declaration.get("id")
        if not isinstance(identifier, dict):
            identifier = {}
        name = identifier.get("name")

        if not name:
            # Handle export default function/class without identifier
            if is_default and decl_type in {"FunctionDeclaration", "ClassDeclaration"}:
                name = "default"
            else:
                return None

        export_type_map = {
            "ClassDeclaration": "class",
            "FunctionDeclaration": "function",
            "TSInterfaceDeclaration": "interface",
            "TSTypeAliasDeclaration": "type",
            "TSEnumDeclaration": "enum",
            "VariableDeclaration": "variable",
        }

        export_type = (
            export_type_map.get(decl_type, "unknown")
            if isinstance(decl_type, str)
            else "unknown"
        )

        entry: dict[str, Any] = {
            "symbol": name,
            "type": export_type,
            "isDefault": is_default,
        }

        # Include signature details for richer metadata if available
        loc = declaration.get("loc")
        start = loc.get("start") if isinstance(loc, dict) else None
        if isinstance(start, dict):
            entry["signature"] = {"line": start.get("line")}

        return entry

    @staticmethod
    def _infer_export_type_from_specifier(specifier: dict[str, Any]) -> str:
        if specifier.get("exportKind") == "type":
            return "type"
        return "re-export"

    @staticmethod
    def _apply_namespace_metadata(
        entry: dict[str, Any],
        namespace_stack: list[str],
    ) -> None:
        if not namespace_stack:
            return

        nested_name = ".".join(namespace_stack)
        signature = entry.setdefault("signature", {})
        signature["nestedIn"] = nested_name
        signature["isNested"] = True
