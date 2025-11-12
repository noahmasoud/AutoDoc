"""Unit tests for the Confluence client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from services.confluence_client import ConfluenceClient, ConfluenceError


def create_client(response_handler) -> ConfluenceClient:
    transport = httpx.MockTransport(response_handler)
    return ConfluenceClient(
        base_url="https://example.atlassian.net",
        username="user@example.com",
        token="token",
        api_prefix="/rest/api",
        transport=transport,
    )


def assert_json_request(request: httpx.Request) -> dict[str, Any]:
    assert request.headers["Content-Type"] == "application/json"
    return json.loads(request.content.decode())


def test_get_page_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/rest/api/content/123"
        return httpx.Response(200, json={"id": "123", "title": "Test"})

    with create_client(handler) as client:
        response = client.get_page("123")

    assert response["id"] == "123"
    assert response["title"] == "Test"


def test_search_pages_with_title_query() -> None:
    expected = {
        "results": [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
        ],
        "size": 2,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/rest/api/content"
        assert request.url.params["title"] == "AutoDoc"
        assert request.url.params["limit"] == "10"
        return httpx.Response(200, json=expected)

    with create_client(handler) as client:
        response = client.search_pages("AutoDoc", limit=10)

    assert response == expected


def test_create_page_sends_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/rest/api/content"
        payload = assert_json_request(request)
        assert payload["title"] == "New Page"
        assert payload["space"]["key"] == "DOCS"
        assert payload["body"] == {"storage": {"value": "<p>Body</p>"}}
        assert payload["ancestors"] == [{"id": "100"}]
        return httpx.Response(200, json={"id": "123", "title": "New Page"})

    with create_client(handler) as client:
        response = client.create_page(
            title="New Page",
            space_key="DOCS",
            body={"storage": {"value": "<p>Body</p>"}},
            parent_id="100",
        )

    assert response["id"] == "123"


def test_update_page_sends_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PUT"
        assert request.url.path == "/rest/api/content/123"
        payload = assert_json_request(request)
        assert payload["title"] == "Updated"
        assert payload["body"] == {"storage": {"value": "<p>Updated</p>"}}
        assert payload["version"]["number"] == 2
        assert payload["version"]["minorEdit"] is True
        return httpx.Response(200, json={"id": "123", "title": "Updated"})

    with create_client(handler) as client:
        response = client.update_page(
            "123",
            title="Updated",
            body={"storage": {"value": "<p>Updated</p>"}},
            version=2,
            minor_edit=True,
        )

    assert response["id"] == "123"


def test_http_error_raises_confluence_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not found"})

    with create_client(handler) as client:
        with pytest.raises(ConfluenceError):
            client.get_page("missing")
