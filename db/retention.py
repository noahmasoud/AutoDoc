"""
Database retention policy service.

Per SRS 7.2: Keep last 100 runs in local DB. Cascade deletes dependent rows.
"""

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session
from db.models import Run


def cleanup_old_runs(session: Session, keep_count: int = 100) -> int:
    """
    Remove old runs keeping only the most recent N runs.

    Per SRS 7.2: Keep last 100 runs in local DB. Deletes cascade to
    dependent Change and Patch rows via ON DELETE CASCADE.

    Args:
        session: SQLAlchemy session
        keep_count: Number of most recent runs to keep (default 100)

    Returns:
        Number of runs deleted

    Raises:
        ValueError: If keep_count is less than 1
    """
    if keep_count < 1:
        raise ValueError("keep_count must be at least 1")

    # Get total count of runs
    total_count = session.scalar(select(func.count()).select_from(Run))

    if total_count is None or total_count <= keep_count:
        return 0  # Nothing to delete

    # Get the ID of the Nth most recent run (the cutoff point)
    # We want to delete everything older than this
    cutoff_subquery = (
        select(Run.id)
        .order_by(Run.started_at.desc())
        .offset(keep_count)
        .limit(1)
        .scalar_subquery()
    )

    # Get list of IDs to delete (all runs older than the cutoff)
    ids_to_delete_query = (
        select(Run.id).where(Run.id <= cutoff_subquery).order_by(Run.id)
    )

    ids_to_delete = session.scalars(ids_to_delete_query).all()

    if not ids_to_delete:
        return 0

    # Delete runs older than the cutoff
    # CASCADE will automatically delete related Changes and Patches
    delete_count = session.execute(
        delete(Run).where(Run.id.in_(ids_to_delete)),
    ).rowcount

    session.commit()

    return delete_count


def get_run_count(session: Session) -> int:
    """
    Get the current count of runs in the database.

    Args:
        session: SQLAlchemy session

    Returns:
        Number of runs in the database
    """
    count = session.scalar(select(func.count()).select_from(Run))
    return count if count is not None else 0


def get_oldest_run_id(session: Session) -> int | None:
    """
    Get the ID of the oldest run in the database.

    Args:
        session: SQLAlchemy session

    Returns:
        ID of oldest run, or None if no runs exist
    """
    return session.scalar(
        select(Run.id).order_by(Run.started_at.asc()).limit(1),
    )


def get_newest_run_id(session: Session) -> int | None:
    """
    Get the ID of the newest run in the database.

    Args:
        session: SQLAlchemy session

    Returns:
        ID of newest run, or None if no runs exist
    """
    return session.scalar(
        select(Run.id).order_by(Run.started_at.desc()).limit(1),
    )
