"""CLI entrypoint for AutoDoc CI/CD integration.

This module provides a command-line interface for creating runs from CI/CD pipelines.
It accepts --commit, --repo, --branch, --pr-id, and --dry-run flags and orchestrates
the full analysis pipeline: change detection, report generation, and patch creation.

Implements FR-1, FR-3: Accepts commit/branch/repo/PR inputs and emits change_report.json
and patches.json artifacts to ./artifacts/
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.models import Run, PythonSymbol
from db.session import SessionLocal
from autodoc.logging.correlation import generate_correlation_id
from services.change_report_generator import generate_change_report
from services.patches_artifact_exporter import export_patches_artifact
from services.patch_generator import generate_patches_for_run
from services.python_symbol_ingestor import PythonSymbolIngestor
from services.change_detector import detect_changes
from services.change_persister import save_changes_to_database
from services.artifact_loader import load_run_artifact
from schemas.changes import RunArtifact, SymbolData, SignatureInfo, ParameterInfo
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_changed_files(commit_sha: str) -> list[str]:
    """Get list of changed files for a commit.

    Args:
        commit_sha: Git commit SHA

    Returns:
        List of changed file paths

    Raises:
        SystemExit: If git command fails
    """
    try:
        # Get parent commit (if exists)
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{commit_sha}^"],
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            parent_commit = f"{commit_sha}^"
        else:
            # First commit, compare with empty tree
            parent_commit = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

        # Get changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", parent_commit, commit_sha],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_files(
    run_id: int,
    changed_files: list[str],
    commit_sha: str,
    db: Session,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Analyze changed files and extract symbols.

    Args:
        run_id: Run ID
        changed_files: List of changed file paths
        commit_sha: Git commit SHA
        db: Database session

    Returns:
        Tuple of (diffs dict, findings dict)
    """
    python_files = [f for f in changed_files if f.endswith((".py", ".pyi"))]
    ts_files = [f for f in changed_files if f.endswith((".ts", ".tsx"))]

    diffs: dict[str, Any] = {}
    findings: dict[str, Any] = {}

    # Analyze Python files
    if python_files:
        ingestor = PythonSymbolIngestor()
        symbols = ingestor.ingest_files(run_id, python_files, db)
        db.commit()

        # Build diffs and findings from symbols
        for file_path in python_files:
            file_symbols = [s for s in symbols if s.file_path == file_path]
            diffs[file_path] = {
                "added": len([s for s in file_symbols if s.symbol_type == "function"]),
                "removed": 0,
                "modified": 0,
            }
            findings[file_path] = [
                {
                    "symbol": s.symbol_name,
                    "type": s.symbol_type,
                    "qualified_name": s.qualified_name,
                    "docstring": s.docstring,
                }
                for s in file_symbols
            ]

    # Analyze TypeScript files (placeholder - would need TypeScript analyzer)
    if ts_files:
        for file_path in ts_files:
            diffs[file_path] = {"added": 0, "removed": 0, "modified": 0}
            findings[file_path] = []

    return diffs, findings


def build_artifact_from_symbols(
    run: Run,
    symbols: list[PythonSymbol],
) -> RunArtifact:
    """Build a RunArtifact from PythonSymbol records.

    Args:
        run: Run object
        symbols: List of PythonSymbol records

    Returns:
        RunArtifact containing symbol data
    """
    symbol_data_list = []
    for symbol in symbols:
        # Extract signature info from symbol_metadata if available
        signature = None
        if symbol.symbol_metadata:
            metadata = symbol.symbol_metadata
            if isinstance(metadata, dict) and "parameters" in metadata:
                parameters = [
                    ParameterInfo(
                        name=p.get("name", ""),
                        annotation=p.get("annotation"),
                        default_value=p.get("default_value"),
                        kind=p.get("kind"),
                    )
                    for p in metadata.get("parameters", [])
                ]
                signature = SignatureInfo(
                    name=symbol.symbol_name,
                    parameters=parameters,
                    return_annotation=metadata.get("return_annotation"),
                    line_start=symbol.lineno,
                    line_end=None,
                )

        symbol_data = SymbolData(
            file_path=symbol.file_path,
            symbol_name=symbol.symbol_name,
            symbol_type=symbol.symbol_type,
            signature=signature,
            docstring=symbol.docstring,
            is_public=True,  # Assume public for now
        )
        symbol_data_list.append(symbol_data)

    return RunArtifact(
        run_id=run.id,
        repo=run.repo,
        branch=run.branch,
        commit_sha=run.commit_sha,
        symbols=symbol_data_list,
    )


