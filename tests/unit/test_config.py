"""Unit tests for configuration management."""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from autodoc.config import (
    Settings,
    get_settings,
    clear_settings_cache,
    get_database_url,
    get_redis_url,
    is_development,
    is_production,
    is_testing,
    validate_required_secrets,
    EnvironmentConfig,
)


class TestSettings:
    """Test suite for Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        settings = Settings()
        
        # Test application settings
        assert settings.app_name == "AutoDoc"
        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.debug is False
        
        # Test database settings
        assert settings.database.url == "sqlite:///./autodoc.db"
        assert settings.database.is_sqlite is True
        assert settings.database.is_postgresql is False
        
        # Test Redis settings
        assert settings.redis.host == "localhost"
        assert settings.redis.port == 6379
        assert settings.redis.db == 0
        
        # Test API settings
        assert settings.api.host == "0.0.0.0"
        assert settings.api.port == 8000
        assert settings.api.workers == 1
        assert settings.api.reload is False
        
        # Test security settings
        assert settings.security.secret_key == "test-secret-key-for-testing-32-chars-minimum"
        assert settings.security.jwt_secret_key == "test-jwt-secret-key-for-testing-32-chars-minimum"
        assert settings.security.jwt_algorithm == "HS256"
        
        # Test logging settings
        assert settings.logging.level == "INFO"
        assert settings.logging.format == "json"
        
        # Test file settings
        assert settings.file.max_upload_size == 10485760  # 10MB
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]

    def test_environment_validation(self):
        """Test environment validation."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test valid environments
        for env in ["development", "testing", "staging", "production"]:
            os.environ["ENVIRONMENT"] = env
            clear_settings_cache()
            settings = get_settings()
            assert settings.environment == env
        
        # Test invalid environment
        os.environ["ENVIRONMENT"] = "invalid"
        clear_settings_cache()
        with pytest.raises(ValidationError):
            get_settings()
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["ENVIRONMENT"]

    def test_database_url_validation(self):
        """Test database URL validation and conversion."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test SQLite URL conversion
        os.environ["DATABASE_URL"] = "sqlite:///path/to/db.db"
        clear_settings_cache()
        settings = get_settings()
        assert settings.database.url == "sqlite:///./path/to/db.db"
        assert settings.database.is_sqlite is True
        
        # Test PostgreSQL URL
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/db"
        clear_settings_cache()
        settings = get_settings()
        assert settings.database.url == "postgresql://user:pass@localhost:5432/db"
        assert settings.database.is_postgresql is True
        
        # Test invalid URL
        os.environ["DATABASE_URL"] = ""
        clear_settings_cache()
        with pytest.raises(ValidationError):
            get_settings()
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["DATABASE_URL"]

    def test_secret_key_validation(self):
        """Test secret key validation."""
        # Test missing secret key
        with pytest.raises(ValidationError):
            Settings()
        
        # Test short secret key
        os.environ["SECRET_KEY"] = "short"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        with pytest.raises(ValidationError):
            Settings()
        
        # Test valid secret key
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        settings = Settings()
        assert settings.security.secret_key == "test-secret-key-for-testing-32-chars-minimum"
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]

    def test_jwt_secret_key_validation(self):
        """Test JWT secret key validation."""
        # Test missing JWT secret key
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        with pytest.raises(ValidationError):
            Settings()
        
        # Test short JWT secret key
        os.environ["JWT_SECRET_KEY"] = "short"
        with pytest.raises(ValidationError):
            Settings()
        
        # Test valid JWT secret key
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        settings = Settings()
        assert settings.security.jwt_secret_key == "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]

    def test_confluence_configuration(self):
        """Test Confluence configuration."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test not configured
        settings = Settings()
        assert settings.confluence.is_configured is False
        
        # Test partially configured
        os.environ["CONFLUENCE_URL"] = "https://example.atlassian.net"
        clear_settings_cache()
        settings = get_settings()
        assert settings.confluence.is_configured is False
        
        # Test fully configured
        os.environ["CONFLUENCE_USERNAME"] = "test-user"
        os.environ["CONFLUENCE_TOKEN"] = "test-token"
        clear_settings_cache()
        settings = get_settings()
        assert settings.confluence.is_configured is True
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["CONFLUENCE_URL"]
        del os.environ["CONFLUENCE_USERNAME"]
        del os.environ["CONFLUENCE_TOKEN"]

    def test_cors_settings_parsing(self):
        """Test CORS settings parsing."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test string parsing
        os.environ["API_CORS_ORIGINS"] = "http://localhost:3000,https://example.com"
        clear_settings_cache()
        settings = get_settings()
        assert settings.api.cors_origins == ["http://localhost:3000", "https://example.com"]
        
        # Test methods parsing
        os.environ["API_CORS_ALLOW_METHODS"] = "GET,POST,PUT"
        clear_settings_cache()
        settings = get_settings()
        assert settings.api.cors_allow_methods == ["GET", "POST", "PUT"]
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["API_CORS_ORIGINS"]
        del os.environ["API_CORS_ALLOW_METHODS"]

    def test_file_settings_directory_creation(self):
        """Test file settings directory creation."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test directory creation
        os.environ["UPLOAD_DIR"] = "./test_uploads"
        os.environ["TEMP_DIR"] = "./test_temp"
        clear_settings_cache()
        settings = get_settings()
        
        from pathlib import Path
        assert Path(settings.file.upload_dir).exists()
        assert Path(settings.file.temp_dir).exists()
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["UPLOAD_DIR"]
        del os.environ["TEMP_DIR"]


