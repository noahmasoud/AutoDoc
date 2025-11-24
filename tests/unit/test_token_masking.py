"""Unit tests for token masking (FR-28, NFR-9)."""

from core.token_masking import mask_token, mask_payload, mask_dict_keys


class TestMaskToken:
    """Test mask_token function."""

    def test_mask_none(self):
        """Test masking None token."""
        assert mask_token(None) == "••••••••••"

    def test_mask_empty_string(self):
        """Test masking empty string."""
        assert mask_token("") == "••••••••••"

    def test_mask_token_fully(self):
        """Test fully masking a token."""
        token = "ATATT3xFfGF0YOUR_ACTUAL_TOKEN_HERE_1234567890abcdef"
        masked = mask_token(token)
        assert masked == "••••••••••"
        assert token not in masked

    def test_mask_token_partial(self):
        """Test partially masking a token with visible chars."""
        token = "ATATT3xFfGF0TOKEN"
        masked = mask_token(token, visible_chars=5)
        assert masked.startswith("ATATT")
        assert "TOKEN" not in masked
        assert len(masked) >= len(token)

    def test_mask_short_token(self):
        """Test masking short token."""
        assert mask_token("short") == "••••••••••"


class TestMaskPayload:
    """Test mask_payload function."""

    def test_mask_simple_payload(self):
        """Test masking simple payload."""
        payload = {
            "confluence_base_url": "https://test.atlassian.net",
            "space_key": "DOCS",
            "api_token": "ATATT3xFfGF0YOUR_TOKEN_HERE",
        }
        masked = mask_payload(payload)

        assert masked["confluence_base_url"] == payload["confluence_base_url"]
        assert masked["space_key"] == payload["space_key"]
        assert masked["api_token"] == "••••••••••"
        assert "ATATT" not in str(masked)

    def test_mask_nested_payload(self):
        """Test masking nested payload."""
        payload = {
            "connection": {
                "api_token": "SECRET_TOKEN_123",
                "url": "https://test.com",
            },
            "user": {
                "password": "secret_pass",
            },
        }
        masked = mask_payload(payload, deep=True)

        assert masked["connection"]["api_token"] == "••••••••••"
        assert masked["connection"]["url"] == payload["connection"]["url"]
        assert masked["user"]["password"] == "••••••••••"
        assert "SECRET_TOKEN" not in str(masked)
        assert "secret_pass" not in str(masked)

    def test_mask_multiple_fields(self):
        """Test masking multiple sensitive fields."""
        payload = {
            "token": "token1",
            "api_token": "token2",
            "password": "pass1",
            "secret": "secret1",
            "api_key": "key1",
            "normal_field": "normal_value",
        }
        masked = mask_payload(payload)

        assert masked["token"] == "••••••••••"
        assert masked["api_token"] == "••••••••••"
        assert masked["password"] == "••••••••••"
        assert masked["secret"] == "••••••••••"
        assert masked["api_key"] == "••••••••••"
        assert masked["normal_field"] == "normal_value"

    def test_mask_custom_keys(self):
        """Test masking with custom key list."""
        payload = {
            "custom_secret": "secret_value",
            "api_token": "token_value",
            "public_field": "public_value",
        }
        masked = mask_payload(payload, keys=["custom_secret"])

        assert masked["custom_secret"] == "••••••••••"
        assert masked["api_token"] == "token_value"  # Not in custom keys
        assert masked["public_field"] == "public_value"


class TestMaskDictKeys:
    """Test mask_dict_keys function."""

    def test_mask_specific_keys(self):
        """Test masking specific keys."""
        data = {
            "api_token": "TOKEN123",
            "other_field": "value",
        }
        masked = mask_dict_keys(data, ["api_token"])

        assert masked["api_token"] == "••••••••••"
        assert masked["other_field"] == "value"
