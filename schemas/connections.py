"""Pydantic schemas for Confluence connections."""

from datetime import datetime
from pydantic import BaseModel, AnyHttpUrl, Field


class ConnectionCreate(BaseModel):
    """Request payload for creating/updating a connection."""

    confluence_base_url: AnyHttpUrl = Field(..., description="Confluence base URL")
    space_key: str = Field(..., min_length=1, description="Confluence space key")
    api_token: str = Field(..., min_length=1, description="Confluence API token")


class ConnectionOut(BaseModel):
    """Response payload for connection (without token)."""

    id: int
    confluence_base_url: str
    space_key: str
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

