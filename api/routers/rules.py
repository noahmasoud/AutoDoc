from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.session import get_db
from db.models import Rule
from schemas.rules import RuleCreate, RuleUpdate, RuleOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db)):
    return db.execute(select(Rule).order_by(Rule.id)).scalars().all()


@router.post("", response_model=RuleOut, status_code=201)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    row = Rule(**payload.model_dump())
    db.add(row)
    db.flush()
    return row


@router.get("/{rule_id}", response_model=RuleOut)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    row = db.get(Rule, rule_id)
    if not row:
        raise HTTPException(404, "Rule not found")
    return row


@router.put("/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db)):
    row = db.get(Rule, rule_id)
    if not row:
        raise HTTPException(404, "Rule not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.add(row)
    db.flush()
    return row


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    row = db.get(Rule, rule_id)
    if not row:
        raise HTTPException(404, "Rule not found")
    db.delete(row)
    db.flush()
