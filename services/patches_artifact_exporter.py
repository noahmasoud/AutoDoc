"""Service for exporting patches as JSON artifacts.

This module exports patches generated for a run as a JSON artifact file,
which can be downloaded from CI/CD pipelines. This is especially important
for dry-run mode where patches are generated but not applied to Confluence.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import Patch, Run

logger = logging.getLogger(__name__)


def export_patches_artifact(
    db: Session,
    run_id: int,
) -> str:
    """Export patches for a run as a JSON artifact file.

    This function creates a patches.json file in the artifacts/<run_id>/ directory
    containing all patches generated for the run. This is useful for:
    - Dry-run mode: patches are generated but not applied, so they can be reviewed
    - CI/CD artifacts: patches can be downloaded and reviewed before approval

    Args:
        db: Database session
        run_id: ID of the run to export patches for

    Returns:
        Absolute path to the generated patches.json file

    Raises:
        OSError: If the directory cannot be created or file cannot be written
        ValueError: If the run is not found
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

    logger.info(
        f"Exporting {len(patches)} patches for run {run_id}",
        extra={
            "run_id": run_id,
            "patch_count": len(patches),
            "is_dry_run": run.is_dry_run,
        },
    )

    # Create artifacts directory structure: artifacts/<run_id>/
    artifacts_dir = Path("artifacts") / str(run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Build patches data structure
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

    # Create the patches artifact JSON structure
    artifact = {
        "run_id": run_id,
        "repo": run.repo,
        "branch": run.branch,
        "commit_sha": run.commit_sha,
        "is_dry_run": run.is_dry_run,
        "timestamp": datetime.now(UTC).isoformat(),
        "patches_count": len(patches),
        "patches": patches_data,
    }

    # Write JSON file
    patches_path = artifacts_dir / "patches.json"
    with patches_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Exported patches artifact to {patches_path}",
        extra={
            "run_id": run_id,
            "patches_path": str(patches_path),
            "patch_count": len(patches),
        },
    )

    # Return absolute path as string
    return str(patches_path.absolute())
