"""Service for exporting LLM summaries as JSON artifacts.

This module generates LLM summaries for patches and exports them as JSON artifact files,
which can be downloaded from CI/CD pipelines or used for automatic Confluence publishing.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Run
from services.llm_patch_summarizer import (
    LLMAPIKeyMissingError,
    LLMAPIError,
    LLMAPIQuotaExceededError,
    LLMPatchSummary,
    structure_patch_data_for_llm,
    summarize_patches_with_llm,
)

logger = logging.getLogger(__name__)


def export_llm_summary_artifact(
    db: Session,
    run_id: int,
) -> str | None:
    """Generate and export LLM summary as a JSON artifact file.

    This function:
    1. Retrieves patches for the run
    2. Calls LLM summarization service
    3. Saves summary to artifacts/<run_id>/llm_summary.json

    Args:
        db: Database session
        run_id: ID of the run to generate summary for

    Returns:
        Absolute path to the generated llm_summary.json file, or None if generation failed

    Raises:
        ValueError: If the run is not found
        OSError: If the directory cannot be created or file cannot be written
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise ValueError(f"Run {run_id} not found")

    # Load all patches for the run
    patches = (
        db.execute(select(Patch).where(Patch.run_id == run_id).order_by(Patch.id))
        .scalars()
        .all()
    )

    if not patches:
        logger.info(
            f"No patches found for run {run_id}, skipping LLM summary generation",
            extra={"run_id": run_id},
        )
        return None

    logger.info(
        f"Generating LLM summary for {len(patches)} patches in run {run_id}",
        extra={
            "run_id": run_id,
            "patch_count": len(patches),
            "is_dry_run": run.is_dry_run,
        },
    )

    # Build patches data structure (similar to patches_artifact_exporter)
    patches_data: list[dict[str, Any]] = []
    for patch in patches:
        patch_data = {
            "id": patch.id,
            "run_id": patch.run_id,
            "page_id": patch.page_id,
            "status": patch.status,
            "diff_before": patch.diff_before,
            "diff_after": patch.diff_after,
            "approved_by": patch.approved_by,
            "applied_at": patch.applied_at.isoformat() if patch.applied_at else None,
            "error_message": patch.error_message,
        }
        patches_data.append(patch_data)

    # Create patches data structure for LLM
    patches_json = {
        "run_id": run_id,
        "repo": run.repo,
        "branch": run.branch,
        "commit_sha": run.commit_sha,
        "is_dry_run": run.is_dry_run,
        "timestamp": datetime.now(UTC).isoformat(),
        "patches_count": len(patches),
        "patches": patches_data,
    }

    # Generate LLM summary
    try:
        structured_request = structure_patch_data_for_llm(patches_json)
        summary = summarize_patches_with_llm(structured_request)

        logger.info(
            f"Successfully generated LLM summary for run {run_id}",
            extra={"run_id": run_id},
        )

    except LLMAPIKeyMissingError as e:
        logger.warning(
            f"LLM API key not configured, skipping summary generation for run {run_id}: {e}",
            extra={"run_id": run_id},
        )
        return None

    except LLMAPIQuotaExceededError as e:
        logger.warning(
            f"LLM API quota exceeded for run {run_id}, skipping summary generation: {e}",
            extra={"run_id": run_id},
        )
        return None

    except LLMAPIError as e:
        logger.error(
            f"LLM API error for run {run_id}, skipping summary generation: {e}",
            extra={"run_id": run_id},
            exc_info=True,
        )
        return None

    except Exception as e:
        logger.error(
            f"Unexpected error generating LLM summary for run {run_id}: {e}",
            extra={"run_id": run_id},
            exc_info=True,
        )
        return None

    # Create artifacts directory structure: artifacts/<run_id>/
    artifacts_dir = Path("artifacts") / str(run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Create the LLM summary artifact JSON structure
    artifact = {
        "run_id": run_id,
        "repo": run.repo,
        "branch": run.branch,
        "commit_sha": run.commit_sha,
        "is_dry_run": run.is_dry_run,
        "timestamp": datetime.now(UTC).isoformat(),
        "generated_at": datetime.now(UTC).isoformat(),
        "patches_count": len(patches),
        "summary": {
            "summary": summary.summary,
            "changes_description": summary.changes_description,
            "demo_api_explanation": summary.demo_api_explanation,
            "formatted_output": summary.formatted_output,
        },
    }

    # Write JSON file
    summary_path = artifacts_dir / "llm_summary.json"
    try:
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Exported LLM summary artifact to {summary_path}",
            extra={
                "run_id": run_id,
                "summary_path": str(summary_path),
                "patches_count": len(patches),
            },
        )

        # Return absolute path as string
        return str(summary_path.absolute())

    except OSError as e:
        logger.error(
            f"Failed to write LLM summary artifact for run {run_id}: {e}",
            extra={"run_id": run_id, "path": str(summary_path)},
            exc_info=True,
        )
        raise

