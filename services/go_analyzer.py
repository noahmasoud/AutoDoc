"""
Go Analyzer Service for CI/CD Integration

This module processes changed Go files in CI/CD runs,
parses them using the Go AST parser, and logs results
to the run report.
"""

import logging
from pathlib import Path
from typing import Any

from services.go_parser import ParseError, GoParser

logger = logging.getLogger(__name__)


class GoAnalyzer:
    """
    Analyzer for processing Go files in CI/CD runs.

    Detects changed .go files, parses them to extract symbols,
    and logs results for documentation generation.
    """

    def __init__(self) -> None:
        """Initialize the Go analyzer."""
        self.parser = GoParser()

    def analyze_changed_files(
        self,
        changed_files: list[str],
        run_id: str,
    ) -> dict[str, Any]:
        """
        Analyze changed Go files and extract public symbols.

        Args:
            changed_files: List of file paths that have changed
            run_id: Run ID for logging correlation

        Returns:
            Dictionary with analysis results:
            {
                'files_processed': int,
                'files_failed': int,
                'symbols_extracted': {
                    'functions': int,
                    'types': int,
                    'interfaces': int,
                    'structs': int,
                    'consts': int,
                    'vars': int
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
            f"[Run: {run_id}] Starting Go file analysis",
            extra={"run_id": run_id, "files_count": len(changed_files)},
        )

        # Filter to only Go files
        go_files = [f for f in changed_files if self._is_go_file(f)]

        if not go_files:
            logger.info(
                f"[Run: {run_id}] No Go files to analyze",
                extra={"run_id": run_id},
            )
            return {
                "files_processed": 0,
                "files_failed": 0,
                "symbols_extracted": {
                    "functions": 0,
                    "types": 0,
                    "interfaces": 0,
                    "structs": 0,
                    "consts": 0,
                    "vars": 0,
                },
                "files": [],
            }

        logger.info(
            f"[Run: {run_id}] Found {len(go_files)} Go files to analyze",
            extra={"run_id": run_id, "go_files": go_files},
        )

        symbols_extracted: dict[str, int] = {
            "functions": 0,
            "types": 0,
            "interfaces": 0,
            "structs": 0,
            "consts": 0,
            "vars": 0,
        }
        file_results: list[dict[str, Any]] = []
        results: dict[str, Any] = {
            "files_processed": 0,
            "files_failed": 0,
            "symbols_extracted": symbols_extracted,
            "files": file_results,
        }

        # Analyze each Go file
        for file_path in go_files:
            file_result = self._analyze_file(file_path, run_id)
            file_results.append(file_result)

            if file_result["status"] == "success":
                results["files_processed"] += 1
                # Accumulate symbol statistics
                for symbol_type in symbols_extracted:
                    symbols_extracted[symbol_type] += len(
                        file_result["symbols"].get(symbol_type, []),
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
        Analyze a single Go file.

        Args:
            file_path: Path to the Go file
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
            logger.exception(
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
            logger.exception(
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
            logger.exception(
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

    def _is_go_file(self, file_path: str) -> bool:
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

