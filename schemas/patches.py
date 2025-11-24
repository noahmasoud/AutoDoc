from datetime import datetime
from pydantic import BaseModel


class PatchBase(BaseModel):
    run_id: int
    page_id: str
    diff_before: str
    diff_after: str


class PatchCreate(PatchBase):
    pass


class PatchUpdate(BaseModel):
    run_id: int | None = None
    page_id: str | None = None
    diff_before: str | None = None
    diff_after: str | None = None
    approved_by: str | None = None
    applied_at: datetime | None = None
    status: str | None = None


class PatchOut(PatchBase):
    id: int
    approved_by: str | None
    applied_at: datetime | None
    status: str

    model_config = {"from_attributes": True}
