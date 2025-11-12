"""Confluence REST API client."""

from __future__ import annotations

import logging
from typing import Any, Iterable

import httpx


logger = logging.getLogger(__name__)


class ConfluenceError(Exception):
    """Base exception for Confluence client errors."""


class ConfluenceClient:
    """Simple Confluence REST API client."""

    def __init__(
        self,
        base_url: str,
        username: str,
        token: str,
        *,
        api_prefix: str = "/wiki/rest/api",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_prefix = self._normalize_prefix(api_prefix)
        self._client = httpx.Client(
            base_url=f"{self._base_url}{self._api_prefix}",
            auth=httpx.BasicAuth(username, token),
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            transport=transport,
        )

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        if not prefix:
            return ""
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix.rstrip("/")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "ConfluenceClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def get_page(
        self, page_id: str | int, *, expand: Iterable[str] | None = None
    ) -> dict[str, Any]:
        """Retrieve a Confluence page by ID."""
        params = {}
        if expand:
            params["expand"] = ",".join(expand)
        return self._request("GET", f"/content/{page_id}", params=params)

    def search_pages(
        self,
        query: str,
        *,
        limit: int = 25,
        start: int = 0,
        expand: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Search for Confluence pages matching the provided query."""
        params: dict[str, Any] = {
            "title": query,
            "limit": limit,
            "start": start,
            "type": "page",
        }
        if expand:
            params["expand"] = ",".join(expand)
        return self._request("GET", "/content", params=params)

    def create_page(
        self,
        *,
        title: str,
        space_key: str,
        body: dict[str, Any],
        parent_id: str | int | None = None,
    ) -> dict[str, Any]:
        """Create a Confluence page."""
        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": body,
        }
        if parent_id is not None:
            payload["ancestors"] = [{"id": str(parent_id)}]
        return self._request("POST", "/content", json=payload)

    def update_page(
        self,
        page_id: str | int,
        *,
        title: str,
        body: dict[str, Any],
        version: int,
        minor_edit: bool = False,
    ) -> dict[str, Any]:
        """Update an existing Confluence page."""
        payload: dict[str, Any] = {
            "id": str(page_id),
            "type": "page",
            "title": title,
            "body": body,
            "version": {
                "number": version,
                "minorEdit": minor_edit,
            },
        }
        return self._request("PUT", f"/content/{page_id}", json=payload)

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.request(method, url, params=params, json=json)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Confluence API error",
                extra={
                    "status_code": exc.response.status_code,
                    "method": method,
                    "url": str(exc.request.url),
                    "body": json,
                },
            )
            raise ConfluenceError(
                f"Confluence API returned {exc.response.status_code}: {exc.response.text}",
            ) from exc
        except httpx.HTTPError as exc:
            logger.error(
                "Confluence API request failed",
                extra={"method": method, "url": url, "error": str(exc)},
            )
            raise ConfluenceError(str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ConfluenceError(
                "Failed to decode Confluence response as JSON"
            ) from exc
