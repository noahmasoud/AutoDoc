import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Run, Prompt
from db.session import get_db
from schemas.patches import LLMPatchSummaryResponse, PatchOut
from services.confluence_client import ConfluenceClient
from services.confluence_publisher import ConfluencePublisher

router = APIRouter(prefix="/patches", tags=["patches"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[PatchOut])
def list_patches(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(Patch).order_by(Patch.id)
    if run_id is not None:
        stmt = stmt.where(Patch.run_id == run_id)
    patches = db.execute(stmt).scalars().all()

    # Parse diff_structured from JSON string to dict for all patches
    import json

    for patch in patches:
        if patch.diff_structured and isinstance(patch.diff_structured, str):
            try:
                patch.diff_structured = json.loads(patch.diff_structured)
            except (json.JSONDecodeError, TypeError):
                patch.diff_structured = None

    return patches


@router.get("/summarize", response_model=LLMPatchSummaryResponse)
def summarize_patches_with_llm(
    run_id: int = Query(..., description="Run ID to summarize patches for"),
    prompt_id: int | None = Query(
        None,
        description="Optional prompt ID to use for summarization. If not provided, uses default prompt.",
    ),
    db: Session = Depends(get_db),
):
    """Generate LLM summary for patches in a run.

    This endpoint generates a summary of all patches for a run using Claude API.
    The summary is not automatically saved as an artifact unless explicitly requested.

    Args:
        run_id: The run ID to summarize
        prompt_id: Optional prompt ID to use. If not provided, uses the default prompt.
        db: Database session

    Returns:
        LLMPatchSummaryResponse with summary fields

    Raises:
        HTTPException: If run not found, no patches, prompt not found, or LLM API errors
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Load patches for the run
    patches = (
        db.execute(select(Patch).where(Patch.run_id == run_id).order_by(Patch.id))
        .scalars()
        .all()
    )

    if not patches:
        raise HTTPException(
            status_code=404, detail=f"No patches found for run {run_id}"
        )

    # Load prompt if provided, otherwise use None (will use default)
    prompt_content = None
    if prompt_id is not None:
        prompt = db.get(Prompt, prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=404, detail=f"Prompt with ID {prompt_id} not found"
            )
        if not prompt.is_active:
            raise HTTPException(
                status_code=400, detail=f"Prompt with ID {prompt_id} is not active"
            )
        prompt_content = prompt.content

    try:
        from services.llm_patch_summarizer import (
            LLMAPIError,
            LLMAPIKeyMissingError,
            LLMAPIQuotaExceededError,
            structure_patch_data_for_llm,
            summarize_patches_with_llm as generate_summary,
        )

        # Build patches data structure
        patches_data = []
        for patch in patches:
            patch_data = {
                "id": patch.id,
                "run_id": patch.run_id,
                "page_id": patch.page_id,
                "status": patch.status,
                "diff_before": patch.diff_before,
                "diff_after": patch.diff_after,
                "approved_by": patch.approved_by,
                "applied_at": patch.applied_at.isoformat()
                if patch.applied_at
                else None,
                "error_message": patch.error_message,
            }
            patches_data.append(patch_data)

        patches_json = {
            "run_id": run_id,
            "repo": run.repo,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "is_dry_run": run.is_dry_run,
            "patches_count": len(patches),
            "patches": patches_data,
        }

        structured_request = structure_patch_data_for_llm(patches_json)
        summary = generate_summary(structured_request, prompt_template=prompt_content)

        return LLMPatchSummaryResponse(
            summary=summary.summary,
            changes_description=summary.changes_description,
            demo_api_explanation=summary.demo_api_explanation,
            formatted_output=summary.formatted_output,
        )

    except LLMAPIKeyMissingError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except LLMAPIQuotaExceededError as e:
        raise HTTPException(
            status_code=429, detail=f"LLM API quota exceeded: {e}"
        ) from e
    except LLMAPIError as e:
        raise HTTPException(status_code=500, detail=f"LLM API error: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error generating LLM summary for run {run_id}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {e}"
        ) from e


@router.get("/{patch_id}", response_model=PatchOut)
def get_patch(patch_id: int, db: Session = Depends(get_db)):
    """Get a single patch by ID."""
    try:
        patch = db.get(Patch, patch_id)
        if not patch:
            raise HTTPException(status_code=404, detail="Patch not found")

        # Ensure diff_structured is a dict, not a string
        # SQLite JSON columns sometimes return strings instead of dicts
        import json

        if patch.diff_structured and isinstance(patch.diff_structured, str):
            try:
                patch.diff_structured = json.loads(patch.diff_structured)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, set to None
                patch.diff_structured = None

        return patch
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting patch {patch_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve patch: {e}",
        ) from e


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
        # Load connection from database
        from db.models import Connection
        from core.encryption import decrypt_token
        from autodoc.config.settings import ConfluenceSettings, get_settings

        connection = db.execute(select(Connection).limit(1)).scalar_one_or_none()
        if not connection:
            raise HTTPException(
                status_code=404,
                detail="No Confluence connection found. Please configure a connection first.",
            )

        # Get app settings
        app_settings = get_settings()

        # Try to decrypt the token from database, fallback to settings token
        try:
            decrypted_token = decrypt_token(connection.encrypted_token)
        except Exception as e:
            logger.warning(f"Failed to decrypt database token, falling back to settings: {e}")
            # Fallback to settings token if database token can't be decrypted
            decrypted_token = app_settings.confluence.token
            if not decrypted_token:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to decrypt connection token and no fallback token in settings: {e}",
                ) from e

        # For Confluence Cloud, username MUST be the email address, not the token
        # Use CONFLUENCE_USERNAME from settings, or raise error if not set
        username = app_settings.confluence.username
        if not username:
            raise HTTPException(
                status_code=500,
                detail="CONFLUENCE_USERNAME is required for Confluence API authentication. "
                "Please set CONFLUENCE_USERNAME in your .env file with your Confluence email address.",
            )

        confluence_settings = ConfluenceSettings(
            url=connection.confluence_base_url,
            username=username,  # Must be email address for Confluence Cloud
            token=decrypted_token,
            space_key=connection.space_key,
            timeout=app_settings.confluence.timeout,
            max_retries=app_settings.confluence.max_retries,
        )

        # Get Confluence client and publisher with database connection settings
        client = ConfluenceClient(settings=confluence_settings)
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
        # Note: ConfluenceClient.update_page expects keyword arguments, not a dict
        # The publisher.update_page accepts a dict but needs to extract the args
        # For now, call the client directly with the correct signature
        result = client.update_page(
            page_id=patch.page_id,
            title=f"AutoDoc: {rule.name}",  # Use rule name as title
            body=patch.diff_after,
            representation="storage",
        )

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


class PublishSummaryRequest(BaseModel):
    """Request model for manual LLM summary publishing."""

    strategy: str = "append_to_patches"


@router.get("/llm-summary-artifact/{run_id}")
def get_llm_summary_artifact(run_id: int, db: Session = Depends(get_db)):
    """Retrieve the LLM summary artifact JSON file for a run.

    This endpoint returns the llm_summary.json artifact file that contains the
    LLM-generated summary for all patches in the run.

    Args:
        run_id: The run ID
        db: Database session

    Returns:
        LLM summary artifact JSON data

    Raises:
        HTTPException: If run not found or artifact doesn't exist
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Try to load the LLM summary artifact file
    summary_path = Path("artifacts") / str(run_id) / "llm_summary.json"

    if not summary_path.exists():
        # Try to generate it if it doesn't exist
        try:
            from services.llm_summary_artifact_exporter import (
                export_llm_summary_artifact,
            )

            result_path = export_llm_summary_artifact(db, run_id)
            # If generation failed (e.g., API key missing), result_path will be None
            if result_path is None or not summary_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"LLM summary artifact not available for run {run_id}. "
                    "This may be due to missing API key, quota exceeded, or other error. "
                    "Check server logs for details.",
                )
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=404,
                detail=f"LLM summary artifact not found for run {run_id} and could not be generated: {exc!s}",
            ) from exc

    try:
        with summary_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to read LLM summary artifact: {exc!s}"
        ) from exc


