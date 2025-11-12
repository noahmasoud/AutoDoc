"""Unit tests for the Confluence client helper."""

from __future__ import annotations

import httpx
import pytest
from typing import cast

from autodoc.config.settings import ConfluenceSettings
from services.confluence_client import (
    ConfluenceClient,
    ConfluenceConflictError,
    ConfluenceError,
)


class FakeHttpClient:
    """Minimal httpx.Client stand-in for unit testing."""

    def __init__(
        self,
        base_url: str,
        *,
        get_responses: list[dict] | None = None,
        put_responses: list[dict] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._get_responses = get_responses or []
        self._put_responses = put_responses or []
        self.put_history: list[tuple[str, dict | None]] = []

    def _make_response(self, method: str, path: str, payload: dict) -> httpx.Response:
        status = payload.get("status", 200)
        request = httpx.Request(method, f"{self.base_url}{path}")
        response_kwargs = {}
        if "json" in payload:
            response_kwargs["json"] = payload["json"]
        if "text" in payload:
            response_kwargs["text"] = payload["text"]
        return httpx.Response(status, request=request, **response_kwargs)

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        del params  # not needed for tests
        if not self._get_responses:
            raise AssertionError("Unexpected GET request")
        payload = self._get_responses.pop(0)
        return self._make_response("GET", path, payload)

    def put(self, path: str, json: dict | None = None) -> httpx.Response:
        self.put_history.append((path, json))
        if not self._put_responses:
            raise AssertionError("Unexpected PUT request")
        payload = self._put_responses.pop(0)
        return self._make_response("PUT", path, payload)

    def delete(self, path: str, params: dict | None = None) -> httpx.Response:
        del params
        return self._make_response("DELETE", path, {"status": 204})

    def close(self) -> None:  # pragma: no cover - required by ConfluenceClient
        """Compatibility with httpx.Client interface."""


def _make_settings(max_retries: int = 0) -> ConfluenceSettings:
    return ConfluenceSettings(
        url="https://example.atlassian.net",
        username="user@example.com",
        token="api-token",
        max_retries=max_retries,
    )


def _base_url(settings: ConfluenceSettings) -> str:
    if settings.url is None:
        raise AssertionError("settings.url must be configured for tests")
    return settings.url.rstrip("/") + "/wiki/rest/api"


def _page_payload(version_number: int) -> dict:
    return {
        "id": "123",
        "title": "Sample Page",
        "type": "page",
        "status": "current",
        "version": {"number": version_number},
        "body": {
            "storage": {
                "value": "<p>Body</p>",
                "representation": "storage",
            },
        },
    }


def _make_confluence_client(
    settings: ConfluenceSettings,
    fake_http_client: FakeHttpClient,
) -> ConfluenceClient:
    client = ConfluenceClient(settings=settings)
    real_http_client = client._client
    client._client = cast("httpx.Client", fake_http_client)
    real_http_client.close()
    return client


def test_update_page_increments_version_number() -> None:
    settings = _make_settings(max_retries=0)
    fake_client = FakeHttpClient(
        _base_url(settings),
        get_responses=[
            {"json": _page_payload(3)},
        ],
        put_responses=[
            {"json": _page_payload(4)},
        ],
    )

    client = _make_confluence_client(settings, fake_client)

    result = client.update_page(
        "123",
        title="Sample Page",
        body="<p>Updated body</p>",
    )

    assert fake_client.put_history  # ensure request was sent
    _, payload = fake_client.put_history[0]
    assert payload is not None
    assert payload["version"]["number"] == 4
    assert result["version"]["number"] == 4


def test_update_page_retries_on_conflict_and_succeeds() -> None:
    settings = _make_settings(max_retries=2)
    fake_client = FakeHttpClient(
        _base_url(settings),
        get_responses=[
            {"json": _page_payload(1)},
            {"json": _page_payload(2)},
        ],
        put_responses=[
            {"status": 409, "text": "Conflict"},
            {"json": _page_payload(3)},
        ],
    )

    client = _make_confluence_client(settings, fake_client)

    result = client.update_page(
        "123",
        title="Sample Page",
        body="<p>Updated body</p>",
    )

    assert len(fake_client.put_history) == 2
    # First attempt should target version 2, second attempt version 3.
    first_payload = fake_client.put_history[0][1]
    second_payload = fake_client.put_history[1][1]
    assert first_payload is not None
    assert first_payload["version"]["number"] == 2
    assert second_payload is not None
    assert second_payload["version"]["number"] == 3
    assert result["version"]["number"] == 3


def test_update_page_conflict_exhausts_retries() -> None:
    settings = _make_settings(max_retries=1)
    fake_client = FakeHttpClient(
        _base_url(settings),
        get_responses=[
            {"json": _page_payload(5)},
            {"json": _page_payload(6)},
        ],
        put_responses=[
            {"status": 409, "text": "Conflict"},
            {"status": 409, "text": "Conflict"},
        ],
    )

    client = _make_confluence_client(settings, fake_client)

    with pytest.raises(ConfluenceConflictError):
        client.update_page(
            "123",
            title="Sample Page",
            body="<p>Updated body</p>",
        )

    assert len(fake_client.put_history) == 2


def test_update_page_requires_version_metadata() -> None:
    settings = _make_settings(max_retries=0)
    fake_client = FakeHttpClient(
        _base_url(settings),
        get_responses=[
            {"json": {"id": "123", "title": "No version metadata"}},
        ],
        put_responses=[],
    )

    client = _make_confluence_client(settings, fake_client)

    with pytest.raises(ConfluenceError):
        client.update_page(
            "123",
            title="Sample Page",
            body="<p>Updated body</p>",
        )

    assert not fake_client.put_history
