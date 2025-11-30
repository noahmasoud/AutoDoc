from pydantic import BaseModel, Field


class TemplateBase(BaseModel):
    name: str
    format: str = Field(..., description="Template format: 'Markdown' or 'Storage'")
    body: str = Field(..., description="Template body with placeholders")
    variables: dict | None = Field(
        None, description="Documented variables (metadata only)"
    )


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: str | None = None
    format: str | None = None
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
