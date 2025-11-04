"""
TypeScript code analyzer using AST parsing.

This module provides TypeScript code analysis capabilities including:
- AST traversal and node extraction
- JSDoc comment extraction and parsing
- Symbol extraction (functions, classes, interfaces, etc.)
- Type information extraction
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from autodoc.logging.logger import get_logger

logger = get_logger(__name__)


class TypeScriptAnalyzer:
    """
    Analyzes TypeScript code using the TypeScript compiler API.

    This analyzer extracts symbols, types, and JSDoc comments from TypeScript
    source files to support automated documentation generation.
    """

    def __init__(self, ts_compiler_path: str | None = None):
        """
        Initialize the TypeScript analyzer.

        Args:
            ts_compiler_path: Optional path to TypeScript compiler executable.
                            If not provided, will use 'tsc' from PATH.
        """
        self.ts_compiler_path = ts_compiler_path or "tsc"
        self.logger = logger

    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """
        Analyze a TypeScript file and extract AST information.

        Extracts symbols with integrated JSDoc documentation, including parsed tags.
        Symbols in the output contain a 'jsdoc' field with normalized text and tags.

        Args:
            file_path: Path to the TypeScript file to analyze

        Returns:
            Dictionary containing:
            - file_path: Path to the analyzed file
            - symbols: List of symbols with integrated JSDoc data (jsdoc field)
            - jsdoc_comments: List of all JSDoc comments (for reference)
            - imports: List of import statements
            - exports: List of export statements
        """
        self.logger.info("Analyzing TypeScript file", extra={"file": str(file_path)})

        try:
            # Read the source file
            source_code = file_path.read_text(encoding="utf-8")

            # Parse AST and extract information
            ast_data = self._parse_ast(file_path, source_code)

            # Extract symbols and JSDoc comments
            analysis_result = {
                "file_path": str(file_path),
                "symbols": self._extract_symbols(ast_data),
                "jsdoc_comments": self._extract_jsdoc_comments(ast_data),
                "imports": self._extract_imports(ast_data),
                "exports": self._extract_exports(ast_data),
            }

            self.logger.debug(
                "Analysis complete",
                extra={
                    "file": str(file_path),
                    "symbols_count": len(analysis_result["symbols"]),
                    "jsdoc_count": len(analysis_result["jsdoc_comments"]),
                },
            )

            return analysis_result

        except Exception as e:
            self.logger.exception(
                "Failed to analyze TypeScript file",
                extra={"file": str(file_path)},
            )
            raise

    def _parse_ast(self, file_path: Path, source_code: str) -> dict[str, Any]:
        """
        Parse TypeScript source code into AST using TypeScript compiler API.

        This method uses the TypeScript compiler API via Node.js to parse
        the source code and return an AST structure that includes:
        - All AST nodes with position information
        - Leading comments (including JSDoc)
        - Trailing comments
        - Source file metadata

        Args:
            file_path: Path to the source file
            source_code: Source code content

        Returns:
            Dictionary containing parsed AST data
        """
        # Create a temporary script to extract AST using TypeScript compiler API
        script_content = f"""
const ts = require('typescript');

const sourceCode = {json.dumps(source_code)};
const fileName = {json.dumps(str(file_path))};

// Create a source file
const sourceFile = ts.createSourceFile(
    fileName,
    sourceCode,
    ts.ScriptTarget.Latest,
    true  // setParentNodes - required for comment extraction
);

