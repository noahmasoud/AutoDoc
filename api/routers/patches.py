from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.session import get_db
from db.models import Patch
from schemas.patches import PatchOut

router = APIRouter(prefix="/patches", tags=["patches"])


@router.get("", response_model=list[PatchOut])
def list_patches(run_id: int | None = Query(None), db: Session = Depends(get_db)):
    stmt = select(Patch).order_by(Patch.id)
    if run_id is not None:
        stmt = stmt.where(Patch.run_id == run_id)
    return db.execute(stmt).scalars().all()
