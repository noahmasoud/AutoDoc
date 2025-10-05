from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.session import get_db
from db.models import Run
from schemas.runs import RunCreate, RunOut, RunsPage

router = APIRouter(prefix="/runs", tags=["runs"])


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
    row = Run(**payload.model_dump(exclude_unset=True))
    db.add(row)
    db.flush()
    return row
