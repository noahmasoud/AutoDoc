from pydantic import BaseModel, Field
from datetime import datetime


class PromptBase(BaseModel):
    name: str = Field(description="Prompt name/identifier")
    content: str = Field(description="Prompt template content with placeholders")
    is_default: bool = Field(default=False, description="Whether this is a default system prompt")
    is_active: bool = Field(default=True, description="Whether prompt is available for use")


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_active: bool | None = None


class PromptOut(PromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

