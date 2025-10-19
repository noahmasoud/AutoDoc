from datetime import datetime
from pydantic import BaseModel


class RuleBase(BaseModel):
    name: str
    pattern: str
    is_active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    pattern: str | None = None
    is_active: bool | None = None


class RuleOut(RuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
