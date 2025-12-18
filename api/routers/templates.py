from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.session import get_db
from db.models import Template
from schemas.templates import (
    TemplateCreate,
    TemplateUpdate,
    TemplateOut,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from autodoc.templates.engine import (
    MissingVariableError,
    TemplateEngine,
    TemplateError,
    TemplateSyntaxError,
    UnsupportedFormatError,
)


def _prepare_template_variables(
    template_body: str,
    provided_variables: dict | None,
) -> dict | None:
    """Prepare template variables, auto-extracting if not provided.

    If variables are explicitly provided, use them. Otherwise, extract
    variable names from the template body.

    Args:
        template_body: Template body content
        provided_variables: Variables provided by user (can be None)

    Returns:
        Variables dictionary or None
    """
    if provided_variables is not None:
        # User provided variables explicitly - use them
        return provided_variables

    # Auto-extract variables from template body
    extracted = TemplateEngine.extract_variables(template_body)

    # Return None if no variables found, otherwise return extracted
    return extracted if extracted else None


router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.execute(select(Template).order_by(Template.id)).scalars().all()


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new template.

    If variables are not provided, they will be automatically extracted
    from the template body.
    """
    template_data = payload.model_dump()

    # Auto-extract variables if not provided
    template_data["variables"] = _prepare_template_variables(
        template_data["body"],
        template_data.get("variables"),
    )

    row = Template(**template_data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    row = db.get(Template, template_id)
    if not row:
        raise HTTPException(404, "Template not found")
    return row


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing template.

    If body is updated and variables are not explicitly provided, variables
    will be auto-extracted from the new template body.
    """
    row = db.get(Template, template_id)
    if not row:
        raise HTTPException(404, "Template not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If body is being updated and variables not explicitly provided, extract them
    if "body" in update_data and "variables" not in update_data:
        update_data["variables"] = _prepare_template_variables(
            update_data["body"],
            None,  # No variables provided, extract from body
        )
    elif "variables" in update_data:
        # Variables explicitly provided - use them as-is
        pass

    for k, v in update_data.items():
        setattr(row, k, v)

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    try:
        row = db.get(Template, template_id)
        if not row:
            raise HTTPException(404, "Template not found")
        db.delete(row)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DELETE ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(500, f"Delete failed: {e!s}") from e


@router.post("/preview", response_model=TemplatePreviewResponse)
def preview_template(request: TemplatePreviewRequest, db: Session = Depends(get_db)):
    """Preview a template with variable substitution.

    Per FR-20: Template preview functionality for testing templates
    before saving or applying them.

    Args:
        request: Preview request with template and variables
        db: Database session

    Returns:
        Rendered template content

    Raises:
        HTTPException: If template_id is provided but template not found
        ValueError: If template format is invalid
    """
    engine = TemplateEngine()

    # If template_id is provided, load from database
    if request.template_id:
        template = db.get(Template, request.template_id)
        if not template:
            raise HTTPException(404, "Template not found")
        template_body = template.body
        template_format = template.format
    elif request.template_body and request.template_format:
        # Use provided template body and format
        template_body = request.template_body
        template_format = request.template_format
    else:
        raise HTTPException(
            400,
            "Either template_id or both template_body and template_format must be provided",
        )

    # Render template
    try:
        rendered = TemplateEngine.render(
            template_body, template_format, request.variables
        )
    except (
        UnsupportedFormatError,
        TemplateSyntaxError,
        MissingVariableError,
        TemplateError,
    ) as e:
        raise HTTPException(400, str(e)) from e

    return TemplatePreviewResponse(rendered=rendered, template_id=request.template_id)
