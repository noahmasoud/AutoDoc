from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    repo: str
    branch: str
    commit_sha: str
    started_at: datetime | None = None
    status: str = "Awaiting Review"
    correlation_id: str | None = None
    description: str | None = None
    is_dry_run: bool = False


class RunOut(BaseModel):
    id: int
    repo: str
    branch: str
    commit_sha: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    correlation_id: str
    is_dry_run: bool = False
    description: str | None = None

    model_config = {"from_attributes": True}


class RunsPage(BaseModel):
    items: list[RunOut]
    page: int
    page_size: int
    total: int
