"""Confluence REST API client service."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import Any

import httpx

from autodoc.config.settings import ConfluenceSettings, get_settings
from autodoc.logging.logger import StructuredLogger

LOGGER = StructuredLogger("autodoc.integrations.confluence")


class ConfluenceClientError(Exception):
    """Base class for Confluence client errors."""


class ConfluenceConfigurationError(ConfluenceClientError):
    """Raised when Confluence settings are missing or invalid."""


class ConfluenceRequestError(ConfluenceClientError):
    """Raised when a Confluence API request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


@dataclass(slots=True)
class ConfluenceAuth:
    """Encapsulates API token authentication header."""

    username: str
    token: str

    def build_header(self) -> str:
        """Return the Authorization header value for Basic auth."""
        credentials = f"{self.username}:{self.token}".encode()
        encoded = base64.b64encode(credentials).decode()
        return f"Basic {encoded}"


class ConfluenceClient:
    """Service for interacting with the Confluence REST API."""

    def __init__(
        self,
        settings: ConfluenceSettings | None = None,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings().confluence

        if not self.settings.url:
            raise ConfluenceConfigurationError("Confluence base URL is not configured.")

        if not self.settings.username or not self.settings.token:
            raise ConfluenceConfigurationError(
                "Confluence credentials are incomplete; username and token are required.",
            )

        self.base_url = self.settings.url.rstrip("/")
        self.auth = ConfluenceAuth(
            username=self.settings.username,
            token=self.settings.token,
        )
        self._client = client or self._create_http_client()

    def _create_http_client(self) -> httpx.Client:
        """Create an HTTPX client with default configuration."""
        headers: MutableMapping[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AutoDoc-ConfluenceClient/1.0",
            "Authorization": self.auth.build_header(),
        }

        timeout = httpx.Timeout(self.settings.timeout)
        transport = httpx.HTTPTransport(retries=self.settings.max_retries)

        return httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> ConfluenceClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        """Send an HTTP request to the Confluence API."""
        url_path = path if path.startswith("/") else f"/{path}"

        if headers is not None and not isinstance(headers, Mapping):
            headers = dict(headers)
        if params is not None and not isinstance(params, Mapping):
            params = dict(params)
        if json_body is not None and not isinstance(json_body, Mapping):
            json_body = dict(json_body)

        request_headers = dict(headers or {})
        if request_headers:
            combined_headers = self._client.headers.copy()
            combined_headers.update(request_headers)
        else:
            combined_headers = None

        LOGGER.log_api_request(method.upper(), url_path)

        try:
            response = self._client.request(
                method,
                url_path,
                params=params,
                json=json_body,
                headers=combined_headers,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            LOGGER.exception(
                "Confluence request failed with status code",
                method=method,
                path=url_path,
                status_code=exc.response.status_code,
                response_body=self._safe_response_body(exc.response),
            )
            raise ConfluenceRequestError(
                f"Confluence API request failed with status code {exc.response.status_code}",
                status_code=exc.response.status_code,
                response_text=self._safe_response_body(exc.response),
            ) from exc

        except httpx.HTTPError as exc:
            LOGGER.exception(
                "Confluence request encountered an HTTP error",
                method=method,
                path=url_path,
            )
            raise ConfluenceRequestError(
                "Confluence API request failed due to a network error.",
            ) from exc

        LOGGER.log_api_response(method.upper(), url_path, response.status_code)
        return response

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        """Execute a GET request."""
        return self.request("GET", path, params=params, headers=headers)

    def check_connectivity(self) -> bool:
        """Validate connectivity to Confluence."""
        response = self.get("/rest/api/space", params={"limit": 1})

        LOGGER.debug(
            "Confluence connectivity check succeeded",
            status_code=response.status_code,
        )
        return True

    @staticmethod
    def _safe_response_body(response: httpx.Response) -> str:
        """Safely extract response body for logging."""
        try:
            if not response.text:
                return ""
            parsed = response.json()
        except (json.JSONDecodeError, ValueError):
            return response.text[:1024]
        return json.dumps(parsed)[:1024]


def get_confluence_client() -> ConfluenceClient:
    """Factory helper to create a configured Confluence client."""
    return ConfluenceClient()
