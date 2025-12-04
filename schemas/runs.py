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
    is_dry_run: bool = False  # From SCRUM-49
    mode: str = "PRODUCTION"  # From SCRUM-51
    completed_at: datetime | None = None


class RunOut(BaseModel):
    id: int
    repo: str
    branch: str
    commit_sha: str
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    correlation_id: str
    is_dry_run: bool = False  # From SCRUM-49
    mode: str  # From SCRUM-51
    description: str | None = None

    model_config = {"from_attributes": True}

    @property
    def display_status(self) -> str:
        """Get display-friendly status that includes dry-run indication."""
        base_status = self.status
        if self.is_dry_run:
            return f"{base_status} (Dry Run)"
        return base_status

    @property
    def run_type_label(self) -> str:
        """Get a label indicating the run type for UI display."""
        return "Dry Run" if self.is_dry_run else "Normal Run"


class RunsPage(BaseModel):
    items: list[RunOut]
    page: int
    page_size: int
    total: int