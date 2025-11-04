"""
TypeScript code analyzer using AST parsing.

This module provides TypeScript code analysis capabilities including:
- AST traversal and node extraction
- JSDoc comment extraction and parsing
- Symbol extraction (functions, classes, interfaces, etc.)
- Type information extraction
"""

import json
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

        Args:
            file_path: Path to the TypeScript file to analyze

        Returns:
            Dictionary containing extracted symbols, types, and JSDoc comments
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

        This is a placeholder for symbol extraction logic that will be
        implemented in subsequent steps.

        Args:
            ast_data: Parsed AST data

        Returns:
            List of extracted symbols
        """
        # Placeholder - will be implemented in later steps
        return []

    def _extract_jsdoc_comments(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract JSDoc comments from AST nodes.

        This method identifies and extracts JSDoc comments from the AST,
        specifically looking for multi-line comments that start with /**.
        These comments are associated with their following AST nodes.

        Args:
            ast_data: Parsed AST data containing nodes with comments

        Returns:
            List of JSDoc comment objects with their associated node information
        """
        jsdoc_comments: list[dict[str, Any]] = []

        if "nodes" not in ast_data:
            return jsdoc_comments

        for node in ast_data["nodes"]:
            # Check for leading comments that are JSDoc
            if "leadingComments" in node:
                jsdoc_comments.extend(
                    {
                        "comment_text": comment["text"],
                        "position": {
                            "start": comment["pos"],
                            "end": comment["end"],
                        },
                        "associated_node": {
                            "kind": node.get("kind"),
                            "text": node.get("text", "")[:100],  # First 100 chars
                            "start": node.get("start"),
                        },
                    }
                    for comment in node["leadingComments"]
                    if comment.get("isJSDoc", False)
                )

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
