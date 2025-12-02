"""CLI entrypoint for AutoDoc CI/CD integration.

This module provides a command-line interface for creating runs from CI/CD pipelines.
It accepts --commit, --repo, --branch, --pr-id, and --dry-run flags and creates
a Run entity in the database with the is_dry_run flag set appropriately.
"""

import argparse
import sys
from datetime import UTC, datetime

from db.models import Run
from db.session import SessionLocal
from autodoc.logging.correlation import generate_correlation_id


def create_run_from_cli(
    commit_sha: str,
    repo: str,
    branch: str = "main",
    pr_id: str | None = None,
    is_dry_run: bool = False,
) -> int:
    """Create a run from CLI arguments.

    Args:
        commit_sha: Git commit SHA
        repo: Repository name/URL
        branch: Git branch name (default: "main")
        pr_id: Pull/Merge request ID (optional)
        is_dry_run: Whether this is a dry-run (default: False)

    Returns:
        The created run ID

    Raises:
        SystemExit: If run creation fails
    """
    db = SessionLocal()
    try:
        correlation_id = generate_correlation_id()
        run = Run(
            repo=repo,
            branch=branch,
            commit_sha=commit_sha,
            started_at=datetime.now(UTC),
            status="Awaiting Review",
            correlation_id=correlation_id,
            is_dry_run=is_dry_run,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        print(f"Created run {run.id} (dry_run={is_dry_run})")
        return run.id
    except Exception as e:
        db.rollback()
        print(f"Error creating run: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="AutoDoc CLI - Create runs from CI/CD pipelines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --commit abc123 --repo myorg/myrepo
  %(prog)s --commit abc123 --repo myorg/myrepo --branch dev --pr-id 42
  %(prog)s --commit abc123 --repo myorg/myrepo --dry-run
        """,
    )

    parser.add_argument(
        "--commit",
        required=True,
        help="Git commit SHA to analyze",
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository name (e.g., owner/repo)",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch name (default: main)",
    )
    parser.add_argument(
        "--pr-id",
        help="Pull/Merge request ID (optional)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate patches without updating Confluence (FR-14, UC-4)",
    )

    args = parser.parse_args()

    run_id = create_run_from_cli(
        commit_sha=args.commit,
        repo=args.repo,
        branch=args.branch,
        pr_id=args.pr_id,
        is_dry_run=args.dry_run,
    )

    print(f"Run ID: {run_id}")
    sys.exit(0)


if __name__ == "__main__":
    main()
