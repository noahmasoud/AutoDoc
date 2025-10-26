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

    pass


class ParseError(TypeScriptParserError):
    """Raised when TypeScript parsing fails."""

    pass


class NodeJSNotFoundError(TypeScriptParserError):
    """Raised when Node.js is not found on the system."""

    pass


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
            parser_script = Path(__file__).parent.parent / "scripts" / "parse-typescript.js"
        
        self.parser_script = Path(parser_script)
        
        if not self.parser_script.exists():
            raise FileNotFoundError(
                f"Parser script not found: {self.parser_script}"
            )
        
        # Verify Node.js is available
        self._check_nodejs()

    def _check_nodejs(self) -> None:
        """Check if Node.js is installed and available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
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
                "Please install Node.js >= 18.0.0 to use the TypeScript parser."
            )
        except subprocess.TimeoutExpired:
            raise NodeJSNotFoundError("Node.js version check timed out")

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
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )
            
            if result.returncode != 0:
                # Try to parse error from stderr
                error_data = self._parse_error_output(result.stderr)
                raise ParseError(
                    f"Parsing failed: {error_data.get('message', 'Unknown error')}"
                )
            
            # Parse JSON output
            ast_data = json.loads(result.stdout)
            
            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}"
                )
            
            logger.info("Successfully parsed TypeScript file")
            return ast_data["ast"]
            
        except subprocess.TimeoutExpired:
            raise ParseError("Parser timed out after 30 seconds")
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON output: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Parser script not found: {self.parser_script}"
            )

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
                input=source_code,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                error_data = self._parse_error_output(result.stderr)
                raise ParseError(
                    f"Parsing failed: {error_data.get('message', 'Unknown error')}"
                )
            
            ast_data = json.loads(result.stdout)
            
            if not ast_data.get("success"):
                error_info = ast_data.get("error", {})
                raise ParseError(
                    f"Parse error: {error_info.get('message', 'Unknown error')}"
                )
            
            logger.info("Successfully parsed TypeScript source code")
            return ast_data["ast"]
            
        except subprocess.TimeoutExpired:
            raise ParseError("Parser timed out after 30 seconds")
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON output: {e}")

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

    def extract_public_symbols(self, ast: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
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
                    symbols["classes"].append({
                        "name": node["id"]["name"],
                        "line": node.get("loc", {}).get("start", {}).get("line"),
                        "decorators": len(node.get("decorators", [])),
                    })
            
            elif node.get("type") == "FunctionDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["functions"].append({
                        "name": node["id"]["name"],
                        "line": node.get("loc", {}).get("start", {}).get("line"),
                        "async": node.get("async", False),
                    })
            
            elif node.get("type") == "TSInterfaceDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["interfaces"].append({
                        "name": node["id"]["name"],
                        "line": node.get("loc", {}).get("start", {}).get("line"),
                    })
            
            elif node.get("type") == "TSTypeAliasDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["types"].append({
                        "name": node["id"]["name"],
                        "line": node.get("loc", {}).get("start", {}).get("line"),
                    })
            
            elif node.get("type") == "TSEnumDeclaration":
                if node.get("id", {}).get("name"):
                    symbols["enums"].append({
                        "name": node["id"]["name"],
                        "line": node.get("loc", {}).get("start", {}).get("line"),
                    })
        
        return symbols