// Function to extract AST node with comments
function extractNodeWithComments(node) {{
    const result = {{
        kind: ts.SyntaxKind[node.kind],
        text: node.getText(sourceFile),
        pos: node.pos,
        end: node.end,
        start: node.getStart(sourceFile),
        fullStart: node.getFullStart(),
    }};
    
    // Extract leading comments (including JSDoc)
    const leadingComments = ts.getLeadingCommentRanges(sourceFile.getFullText(), node.getFullStart());
    if (leadingComments) {{
        result.leadingComments = leadingComments.map(comment => {{
            const commentText = sourceFile.getFullText().substring(comment.pos, comment.end);
            return {{
                kind: comment.kind === ts.SyntaxKind.SingleLineCommentTrivia ? 'single-line' : 'multi-line',
                text: commentText,
                pos: comment.pos,
                end: comment.end,
                isJSDoc: comment.kind === ts.SyntaxKind.MultiLineCommentTrivia &&
                         commentText.trim().startsWith('/**'),
            }};
        }});
    }}
    
    // Extract trailing comments
    const trailingComments = ts.getTrailingCommentRanges(sourceFile.getFullText(), node.end);
    if (trailingComments) {{
        result.trailingComments = trailingComments.map(comment => {{
            return {{
                kind: comment.kind === ts.SyntaxKind.SingleLineCommentTrivia ? 'single-line' : 'multi-line',
                text: sourceFile.getFullText().substring(comment.pos, comment.end),
                pos: comment.pos,
                end: comment.end,
            }};
        }});
    }}
    
    return result;
}}

// Function to traverse AST and collect all nodes
function traverseAST(node, collector) {{
    collector.push(extractNodeWithComments(node));
    ts.forEachChild(node, (child) => traverseAST(child, collector));
}}

// Collect all nodes
const nodes = [];
traverseAST(sourceFile, nodes);

