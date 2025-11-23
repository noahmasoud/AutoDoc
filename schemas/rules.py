from pydantic import BaseModel


class RuleBase(BaseModel):
    name: str
    selector: str
    space_key: str
    page_id: str
    template_id: int | None = None
    auto_approve: bool = False
    priority: int = 0


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    selector: str | None = None
    space_key: str | None = None
    page_id: str | None = None
    template_id: int | None = None
    auto_approve: bool | None = None
    priority: int | None = None


class RuleOut(RuleBase):
    id: int

    model_config = {"from_attributes": True}
