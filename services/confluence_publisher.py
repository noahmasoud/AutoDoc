"""High-level publisher that coordinates Confluence page updates."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from services.page_rollback import PageRollbackRegistry, PageSnapshot


logger = logging.getLogger(__name__)


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
        run_mode: str = "PRODUCTION",
    ) -> None:
        self._client = client
        self._rollback_registry = rollback_registry or PageRollbackRegistry()
        self._run_mode = run_mode

    @property
    def rollback_registry(self) -> PageRollbackRegistry:
        """Expose the rollback registry for external inspection."""
        return self._rollback_registry

    def update_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a Confluence page after recording the previous snapshot."""

        if self._run_mode == "TEST":
            logger.info(
                "TEST MODE: Skipping Confluence page update for page %s",
                payload.get("id"),
            )
            return {"id": payload.get("id"), "status": "test_mode_skipped"}

        page_id = payload.get("id")
        if not page_id:
            msg = "update payload must include 'id'"
            raise ValueError(msg)

        current_state = self._client.get_page(page_id)
        snapshot: PageSnapshot | None = None
        if current_state is not None:
            content = current_state.get("content", "")
            version = current_state.get("version")
            snapshot = self._rollback_registry.record_snapshot(
                page_id=page_id,
                content=str(content),
                version=version if isinstance(version, int) else None,
            )
            logger.debug(
                "Recorded rollback snapshot for page '%s' (version=%s)",
                page_id,
                snapshot.version,
            )
        try:
            return self._client.update_page(payload)
        except Exception as exc:
            logger.exception(
                "Page update failed for '%s'; attempting rollback",
                page_id,
            )

            snapshot = snapshot or self._rollback_registry.latest_snapshot(page_id)
            if snapshot is None:
                logger.exception(
                    "Rollback skipped for page '%s'; no snapshot available",
                    page_id,
                )
                raise

            restore_error: Exception | None = None
            try:
                logger.warning(
                    "Restoring page '%s' to captured version %s",
                    page_id,
                    snapshot.version,
                )
                self._restore_snapshot(snapshot)
            except Exception as rollback_exc:
                restore_error = rollback_exc
                logger.exception(
                    "Rollback attempt failed for page '%s'",
                    page_id,
                )
            else:
                logger.info(
                    "Rollback completed successfully for page '%s'",
                    page_id,
                )

            raise RollbackError(
                page_id=page_id,
                original_error=exc,
                restore_error=restore_error,
            ) from exc

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Confluence page. The resulting snapshot is tracked for rollback."""
        if self._run_mode == "TEST":
            logger.info(
                "TEST MODE: Skipping Confluence page creation for page %s",
                payload.get("id"),
            )
            return {"id": payload.get("id"), "status": "test_mode_skipped"}

        try:
            result = self._client.create_page(payload)
        except Exception as exc:
            logger.exception(
                "Page creation failed; attempting rollback using latest snapshot",
            )
            page_id = payload.get("id")
            if not page_id:
                logger.exception(
                    "Rollback skipped for create attempt; payload missing 'id'",
                )
                raise

            snapshot = self._rollback_registry.latest_snapshot(page_id)
            if snapshot is None:
                logger.exception(
                    "Rollback skipped for page '%s'; no snapshot available",
                    page_id,
                )
                raise

            restore_error: Exception | None = None
            try:
                logger.warning(
                    "Restoring page '%s' to captured version %s",
                    page_id,
                    snapshot.version,
                )
                self._restore_snapshot(snapshot)
            except Exception as rollback_exc:
                restore_error = rollback_exc
                logger.exception(
                    "Rollback attempt failed for page '%s'",
                    page_id,
                )
            else:
                logger.info(
                    "Rollback completed successfully for page '%s'",
                    page_id,
                )

            raise RollbackError(
                page_id=page_id,
                original_error=exc,
                restore_error=restore_error,
            ) from exc

        page_id = result.get("id")
        if page_id:
            content = payload.get("content", "")
            self._rollback_registry.record_snapshot(
                page_id=page_id,
                content=str(content),
                version=result.get("version"),
            )
            logger.debug(
                "Recorded snapshot for newly created page '%s' (version=%s)",
                page_id,
                result.get("version"),
            )
        return result

    def _restore_snapshot(self, snapshot: PageSnapshot) -> dict[str, Any]:
        """Restore the provided snapshot using the client update operation."""
        restore_payload: dict[str, Any] = {
            "id": snapshot.page_id,
            "content": snapshot.content,
        }
        if snapshot.version is not None:
            restore_payload["version"] = snapshot.version
        return self._client.update_page(restore_payload)


class RollbackError(RuntimeError):
    """Raised when a page operation fails and rollback is attempted."""

    def __init__(
        self,
        *,
        page_id: str,
        original_error: Exception,
        restore_error: Exception | None,
    ) -> None:
        details = (
            f"Rollback attempted for page '{page_id}' after failure: {original_error!s}"
        )
        if restore_error is not None:
            details = f"{details}. Rollback attempt also failed: {restore_error!s}"
        super().__init__(details)
        self.page_id = page_id
        self.original_error = original_error
        self.restore_error = restore_error
