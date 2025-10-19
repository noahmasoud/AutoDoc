from datetime import datetime
from pydantic import BaseModel


class TemplateBase(BaseModel):
    name: str
    content: str


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


class TemplateOut(TemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
