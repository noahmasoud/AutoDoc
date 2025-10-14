"""AutoDoc Logging Module.

Structured logging with correlation ID support for CI/CD runs and API requests.
Implements FR-23: Structured logs with run correlation IDs.
"""

from .context import (
    LoggingContext,
    log_context,
    log_request_context,
    log_run_context,
)
from .correlation import (
    CorrelationContext,
    CorrelationContextManager,
    clear_correlation_context,
    get_correlation_id,
    request_correlation_context,
    run_correlation_context,
    set_correlation_id,
    set_request_context,
    set_run_context,
)
from .logger import (
    configure_logging,
    get_logger,
    setup_logging,
)

__all__ = [
    # Correlation ID management
    "CorrelationContext",
    "CorrelationContextManager",
    # Context management
    "LoggingContext",
    "clear_correlation_context",
    "configure_logging",
    "get_correlation_id",
    # Logger management
    "get_logger",
    "log_context",
    "log_request_context",
    "log_run_context",
    "request_correlation_context",
    "run_correlation_context",
    "set_correlation_id",
    "set_request_context",
    "set_run_context",
    "setup_logging",
]
