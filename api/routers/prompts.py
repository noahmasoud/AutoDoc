from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.session import get_db
from db.models import Prompt
from schemas.prompts import (
    PromptCreate,
    PromptUpdate,
    PromptOut,
)

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptOut])
def list_prompts(db: Session = Depends(get_db)):
    """List all prompts, ordered by default prompts first, then by name."""
    prompts = db.execute(select(Prompt).order_by(Prompt.is_default.desc(), Prompt.name)).scalars().all()
    return prompts


@router.post("", response_model=PromptOut, status_code=201)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)):
    """Create a new custom prompt.
    
    Users can create up to 10 custom prompts (non-default prompts).
    Default prompts cannot be created via API - they are system-managed.
    """
    if payload.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot create default prompts via API. Default prompts are system-managed."
        )
    
    # Check custom prompt limit (10 custom prompts max)
    custom_prompt_count = db.execute(
        select(func.count(Prompt.id)).where(Prompt.is_default == False)
    ).scalar()
    
    if custom_prompt_count >= 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum of 10 custom prompts allowed. Please delete an existing custom prompt first."
        )
    
    row = Prompt(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{prompt_id}", response_model=PromptOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """Get a single prompt by ID."""
    row = db.get(Prompt, prompt_id)
    if not row:
        raise HTTPException(404, "Prompt not found")
    return row


@router.put("/{prompt_id}", response_model=PromptOut)
def update_prompt(
    prompt_id: int,
    payload: PromptUpdate,
    db: Session = Depends(get_db),
):
    """Update a prompt.
    
    Default prompts can have their is_active status changed, but name and content cannot be modified.
    Custom prompts can be fully updated.
    """
    row = db.get(Prompt, prompt_id)
    if not row:
        raise HTTPException(404, "Prompt not found")
    
    # Default prompts: only allow updating is_active
    if row.is_default:
        if payload.name is not None or payload.content is not None:
            raise HTTPException(
                status_code=400,
                detail="Cannot modify name or content of default prompts. Only is_active can be changed."
            )
    
    # Apply updates
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(row, k, v)
    
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    """Delete a prompt.
    
    Default prompts cannot be deleted.
    """
    row = db.get(Prompt, prompt_id)
    if not row:
        raise HTTPException(404, "Prompt not found")
    
    if row.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default prompts. Only custom prompts can be deleted."
        )
    
    db.delete(row)
    db.commit()

