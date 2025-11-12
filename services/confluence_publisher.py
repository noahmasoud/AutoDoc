"""High-level publisher that coordinates Confluence page updates."""

from __future__ import annotations

from typing import Any, Protocol

from services.page_rollback import PageRollbackRegistry


class ConfluenceClientProtocol(Protocol):
    """Protocol describing the Confluence client operations used by the publisher."""

    def get_page(self, page_id: str) -> dict[str, Any] | None: ...

    def update_page(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]: ...


class ConfluencePublisher:
    """Coordinates Confluence page operations while tracking snapshot history."""

    def __init__(
        self,
        client: ConfluenceClientProtocol,
        rollback_registry: PageRollbackRegistry | None = None,
    ) -> None:
        self._client = client
        self._rollback_registry = rollback_registry or PageRollbackRegistry()

    @property
    def rollback_registry(self) -> PageRollbackRegistry:
        """Expose the rollback registry for external inspection."""
        return self._rollback_registry

    def update_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a Confluence page after recording the previous snapshot."""
        page_id = payload.get("id")
        if not page_id:
            msg = "update payload must include 'id'"
            raise ValueError(msg)

        current_state = self._client.get_page(page_id)
        if current_state is not None:
            content = current_state.get("content", "")
            version = current_state.get("version")
            self._rollback_registry.record_snapshot(
                page_id=page_id,
                content=str(content),
                version=version if isinstance(version, int) else None,
            )

        return self._client.update_page(payload)

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Confluence page. The resulting snapshot is tracked for rollback."""
        result = self._client.create_page(payload)
        page_id = result.get("id")
        if page_id:
            content = payload.get("content", "")
            self._rollback_registry.record_snapshot(
                page_id=page_id,
                content=str(content),
                version=result.get("version"),
            )
        return result