class TestSettingsUtilities:
    """Test suite for settings utility functions."""

    def test_get_database_url(self):
        """Test get_database_url function."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        
        url = get_database_url()
        assert url == "sqlite:///./test.db"
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["DATABASE_URL"]

    def test_get_redis_url(self):
        """Test get_redis_url function."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        
        url = get_redis_url()
        assert url == "redis://localhost:6379/0"
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["REDIS_URL"]

    def test_environment_checkers(self):
        """Test environment checker functions."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Test development
        os.environ["ENVIRONMENT"] = "development"
        clear_settings_cache()
        assert is_development() is True
        assert is_production() is False
        assert is_testing() is False
        
        # Test production
        os.environ["ENVIRONMENT"] = "production"
        clear_settings_cache()
        assert is_development() is False
        assert is_production() is True
        assert is_testing() is False
        
        # Test testing
        os.environ["ENVIRONMENT"] = "testing"
        clear_settings_cache()
        assert is_development() is False
        assert is_production() is False
        assert is_testing() is True
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
        del os.environ["ENVIRONMENT"]

    def test_validate_required_secrets(self):
        """Test validate_required_secrets function."""
        # Test missing secrets
        with pytest.raises(ValueError, match="SECRET_KEY"):
            validate_required_secrets()
        
        # Test valid secrets
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Should not raise
        validate_required_secrets()
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]


class TestEnvironmentConfig:
    """Test suite for EnvironmentConfig class."""

    def test_get_database_config(self):
        """Test get_database_config method."""
        # Test development config
        config = EnvironmentConfig.get_database_config("development")
        assert config["DATABASE_URL"] == "sqlite:///./autodoc.db"
        assert config["DB_POOL_SIZE"] == "5"
        
        # Test testing config
        config = EnvironmentConfig.get_database_config("testing")
        assert config["DATABASE_URL"] == "sqlite:///./test_autodoc.db"
        assert config["DB_POOL_SIZE"] == "1"
        
        # Test production config
        config = EnvironmentConfig.get_database_config("production")
        assert config["DATABASE_URL"] == "sqlite:///./autodoc_prod.db"
        assert config["DB_POOL_SIZE"] == "10"

    def test_get_redis_config(self):
        """Test get_redis_config method."""
        # Test development config
        config = EnvironmentConfig.get_redis_config("development")
        assert config["REDIS_URL"] == "redis://localhost:6379/0"
        assert config["REDIS_MAX_CONNECTIONS"] == "10"
        
        # Test testing config
        config = EnvironmentConfig.get_redis_config("testing")
        assert config["REDIS_URL"] == "redis://localhost:6379/1"
        assert config["REDIS_MAX_CONNECTIONS"] == "1"

    def test_get_api_config(self):
        """Test get_api_config method."""
        # Test development config
        config = EnvironmentConfig.get_api_config("development")
        assert config["API_RELOAD"] == "true"
        assert config["API_WORKERS"] == "1"
        
        # Test production config
        config = EnvironmentConfig.get_api_config("production")
        assert config["API_RELOAD"] == "false"
        assert config["API_WORKERS"] == "4"

    def test_get_security_config(self):
        """Test get_security_config method."""
        # Test missing secrets
        with pytest.raises(ValueError, match="Missing required environment variables"):
            EnvironmentConfig.get_security_config()
        
        # Test with secrets
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        config = EnvironmentConfig.get_security_config("development")
        assert config["SECRET_KEY"] == "test-secret-key-for-testing-32-chars-minimum"
        assert config["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] == "60"
        
        config = EnvironmentConfig.get_security_config("production")
        assert config["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] == "15"
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]

    def test_get_logging_config(self):
        """Test get_logging_config method."""
        # Test development config
        config = EnvironmentConfig.get_logging_config("development")
        assert config["LOG_LEVEL"] == "DEBUG"
        assert config["LOG_FORMAT"] == "text"
        
        # Test production config
        config = EnvironmentConfig.get_logging_config("production")
        assert config["LOG_LEVEL"] == "INFO"
        assert config["LOG_FORMAT"] == "json"


class TestSettingsCaching:
    """Test suite for settings caching."""

    def test_settings_caching(self):
        """Test that settings are properly cached."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance (cached)
        assert settings1 is settings2
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]

    def test_clear_settings_cache(self):
        """Test clearing settings cache."""
        # Set required environment variables
        os.environ["SECRET_KEY"] = "test-secret-key-for-testing-32-chars-minimum"
        os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-32-chars-minimum"
        
        # Get settings
        settings1 = get_settings()
        
        # Clear cache
        clear_settings_cache()
        
        # Get settings again
        settings2 = get_settings()
        
        # Should be different instances
        assert settings1 is not settings2
        
        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["JWT_SECRET_KEY"]
