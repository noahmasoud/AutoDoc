"""Pydantic schemas for Confluence page operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field


class ConfluenceLinkModel(BaseModel):
    """Hypermedia links for a Confluence page."""

    web_ui: str | None = Field(default=None, alias="webUI")
    api: str | None = Field(default=None)

    model_config = {"allow_population_by_field_name": True}


if TYPE_CHECKING:
    from datetime import datetime


class PageVersion(BaseModel):
    """Represents the version information of a Confluence page."""

    number: int
    minor_edit: bool | None = Field(default=None, alias="minorEdit")
    when: datetime | None = None
    message: str | None = None

    model_config = {"allow_population_by_field_name": True}


class PageBodyStorage(BaseModel):
    """Storage representation for Confluence page body."""

    value: str
    representation: str = "storage"


class PageBody(BaseModel):
    """Container model for Confluence page body payload."""

    storage: PageBodyStorage


class PageCreate(BaseModel):
    """Schema for creating a Confluence page."""

    space: str
    title: str
    body: str
    parent_id: str | None = Field(default=None, alias="parentId")
    representation: str = "storage"

    model_config = {"allow_population_by_field_name": True}


class PageUpdate(BaseModel):
    """Schema for updating a Confluence page."""

    title: str
    body: str
    representation: str = "storage"
    minor_edit: bool = Field(default=False, alias="minorEdit")
    message: str | None = None

    model_config = {"allow_population_by_field_name": True}


class PageOut(BaseModel):
    """Schema representing a Confluence page response."""

    id: str
    title: str
    status: str | None = None
    body: PageBody
    version: PageVersion
    space: dict[str, Any] | None = None
    links: ConfluenceLinkModel | None = None

    model_config = {"from_attributes": True}


class PageSearchResult(BaseModel):
    """Single search hit for Confluence pages."""

    id: str
    title: str
    version: PageVersion | None = None
    links: ConfluenceLinkModel | None = None

    model_config = {"from_attributes": True}


class PageSearchResponse(BaseModel):
    """Collection of search results."""

    query: str
    items: list[PageSearchResult]
    limit: int
    start: int


class PageDeleteResponse(BaseModel):
    """Response payload for page deletion."""

    page_id: str
    status: str = "deleted"
