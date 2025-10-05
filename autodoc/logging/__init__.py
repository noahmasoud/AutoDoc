"""AutoDoc Logging Module.

Structured logging with correlation ID support for CI/CD runs and API requests.
Implements FR-23: Structured logs with run correlation IDs.
"""

from .correlation import (
    CorrelationContext,
    CorrelationContextManager,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_context,
    set_run_context,
    set_request_context,
    run_correlation_context,
    request_correlation_context,
)
from .logger import (
    get_logger,
    setup_logging,
    configure_logging,
)
from .context import (
    LoggingContext,
    log_context,
    log_run_context,
    log_request_context,
)

__all__ = [
    # Correlation ID management
    "CorrelationContext",
    "CorrelationContextManager",
    "get_correlation_id",
    "set_correlation_id", 
    "clear_correlation_context",
    "set_run_context",
    "set_request_context",
    "run_correlation_context",
    "request_correlation_context",
    
    # Logger management
    "get_logger",
    "setup_logging",
    "configure_logging",
    
    # Context management
    "LoggingContext",
    "log_context",
    "log_run_context",
    "log_request_context",
]
