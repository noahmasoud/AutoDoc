"""Pydantic schemas for LLM configuration."""

from datetime import datetime
from pydantic import BaseModel, Field


class LLMConfigCreate(BaseModel):
    """Request payload for creating/updating LLM configuration."""

    model: str = Field(..., min_length=1, description="LLM model name (e.g., claude-sonnet-4-20250514)")
    api_key: str = Field(..., min_length=1, description="LLM API key")


class LLMConfigTestRequest(BaseModel):
    """Request payload for testing LLM configuration."""

    model: str = Field(..., min_length=1, description="LLM model name")
    api_key: str = Field(..., min_length=1, description="LLM API key")


class LLMConfigTestResponse(BaseModel):
    """Response payload for LLM configuration test."""

    ok: bool
    details: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class LLMConfigOut(BaseModel):
    """Response payload for LLM configuration (without API key)."""

    id: int
    model: str
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

