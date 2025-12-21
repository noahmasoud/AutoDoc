from pydantic import BaseModel, field_validator
from typing import Literal


class RuleBase(BaseModel):
    name: str
    selector: str
    space_key: str
    page_id: str
    template_id: int | None = None
    prompt_id: int | None = None
    auto_approve: bool = False
    priority: int = 0
    update_strategy: Literal["replace", "append", "modify_section"] = "replace"

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate priority is non-negative."""
        if v < 0:
            raise ValueError("Priority must be non-negative")
        return v

    @field_validator("page_id", "space_key")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate page_id and space_key are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("update_strategy")
    @classmethod
    def validate_update_strategy(cls, v: str) -> str:
        """Validate update_strategy is one of the allowed values."""
        if v not in ("replace", "append", "modify_section"):
            raise ValueError("update_strategy must be 'replace', 'append', or 'modify_section'")
        return v


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    selector: str | None = None
    space_key: str | None = None
    page_id: str | None = None
    template_id: int | None = None
    prompt_id: int | None = None
    auto_approve: bool | None = None
    priority: int | None = None
    update_strategy: Literal["replace", "append", "modify_section"] | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int | None) -> int | None:
        """Validate priority is non-negative."""
        if v is not None and v < 0:
            raise ValueError("Priority must be non-negative")
        return v

    @field_validator("page_id", "space_key")
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Validate page_id and space_key are not empty if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty")
        return v.strip() if v else None


class RuleOut(RuleBase):
    id: int

    model_config = {"from_attributes": True}
