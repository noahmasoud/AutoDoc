import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Run
from db.session import get_db
from schemas.patches import PatchOut
from services.confluence_client import ConfluenceClient
from services.confluence_publisher import ConfluencePublisher

router = APIRouter(prefix="/patches", tags=["patches"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[PatchOut])
def list_patches(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(Patch).order_by(Patch.id)
    if run_id is not None:
        stmt = stmt.where(Patch.run_id == run_id)
    return db.execute(stmt).scalars().all()


@router.get("/{patch_id}", response_model=PatchOut)
def get_patch(patch_id: int, db: Session = Depends(get_db)):
    """Get a single patch by ID."""
    patch = db.get(Patch, patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")
    return patch


@router.post("/{patch_id}/apply", response_model=PatchOut)
def apply_patch(
    patch_id: int,
    approved_by: str | None = None,
    db: Session = Depends(get_db),
):
    """Apply a patch to Confluence.

    If the run has is_dry_run=True, skips Confluence REST calls but still
    updates the patch status to 'Applied'. This implements FR-14 and UC-4.

    Args:
        patch_id: The patch ID to apply
        approved_by: User who approved the patch (optional)
        db: Database session

    Returns:
        The updated patch

    Raises:
        HTTPException: If patch not found or application fails
    """
    patch = db.get(Patch, patch_id)
    if not patch:
        raise HTTPException(status_code=404, detail="Patch not found")

    # Get the run to check is_dry_run flag
    run = db.get(Run, patch.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Check if this is a dry-run
    if run.is_dry_run:
        logger.info(
            f"Skipping Confluence update for patch {patch_id} (dry-run mode)",
            extra={
                "patch_id": patch_id,
                "run_id": run.id,
                "is_dry_run": True,
            },
        )
        # Update patch status without calling Confluence
        patch.status = "Applied"
        patch.approved_by = approved_by
        patch.applied_at = datetime.now(UTC)
        db.commit()
        db.refresh(patch)
        return patch

    # Normal flow: apply patch to Confluence
    try:
        # Get Confluence client and publisher
        client = ConfluenceClient()
        publisher = ConfluencePublisher(client)

        # Get the rule to find space_key
        from db.models import Rule

        rule = (
            db.execute(select(Rule).where(Rule.page_id == patch.page_id))
            .scalars()
            .first()
        )

        if not rule:
            raise HTTPException(
                status_code=404,
                detail=f"Rule not found for page_id {patch.page_id}",
            )

        # Update the Confluence page
        update_payload = {
            "id": patch.page_id,
            "title": f"AutoDoc: {rule.name}",  # Use rule name as title
            "body": patch.diff_after,
            "representation": "storage",
        }

        result = publisher.update_page(update_payload)

        # Update patch status
        patch.status = "Applied"
        patch.approved_by = approved_by
        patch.applied_at = datetime.now(UTC)
        db.commit()
        db.refresh(patch)

        logger.info(
            f"Successfully applied patch {patch_id} to Confluence page {patch.page_id}",
            extra={
                "patch_id": patch_id,
                "page_id": patch.page_id,
                "run_id": run.id,
                "version": result.get("version"),
            },
        )

        client.close()
        return patch

    except Exception as e:
        db.rollback()
        logger.exception(
            f"Failed to apply patch {patch_id} to Confluence",
            extra={"patch_id": patch_id, "run_id": run.id},
        )
        patch.status = "ERROR"
        patch.error_message = {"error": str(e), "type": type(e).__name__}
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply patch to Confluence: {e}",
        ) from e
