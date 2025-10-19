"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from autodoc.config import (
    Settings,
    clear_settings_cache,
    get_database_url,
    get_redis_url,
    get_settings,
    is_development,
    is_production,
    is_testing,
    validate_required_secrets,
)


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        # Clear environment and set only required variables
        with patch.dict(os.environ, {}, clear=True):
            os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
            os.environ["JWT_SECRET_KEY"] = (
                "test-jwt-secret-key-for-testing-32-chars-minimum"
            )
            # Ensure DEBUG is not set
            if "DEBUG" in os.environ:
                del os.environ["DEBUG"]

            clear_settings_cache()
            # Create settings without loading .env file
            settings = Settings.model_validate({})

            # Test default values
            assert settings.app_name == "AutoDoc"
            assert settings.app_version == "0.1.0"
            assert settings.environment == "development"
            # Note: debug defaults to False unless explicitly set to True
            assert settings.debug is False

            # Test database defaults
            assert settings.database.url == "sqlite:///./autodoc.db"
            assert settings.database.pool_size == 5

            # Test API defaults
            assert settings.api.host == "0.0.0.0"
            assert settings.api.port == 8000

    def test_environment_override(self) -> None:
        """Test environment variable overrides."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )
        os.environ["ENVIRONMENT"] = "production"
        os.environ["DEBUG"] = "true"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/test"

        clear_settings_cache()
        settings = get_settings()

        assert settings.environment == "production"
        assert settings.debug is True
        assert settings.database.url == "postgresql://user:pass@localhost:5432/test"

    def test_secret_validation(self) -> None:
        """Test secret key validation."""
        # Test with valid secrets
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        clear_settings_cache()
        settings = get_settings()

        assert len(settings.security.secret_key) >= 32
        assert len(settings.security.jwt_secret_key) >= 32

    def test_database_url_validation(self) -> None:
        """Test database URL validation."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        # Test empty URL
        os.environ["DATABASE_URL"] = ""
        clear_settings_cache()

        with pytest.raises(ValueError, match="Database URL cannot be empty"):
            get_settings()

        # Test valid URL
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        clear_settings_cache()
        settings = get_settings()
        assert settings.database.url == "sqlite:///./test.db"

    def test_utility_functions(self) -> None:
        """Test utility functions."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        # Test environment detection
        os.environ["ENVIRONMENT"] = "development"
        clear_settings_cache()
        assert is_development() is True
        assert is_production() is False
        assert is_testing() is False

        os.environ["ENVIRONMENT"] = "production"
        clear_settings_cache()
        assert is_development() is False
        assert is_production() is True
        assert is_testing() is False

        os.environ["ENVIRONMENT"] = "testing"
        clear_settings_cache()
        assert is_development() is False
        assert is_production() is False
        assert is_testing() is True

        # Test URL getters
        # Clear any previous DATABASE_URL setting
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        clear_settings_cache()
        db_url = get_database_url()
        assert db_url == "sqlite:///./autodoc.db"

        redis_url = get_redis_url()
        assert redis_url == "redis://localhost:6379/0"

    def test_required_secrets_validation(self) -> None:
        """Test required secrets validation."""
        # Test missing secrets - Settings creation will succeed with defaults
        with patch.dict(os.environ, {}, clear=True):
            clear_settings_cache()
            # Settings creation will succeed with default values
            validate_required_secrets()

        # Test with secrets
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )
        clear_settings_cache()

        # Should not raise
        validate_required_secrets()

    def test_cors_settings_parsing(self) -> None:
        """Test CORS settings parsing."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        # Test JSON parsing
        os.environ["API_CORS_ORIGINS"] = (
            '["http://localhost:3000", "https://example.com"]'
        )
        clear_settings_cache()
        settings = get_settings()

        # Should work without errors
        assert settings.api.cors_origins is not None
        assert len(settings.api.cors_origins) == 2

    def test_confluence_settings(self) -> None:
        """Test Confluence settings."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        # Test default Confluence settings
        clear_settings_cache()
        settings = get_settings()

        assert settings.confluence.url is None
        assert settings.confluence.username is None
        assert settings.confluence.token is None
        assert settings.confluence.is_configured is False

        # Test configured Confluence
        os.environ["CONFLUENCE_URL"] = "https://test.atlassian.net"
        os.environ["CONFLUENCE_USERNAME"] = "test@example.com"
        os.environ["CONFLUENCE_TOKEN"] = "test-token"
        clear_settings_cache()
        settings = get_settings()

        assert settings.confluence.url == "https://test.atlassian.net"
        assert settings.confluence.username == "test@example.com"
        assert settings.confluence.token == "test-token"
        assert settings.confluence.is_configured is True

    def test_logging_settings(self) -> None:
        """Test logging settings."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        clear_settings_cache()
        settings = get_settings()

        assert settings.logging.level == "INFO"
        assert settings.logging.format == "json"
        assert settings.logging.file is None
        assert settings.logging.max_size == 10485760
        assert settings.logging.backup_count == 5

    def test_file_settings(self) -> None:
        """Test file settings."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        clear_settings_cache()
        settings = get_settings()

        # Paths are resolved to absolute paths by the validator
        assert settings.file.upload_dir.endswith("/uploads")
        assert settings.file.temp_dir.endswith("/temp")
        assert "py" in settings.file.allowed_extensions
        assert settings.file.max_upload_size == 10485760  # 10MB in bytes

    def test_settings_caching(self) -> None:
        """Test settings caching behavior."""
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = (
            "test-jwt-secret-key-for-testing-32-chars-minimum"
        )

        # First call
        settings1 = get_settings()
        # Second call should return cached instance
        settings2 = get_settings()

        assert settings1 is settings2

        # Clear cache and get new instance
        clear_settings_cache()
        settings3 = get_settings()

        assert settings1 is not settings3
