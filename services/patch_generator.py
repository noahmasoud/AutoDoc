"""Service for generating patches from file changes using rule engine.

This module integrates the rule engine to map changed files to Confluence pages
and generate patches for documentation updates.
"""

import logging
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Change, Patch, Rule, Run
from services.change_persister import get_changes_for_run
from services.rule_engine import (
    InvalidTargetError,
    resolve_target_page,
)

logger = logging.getLogger(__name__)


class PatchGenerationError(Exception):
    """Raised when patch generation fails."""


def generate_patches_for_run(  # noqa: PLR0915
    db: Session,
    run_id: int,
) -> list[Patch]:
    """Generate patches for a run based on file changes and rules.

    This function:
    1. Retrieves all changes for the run
    2. Gets all active rules from the database
    3. Maps each changed file to a Confluence page using the rule engine
    4. Generates patch content for each file/page mapping
    5. Saves patches to the database

    Args:
        db: Database session
        run_id: ID of the run to generate patches for

    Returns:
        List of created Patch database records

    Raises:
        PatchGenerationError: If patch generation fails
    """
    try:
        # Verify run exists
        run = db.get(Run, run_id)
        if not run:
            raise PatchGenerationError(f"Run {run_id} not found")

        logger.info(
            f"Starting patch generation for run {run_id}",
            extra={"run_id": run_id},
        )

        # Get all changes for this run
        changes = get_changes_for_run(db, run_id)
        if not changes:
            logger.info(
                f"No changes found for run {run_id}, no patches to generate",
                extra={"run_id": run_id},
            )
            return []

        # Get all active rules from database
        rules = db.execute(select(Rule)).scalars().all()
        if not rules:
            logger.warning(
                "No rules found in database, cannot generate patches",
                extra={"run_id": run_id},
            )
            return []

        logger.info(
            f"Found {len(changes)} changes and {len(rules)} rules",
            extra={
                "run_id": run_id,
                "change_count": len(changes),
                "rule_count": len(rules),
            },
        )

        # Group changes by file path (multiple symbols can change in same file)
        changes_by_file: dict[str, list[Change]] = defaultdict(list)
        for change in changes:
            changes_by_file[change.file_path].append(change)

        # Generate patches for each unique file
        patches_created = []
        files_with_patches = set()
        files_without_rules = []

        for file_path, file_changes in changes_by_file.items():
            try:
                # Use rule engine to resolve target page
                matching_rule = resolve_target_page(file_path, list(rules))

                if not matching_rule:
                    files_without_rules.append(file_path)
                    logger.debug(
                        f"No matching rule for file: {file_path}",
                        extra={"run_id": run_id, "file_path": file_path},
                    )
                    continue

                # Generate patch content
                # For now, create a simple patch with change summary
                # Template rendering can be added later
                diff_before = _generate_before_content(file_changes)
                diff_after = _generate_after_content(file_changes, matching_rule)

                # Create patch record
                patch = Patch(
                    run_id=run_id,
                    page_id=matching_rule.page_id,
                    diff_before=diff_before,
                    diff_after=diff_after,
                    status="Proposed",
                )
                db.add(patch)
                patches_created.append(patch)
                files_with_patches.add(file_path)

                logger.info(
                    f"Generated patch for file {file_path} -> page {matching_rule.page_id}",
                    extra={
                        "run_id": run_id,
                        "file_path": file_path,
                        "page_id": matching_rule.page_id,
                        "rule_id": matching_rule.id,
                        "rule_name": matching_rule.name,
                    },
                )

            except InvalidTargetError as e:
                logger.warning(
                    f"Invalid target configuration for file {file_path}: {e}",
                    extra={"run_id": run_id, "file_path": file_path},
                )
                continue
            except Exception as e:
                logger.exception(
                    f"Error generating patch for file {file_path}: {e}",
                    extra={"run_id": run_id, "file_path": file_path},
                )
                # Continue with other files even if one fails
                continue

        # Commit all patches at once
        if patches_created:
            db.commit()

            # Refresh records to get IDs
            for patch in patches_created:
                db.refresh(patch)

            logger.info(
                f"Successfully generated {len(patches_created)} patches for run {run_id}",
                extra={
                    "run_id": run_id,
                    "patch_count": len(patches_created),
                    "files_with_patches": len(files_with_patches),
                    "files_without_rules": len(files_without_rules),
                },
            )
        else:
            logger.info(
                f"No patches generated for run {run_id}",
                extra={
                    "run_id": run_id,
                    "files_without_rules": len(files_without_rules),
                },
            )

        # Update run status if no patches were generated
        if not patches_created and files_without_rules:
            if run.status == "Awaiting Review":
                run.status = "Completed (no patches)"
                db.commit()
                logger.info(
                    f"Updated run {run_id} status to 'Completed (no patches)'",
                    extra={"run_id": run_id},
                )

        return patches_created

    except PatchGenerationError:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(
            f"Error generating patches for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        raise PatchGenerationError(f"Failed to generate patches: {e}") from e


def _generate_before_content(changes: list[Change]) -> str:
    """Generate 'before' content for a patch.

    Args:
        changes: List of changes for a file

    Returns:
        String representation of the before state
    """
    lines = ["# Before Changes", ""]
    for change in changes:
        if change.change_type == "removed":
            lines.append(f"- **{change.symbol}** (removed)")
        elif change.change_type == "modified":
            lines.append(f"- **{change.symbol}** (modified)")
            if change.signature_before:
                lines.append(f"  - Previous: {change.signature_before}")
    return "\n".join(lines)


def _generate_after_content(changes: list[Change], rule: Rule) -> str:
    """Generate 'after' content for a patch.

    Args:
        changes: List of changes for a file
        rule: The matching rule for this file

    Returns:
        String representation of the after state
    """
    lines = ["# After Changes", ""]
    lines.append(f"**File:** `{changes[0].file_path}`")
    lines.append(f"**Target Page:** {rule.page_id}")
    lines.append(f"**Rule:** {rule.name}")
    lines.append("")

    for change in changes:
        if change.change_type == "added":
            lines.append(f"- **{change.symbol}** (added)")
        elif change.change_type == "modified":
            lines.append(f"- **{change.symbol}** (modified)")
            if change.signature_after:
                lines.append(f"  - New: {change.signature_after}")
        elif change.change_type == "removed":
            lines.append(f"- **{change.symbol}** (removed)")

    lines.append("")
    lines.append("---")
    lines.append("*This patch was automatically generated by AutoDoc*")

    return "\n".join(lines)
