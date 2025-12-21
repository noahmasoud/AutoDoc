#!/usr/bin/env python3
"""
Save symbols to database for a run.

This script takes a run_id and list of changed files,
then uses the appropriate ingestor to save symbols.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from db.session import SessionLocal
from services.python_symbol_ingestor import PythonSymbolIngestor
from services.javascript_symbol_ingestor import JavaScriptSymbolIngestor
from services.go_symbol_ingestor import GoSymbolIngestor


def save_symbols(run_id: int, changed_files: list[str]) -> dict[str, int]:
    """
    Save symbols for all changed files.
    
    Args:
        run_id: The run ID
        changed_files: List of file paths
        
    Returns:
        Dictionary with counts of symbols saved per language
    """
    db: Session = SessionLocal()
    
    try:
        python_files = [f for f in changed_files if f.endswith('.py')]
        js_files = [f for f in changed_files if f.endswith(('.js', '.jsx'))]
        go_files = [f for f in changed_files if f.endswith('.go')]
        
        counts = {
            'python': 0,
            'javascript': 0,
            'go': 0,
        }
        
        # Save Python symbols
        if python_files:
            ingestor = PythonSymbolIngestor()
            symbols = ingestor.ingest_files(run_id, python_files, db)
            counts['python'] = len(symbols)
        
        # Save JavaScript symbols
        if js_files:
            ingestor = JavaScriptSymbolIngestor()
            symbols = ingestor.ingest_files(run_id, js_files, db)
            counts['javascript'] = len(symbols)
        
        # Save Go symbols
        if go_files:
            try:
                ingestor = GoSymbolIngestor()
                symbols = ingestor.ingest_files(run_id, go_files, db)
                counts['go'] = len(symbols)
            except Exception as e:
                # Go might not be installed
                print(f"Warning: Could not save Go symbols: {e}", file=sys.stderr)
        
        db.commit()
        return counts
        
    except Exception as e:
        db.rollback()
        print(f"Error saving symbols: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: save_symbols_to_db.py <run_id> <file1> [file2 ...]", file=sys.stderr)
        sys.exit(1)
    
    run_id = int(sys.argv[1])
    changed_files = sys.argv[2:]
    
    counts = save_symbols(run_id, changed_files)
    
    # Output JSON
    import json
    print(json.dumps(counts))


if __name__ == "__main__":
    main()

