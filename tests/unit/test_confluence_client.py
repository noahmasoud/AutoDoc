"""Unit tests for the Confluence client."""

from __future__ import annotations

import json
from typing import Any, Callable

import httpx
import pytest

from services.confluence_client import ConfluenceClient, ConfluenceError


def create_client(
    response_handler: Callable[[httpx.Request], httpx.Response],
    *,
    max_retries: int = 3,
) -> ConfluenceClient:
    transport = httpx.MockTransport(response_handler)
    return ConfluenceClient(
        base_url="https://example.atlassian.net",
        username="user@example.com",
        token="token",
        api_prefix="/rest/api",
        max_retries=max_retries,
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


def test_search_pages_fetch_all_aggregates_results() -> None:
    responses = {
        0: {
            "results": [{"id": "1", "title": "Doc 1"}],
            "size": 1,
            "limit": 1,
            "start": 0,
            "totalSize": 2,
            "_links": {
                "self": "/rest/api/content/search?start=0",
                "next": "/rest/api/content/search?start=1",
            },
        },
        1: {
            "results": [{"id": "2", "title": "Doc 2"}],
            "size": 1,
            "limit": 1,
            "start": 1,
            "totalSize": 2,
            "_links": {"self": "/rest/api/content/search?start=1"},
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/rest/api/content/search"
        params = httpx.QueryParams(request.url.query.decode())
        assert params["cql"] == 'space="DOCS"'
        start = int(params.get("start", "0"))
        assert params["limit"] == "1"
        return httpx.Response(200, json=responses[start])

    with create_client(handler) as client:
        result = client.search_pages('space="DOCS"', limit=1)

    titles = [entry["title"] for entry in result["results"]]
    assert titles == ["Doc 1", "Doc 2"]
    assert result["total"] == 2
    assert result["next_start"] is None


def test_search_pages_single_page_when_fetch_all_disabled() -> None:
    page = {
        "results": [{"id": "99", "title": "Single Page"}],
        "size": 1,
        "limit": 25,
        "start": 10,
        "totalSize": 50,
        "_links": {"self": "/rest/api/content/search?start=10"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        params = httpx.QueryParams(request.url.query.decode())
        assert params["cql"] == 'title ~ "Single"'
        assert params["start"] == "10"
        return httpx.Response(200, json=page)

    with create_client(handler) as client:
        result = client.search_pages('title ~ "Single"', start=10, fetch_all=False)

    assert result["results"][0]["id"] == "99"
    assert result["start"] == 10
    assert result["next_start"] is None
    assert result["is_last_page"] is True


def test_search_pages_respects_max_results_cap() -> None:
    responses = {
        0: {
            "results": [{"id": "1"}, {"id": "2"}],
            "size": 2,
            "limit": 2,
            "start": 0,
            "totalSize": 5,
            "_links": {
                "self": "/rest/api/content/search?start=0",
                "next": "/rest/api/content/search?start=2",
            },
        },
        2: {
            "results": [{"id": "3"}, {"id": "4"}],
            "size": 2,
            "limit": 2,
            "start": 2,
            "totalSize": 5,
            "_links": {
                "self": "/rest/api/content/search?start=2",
                "next": "/rest/api/content/search?start=4",
            },
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        params = httpx.QueryParams(request.url.query.decode())
        start = int(params.get("start", "0"))
        return httpx.Response(200, json=responses[start])

    with create_client(handler) as client:
        result = client.search_pages("type=page", limit=2, max_results=3)

    ids = [entry["id"] for entry in result["results"]]
    assert ids == ["1", "2", "3"]
    assert result["next_start"] == 4


def test_request_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["count"] += 1
        if call_count["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(
            200,
            json={"results": [], "size": 0, "limit": 25, "start": 0},
        )

    slept: list[float] = []
    monkeypatch.setattr("services.confluence_client.time.sleep", slept.append)

    with create_client(handler, max_retries=2) as client:
        result = client.search_pages("type=page", fetch_all=False)

    assert result["results"] == []
    assert call_count["count"] == 2
    assert slept == [0.0]


def test_limit_validation() -> None:
    with create_client(lambda _request: httpx.Response(200, json={})) as client:
        with pytest.raises(ValueError):
            client.search_pages("type=page", limit=0)


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
