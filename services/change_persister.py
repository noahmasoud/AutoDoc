"""Service for persisting detected changes to the database."""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Change
from schemas.changes import ChangeDetected


logger = logging.getLogger(__name__)


class ChangePersistenceError(Exception):
    """Raised when change persistence fails."""


def save_changes_to_database(
    db: Session,
    run_id: int,
    changes: list[ChangeDetected],
) -> list[Change]:
    """Save detected changes to the database.

    This function converts ChangeDetected objects into Change database records
    and persists them with proper tagging as added, removed, or modified.

    Args:
        db: Database session
        run_id: ID of the run these changes belong to
        changes: List of detected changes to save

    Returns:
        List of created Change database records

    Raises:
        ChangePersistenceError: If persistence fails
    """
    try:
        if not changes:
            logger.info(
                "No changes to save",
                extra={"run_id": run_id},
            )
            return []

        logger.info(
            f"Saving {len(changes)} changes to database",
            extra={
                "run_id": run_id,
                "total_changes": len(changes),
                "added": sum(1 for c in changes if c.change_type == "added"),
                "removed": sum(1 for c in changes if c.change_type == "removed"),
                "modified": sum(1 for c in changes if c.change_type == "modified"),
            },
        )

        # Convert ChangeDetected to Change database records
        change_records = []
        for change_detected in changes:
            change_record = Change(
                run_id=run_id,
                file_path=change_detected.file_path,
                symbol=change_detected.symbol_name,
                change_type=change_detected.change_type,
                signature_before=change_detected.signature_before,
                signature_after=change_detected.signature_after,
            )
            change_records.append(change_record)
            db.add(change_record)

        # Commit all changes at once
        db.commit()

        # Refresh records to get IDs
        for change_record in change_records:
            db.refresh(change_record)

        logger.info(
            f"Successfully saved {len(change_records)} changes",
            extra={"run_id": run_id},
        )

        return change_records

    except Exception as e:
        db.rollback()
        logger.exception(
            f"Error saving changes to database: {e}",
            extra={"run_id": run_id},
        )
        raise ChangePersistenceError(f"Failed to save changes: {e}") from e


def get_changes_for_run(
    db: Session,
    run_id: int,
) -> list[Change]:
    """Retrieve all changes for a specific run.

    Args:
        db: Database session
        run_id: ID of the run to get changes for

    Returns:
        List of Change database records

    Raises:
        ChangePersistenceError: If retrieval fails
    """
    try:
        logger.debug(
            f"Retrieving changes for run {run_id}",
            extra={"run_id": run_id},
        )

        changes = (
            db.execute(select(Change).where(Change.run_id == run_id)).scalars().all()
        )

        logger.info(
            f"Retrieved {len(changes)} changes for run {run_id}",
            extra={"run_id": run_id, "change_count": len(changes)},
        )

        return list(changes)

    except Exception as e:
        logger.exception(
            f"Error retrieving changes for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        raise ChangePersistenceError(f"Failed to retrieve changes: {e}") from e


def get_changes_by_type(
    db: Session,
    run_id: int,
    change_type: str,
) -> list[Change]:
    """Retrieve changes of a specific type for a run.

    Args:
        db: Database session
        run_id: ID of the run to get changes for
        change_type: Type of changes to retrieve ('added', 'removed', 'modified')

    Returns:
        List of Change database records

    Raises:
        ChangePersistenceError: If retrieval fails
    """
    try:
        if change_type not in ("added", "removed", "modified"):
            raise ValueError(
                f"Invalid change_type: {change_type}. "
                "Must be 'added', 'removed', or 'modified'",
            )

        logger.debug(
            f"Retrieving {change_type} changes for run {run_id}",
            extra={"run_id": run_id, "change_type": change_type},
        )

        changes = (
            db.execute(
                select(Change).where(
                    Change.run_id == run_id,
                    Change.change_type == change_type,
                ),
            )
            .scalars()
            .all()
        )

        logger.info(
            f"Retrieved {len(changes)} {change_type} changes for run {run_id}",
            extra={
                "run_id": run_id,
                "change_type": change_type,
                "change_count": len(changes),
            },
        )

        return list(changes)

    except ValueError:
        raise
    except Exception as e:
        logger.exception(
            f"Error retrieving {change_type} changes for run {run_id}: {e}",
            extra={"run_id": run_id, "change_type": change_type},
        )
        raise ChangePersistenceError(f"Failed to retrieve changes: {e}") from e
