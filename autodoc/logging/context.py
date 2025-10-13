"""Context managers for logging with correlation IDs.

Provides convenient context managers for common logging scenarios.
"""

from contextlib import contextmanager
from typing import Any

from .correlation import (
    CorrelationContextManager,
    generate_request_id,
    generate_run_id,
)
from .logger import get_logger


class LoggingContext:
    """Base logging context manager."""

    def __init__(self, logger_name: str):
        """Initialize the logging context.

        Args:
            logger_name: Name of the logger to use
        """
        self.logger = get_logger(logger_name)

    def log_event(self, event_type: str, message: str, **kwargs) -> None:
        """Log an event with structured data.

        Args:
            event_type: Type of event
            message: Log message
            **kwargs: Additional structured data
        """
        extra = {"event_type": event_type, **kwargs}
        self.logger.info(message, extra=extra)


@contextmanager
def log_context(
    logger_name: str,
    correlation_id: str | None = None,
    **context_kwargs,
):
    """Context manager for logging with correlation ID.

    Args:
        logger_name: Name of the logger to use
        correlation_id: Optional correlation ID
        **context_kwargs: Additional context parameters

    Yields:
        LoggingContext instance
    """
    with CorrelationContextManager(correlation_id=correlation_id, **context_kwargs):
        context = LoggingContext(logger_name)
        try:
            yield context
        except Exception as e:
            context.logger.exception(
                "Error in logging context: %s",
                str(e),
                extra={"event_type": "context_error", "error": str(e)},
            )
            raise


@contextmanager
def log_run_context(
    logger_name: str,
    run_id: str | None = None,
    commit_sha: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    pr_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Context manager for CI/CD run logging.

    Args:
        logger_name: Name of the logger to use
        run_id: Optional run ID (generated if not provided)
        commit_sha: Git commit SHA
        repo: Repository name/URL
        branch: Git branch name
        pr_id: Pull/Merge request ID
        metadata: Additional metadata

    Yields:
        LoggingContext instance
    """
    if run_id is None:
        run_id = generate_run_id()

    with CorrelationContextManager(
        run_id=run_id,
        commit_sha=commit_sha,
        repo=repo,
        branch=branch,
        pr_id=pr_id,
        metadata=metadata,
    ):
        context = LoggingContext(logger_name)

        # Log run start
        context.log_event(
            "run_start",
            f"Run started: {run_id}",
            run_id=run_id,
            commit_sha=commit_sha,
            repo=repo,
            branch=branch,
            pr_id=pr_id,
        )

        try:
            yield context
            # Log run completion
            context.log_event(
                "run_complete",
                f"Run completed successfully: {run_id}",
                run_id=run_id,
                status="success",
            )
        except Exception as e:
            # Log run error
            context.log_event(
                "run_error",
                f"Run failed: {run_id} - {e!s}",
                run_id=run_id,
                status="error",
                error=str(e),
            )
            raise


@contextmanager
def log_request_context(
    logger_name: str,
    request_id: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Context manager for API request logging.

    Args:
        logger_name: Name of the logger to use
        request_id: Optional request ID (generated if not provided)
        user_id: User ID
        metadata: Additional metadata

    Yields:
        LoggingContext instance
    """
    if request_id is None:
        request_id = generate_request_id()

    with CorrelationContextManager(
        request_id=request_id,
        user_id=user_id,
        metadata=metadata,
    ):
        context = LoggingContext(logger_name)

        # Log request start
        context.log_event(
            "request_start",
            f"Request started: {request_id}",
            request_id=request_id,
            user_id=user_id,
        )

        try:
            yield context
            # Log request completion
            context.log_event(
                "request_complete",
                f"Request completed successfully: {request_id}",
                request_id=request_id,
                status="success",
            )
        except Exception as e:
            # Log request error
            context.log_event(
                "request_error",
                f"Request failed: {request_id} - {e!s}",
                request_id=request_id,
                status="error",
                error=str(e),
            )
            raise


class RunLoggingContext(LoggingContext):
    """Specialized logging context for CI/CD runs."""

    def __init__(self, logger_name: str, run_id: str):
        """Initialize the run logging context.

        Args:
            logger_name: Name of the logger to use
            run_id: Run ID
        """
        super().__init__(logger_name)
        self.run_id = run_id

    def log_analyzer_start(self, file_count: int) -> None:
        """Log analyzer start."""
        self.log_event(
            "analyzer_start",
            f"Starting analysis for {file_count} files",
            run_id=self.run_id,
            file_count=file_count,
        )

    def log_analyzer_complete(self, findings_count: int) -> None:
        """Log analyzer completion."""
        self.log_event(
            "analyzer_complete",
            f"Analysis complete with {findings_count} findings",
            run_id=self.run_id,
            findings_count=findings_count,
        )

    def log_patch_generated(
        self,
        patch_id: str,
        page_id: str,
        template_id: str,
    ) -> None:
        """Log patch generation."""
        self.log_event(
            "patch_generated",
            f"Patch generated: {patch_id} for page {page_id}",
            run_id=self.run_id,
            patch_id=patch_id,
            page_id=page_id,
            template_id=template_id,
        )

    def log_confluence_update(self, page_id: str, version: int, success: bool) -> None:
        """Log Confluence update."""
        status = "success" if success else "failed"
        self.log_event(
            "confluence_update",
            f"Confluence update {status}: page {page_id} version {version}",
            run_id=self.run_id,
            page_id=page_id,
            version=version,
            success=success,
        )


class RequestLoggingContext(LoggingContext):
    """Specialized logging context for API requests."""

    def __init__(self, logger_name: str, request_id: str):
        """Initialize the request logging context.

        Args:
            logger_name: Name of the logger to use
            request_id: Request ID
        """
        super().__init__(logger_name)
        self.request_id = request_id

    def log_authentication(self, user_id: str, success: bool) -> None:
        """Log authentication attempt."""
        status = "success" if success else "failed"
        self.log_event(
            "authentication",
            f"Authentication {status} for user {user_id}",
            request_id=self.request_id,
            user_id=user_id,
            success=success,
        )

    def log_authorization(self, resource: str, action: str, success: bool) -> None:
        """Log authorization check."""
        status = "granted" if success else "denied"
        self.log_event(
            "authorization",
            f"Authorization {status}: {action} on {resource}",
            request_id=self.request_id,
            resource=resource,
            action=action,
            success=success,
        )

    def log_validation_error(self, field: str, error: str) -> None:
        """Log validation error."""
        self.log_event(
            "validation_error",
            f"Validation error in {field}: {error}",
            request_id=self.request_id,
            field=field,
            error=error,
        )
