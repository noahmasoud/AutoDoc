"""FastAPI router providing Confluence page CRUD endpoints."""

from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.pages import (
    PageCreate,
    PageOut,
    PageSearchResponse,
    PageSearchResult,
    PageUpdate,
    PageDeleteResponse,
)
from services.confluence_client import (
    ConfluenceClient,
    ConfluenceConfigurationError,
    ConfluenceError,
    ConfluenceHTTPError,
)

router = APIRouter(prefix="/pages", tags=["pages"])


def get_confluence_client() -> Generator[ConfluenceClient, None, None]:
    """Dependency that yields a Confluence client instance."""
    try:
        client = ConfluenceClient()
    except ConfluenceError as exc:  # Configuration issues should surface early.
        raise translate_confluence_exception(exc) from exc

    try:
        yield client
    finally:
        client.close()


ConfluenceDep = Annotated[ConfluenceClient, Depends(get_confluence_client)]


def translate_confluence_exception(exc: ConfluenceError) -> HTTPException:
    """Translate low-level Confluence errors into HTTP responses."""
    if isinstance(exc, ConfluenceConfigurationError):
        return HTTPException(
            status_code=503,
            detail=(
                "Confluence integration is not configured. "
                "Please provide CONFLUENCE_URL, CONFLUENCE_USERNAME, and "
                "CONFLUENCE_TOKEN."
            ),
        )

    if isinstance(exc, ConfluenceHTTPError):
        return HTTPException(
            status_code=502,
            detail=str(exc),
        )

    return HTTPException(
        status_code=500,
        detail=str(exc),
    )


@router.get(
    "/search",
    response_model=PageSearchResponse,
    summary="Search Confluence pages",
)
def search_pages(
    query: Annotated[str, Query(alias="q", min_length=1)],
    client: ConfluenceDep,
    *,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    start: Annotated[int, Query(ge=0)] = 0,
    space_key: Annotated[str | None, Query(alias="spaceKey")] = None,
) -> PageSearchResponse:
    """Search for pages within Confluence using CQL text queries."""
    try:
        items = client.search_pages(
            query=query,
            space_key=space_key,
            limit=limit,
            start=start,
        )
    except ConfluenceError as exc:
        raise translate_confluence_exception(exc) from exc

    results = [PageSearchResult(**item) for item in items]
    return PageSearchResponse(
        query=query,
        items=results,
        limit=limit,
        start=start,
    )


@router.get(
    "/{page_id}",
    response_model=PageOut,
    summary="Retrieve a Confluence page",
)
def get_page(page_id: str, client: ConfluenceDep) -> PageOut:
    """Retrieve a single Confluence page by its identifier."""
    try:
        page = client.get_page(page_id)
    except ConfluenceError as exc:
        raise translate_confluence_exception(exc) from exc
    return PageOut(**page)


@router.post(
    "",
    response_model=PageOut,
    status_code=201,
    summary="Create a Confluence page",
)
def create_page(
    payload: PageCreate,
    client: ConfluenceDep,
) -> PageOut:
    """Create a new Confluence page in the configured space."""
    try:
        page = client.create_page(
            space_key=payload.space,
            title=payload.title,
            body=payload.body,
            representation=payload.representation,
            parent_id=payload.parent_id,
        )
    except ConfluenceError as exc:
        raise translate_confluence_exception(exc) from exc
    return PageOut(**page)


@router.put(
    "/{page_id}",
    response_model=PageOut,
    summary="Update a Confluence page",
)
def update_page(
    page_id: str,
    payload: PageUpdate,
    client: ConfluenceDep,
) -> PageOut:
    """Update content and metadata for an existing Confluence page."""
    try:
        page = client.update_page(
            page_id,
            title=payload.title,
            body=payload.body,
            representation=payload.representation,
            minor_edit=payload.minor_edit,
            message=payload.message,
        )
    except ConfluenceError as exc:
        raise translate_confluence_exception(exc) from exc
    return PageOut(**page)


@router.delete(
    "/{page_id}",
    response_model=PageDeleteResponse,
    summary="Delete a Confluence page",
)
def delete_page(page_id: str, client: ConfluenceDep) -> PageDeleteResponse:
    """Delete (or trash) a Confluence page by ID."""
    try:
        client.delete_page(page_id)
    except ConfluenceError as exc:
        raise translate_confluence_exception(exc) from exc
    return PageDeleteResponse(page_id=page_id, status="deleted")
