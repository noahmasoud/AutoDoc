"""Confluence REST API client."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, ClassVar, Iterable, Mapping

import httpx


logger = logging.getLogger(__name__)


class ConfluenceError(Exception):
    """Base exception for Confluence client errors."""


class ConfluenceClient:
    """Confluence REST API client with retry-aware helpers."""

    BODY_REPRESENTATION_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "storage",
            "atlas_doc_format",
            "editor",
            "view",
            "export_view",
            "wiki",
        },
    )

    def __init__(
        self,
        base_url: str,
        username: str,
        token: str,
        *,
        api_prefix: str = "/wiki/rest/api",
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_prefix = self._normalize_prefix(api_prefix)
        self._max_retries = max(0, max_retries)
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
        self,
        page_id: str | int,
        *,
        expand: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a Confluence page by ID."""
        params = {}
        if expand:
            params["expand"] = ",".join(expand)
        return self._request("GET", f"/content/{page_id}", params=params)

    def search_pages(
        self,
        cql: str,
        *,
        limit: int = 25,
        start: int = 0,
        expand: Iterable[str] | None = None,
        cql_context: Mapping[str, Any] | None = None,
        include_archived: bool = False,
        fetch_all: bool = True,
        max_results: int | None = None,
    ) -> dict[str, Any]:
        """Search Confluence pages using the CQL API.

        Args:
            cql: Confluence Query Language expression.
            limit: Page size for each API call (max 250).
            start: Starting offset for results.
            expand: Fields to expand in the response.
            cql_context: Optional CQL context mapping.
            include_archived: Whether to include archived spaces.
            fetch_all: When True, automatically paginate through all results.
            max_results: Optional cap on the number of results returned.

        Returns:
            When fetch_all is True, returns a dictionary containing the aggregated
            results list, overall total (when provided by the API), and the next
            start offset if more results are available. When fetch_all is False,
            returns metadata for a single page of results with the same keys.
        """

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        def build_params(current_start: int) -> dict[str, Any]:
            params: dict[str, Any] = {
                "cql": cql,
                "limit": limit,
                "start": current_start,
                "includeArchivedSpaces": str(include_archived).lower(),
            }
            if expand:
                params["expand"] = ",".join(expand)
            if cql_context:
                params["cqlcontext"] = cql_context
            return params

        if not fetch_all:
            page = self._request("GET", "/content/search", params=build_params(start))
            return self._build_page_metadata(page, limit)

        aggregated_results: list[dict[str, Any]] = []
        total = None
        next_start = start

        while True:
            page = self._request(
                "GET", "/content/search", params=build_params(next_start)
            )
            page_meta = self._build_page_metadata(page, limit)

            aggregated_results.extend(page_meta["results"])
            total = page_meta["total"] if page_meta["total"] is not None else total

            if max_results is not None and len(aggregated_results) >= max_results:
                aggregated_results = aggregated_results[:max_results]
                next_start = page_meta["next_start"]
                break

            if page_meta["is_last_page"]:
                next_start = None
                break

            if page_meta["next_start"] is None:
                next_start = None
                break

            next_start = page_meta["next_start"]

        return {
            "results": aggregated_results,
            "total": total if total is not None else len(aggregated_results),
            "next_start": next_start,
        }

    def create_page(
        self,
        *,
        title: str,
        space_key: str,
        body: str | dict[str, Any],
        parent_id: str | int | None = None,
        representation: str = "storage",
        content_type: str | None = None,
        body_key: str | None = None,
    ) -> dict[str, Any]:
        """Create a Confluence page."""
        payload: dict[str, Any] = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": self.build_body(
                body,
                representation=representation,
                content_type=content_type,
                body_key=body_key,
            ),
        }
        if parent_id is not None:
            payload["ancestors"] = [{"id": str(parent_id)}]
        return self._request("POST", "/content", json=payload)

    def update_page(
        self,
        page_id: str | int,
        *,
        title: str,
        body: str | dict[str, Any],
        version: int,
        minor_edit: bool = False,
        representation: str = "storage",
        content_type: str | None = None,
        body_key: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing Confluence page."""
        payload: dict[str, Any] = {
            "id": str(page_id),
            "type": "page",
            "title": title,
            "body": self.build_body(
                body,
                representation=representation,
                content_type=content_type,
                body_key=body_key,
            ),
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
        attempt = 0
        while True:
            try:
                response = self._client.request(method, url, params=params, json=json)
                response.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code == 429 and attempt < self._max_retries:
                    wait_time = self._retry_after_seconds(exc.response)
                    logger.warning(
                        "Confluence API rate limited request; retrying",
                        extra={
                            "method": method,
                            "url": str(exc.request.url),
                            "retry_after": wait_time,
                            "attempt": attempt + 1,
                        },
                    )
                    time.sleep(wait_time)
                    attempt += 1
                    continue

                if status_code >= 500 and attempt < self._max_retries:
                    wait_time = self._backoff_seconds(attempt)
                    logger.warning(
                        "Confluence API temporary error; retrying",
                        extra={
                            "method": method,
                            "url": str(exc.request.url),
                            "status_code": status_code,
                            "retry_in": wait_time,
                            "attempt": attempt + 1,
                        },
                    )
                    time.sleep(wait_time)
                    attempt += 1
                    continue

                logger.error(
                    "Confluence API error",
                    extra={
                        "status_code": status_code,
                        "method": method,
                        "url": str(exc.request.url),
                        "body": json,
                    },
                )
                raise ConfluenceError(
                    f"Confluence API returned {status_code}: {exc.response.text}",
                ) from exc
            except httpx.HTTPError as exc:
                if attempt < self._max_retries:
                    wait_time = self._backoff_seconds(attempt)
                    logger.warning(
                        "Confluence API request failed; retrying",
                        extra={"method": method, "url": url, "error": str(exc)},
                    )
                    time.sleep(wait_time)
                    attempt += 1
                    continue

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

    @staticmethod
    def _retry_after_seconds(response: httpx.Response) -> float:
        header = response.headers.get("Retry-After")
        if not header:
            return 1.0
        try:
            return max(0.0, float(header))
        except ValueError:
            return 1.0

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        return min(2**attempt, 30.0)

    @staticmethod
    def _build_page_metadata(page: dict[str, Any], limit: int) -> dict[str, Any]:
        results = page.get("results", []) or []
        size = page.get("size", len(results))
        current_limit = page.get("limit", limit)
        start = page.get("start", 0)
        links = page.get("_links") or {}
        has_next_link = bool(links.get("next"))
        is_last_page = not has_next_link
        if not results or size < current_limit:
            is_last_page = True
        next_start = None if is_last_page else start + current_limit
        total = page.get("totalSize")

        return {
            "results": results,
            "start": start,
            "limit": current_limit,
            "size": size,
            "total": total,
            "next_start": next_start,
            "is_last_page": is_last_page,
            "links": links,
        }

    @staticmethod
    def build_body(
        body: str | dict[str, Any],
        *,
        representation: str = "storage",
        content_type: str | None = None,
        body_key: str | None = None,
    ) -> dict[str, Any]:
        """Return a Confluence body payload for the given content."""
        if isinstance(body, Mapping) and ConfluenceClient._looks_like_body(body):
            return dict(body)

        resolved_key = body_key or representation

        if representation == "atlas_doc_format" and not isinstance(body, str):
            value = json.dumps(body)
        elif isinstance(body, str):
            value = body
        else:
            value = json.dumps(body)

        payload: dict[str, Any] = {
            "value": value,
            "representation": representation,
        }

        if content_type:
            payload["contentType"] = content_type

        return {resolved_key: payload}

    @staticmethod
    def _looks_like_body(body: Mapping[str, Any]) -> bool:
        return any(key in ConfluenceClient.BODY_REPRESENTATION_KEYS for key in body)
