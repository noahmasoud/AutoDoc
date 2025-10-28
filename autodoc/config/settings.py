"""AutoDoc Settings Configuration.

Pydantic Settings-based configuration with secure environment variable handling.
All secrets are read from environment variables only and never persisted.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DB_", populate_by_name=True)

    # Database URL with SQLite as default for capstone
    url: str = Field(
        default="sqlite:///./autodoc.db",
        description="Database connection URL",
        alias="DATABASE_URL",
    )

    # Database connection pool settings
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(
        default=10,
        description="Maximum database connection overflow",
    )
    pool_timeout: int = Field(
        default=30,
        description="Database connection pool timeout in seconds",
    )
    pool_recycle: int = Field(
        default=3600,
        description="Database connection recycle time in seconds",
    )

    @field_validator("url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")

        # Ensure SQLite URLs use proper format
        if v.startswith("sqlite://"):
            # Convert sqlite:///path to sqlite:///./path for relative paths
            if v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
                if not v.startswith("sqlite:///./"):
                    v = v.replace("sqlite:///", "sqlite:///./")

        return v

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.url.startswith("sqlite://")

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.url.startswith("postgresql://") or self.url.startswith(
            "postgres://",
        )


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    url: str | None = Field(default=None, description="Redis connection URL")
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: str | None = Field(default=None, description="Redis password")
    max_connections: int = Field(default=10, description="Maximum Redis connections")
    socket_timeout: int = Field(
        default=5,
        description="Redis socket timeout in seconds",
    )

    @field_validator("url", mode="before")
    @classmethod
    def build_redis_url(cls, v: str | None, info: Any) -> str | None:
        """Build Redis URL from components if not provided."""
        if v:
            return v

        # Build URL from components if available
        if hasattr(info, "data"):
            host = info.data.get("host", "localhost")
            port = info.data.get("port", 6379)
            db = info.data.get("db", 0)
            password = info.data.get("password")

            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            return f"redis://{host}:{port}/{db}"

        return None


class APISettings(BaseSettings):
    """API server configuration settings."""

    model_config = SettingsConfigDict(env_prefix="API_")

    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, description="API server port")
    workers: int = Field(default=1, description="Number of API workers")
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow CORS credentials",
    )
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="CORS allowed methods",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="CORS allowed headers",
    )


class SecuritySettings(BaseSettings):
    """Security configuration settings.

    All secrets are read from environment variables only and never persisted.
    """

    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        populate_by_name=True,
    )

    # Secret keys (MUST be provided via environment)
    secret_key: str = Field(
        default="dev-secret-key-change-in-production-must-be-32-chars-minimum",
        description="Application secret key for encryption and signing",
        alias="SECRET_KEY",
    )
    jwt_secret_key: str = Field(
        default="dev-jwt-secret-key-must-be-32-chars-minimum",
        description="JWT signing secret key",
        alias="JWT_SECRET_KEY",
    )

    # JWT settings
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration in minutes",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiration in days",
    )

    # Password hashing
    password_min_length: int = Field(default=8, description="Minimum password length")
    password_require_special_chars: bool = Field(
        default=True,
        description="Require special characters in passwords",
    )

    # Rate limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Rate limit requests per minute",
    )
    rate_limit_window: int = Field(
        default=60,
        description="Rate limit window in seconds",
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key strength."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v


class ConfluenceSettings(BaseSettings):
    """Confluence integration settings.

    All credentials are read from environment variables only.
    """

    model_config = SettingsConfigDict(env_prefix="CONFLUENCE_")

    # Confluence connection (MUST be provided via environment for production)
    url: str | None = Field(default=None, description="Confluence base URL")
    username: str | None = Field(default=None, description="Confluence username")
    token: str | None = Field(default=None, description="Confluence API token")

    # Confluence settings
    space_key: str | None = Field(
        default=None,
        description="Default Confluence space key",
    )
    page_prefix: str = Field(default="AutoDoc", description="Page title prefix")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    @field_validator("url")
    @classmethod
    def validate_confluence_url(cls, v: str | None) -> str | None:
        """Validate Confluence URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Confluence URL must start with http:// or https://")
        return v

    @property
    def is_configured(self) -> bool:
        """Check if Confluence is properly configured."""
        return all([self.url, self.username, self.token])


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format (json, text)")
    file: str | None = Field(default=None, description="Log file path")
    max_size: int = Field(
        default=10485760,
        description="Maximum log file size in bytes",
    )  # 10MB
    backup_count: int = Field(default=5, description="Number of log file backups")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {', '.join(valid_formats)}")
        return v.lower()


class FileSettings(BaseSettings):
    """File storage configuration settings."""

    model_config = SettingsConfigDict(env_prefix="FILE_")

    upload_dir: str = Field(default="./uploads", description="File upload directory")
    max_upload_size: int = Field(
        default=10485760,
        description="Maximum upload size in bytes",
    )  # 10MB
    allowed_extensions: list[str] = Field(
        default=["py", "js", "ts", "md", "txt", "json", "yaml", "yml"],
        description="Allowed file extensions",
    )
    temp_dir: str = Field(default="./temp", description="Temporary files directory")

    @field_validator("upload_dir", "temp_dir")
    @classmethod
    def create_directories(cls, v: str) -> str:
        """Create directories if they don't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())


class Settings(BaseSettings):
    """Main application settings.

    Combines all configuration settings with secure environment variable handling.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="allow",  # Allow extra fields for development flexibility
    )

    # Application metadata
    app_name: str = Field(default="AutoDoc", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Application environment",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Component settings
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings())
    redis: RedisSettings = Field(default_factory=lambda: RedisSettings())
    api: APISettings = Field(default_factory=lambda: APISettings())
    security: SecuritySettings = Field(default_factory=lambda: SecuritySettings())
    confluence: ConfluenceSettings = Field(default_factory=lambda: ConfluenceSettings())
    logging: LoggingSettings = Field(default_factory=lambda: LoggingSettings())
    file: FileSettings = Field(default_factory=lambda: FileSettings())

    # Python path
    pythonpath: str | None = Field(default=None, description="Python path")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment setting."""
        valid_environments = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(
                f"Environment must be one of: {', '.join(valid_environments)}",
            )
        return v.lower()

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, v: str | bool) -> bool:
        """Parse debug setting from string or boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.environment == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    This function caches the settings to avoid re-parsing environment variables
    on every access. The cache is cleared when environment variables change.
    """
    return Settings()


def clear_settings_cache() -> None:
    """Clear the settings cache."""
    get_settings.cache_clear()


def get_database_url() -> str:
    """Get database URL from settings."""
    return get_settings().database.url


def get_redis_url() -> str | None:
    """Get Redis URL from settings."""
    return get_settings().redis.url


def is_development() -> bool:
    """Check if running in development mode."""
    return get_settings().is_development


def is_production() -> bool:
    """Check if running in production mode."""
    return get_settings().is_production


def is_testing() -> bool:
    """Check if running in testing mode."""
    return get_settings().is_testing


def validate_required_secrets() -> None:
    """Validate that all required secrets are provided."""
    settings = get_settings()

    # Check required secrets
    if not settings.security.secret_key:
        raise ValueError("SECRET_KEY environment variable is required")

    if not settings.security.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")

    # Check production-specific requirements
    if settings.is_production:
        if not settings.confluence.is_configured:
            pass

        if settings.debug:
            raise ValueError("DEBUG must be False in production")


def print_config_summary() -> None:
    """Print a summary of the current configuration."""
    get_settings()
