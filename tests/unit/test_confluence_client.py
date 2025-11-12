"""Tests for the Confluence client service."""

from __future__ import annotations

import base64

import httpx
import pytest

from autodoc.config.settings import ConfluenceSettings
from services.confluence_client import (
    ConfluenceClient,
    ConfluenceConfigurationError,
    ConfluenceRequestError,
)


@pytest.fixture
def confluence_settings() -> ConfluenceSettings:
    return ConfluenceSettings(
        url="https://example.atlassian.net/wiki",
        username="user@example.com",
        token="token123",
        timeout=5,
        max_retries=0,
    )


def _make_mock_transport(handler):
    """Helper to create a mock transport with the internal signature."""

    def factory(**_: int):
        return httpx.MockTransport(handler)

    return factory


def test_confluence_client_requires_configuration(
    confluence_settings: ConfluenceSettings,
) -> None:
    incomplete_settings = ConfluenceSettings(
        url=None,
        username=confluence_settings.username,
        token=confluence_settings.token,
    )

    with pytest.raises(ConfluenceConfigurationError):
        ConfluenceClient(settings=incomplete_settings)

    missing_token = ConfluenceSettings(
        url=confluence_settings.url,
        username=confluence_settings.username,
        token=None,
    )

    with pytest.raises(ConfluenceConfigurationError):
        ConfluenceClient(settings=missing_token)


def test_confluence_client_builds_basic_auth_header(
    monkeypatch: pytest.MonkeyPatch,
    confluence_settings: ConfluenceSettings,
) -> None:
    captured_header: dict[str, str | None] = {"Authorization": None}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_header["Authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"results": []})

    fake_transport_factory = _make_mock_transport(handler)
    monkeypatch.setattr(
        "services.confluence_client.httpx.HTTPTransport", fake_transport_factory
    )

    client = ConfluenceClient(settings=confluence_settings)
    client.get("/rest/api/space")

    expected = base64.b64encode(
        f"{confluence_settings.username}:{confluence_settings.token}".encode(),
    ).decode()

    assert captured_header["Authorization"] == f"Basic {expected}"


def test_confluence_connectivity_check_success(
    monkeypatch: pytest.MonkeyPatch,
    confluence_settings: ConfluenceSettings,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/rest/api/space")
        return httpx.Response(200, json={"results": []})

    fake_transport_factory = _make_mock_transport(handler)
    monkeypatch.setattr(
        "services.confluence_client.httpx.HTTPTransport", fake_transport_factory
    )

    client = ConfluenceClient(settings=confluence_settings)
    assert client.check_connectivity() is True


def test_confluence_request_raises_for_error_status(
    monkeypatch: pytest.MonkeyPatch,
    confluence_settings: ConfluenceSettings,
) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "server"})

    fake_transport_factory = _make_mock_transport(handler)
    monkeypatch.setattr(
        "services.confluence_client.httpx.HTTPTransport", fake_transport_factory
    )

    client = ConfluenceClient(settings=confluence_settings)

    with pytest.raises(ConfluenceRequestError) as exc_info:
        client.get("/rest/api/space")

    assert exc_info.value.status_code == 500
