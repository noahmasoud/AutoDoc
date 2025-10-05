"""Structured logger implementation for AutoDoc.

Provides structured logging with correlation ID support and configurable output formats.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timezone

from .correlation import get_correlation_context


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def __init__(self, include_correlation: bool = True):
        """Initialize the structured formatter.
        
        Args:
            include_correlation: Whether to include correlation IDs in logs
        """
        super().__init__()
        self.include_correlation = include_correlation
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation context if available
        if self.include_correlation:
            context = get_correlation_context()
            if context:
                log_data.update(context.to_log_fields())
        
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage"
            }:
                log_data[key] = value
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Custom formatter for human-readable text logging."""
    
    def __init__(self, include_correlation: bool = True):
        """Initialize the text formatter.
        
        Args:
            include_correlation: Whether to include correlation IDs in logs
        """
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.include_correlation = include_correlation
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as human-readable text."""
        # Get base formatted message
        message = super().format(record)
        
        # Add correlation context if available
        if self.include_correlation:
            context = get_correlation_context()
            if context:
                correlation_parts = [f"corr_id={context.correlation_id}"]
                
                if context.run_id:
                    correlation_parts.append(f"run_id={context.run_id}")
                if context.commit_sha:
                    correlation_parts.append(f"commit={context.commit_sha[:8]}")
                if context.request_id:
                    correlation_parts.append(f"req_id={context.request_id}")
                
                if correlation_parts:
                    message = f"{message} | {' '.join(correlation_parts)}"
        
        return message


def setup_logging(
    level: Union[str, int] = "INFO",
    format_type: str = "json",
    log_file: Optional[Union[str, Path]] = None,
    include_correlation: bool = True,
) -> None:
    """Setup logging configuration for AutoDoc.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format ("json" or "text")
        log_file: Optional log file path
        include_correlation: Whether to include correlation IDs in logs
    """
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Set formatter based on type
    if format_type.lower() == "json":
        formatter = StructuredFormatter(include_correlation=include_correlation)
    else:
        formatter = TextFormatter(include_correlation=include_correlation)
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def configure_logging(
    level: Union[str, int] = "INFO",
    format_type: str = "json",
    log_file: Optional[Union[str, Path]] = None,
    include_correlation: bool = True,
    logger_configs: Optional[Dict[str, Union[str, int]]] = None,
) -> None:
    """Configure logging with additional logger-specific settings.
    
    Args:
        level: Default logging level
        format_type: Log format ("json" or "text")
        log_file: Optional log file path
        include_correlation: Whether to include correlation IDs in logs
        logger_configs: Logger-specific level configurations
    """
    # Setup basic logging
    setup_logging(
        level=level,
        format_type=format_type,
        log_file=log_file,
        include_correlation=include_correlation,
    )
    
    # Configure specific loggers
    if logger_configs:
        for logger_name, logger_level in logger_configs.items():
            if isinstance(logger_level, str):
                logger_level = getattr(logging, logger_level.upper(), logging.INFO)
            logging.getLogger(logger_name).setLevel(logger_level)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance with correlation ID support
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Enhanced logger with structured logging methods."""
    
    def __init__(self, name: str):
        """Initialize the structured logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(name)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Any] = None,
    ) -> None:
        """Log with correlation context.
        
        Args:
            level: Log level
            message: Log message
            extra: Additional fields
            exc_info: Exception information
        """
        # Merge extra fields with correlation context
        log_extra = extra or {}
        
        # Add correlation context
        context = get_correlation_context()
        if context:
            log_extra.update(context.to_log_fields())
        
        self.logger.log(level, message, extra=log_extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        self._log_with_context(logging.ERROR, message, kwargs, exc_info=True)
    
    def log_run_start(self, run_id: str, **kwargs) -> None:
        """Log run start event."""
        self.info(
            "Run started",
            event_type="run_start",
            run_id=run_id,
            **kwargs
        )
    
    def log_run_complete(self, run_id: str, status: str, **kwargs) -> None:
        """Log run completion event."""
        self.info(
            "Run completed",
            event_type="run_complete",
            run_id=run_id,
            status=status,
            **kwargs
        )
    
    def log_run_error(self, run_id: str, error: str, **kwargs) -> None:
        """Log run error event."""
        self.error(
            "Run failed",
            event_type="run_error",
            run_id=run_id,
            error=error,
            **kwargs
        )
    
    def log_patch_created(self, patch_id: str, page_id: str, **kwargs) -> None:
        """Log patch creation event."""
        self.info(
            "Patch created",
            event_type="patch_created",
            patch_id=patch_id,
            page_id=page_id,
            **kwargs
        )
    
    def log_patch_applied(self, patch_id: str, page_id: str, **kwargs) -> None:
        """Log patch application event."""
        self.info(
            "Patch applied",
            event_type="patch_applied",
            patch_id=patch_id,
            page_id=page_id,
            **kwargs
        )
    
    def log_api_request(self, method: str, path: str, **kwargs) -> None:
        """Log API request event."""
        self.info(
            "API request",
            event_type="api_request",
            method=method,
            path=path,
            **kwargs
        )
    
    def log_api_response(self, method: str, path: str, status_code: int, **kwargs) -> None:
        """Log API response event."""
        self.info(
            "API response",
            event_type="api_response",
            method=method,
            path=path,
            status_code=status_code,
            **kwargs
        )
