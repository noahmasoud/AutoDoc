from datetime import datetime
from pydantic import BaseModel


class PatchBase(BaseModel):
    run_id: int
    file_path: str
    diff_text: str


class PatchCreate(PatchBase):
    pass


class PatchUpdate(BaseModel):
    run_id: int | None = None
    file_path: str | None = None
    diff_text: str | None = None


class PatchOut(PatchBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