@router.post("/publish-summary/{run_id}")
def publish_llm_summary(
    run_id: int,
    request: PublishSummaryRequest = PublishSummaryRequest(),
    db: Session = Depends(get_db),
):
    """Manually trigger LLM summary publishing to Confluence.

    This endpoint allows manual publishing of LLM summaries to Confluence pages.
    The summary must already exist as an artifact (use /patches/llm-summary-artifact/{run_id}
    to generate it first if needed).

    Args:
        run_id: The run ID to publish summary for
        request: Publishing request with strategy
        db: Database session

    Returns:
        Dictionary with publishing results

    Raises:
        HTTPException: If run not found, artifact missing, or publishing fails
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        from services.llm_summary_publisher import publish_llm_summary_to_confluence

        result = publish_llm_summary_to_confluence(
            db, run_id, strategy=request.strategy
        )

        if result.get("skipped"):
            return {
                "success": True,
                "message": f"Publishing skipped: {result.get('reason', 'unknown')}",
                **result,
            }

        if result.get("success"):
            return {
                "success": True,
                "message": f"Successfully published LLM summary to {len(result.get('pages_updated', []))} page(s)",
                **result,
            }
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish summary: {result.get('errors', ['Unknown error'])}",
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"LLM summary artifact not found. Generate it first using GET /patches/llm-summary-artifact/{run_id}",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception(f"Failed to publish LLM summary for run {run_id}")
        raise HTTPException(
            status_code=500, detail=f"Failed to publish summary: {e}"
        ) from e
