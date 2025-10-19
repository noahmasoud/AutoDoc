"""Correlation ID management for structured logging.

Provides thread-local storage for correlation IDs to track requests and runs
across the AutoDoc system.
"""

import uuid
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Optional

# Thread-local storage for correlation IDs
_correlation_context: ContextVar[Optional["CorrelationContext"]] = ContextVar(
    "correlation_context",
    default=None,
)


@dataclass
class CorrelationContext:
    """Correlation context for tracking requests and runs."""

    # Primary correlation ID
    correlation_id: str

    # Run-specific information
    run_id: str | None = None
    commit_sha: str | None = None
    repo: str | None = None
    branch: str | None = None
    pr_id: str | None = None

    # Request-specific information
    request_id: str | None = None
    user_id: str | None = None

    # Timing information
    started_at: datetime | None = None

    # Additional metadata
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.started_at is None:
            self.started_at = datetime.now(UTC)

        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)

        # Convert datetime to ISO string
        if data["started_at"]:
            data["started_at"] = data["started_at"].isoformat()

        return data

    def to_log_fields(self) -> dict[str, Any]:
        """Convert to structured log fields."""
        fields = {
            "correlation_id": self.correlation_id,
        }

        if self.run_id:
            fields["run_id"] = self.run_id
        if self.commit_sha:
            fields["commit_sha"] = self.commit_sha
        if self.repo:
            fields["repo"] = self.repo
        if self.branch:
            fields["branch"] = self.branch
        if self.pr_id:
            fields["pr_id"] = self.pr_id
        if self.request_id:
            fields["request_id"] = self.request_id
        if self.user_id:
            fields["user_id"] = self.user_id

        # Add metadata
        if self.metadata:
            for key, value in self.metadata.items():
                fields[f"meta_{key}"] = value

        return fields


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def generate_run_id() -> str:
    """Generate a new run ID."""
    return f"run_{uuid.uuid4().hex[:12]}"


def generate_request_id() -> str:
    """Generate a new request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_correlation_id() -> str | None:
    """Get the current correlation ID."""
    context = _correlation_context.get()
    return context.correlation_id if context else None


def get_correlation_context() -> CorrelationContext | None:
    """Get the current correlation context."""
    return _correlation_context.get()


def set_correlation_id(
    correlation_id: str | None = None,
    run_id: str | None = None,
    commit_sha: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    pr_id: str | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CorrelationContext:
    """Set the correlation context.

    Args:
        correlation_id: Primary correlation ID (generated if not provided)
        run_id: Run ID for CI/CD operations
        commit_sha: Git commit SHA
        repo: Repository name/URL
        branch: Git branch name
        pr_id: Pull/Merge request ID
        request_id: Request ID for API calls
        user_id: User ID for authentication
        metadata: Additional metadata

    Returns:
        The created correlation context
    """
    if correlation_id is None:
        correlation_id = generate_correlation_id()

    context = CorrelationContext(
        correlation_id=correlation_id,
        run_id=run_id,
        commit_sha=commit_sha,
        repo=repo,
        branch=branch,
        pr_id=pr_id,
        request_id=request_id,
        user_id=user_id,
        metadata=metadata or {},
    )

    _correlation_context.set(context)
    return context


def clear_correlation_context() -> None:
    """Clear the current correlation context."""
    _correlation_context.set(None)


def update_correlation_metadata(key: str, value: Any) -> None:
    """Update metadata in the current correlation context.

    Args:
        key: Metadata key
        value: Metadata value
    """
    context = _correlation_context.get()
    if context and context.metadata is not None:
        context.metadata[key] = value


def set_run_context(
    run_id: str,
    commit_sha: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    pr_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CorrelationContext:
    """Set correlation context for a CI/CD run.

    Args:
        run_id: Run ID
        commit_sha: Git commit SHA
        repo: Repository name/URL
        branch: Git branch name
        pr_id: Pull/Merge request ID
        metadata: Additional metadata

    Returns:
        The created correlation context
    """
    return set_correlation_id(
        run_id=run_id,
        commit_sha=commit_sha,
        repo=repo,
        branch=branch,
        pr_id=pr_id,
        metadata=metadata,
    )


def set_request_context(
    request_id: str,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CorrelationContext:
    """Set correlation context for an API request.

    Args:
        request_id: Request ID
        user_id: User ID
        metadata: Additional metadata

    Returns:
        The created correlation context
    """
    return set_correlation_id(
        request_id=request_id,
        user_id=user_id,
        metadata=metadata,
    )


class CorrelationContextManager:
    """Context manager for correlation IDs."""

    def __init__(
        self,
        correlation_id: str | None = None,
        run_id: str | None = None,
        commit_sha: str | None = None,
        repo: str | None = None,
        branch: str | None = None,
        pr_id: str | None = None,
        request_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Initialize the context manager."""
        self.correlation_id = correlation_id
        self.run_id = run_id
        self.commit_sha = commit_sha
        self.repo = repo
        self.branch = branch
        self.pr_id = pr_id
        self.request_id = request_id
        self.user_id = user_id
        self.metadata = metadata
        self._previous_context: CorrelationContext | None = None

    def __enter__(self) -> CorrelationContext:
        """Enter the context."""
        self._previous_context = _correlation_context.get()

        return set_correlation_id(
            correlation_id=self.correlation_id,
            run_id=self.run_id,
            commit_sha=self.commit_sha,
            repo=self.repo,
            branch=self.branch,
            pr_id=self.pr_id,
            request_id=self.request_id,
            user_id=self.user_id,
            metadata=self.metadata,
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        _correlation_context.set(self._previous_context)


# Convenience functions for common use cases
def run_correlation_context(
    run_id: str,
    commit_sha: str | None = None,
    repo: str | None = None,
    branch: str | None = None,
    pr_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CorrelationContextManager:
    """Create a correlation context manager for a CI/CD run."""
    return CorrelationContextManager(
        run_id=run_id,
        commit_sha=commit_sha,
        repo=repo,
        branch=branch,
        pr_id=pr_id,
        metadata=metadata,
    )


def request_correlation_context(
    request_id: str,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> CorrelationContextManager:
    """Create a correlation context manager for an API request."""
    return CorrelationContextManager(
        request_id=request_id,
        user_id=user_id,
        metadata=metadata,
    )