def detect_and_persist_changes(
    run_id: int,
    repo: str,
    branch: str,
    commit_sha: str,
    db: Session,
) -> None:
    """Detect changes by comparing with previous run and persist them.

    Args:
        run_id: Current run ID
        repo: Repository name
        branch: Branch name
        commit_sha: Commit SHA
        db: Database session
    """
    # Load current run and symbols
    run = db.get(Run, run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    current_symbols = (
        db.execute(
            select(PythonSymbol).where(PythonSymbol.run_id == run_id)
        )
        .scalars()
        .all()
    )

    # Build current artifact from symbols
    current_artifact = build_artifact_from_symbols(run, list(current_symbols))

    # Find previous run for same repo/branch
    previous_run = (
        db.execute(
            select(Run)
            .where(Run.repo == repo, Run.branch == branch, Run.id < run_id)
            .order_by(desc(Run.id))
            .limit(1)
        )
        .scalar_one_or_none()
    )

    previous_artifact = None
    if previous_run:
        try:
            previous_artifact = load_run_artifact(db, previous_run.id)
        except Exception as e:
            logger.warning(f"Could not load previous artifact: {e}")

    # Detect changes
    detected_changes = detect_changes(previous_artifact, current_artifact)

    # Persist changes
    if detected_changes:
        save_changes_to_database(db, run_id, detected_changes)
        db.commit()


def create_run_from_cli(
    commit_sha: str,
    repo: str,
    branch: str = "main",
    pr_id: str | None = None,
    is_dry_run: bool = False,
) -> int:
    """Create a run from CLI arguments and run full analysis pipeline.

    Args:
        commit_sha: Git commit SHA
        repo: Repository name/URL
        branch: Git branch name (default: "main")
        pr_id: Pull/Merge request ID (optional)
        is_dry_run: Whether this is a dry-run (default: False)

    Returns:
        The created run ID

    Raises:
        SystemExit: If run creation or analysis fails
    """
    db = SessionLocal()
    try:
        # Step 1: Create run
        correlation_id = generate_correlation_id()
        run = Run(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            started_at=datetime.now(timezone.utc),
            status="Processing",
            correlation_id=correlation_id,
            is_dry_run=is_dry_run,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

        print(f"Created run {run_id} (dry_run={is_dry_run})")

        # Step 2: Get changed files
        print("Getting changed files...")
        changed_files = get_changed_files(commit_sha)
        print(f"Found {len(changed_files)} changed file(s)")

        if not changed_files:
            print("No files changed, generating empty report")
            diffs = {}
            findings = {}
        else:
            # Step 3: Analyze files
            print("Analyzing files...")
            diffs, findings = analyze_files(run_id, changed_files, commit_sha, db)

            # Step 4: Detect and persist changes
            print("Detecting changes...")
            detect_and_persist_changes(run_id, repo, branch, commit_sha, db)

        # Step 5: Generate change report to ./artifacts/change_report.json
        print("Generating change report...")
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)

        # Generate report using the service (it creates run_id subdirectory)
        report_path = generate_change_report(
            run_id=str(run_id),
            diffs=diffs,
            findings=findings,
            is_dry_run=is_dry_run,
        )

        # Copy to blessed location: ./artifacts/change_report.json
        blessed_report_path = artifacts_dir / "change_report.json"
        with open(report_path) as f:
            report_data = json.load(f)
        # Add metadata from run
        report_data["metadata"] = {
            "run_id": run_id,
            "commit_sha": commit_sha,
            "repo": repo,
            "branch": branch,
            "pr_id": pr_id,
            "is_dry_run": is_dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(blessed_report_path, "w") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"Change report written to {blessed_report_path}")

        # Step 6: Generate patches
        print("Generating patches...")
        patches = []
        blessed_patches_path = None
        try:
            patches = generate_patches_for_run(db, run_id)
            db.commit()
            print(f"Generated {len(patches)} patch(es)")

            # Export patches artifact
            if patches:
                patches_path = export_patches_artifact(db, run_id)
                print(f"Patches exported to {patches_path}")

                # Copy to blessed location: ./artifacts/patches.json
                blessed_patches_dir = artifacts_dir / "patches"
                blessed_patches_dir.mkdir(exist_ok=True)
                blessed_patches_path = artifacts_dir / "patches.json"

                with open(patches_path) as f:
                    patches_data = json.load(f)
                with open(blessed_patches_path, "w") as f:
                    json.dump(patches_data, f, indent=2, ensure_ascii=False)
                print(f"Patches written to {blessed_patches_path}")
        except Exception as e:
            logger.warning(f"Patch generation failed: {e}", exc_info=True)
            print(f"Warning: Patch generation failed: {e}")

        # Update run status
        run.status = "Awaiting Review"
        db.commit()

        print(f"\nRun {run_id} completed successfully")
        print(f"Artifacts:")
        print(f"  - {blessed_report_path}")
        if blessed_patches_path:
            print(f"  - {blessed_patches_path}")

        return run_id
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        logger.exception("CLI execution failed")
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AutoDoc CLI - CI/CD integration (FR-1, FR-3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --commit abc123 --repo myorg/myrepo
  %(prog)s --commit abc123 --repo myorg/myrepo --branch dev --pr-id 42
  %(prog)s --commit abc123 --repo myorg/myrepo --dry-run

Outputs:
  - ./artifacts/change_report.json
  - ./artifacts/patches.json
        """,
    )

    parser.add_argument(
        "--commit",
        required=True,
        help="Git commit SHA to analyze (FR-1)",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name (e.g., owner/repo) (FR-1)",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch name (default: main) (FR-1)",
    )
    parser.add_argument(
        "--pr-id",
        help="Pull/Merge request ID (optional) (FR-1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate patches without updating Confluence (FR-14, UC-4)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_id = create_run_from_cli(
        commit_sha=args.commit,
        repo=args.repo,
        branch=args.branch,
        pr_id=args.pr_id,
        is_dry_run=args.dry_run,
    )

    print(f"\nRun ID: {run_id}")
    sys.exit(0)


if __name__ == "__main__":
    main()
