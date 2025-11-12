"""Utilities for tracking page state prior to modifications."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, UTC


@dataclass(slots=True)
class PageSnapshot:
    """Represents a concrete snapshot of a page's content."""

    page_id: str
    content: str
    version: int | None
    captured_at: datetime


class PageRollbackRegistry:
    """Registry that stores page snapshots prior to modifications."""

    def __init__(self, max_history: int = 5) -> None:
        if max_history < 1:
            msg = "max_history must be at least 1"
            raise ValueError(msg)
        self._max_history = max_history
        self._history: dict[str, deque[PageSnapshot]] = {}

    def record_snapshot(
        self,
        page_id: str,
        content: str,
        version: int | None,
        *,
        captured_at: datetime | None = None,
    ) -> PageSnapshot:
        """Store a snapshot for the provided page identifier."""
        snapshot = PageSnapshot(
            page_id=page_id,
            content=content,
            version=version,
            captured_at=captured_at or datetime.now(UTC),
        )
        history = self._history.setdefault(page_id, deque(maxlen=self._max_history))
        history.append(snapshot)
        return snapshot

    def get_history(self, page_id: str) -> deque[PageSnapshot]:
        """Return the stored history for the provided page."""
        return self._history.get(page_id, deque())
