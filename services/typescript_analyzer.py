"""
TypeScript Analyzer Service for CI/CD Integration

This module processes changed TypeScript files in CI/CD runs,
parses them using the TypeScript AST parser, and logs results
to the run report.
"""

import logging
from pathlib import Path
from typing import Any

from services.typescript_parser import ParseError, TypeScriptParser

logger = logging.getLogger(__name__)


class TypeScriptAnalyzer:
    """
    Analyzer for processing TypeScript files in CI/CD runs.
    
    Detects changed .ts files, parses them to extract symbols,
    and logs results for documentation generation.
    """

    def __init__(self) -> None:
        """Initialize the TypeScript analyzer."""
        self.parser = TypeScriptParser()

    def analyze_changed_files(
        self,
        changed_files: list[str],
        run_id: str,
    ) -> dict[str, Any]:
        """
        Analyze changed TypeScript files and extract public symbols.
        
        Args:
            changed_files: List of file paths that have changed
            run_id: Run ID for logging correlation
            
        Returns:
            Dictionary with analysis results:
            {
                'files_processed': int,
                'files_failed': int,
                'symbols_extracted': {
                    'classes': int,
                    'functions': int,
                    'interfaces': int,
                    'types': int,
                    'enums': int
                },
                'files': [
                    {
                        'file_path': str,
                        'status': 'success' | 'failed',
                        'symbols': {...},
                        'error': str (if failed)
                    }
                ]
            }
        """
        logger.info(
            f"[Run: {run_id}] Starting TypeScript file analysis",
            extra={"run_id": run_id, "files_count": len(changed_files)},
        )

        # Filter to only TypeScript files
        ts_files = [f for f in changed_files if self._is_typescript_file(f)]

        if not ts_files:
            logger.info(
                f"[Run: {run_id}] No TypeScript files to analyze",
                extra={"run_id": run_id},
            )
            return {
                "files_processed": 0,
                "files_failed": 0,
                "symbols_extracted": {
                    "classes": 0,
                    "functions": 0,
                    "interfaces": 0,
                    "types": 0,
                    "enums": 0,
                },
                "files": [],
            }

        logger.info(
            f"[Run: {run_id}] Found {len(ts_files)} TypeScript files to analyze",
            extra={"run_id": run_id, "ts_files": ts_files},
        )

        results = {
            "files_processed": 0,
            "files_failed": 0,
            "symbols_extracted": {
                "classes": 0,
                "functions": 0,
                "interfaces": 0,
                "types": 0,
                "enums": 0,
            },
            "files": [],
        }

        # Analyze each TypeScript file
        for file_path in ts_files:
            file_result = self._analyze_file(file_path, run_id)
            results["files"].append(file_result)

            if file_result["status"] == "success":
                results["files_processed"] += 1
                # Accumulate symbol statistics
                for symbol_type in results["symbols_extracted"]:
                    results["symbols_extracted"][symbol_type] += len(
                        file_result["symbols"].get(symbol_type, [])
                    )
            else:
                results["files_failed"] += 1

        logger.info(
            f"[Run: {run_id}] Analysis complete: "
            f"{results['files_processed']} processed, "
            f"{results['files_failed']} failed",
            extra={
                "run_id": run_id,
                "files_processed": results["files_processed"],
                "files_failed": results["files_failed"],
                "symbols": results["symbols_extracted"],
            },
        )

        return results

    def _analyze_file(self, file_path: str, run_id: str) -> dict[str, Any]:
        """
        Analyze a single TypeScript file.
        
        Args:
            file_path: Path to the TypeScript file
            run_id: Run ID for logging
            
        Returns:
            Dictionary with file analysis results
        """
        logger.debug(
            f"[Run: {run_id}] Analyzing file: {file_path}",
            extra={"run_id": run_id, "file_path": file_path},
        )

        try:
            # Parse the file
            ast = self.parser.parse_file(file_path)

            # Extract public symbols
            symbols = self.parser.extract_public_symbols(ast)

            logger.info(
                f"[Run: {run_id}] Successfully analyzed {file_path}",
                extra={
                    "run_id": run_id,
                    "file_path": file_path,
                    "symbols_count": sum(len(s) for s in symbols.values()),
                },
            )

            return {
                "file_path": file_path,
                "status": "success",
                "symbols": symbols,
            }

        except ParseError as e:
            logger.error(
                f"[Run: {run_id}] Parse error for {file_path}: {e}",
                extra={
                    "run_id": run_id,
                    "file_path": file_path,
                    "error": str(e),
                },
            )
            return {
                "file_path": file_path,
                "status": "failed",
                "error": str(e),
                "symbols": {},
            }

        except FileNotFoundError as e:
            logger.error(
                f"[Run: {run_id}] File not found: {file_path}",
                extra={
                    "run_id": run_id,
                    "file_path": file_path,
                    "error": str(e),
                },
            )
            return {
                "file_path": file_path,
                "status": "failed",
                "error": f"File not found: {e}",
                "symbols": {},
            }

        except Exception as e:
            logger.error(
                f"[Run: {run_id}] Unexpected error analyzing {file_path}: {e}",
                extra={
                    "run_id": run_id,
                    "file_path": file_path,
                    "error": str(e),
                },
            )
            return {
                "file_path": file_path,
                "status": "failed",
                "error": f"Unexpected error: {e}",
                "symbols": {},
            }

    def _is_typescript_file(self, file_path: str) -> bool:
        """
        Check if a file is a TypeScript file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file is TypeScript (.ts or .tsx)
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        return suffix in {".ts", ".tsx"}

