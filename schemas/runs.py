from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    status: str | None = "created"
    description: str | None = None
    is_dry_run: bool = False


class RunOut(BaseModel):
    id: int
    status: str
    description: str | None = None
    created_at: datetime
    is_dry_run: bool = False

    model_config = {"from_attributes": True}


class RunsPage(BaseModel):
    items: list[RunOut]
    page: int
    page_size: int
    total: int
