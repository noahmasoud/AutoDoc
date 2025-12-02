from pydantic import BaseModel, Field
from typing import Literal


class TemplateBase(BaseModel):
    name: str
    format: Literal["Markdown", "Storage"] = Field(
        description="Template format: 'Markdown' for markdown templates, 'Storage' for Confluence Storage Format"
    )
    body: str = Field(description="Template body/content with placeholder variables")
    variables: dict | None = Field(
        default=None, description="Optional variables documentation/metadata"
    )


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    format: Literal["Markdown", "Storage"] | None = None
    body: str | None = None
    variables: dict | None = None


class TemplateOut(TemplateBase):
    id: int

    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    """Request model for template preview."""

    template_id: int | None = None
    template_body: str | None = None
    template_format: str | None = None
    variables: dict = Field(default_factory=dict)


class TemplatePreviewResponse(BaseModel):
    """Response model for template preview."""

    rendered: str
    template_id: int | None = None