// Output JSON
console.log(JSON.stringify({{
    sourceFile: {{
        fileName: sourceFile.fileName,
        languageVersion: sourceFile.languageVersion,
        hasNoDefaultLib: sourceFile.hasNoDefaultLib,
    }},
    nodes: nodes,
}}, null, 2));
"""

        try:
            # Execute the Node.js script
            process = subprocess.run(
                ["node", "-e", script_content],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )

            # Parse the JSON output
            return json.loads(process.stdout)

        except subprocess.TimeoutExpired:
            self.logger.exception(
                "AST parsing timed out",
                extra={"file": str(file_path)},
            )
            raise TimeoutError("AST parsing exceeded timeout") from None
        except subprocess.CalledProcessError as e:
            self.logger.exception(
                "Failed to parse AST",
                extra={"file": str(file_path), "error": e.stderr},
            )
            raise RuntimeError(f"AST parsing failed: {e.stderr}") from e
        except json.JSONDecodeError as e:
            self.logger.exception(
                "Failed to parse AST JSON output",
                extra={"file": str(file_path)},
            )
            raise RuntimeError(f"Failed to parse AST JSON: {e}") from e

    def _extract_symbols(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract symbols (functions, classes, interfaces, etc.) from AST.

        Extracts symbols from AST nodes and includes their associated JSDoc
        comments and parsed tags.

        Args:
            ast_data: Parsed AST data

        Returns:
            List of extracted symbols with integrated JSDoc documentation
        """
        symbols: list[dict[str, Any]] = []

        if "nodes" not in ast_data:
            return symbols

        # First pass: Extract all symbols from AST nodes
        for node in ast_data["nodes"]:
            symbol_info = self._extract_symbol_info(node)
            if symbol_info:
                # Create symbol entry
                symbol: dict[str, Any] = {
                    "name": symbol_info.get("name"),
                    "type": symbol_info.get("type"),
                    "kind": symbol_info.get("kind"),
                    "text_preview": symbol_info.get("text_preview"),
                    "position": symbol_info.get("position"),
                    "jsdoc": None,  # Will be populated if JSDoc found
                }

                # Check for associated JSDoc comment
                jsdoc_data = self._extract_jsdoc_for_node(node)
                if jsdoc_data:
                    symbol["jsdoc"] = jsdoc_data

                symbols.append(symbol)

        return symbols

    def _extract_jsdoc_for_node(self, node: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extract and parse JSDoc comment for a specific AST node.

        This method extracts JSDoc comments from leading comments of a node,
        normalizes the text, and parses tags.

        Args:
            node: AST node dictionary

        Returns:
            Dictionary with JSDoc data (raw_text, normalized_text, tags) or None
        """
        if "leadingComments" not in node:
            return None

        # Find JSDoc comment (first JSDoc comment is typically the one for the symbol)
        for comment in node.get("leadingComments", []):
            if comment.get("isJSDoc", False):
                raw_text = comment.get("text", "")
                normalized_text = self._normalize_comment_text(raw_text)
                parsed_tags = self._parse_jsdoc_tags(normalized_text)

                return {
                    "raw_text": raw_text,
                    "normalized_text": normalized_text,
                    "tags": parsed_tags,
                    "position": {
                        "start": comment.get("pos"),
                        "end": comment.get("end"),
                    },
                }

        return None

    def _normalize_comment_text(self, comment_text: str) -> str:
        """
        Normalize JSDoc comment text by removing markers and formatting.

        This method cleans up JSDoc comments by:
        - Removing JSDoc markers (/** and */)
        - Stripping leading asterisks from each line
        - Removing extra whitespace
        - Preserving the structure and content

        Args:
            comment_text: Raw JSDoc comment text from AST

        Returns:
            Normalized comment text without JSDoc formatting markers
        """
        if not comment_text:
            return ""

        # Remove JSDoc opening and closing markers
        normalized = comment_text.strip()

        # Remove /** from the beginning
        normalized = normalized.removeprefix("/**")

        # Remove */ from the end
        normalized = normalized.removesuffix("*/")

        # Split into lines and process each
        lines = normalized.split("\n")
        normalized_lines = []

        for line in lines:
            # Strip leading whitespace
            line = line.strip()

            # Remove leading asterisk if present (JSDoc format)
            if line.startswith("*"):
                line = line[1:].strip()

            # Skip empty lines unless they're part of content structure
            if line:
                normalized_lines.append(line)
            elif (
                normalized_lines
            ):  # Preserve intentional blank lines between paragraphs
                normalized_lines.append("")

        # Join lines back together
        return "\n".join(normalized_lines).strip()

    def _parse_jsdoc_tags(self, normalized_text: str) -> dict[str, Any]:
        """
        Parse JSDoc tags from normalized comment text.

        Extracts common JSDoc tags including:
        - @param: Parameter descriptions
        - @returns/@return: Return value descriptions
        - @deprecated: Deprecation notices
        - @throws/@exception: Exception descriptions
        - @example: Code examples
        - @see: References
        - @since: Version information
        - @author: Author information
        - @version: Version information
        - @type: Type information
        - @typedef: Type definitions

        Args:
            normalized_text: Normalized JSDoc comment text (without markers)

        Returns:
            Dictionary containing parsed tags organized by tag type
        """
        tags: dict[str, Any] = {
            "params": [],
            "returns": None,
            "deprecated": None,
            "throws": [],
            "examples": [],
            "see": [],
            "since": None,
            "author": [],
            "version": None,
            "type": None,
            "typedef": None,
            "custom": [],
        }

        if not normalized_text:
            return tags

        # Pattern to match JSDoc tags
        # Matches: @tagName {type} [name] description or @tagName description
        # Handles formats like:
        # - @param {string} name Description
        # - @param {string} [name] Optional description
        # - @returns {type} Description
        # - @deprecated Description
        tag_pattern = re.compile(
            r"@(\w+)(?:\s+(?:\{([^}]+)\})?(?:\s*\[?([^\]]+)\]?)?(?:\s+(.+))?)?",
            re.MULTILINE,
        )

        lines = normalized_text.split("\n")
        current_tag: str | None = None
        current_tag_content: list[str] = []
        current_tag_type: str | None = None
        current_tag_name: str | None = None

        for line in lines:
            line = line.strip()

            # Check if this line starts a new tag
            tag_match = tag_pattern.match(line)
            if tag_match:
                # Save previous tag if any
                if current_tag and current_tag_content:
                    self._process_tag(
                        tags,
                        current_tag,
                        "\n".join(current_tag_content).strip(),
                        current_tag_type,
                        current_tag_name,
                    )

                # Start new tag
                current_tag = tag_match.group(1).lower()
                tag_type = tag_match.group(2)  # Optional type in braces {type}
                tag_name = tag_match.group(3)  # Optional name
                tag_desc = tag_match.group(4)  # Optional description

                current_tag_type = tag_type
                current_tag_name = tag_name
                current_tag_content = []

                # Add description if present on same line
                if tag_desc:
                    current_tag_content.append(tag_desc)
                # If we have a name but no description, add empty description
                elif tag_name:
                    current_tag_content.append("")
            elif current_tag and line:
                # Continuation of current tag description
                current_tag_content.append(line)
            elif not line and current_tag:
                # Empty line in tag description
                if current_tag_content:
                    current_tag_content.append("")

        # Process last tag
        if current_tag and current_tag_content:
            self._process_tag(
                tags,
                current_tag,
                "\n".join(current_tag_content).strip(),
                current_tag_type,
                current_tag_name,
            )

        return tags

    def _process_tag(
        self,
        tags: dict[str, Any],
        tag_name: str,
        content: str,
        tag_type: str | None,
        tag_param_name: str | None = None,
    ) -> None:
        """
        Process a single JSDoc tag and add it to the tags dictionary.

        Args:
            tags: Dictionary to store parsed tags
            tag_name: Name of the tag (lowercase)
            content: Content of the tag
            tag_type: Optional type information from braces {type}
            tag_param_name: Optional parameter name extracted from tag
        """
        # Extract name and description from content if not already provided
        # Format may be: {name} description or just description
        name = tag_param_name
        description = content.strip()

        # If name not provided in tag but might be in content
        if not name and content:
            # Check if content starts with {name} pattern
            name_match = re.match(r"\{([^}]+)\}\s*(.*)", content)
            if name_match:
                name = name_match.group(1)
                description = name_match.group(2).strip()
            # Check if content starts with [name] pattern (optional parameter)
            elif content.startswith("[") and "]" in content:
                bracket_match = re.match(r"\[([^\]]+)\]\s*(.*)", content)
                if bracket_match:
                    name = bracket_match.group(1)
                    description = bracket_match.group(2).strip()

        tag_data = {
            "name": name,
            "type": tag_type,
            "description": description,
        }

        # Route to appropriate tag list/field using dispatch pattern to reduce complexity
        if tag_name in {"param", "parameter"}:
            tags["params"].append(tag_data)
        elif tag_name in {"returns", "return"}:
            tags["returns"] = tag_data
        elif tag_name == "deprecated":
            tags["deprecated"] = {
                "description": description,
                "since": tag_type,  # Sometimes version is in type position
            }
        elif tag_name in {"throws", "exception"}:
            tags["throws"].append(tag_data)
        elif tag_name == "example":
            tags["examples"].append(description)
        elif tag_name == "see":
            tags["see"].append(description)
        elif tag_name == "since":
            tags["since"] = description or tag_type
        elif tag_name == "author":
            tags["author"].append(description)
        elif tag_name == "version":
            tags["version"] = description or tag_type
        elif tag_name == "type":
            tags["type"] = {
                "type": tag_type,
                "description": description,
            }
        elif tag_name == "typedef":
            tags["typedef"] = tag_data
        else:
            # Custom or unknown tag
            tags["custom"].append(
                {
                    "tag": tag_name,
                    "type": tag_type,
                    "content": content,
                },
            )

    def _extract_symbol_info(self, node: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extract symbol information from an AST node.

        Identifies the type of symbol (function, class, interface, etc.) and
        extracts relevant metadata like name, parameters, return type.

        Args:
            node: AST node dictionary

        Returns:
            Dictionary with symbol information or None if not a symbol node
        """
        node_kind = node.get("kind", "")
        node_text = node.get("text", "")

        # Common symbol node kinds in TypeScript
        symbol_kinds = [
            "FunctionDeclaration",
            "MethodDeclaration",
            "ClassDeclaration",
            "InterfaceDeclaration",
            "TypeAliasDeclaration",
            "VariableDeclaration",
            "PropertyDeclaration",
            "GetAccessor",
            "SetAccessor",
            "Constructor",
            "EnumDeclaration",
            "ModuleDeclaration",
        ]

        if node_kind not in symbol_kinds:
            return None

        # Extract symbol name (basic extraction - can be enhanced)
        symbol_name = None
        symbol_type = node_kind

        # Try to extract name from node text
        # This is a simplified extraction - full implementation would parse the AST properly
        if node_text:
            # Look for function/class/interface name patterns
            # Function: function name(...)
            # Class: class Name
            # Interface: interface Name
            patterns = {
                "FunctionDeclaration": r"function\s+(\w+)",
                "MethodDeclaration": r"(\w+)\s*\([^)]*\)",
                "ClassDeclaration": r"class\s+(\w+)",
                "InterfaceDeclaration": r"interface\s+(\w+)",
                "TypeAliasDeclaration": r"type\s+(\w+)",
                "VariableDeclaration": r"(?:const|let|var)\s+(\w+)",
                "PropertyDeclaration": r"(\w+)\s*:",
                "EnumDeclaration": r"enum\s+(\w+)",
            }

            for pattern_kind, pattern in patterns.items():
                if node_kind == pattern_kind or node_kind.startswith(
                    pattern_kind.split("Declaration")[0],
                ):
                    match = re.search(pattern, node_text)
                    if match:
                        symbol_name = match.group(1)
                        break

        return {
            "name": symbol_name,
            "type": symbol_type,
            "kind": node_kind,
            "text_preview": node_text[:200],  # First 200 chars for context
            "position": {
                "start": node.get("start"),
                "end": node.get("end"),
            },
        }

    def _extract_jsdoc_comments(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract and normalize JSDoc comments from AST nodes.

        This method:
        1. Identifies JSDoc comments from the AST
        2. Normalizes the comment text (removes markers, formatting)
        3. Maps comments to their associated symbols

        Args:
            ast_data: Parsed AST data containing nodes with comments

        Returns:
            List of normalized JSDoc comment objects with symbol mapping
        """
        jsdoc_comments: list[dict[str, Any]] = []

        if "nodes" not in ast_data:
            return jsdoc_comments

        for node in ast_data["nodes"]:
            # Check for leading comments that are JSDoc
            if "leadingComments" in node:
                for comment in node["leadingComments"]:
                    if comment.get("isJSDoc", False):
                        # Normalize the comment text
                        raw_text = comment.get("text", "")
                        normalized_text = self._normalize_comment_text(raw_text)

                        # Parse JSDoc tags from normalized text
                        parsed_tags = self._parse_jsdoc_tags(normalized_text)

                        # Extract symbol information from the associated node
                        symbol_info = self._extract_symbol_info(node)

                        # Create the JSDoc comment entry
                        jsdoc_entry: dict[str, Any] = {
                            "raw_text": raw_text,
                            "normalized_text": normalized_text,
                            "tags": parsed_tags,
                            "position": {
                                "start": comment["pos"],
                                "end": comment["end"],
                            },
                            "associated_node": {
                                "kind": node.get("kind"),
                                "text_preview": node.get("text", "")[:100],
                                "start": node.get("start"),
                                "end": node.get("end"),
                            },
                        }

                        # Add symbol information if available
                        if symbol_info:
                            jsdoc_entry["symbol"] = symbol_info
                            jsdoc_entry["symbol_name"] = symbol_info.get("name")
                            jsdoc_entry["symbol_type"] = symbol_info.get("type")

                        jsdoc_comments.append(jsdoc_entry)

        return jsdoc_comments

    def _extract_imports(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract import statements from AST.

        Placeholder for import extraction logic.

        Args:
            ast_data: Parsed AST data

        Returns:
            List of import statements
        """
        # Placeholder - will be implemented in later steps
        return []

    def _extract_exports(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract export statements from AST.

        Placeholder for export extraction logic.

        Args:
            ast_data: Parsed AST data

        Returns:
            List of export statements
        """
        # Placeholder - will be implemented in later steps
        return []
