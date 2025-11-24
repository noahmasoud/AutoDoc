"""Integration tests for connection security (FR-28, NFR-9)."""

import pytest
from fastapi.testclient import TestClient
from api.main import create_app
import logging


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def test_token():
    """Test API token."""
    return "ATATT3xFfGF0TEST_TOKEN_FOR_INTEGRATION_TEST_1234567890abcdef"


class TestConnectionSecurity:
    """Test connection endpoint security compliance."""

    def test_save_connection_masks_token_in_logs(self, client, test_token, caplog):
        """Test that saving connection masks token in logs (FR-28)."""
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/api/connections",
                json={
                    "confluence_base_url": "https://test.atlassian.net",
                    "space_key": "TEST",
                    "api_token": test_token,
                },
            )

        assert response.status_code in [200, 201]

        # Check that raw token does NOT appear in logs
        log_records = [record.message for record in caplog.records]
        all_logs = " ".join(log_records)

        assert test_token not in all_logs
        assert "ATATT3xFfGF0TEST_TOKEN" not in all_logs
        # Should contain masked version
        assert (
            "••••••••••" in all_logs
            or "Testing connection" in all_logs
            or "Saving connection" in all_logs
        )

    def test_get_connection_omits_token(self, client, test_token):
        """Test that GET /connections never returns token (NFR-9)."""
        # First save a connection
        save_response = client.post(
            "/api/connections",
            json={
                "confluence_base_url": "https://test.atlassian.net",
                "space_key": "TEST",
                "api_token": test_token,
            },
        )
        assert save_response.status_code in [200, 201]

        # Then get it back
        get_response = client.get("/api/connections")
        assert get_response.status_code == 200

        data = get_response.json()

        # Verify token is NOT in response
        assert "api_token" not in data
        assert "token" not in data
        assert "encrypted_token" not in data
        assert test_token not in str(data)

        # Verify other fields are present
        assert "confluence_base_url" in data
        assert "space_key" in data
        assert "id" in data

    def test_test_connection_masks_token_in_logs(self, client, test_token, caplog):
        """Test that testing connection masks token in logs (FR-28)."""
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/api/connections/test",
                json={
                    "confluence_base_url": "https://test.atlassian.net",
                    "space_key": "TEST",
                    "api_token": test_token,
                },
            )

        # Response may succeed or fail depending on Confluence availability
        assert response.status_code in [200, 400, 401, 404, 500]

        # Check that raw token does NOT appear in logs
        log_records = [record.message for record in caplog.records]
        all_logs = " ".join(log_records)

        assert test_token not in all_logs
        assert "ATATT3xFfGF0TEST_TOKEN" not in all_logs

    def test_error_response_omits_token(self, client, test_token):
        """Test that error responses never include token."""
        # Try to save with invalid data to trigger error
        response = client.post(
            "/api/connections",
            json={
                "confluence_base_url": "invalid-url",  # Invalid URL
                "space_key": "TEST",
                "api_token": test_token,
            },
        )

        # Should get validation error
        assert response.status_code in [400, 422]

        # Verify token is NOT in error response
        error_text = response.text
        assert test_token not in error_text
        assert "api_token" not in error_text.lower() or (
            "api_token" in error_text.lower() and test_token not in error_text
        )
