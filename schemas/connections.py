"""Pydantic schemas for Confluence connections."""

from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ConnectionBase(BaseModel):
    """Base schema for connection data."""

    confluence_base_url: str = Field(..., description="Confluence base URL")
    space_key: str = Field(..., min_length=1, description="Confluence space key")

    @field_validator("confluence_base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate and normalize URL."""
        if not v:
            raise ValueError("Confluence base URL cannot be empty")
        # Remove trailing slash
        return v.rstrip("/")


class ConnectionCreate(ConnectionBase):
    """Schema for creating a new connection."""

    api_token: str = Field(..., min_length=1, description="API token (plain text)")


class ConnectionUpdate(BaseModel):
    """Schema for updating a connection (all fields optional)."""

    confluence_base_url: str | None = Field(None, description="Confluence base URL")
    space_key: str | None = Field(None, min_length=1, description="Confluence space key")
    api_token: str | None = Field(
        None, min_length=1, description="API token (only sent if updating)"
    )

    @field_validator("confluence_base_url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate and normalize URL."""
        if v is not None and v:
            return v.rstrip("/")
        return v


class ConnectionOut(ConnectionBase):
    """Schema for connection output (never includes token)."""

    id: int
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestRequest(BaseModel):
    """Schema for testing a connection."""

    confluence_base_url: str
    space_key: str
    api_token: str

    @field_validator("confluence_base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate and normalize URL."""
        if not v:
            raise ValueError("Confluence base URL cannot be empty")
        return v.rstrip("/")


class ConnectionTestResponse(BaseModel):
    """Schema for connection test response."""

    success: bool
    message: str

