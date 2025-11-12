"""Confluence client for page CRUD operations.

This module wraps the Confluence REST API endpoints required for the AutoDoc
page management workflows.  It provides structured helper methods for
searching, retrieving, creating, and updating Confluence pages while
encapsulating authentication, error handling, and payload normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from autodoc.config.settings import ConfluenceSettings, get_settings


class ConfluenceError(Exception):
    """Base exception for Confluence client errors."""


class ConfluenceConfigurationError(ConfluenceError):
    """Raised when Confluence settings are missing or invalid."""


class ConfluenceHTTPError(ConfluenceError):
    """Raised when Confluence returns a non-successful HTTP status."""


@dataclass(slots=True)
class ConfluenceLink:
    """Hypermedia link returned by the Confluence API."""

    web_ui: str | None = None
    api: str | None = None


def _normalize_base_url(url: str) -> str:
    """Ensure the base Confluence URL is ready for REST calls."""
    return url.rstrip("/") + "/wiki/rest/api"


class ConfluenceClient:
    """Typed helper around the Confluence REST API."""

    def __init__(
        self,
        *,
        settings: ConfluenceSettings | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings or get_settings().confluence
        if not self._settings.is_configured:
            raise ConfluenceConfigurationError(
                "Confluence credentials are not configured. "
                "Set CONFLUENCE_URL, CONFLUENCE_USERNAME, and CONFLUENCE_TOKEN.",
            )

        base_url = _normalize_base_url(self._settings.url or "")
        auth = httpx.BasicAuth(
            self._settings.username or "",
            self._settings.token or "",
        )

        self._client = client or httpx.Client(
            base_url=base_url,
            auth=auth,
            timeout=self._settings.timeout,
            headers={"Content-Type": "application/json"},
        )

    #
    # Public API
    #
    def search_pages(
        self,
        query: str,
        *,
        space_key: str | None = None,
        limit: int = 25,
        start: int = 0,
    ) -> list[dict[str, Any]]:
        """Search pages using a CQL query."""
        cql_parts = ["type=page"]
        if space_key:
            cql_parts.append(f'space="{space_key}"')
        if query:
            cql_parts.append(f'text~"{query}"')
        cql = " AND ".join(cql_parts)

        response = self._client.get(
            "/content/search",
            params={
                "cql": cql,
                "limit": limit,
                "start": start,
                "expand": "version",
            },
        )
        self._raise_for_status(response, "Failed to search Confluence pages")

        data = response.json()
        results = data.get("results", [])
        return [self._normalise_page_payload(item) for item in results]

    def get_page(
        self,
        page_id: str,
        *,
        expand: tuple[str, ...] | list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a Confluence page by ID."""
        expand_param = ",".join(expand) if expand else "body.storage,version"
        response = self._client.get(
            f"/content/{page_id}",
            params={"expand": expand_param},
        )
        self._raise_for_status(response, f"Failed to retrieve page {page_id}")
        return self._normalise_page_payload(response.json())

    def create_page(
        self,
        *,
        space_key: str,
        title: str,
        body: str,
        representation: Literal["storage", "wiki"] = "storage",
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new Confluence page."""
        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": body,
                    "representation": representation,
                },
            },
        }

        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]

        response = self._client.post("/content", json=payload)
        self._raise_for_status(response, "Failed to create Confluence page")
        return self._normalise_page_payload(response.json())

    def update_page(
        self,
        page_id: str,
        *,
        title: str,
        body: str,
        representation: Literal["storage", "wiki"] = "storage",
        minor_edit: bool = False,
        message: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing Confluence page.

        The method fetches the current page version before issuing the update
        request to ensure optimistic concurrency expectations can be enforced.
        """
        current = self.get_page(page_id, expand=("version",))
        current_version = current.get("version", {}).get("number")
        if current_version is None:
            raise ConfluenceError(
                f"Page {page_id} does not expose a version number.",
            )

        payload: dict[str, Any] = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {
                "number": current_version,
                "minorEdit": minor_edit,
            },
            "body": {
                "storage": {
                    "value": body,
                    "representation": representation,
                },
            },
        }
        if message:
            payload["version"]["message"] = message

        response = self._client.put(f"/content/{page_id}", json=payload)
        self._raise_for_status(response, f"Failed to update page {page_id}")
        return self._normalise_page_payload(response.json())

    #
    # Housekeeping
    #
    def close(self) -> None:
        """Explicitly close the underlying HTTP client."""
        self._client.close()

    #
    # Internal helpers
    #
    @staticmethod
    def _raise_for_status(response: httpx.Response, detail: str) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ConfluenceHTTPError(
                f"{detail}: {exc.response.status_code} {exc.response.text}",
            ) from exc

    @staticmethod
    def _extract_links(payload: dict[str, Any]) -> ConfluenceLink:
        links = payload.get("_links", {}) or {}
        web_ui = links.get("webui")
        base = links.get("base")
        href = links.get("self")
        return ConfluenceLink(
            web_ui=f"{base}{web_ui}" if base and web_ui else web_ui,
            api=href,
        )

    def _normalise_page_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Normalise the Confluence page payload returned from API calls."""
        version = payload.get("version", {}) or {}
        body_data = payload.get("body", {}) or {}
        storage = body_data.get("storage", {}) or {}

        normalized: dict[str, Any] = {
            "id": payload.get("id"),
            "title": payload.get("title"),
            "type": payload.get("type"),
            "status": payload.get("status"),
            "space": payload.get("space"),
            "version": {
                "number": version.get("number"),
                "minorEdit": version.get("minorEdit"),
                "by": version.get("by"),
                "when": version.get("when"),
                "message": version.get("message"),
            },
            "body": {
                "storage": {
                    "value": storage.get("value"),
                    "representation": storage.get("representation"),
                },
            },
            "links": self._extract_links(payload).__dict__,
        }

        metadata = payload.get("metadata")
        if metadata:
            normalized["metadata"] = metadata

        return normalized


__all__ = [
    "ConfluenceClient",
    "ConfluenceConfigurationError",
    "ConfluenceError",
    "ConfluenceHTTPError",
]
