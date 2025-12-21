#!/usr/bin/env python3
"""
Multi-language file analyzer for AutoDoc.

This script analyzes changed files in Python, JavaScript, and Go,
and returns a unified result format for the autodoc.sh script.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_file(file_path: str, old_content: str, new_content: str) -> dict[str, Any]:
    """
    Analyze a single file and return changes.
    
    Args:
        file_path: Path to the file
        old_content: Old version of the file
        new_content: New version of the file
        
    Returns:
        Dictionary with analysis results
    """
    file_ext = Path(file_path).suffix.lower()
    
    # Route to appropriate analyzer based on file extension
    if file_ext == ".py":
        return _analyze_python_file(file_path, old_content, new_content)
    elif file_ext in (".js", ".jsx"):
        return _analyze_javascript_file(file_path, old_content, new_content)
    elif file_ext == ".go":
        return _analyze_go_file(file_path, old_content, new_content)
    else:
        return {
            "file_path": file_path,
            "error": f"Unsupported file type: {file_ext}",
            "summary": {
                "added_count": 0,
                "modified_count": 0,
                "removed_count": 0,
                "breaking_count": 0,
            },
            "detailed_changes": [],
        }


def _analyze_python_file(file_path: str, old_content: str, new_content: str) -> dict[str, Any]:
    """Analyze a Python file."""
    try:
        from src.analyzer.parser import parse_python_code
        from src.analyzer.extractor import extract_symbols
        from src.analyzer.change_detector import detect_changes

        old_tree = parse_python_code(old_content) if old_content.strip() else None
        new_tree = parse_python_code(new_content) if new_content.strip() else None

        if old_tree and new_tree:
            old_module = extract_symbols(old_tree, file_path)
            new_module = extract_symbols(new_tree, file_path)
            report = detect_changes(old_module, new_module, "HEAD^", "HEAD")

            # Extract detailed changes
            detailed_changes = []
            for change in report.added:
                detailed_changes.append({
                    "file_path": file_path,
                    "symbol": change.symbol_name,
                    "change_type": "added",
                    "signature_before": None,
                    "signature_after": None,
                })
            for change in report.modified:
                detailed_changes.append({
                    "file_path": file_path,
                    "symbol": change.symbol_name,
                    "change_type": "modified",
                    "signature_before": None,
                    "signature_after": None,
                })
            for change in report.removed:
                detailed_changes.append({
                    "file_path": file_path,
                    "symbol": change.symbol_name,
                    "change_type": "removed",
                    "signature_before": None,
                    "signature_after": None,
                })

            result = report.to_dict()
            result["detailed_changes"] = detailed_changes
            return result
        else:
            return {
                "file_path": file_path,
                "summary": {
                    "added_count": 0,
                    "modified_count": 0,
                    "removed_count": 0,
                    "breaking_count": 0,
                },
                "detailed_changes": [],
            }
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "summary": {
                "added_count": 0,
                "modified_count": 0,
                "removed_count": 0,
                "breaking_count": 0,
            },
            "detailed_changes": [],
        }


def _analyze_javascript_file(file_path: str, old_content: str, new_content: str) -> dict[str, Any]:
    """Analyze a JavaScript file."""
    try:
        from services.javascript_parser import JavaScriptParser
        from pathlib import Path
        import tempfile

        parser = JavaScriptParser()

        # Parse both versions - always use temp files to avoid stdin buffer issues
        old_ast = None
        new_ast = None
        
        if old_content.strip():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(old_content)
                temp_old = f.name
            try:
                old_ast = parser.parse_file(temp_old)
            except Exception as e:
                # Log but continue
                print(f"Warning: Failed to parse old version of {file_path}: {e}", file=sys.stderr)
            finally:
                Path(temp_old).unlink(missing_ok=True)
        
        if new_content.strip():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(new_content)
                temp_new = f.name
            try:
                new_ast = parser.parse_file(temp_new)
            except Exception as e:
                # Log but continue
                print(f"Warning: Failed to parse new version of {file_path}: {e}", file=sys.stderr)
            finally:
                Path(temp_new).unlink(missing_ok=True)

        # Handle different scenarios
        if new_ast:
            new_symbols = parser.extract_public_symbols(new_ast)
            
            # Get all symbol names from new version
            new_symbol_names = set()
            for symbol_type in ["functions", "classes", "interfaces", "types", "enums"]:
                for sym in new_symbols.get(symbol_type, []):
                    name = sym.get("name", "")
                    if name:
                        new_symbol_names.add(name)
            
            detailed_changes = []
            added_count = 0
            modified_count = 0
            removed_count = 0
            
            if old_ast:
                # File exists in both versions - compare
                old_symbols = parser.extract_public_symbols(old_ast)
                old_symbol_names = set()
                for symbol_type in ["functions", "classes", "interfaces", "types", "enums"]:
                    for sym in old_symbols.get(symbol_type, []):
                        name = sym.get("name", "")
                        if name:
                            old_symbol_names.add(name)
                
                # Detect changes
                for name in new_symbol_names - old_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "added",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    added_count += 1

                for name in old_symbol_names - new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "removed",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    removed_count += 1

                # Modified symbols (in both but potentially changed)
                for name in old_symbol_names & new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "modified",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    modified_count += 1
            else:
                # New file - all symbols are "added"
                for name in new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "added",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    added_count += 1

            return {
                "file_path": file_path,
                "summary": {
                    "added_count": added_count,
                    "modified_count": modified_count,
                    "removed_count": removed_count,
                    "breaking_count": 0,  # Could be enhanced
                },
                "detailed_changes": detailed_changes,
            }
        else:
            # New file is empty or couldn't be parsed
            return {
                "file_path": file_path,
                "summary": {
                    "added_count": 0,
                    "modified_count": 0,
                    "removed_count": 0,
                    "breaking_count": 0,
                },
                "detailed_changes": [],
            }
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "summary": {
                "added_count": 0,
                "modified_count": 0,
                "removed_count": 0,
                "breaking_count": 0,
            },
            "detailed_changes": [],
        }


def _analyze_go_file(file_path: str, old_content: str, new_content: str) -> dict[str, Any]:
    """Analyze a Go file."""
    try:
        from services.go_parser import GoParser, GoNotFoundError
        from pathlib import Path
        import tempfile

        try:
            parser = GoParser()
        except GoNotFoundError:
            # Go not installed - return empty result
            return {
                "file_path": file_path,
                "error": "Go compiler not found. Please install Go >= 1.18",
                "summary": {
                    "added_count": 0,
                    "modified_count": 0,
                    "removed_count": 0,
                    "breaking_count": 0,
                },
                "detailed_changes": [],
            }

        # Parse both versions - use temporary files since parser expects file paths
        old_ast = None
        new_ast = None
        
        if old_content.strip():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(old_content)
                temp_old = f.name
            try:
                old_ast = parser.parse_file(temp_old)
            finally:
                Path(temp_old).unlink(missing_ok=True)
        
        if new_content.strip():
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(new_content)
                temp_new = f.name
            try:
                new_ast = parser.parse_file(temp_new)
            finally:
                Path(temp_new).unlink(missing_ok=True)

        # Handle different scenarios
        if new_ast:
            new_symbols = parser.extract_public_symbols(new_ast)
            
            # Get all symbol names from new version
            new_symbol_names = set()
            for symbol_type in ["functions", "types", "interfaces", "structs", "consts", "vars"]:
                for sym in new_symbols.get(symbol_type, []):
                    name = sym.get("name", "")
                    if name:
                        new_symbol_names.add(name)
            
            detailed_changes = []
            added_count = 0
            modified_count = 0
            removed_count = 0
            
            if old_ast:
                # File exists in both versions - compare
                old_symbols = parser.extract_public_symbols(old_ast)
                old_symbol_names = set()
                for symbol_type in ["functions", "types", "interfaces", "structs", "consts", "vars"]:
                    for sym in old_symbols.get(symbol_type, []):
                        name = sym.get("name", "")
                        if name:
                            old_symbol_names.add(name)
                
                # Detect changes
                for name in new_symbol_names - old_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "added",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    added_count += 1

                for name in old_symbol_names - new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "removed",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    removed_count += 1

                # Modified symbols
                for name in old_symbol_names & new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "modified",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    modified_count += 1
            else:
                # New file - all symbols are "added"
                for name in new_symbol_names:
                    detailed_changes.append({
                        "file_path": file_path,
                        "symbol": name,
                        "change_type": "added",
                        "signature_before": None,
                        "signature_after": None,
                    })
                    added_count += 1

            return {
                "file_path": file_path,
                "summary": {
                    "added_count": added_count,
                    "modified_count": modified_count,
                    "removed_count": removed_count,
                    "breaking_count": 0,
                },
                "detailed_changes": detailed_changes,
            }
        else:
            # New file is empty or couldn't be parsed
            return {
                "file_path": file_path,
                "summary": {
                    "added_count": 0,
                    "modified_count": 0,
                    "removed_count": 0,
                    "breaking_count": 0,
                },
                "detailed_changes": [],
            }
    except Exception as e:
        return {
            "file_path": file_path,
            "error": str(e),
            "summary": {
                "added_count": 0,
                "modified_count": 0,
                "removed_count": 0,
                "breaking_count": 0,
            },
            "detailed_changes": [],
        }


def main():
    """Main entry point for the analyzer script."""
    if len(sys.argv) < 4:
        print("Usage: analyze_changed_files.py <file_path> <old_file> <new_file>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    old_file = sys.argv[2]
    new_file = sys.argv[3]

    # Read file contents
    try:
        with open(old_file, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = ""

    try:
        with open(new_file, "r", encoding="utf-8") as f:
            new_content = f.read()
    except FileNotFoundError:
        new_content = ""

    # Analyze the file
    result = analyze_file(file_path, old_content, new_content)

    # Output JSON result
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

