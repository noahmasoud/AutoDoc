"""AutoDoc Configuration Module.

This module provides centralized configuration management using Pydantic Settings
for type-safe environment variable handling and validation.
"""

from .settings import (
    Settings,
    clear_settings_cache,
    get_database_url,
    get_redis_url,
    get_settings,
    is_development,
    is_production,
    is_testing,
    print_config_summary,
    validate_required_secrets,
)

__all__ = [
    "Settings",
    "clear_settings_cache",
    "get_database_url",
    "get_redis_url",
    "get_settings",
    "is_development",
    "is_production",
    "is_testing",
    "print_config_summary",
    "validate_required_secrets",
]
