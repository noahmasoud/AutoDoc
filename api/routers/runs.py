import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.session import get_db
from db.models import Run, PythonSymbol
from schemas.runs import RunCreate, RunOut, RunsPage
from schemas.symbols import PythonSymbolList
from services.change_report_generator import generate_change_report
from services.patch_generator import (
    PatchGenerationError,
    generate_patches_for_run,
)

router = APIRouter(prefix="/runs", tags=["runs"])


class ChangeReportRequest(BaseModel):
    """Request model for change report generation."""

    diffs: dict
    findings: dict


class ChangeReportResponse(BaseModel):
    """Response model for change report generation."""

    report_path: str


@router.get("", response_model=RunsPage)
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Run)) or 0
    items = (
        db.execute(
            select(Run)
            .order_by(Run.id.desc())
            .limit(page_size)
            .offset((page - 1) * page_size),
        )
        .scalars()
        .all()
    )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    row = db.get(Run, run_id)
    if not row:
        raise HTTPException(404, "Run not found")
    return row


@router.post("", response_model=RunOut, status_code=201)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    from datetime import datetime, UTC
    import uuid

    # Set defaults for optional fields
    run_data = payload.model_dump(exclude_unset=True)
    if run_data.get("started_at") is None:
        run_data["started_at"] = datetime.now(UTC)
    if run_data.get("correlation_id") is None:
        run_data["correlation_id"] = str(uuid.uuid4())

    row = Run(**run_data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{run_id}/report")
def get_run_report(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve the change report for a run.

    Args:
        run_id: The run ID
        db: Database session

    Returns:
        ChangeReport JSON data

    Raises:
        HTTPException: If the run is not found or report doesn't exist
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Try to load the report file
    report_path = Path("artifacts") / str(run_id) / "change_report.json"

    if not report_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Change report not found for run {run_id}"
        )

    try:
        with report_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to read change report: {exc!s}"
        ) from exc


@router.post("/{run_id}/report", response_model=ChangeReportResponse)
def generate_run_report(
    run_id: int,
    payload: ChangeReportRequest,
    db: Session = Depends(get_db),
):
    """Generate a change report for a run.

    Args:
        run_id: The run ID
        payload: Request containing diffs and findings
        db: Database session

    Returns:
        ChangeReportResponse with the path to the generated JSON file

    Raises:
        HTTPException: If the run is not found
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Generate the change report
    report_path = generate_change_report(
        run_id=str(run_id),
        diffs=payload.diffs,
        findings=payload.findings,
    )

    return ChangeReportResponse(report_path=report_path)


@router.get("/{run_id}/python-symbols", response_model=PythonSymbolList)
def list_python_symbols(run_id: int, db: Session = Depends(get_db)):
    """List persisted Python symbols (including docstrings) for a run."""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    symbols = db.scalars(
        select(PythonSymbol)
        .where(PythonSymbol.run_id == run_id)
        .order_by(
            PythonSymbol.file_path,
            PythonSymbol.symbol_type,
            PythonSymbol.qualified_name,
        ),
    ).all()

    return {"items": symbols}


@router.post("/{run_id}/generate-patches", response_model=dict)
def generate_patches(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Generate patches for a run based on file changes and rules.

    This endpoint uses the rule engine to map changed files to Confluence pages
    and generates patches for documentation updates. Patches are automatically
    exported as JSON artifacts for download from CI/CD.

    Args:
        run_id: The run ID
        db: Database session

    Returns:
        Dictionary with patch generation results

    Raises:
        HTTPException: If the run is not found or patch generation fails
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    try:
        patches = generate_patches_for_run(db, run_id)

        return {
            "run_id": run_id,
            "patches_generated": len(patches),
            "patches": [
                {
                    "id": patch.id,
                    "page_id": patch.page_id,
                    "status": patch.status,
                }
                for patch in patches
            ],
        }
    except PatchGenerationError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{run_id}/patches-artifact")
def get_patches_artifact(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve the patches artifact JSON file for a run.

    This endpoint returns the patches.json artifact file that contains all
    patches generated for the run. This is especially useful for dry-run mode
    where patches are generated but not applied to Confluence.

    Args:
        run_id: The run ID
        db: Database session

    Returns:
        Patches artifact JSON data

    Raises:
        HTTPException: If the run is not found or artifact doesn't exist
    """
    # Verify run exists
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Try to load the patches artifact file
    patches_path = Path("artifacts") / str(run_id) / "patches.json"

    if not patches_path.exists():
        # Try to generate it if it doesn't exist
        try:
            from services.patches_artifact_exporter import export_patches_artifact

            export_patches_artifact(db, run_id)
        except Exception as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Patches artifact not found for run {run_id} and could not be generated: {exc!s}",
            ) from exc

    try:
        with patches_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to read patches artifact: {exc!s}"
        ) from exc
