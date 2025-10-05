from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.session import get_db
from db.models import Template
from schemas.templates import TemplateCreate, TemplateUpdate, TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.execute(select(Template).order_by(Template.id)).scalars().all()


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    row = Template(**payload.model_dump())
    db.add(row)
    db.flush()
    return row


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    row = db.get(Template, template_id)
    if not row:
        raise HTTPException(404, "Template not found")
    return row


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
):
    row = db.get(Template, template_id)
    if not row:
        raise HTTPException(404, "Template not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.add(row)
    db.flush()
    return row


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    row = db.get(Template, template_id)
    if not row:
        raise HTTPException(404, "Template not found")
    db.delete(row)
    db.flush()
