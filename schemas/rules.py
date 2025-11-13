from pydantic import BaseModel, ConfigDict


class RuleBase(BaseModel):
    name: str
    selector: str
    space_key: str
    page_id: str
    template_id: int | None = None
    auto_approve: bool = False


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = None
    selector: str | None = None
    space_key: str | None = None
    page_id: str | None = None
    template_id: int | None = None
    auto_approve: bool | None = None


class RuleOut(RuleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
