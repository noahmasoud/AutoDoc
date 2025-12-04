from datetime import datetime
from pydantic import BaseModel


class RunCreate(BaseModel):
    repo: str
    branch: str
    commit_sha: str
    started_at: datetime
    correlation_id: str
    status: str = "Awaiting Review"
    mode: str = "PRODUCTION"  # defualt mode
    completed_at: datetime | None = None


class RunOut(BaseModel):
    id: int
    repo: str
    branch: str
    commit_sha: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    correlation_id: str
    mode: str  # NEW

    model_config = {"from_attributes": True}


class RunsPage(BaseModel):
    items: list[RunOut]
    page: int
    page_size: int
    total: int
