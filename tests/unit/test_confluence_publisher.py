from __future__ import annotations

from unittest.mock import Mock

import pytest

from services.confluence_publisher import ConfluencePublisher, RollbackError
from services.page_rollback import PageRollbackRegistry


def _make_publisher(
    client: Mock, registry: PageRollbackRegistry | None = None
) -> ConfluencePublisher:
    """Helper to build a publisher with optional registry."""
    return ConfluencePublisher(client=client, rollback_registry=registry)


def test_update_page_records_snapshot_on_success() -> None:
    client = Mock()
    client.get_page.return_value = {"content": "<existing>", "version": 3}
    client.update_page.return_value = {"id": "42"}
    registry = PageRollbackRegistry()
    publisher = _make_publisher(client, registry)

    payload = {"id": "42", "content": "<new>"}

    result = publisher.update_page(payload)

    assert result == {"id": "42"}
    client.update_page.assert_called_once_with(payload)
    history = registry.get_history("42")
    assert len(history) == 1
    snapshot = registry.latest_snapshot("42")
    assert snapshot is not None
    assert snapshot.content == "<existing>"
    assert snapshot.version == 3


def test_update_page_rolls_back_to_snapshot_on_failure() -> None:
    client = Mock()
    client.get_page.return_value = {"content": "<stable>", "version": 5}
    client.update_page.side_effect = [RuntimeError("update failed"), {"id": "42"}]
    registry = PageRollbackRegistry()
    publisher = _make_publisher(client, registry)

    payload = {"id": "42", "content": "<new>"}

    with pytest.raises(RollbackError) as exc_info:
        publisher.update_page(payload)

    assert "update failed" in str(exc_info.value.original_error)
    assert client.update_page.call_count == 2
    restore_call = client.update_page.call_args_list[1]
    assert restore_call.args[0] == {
        "id": "42",
        "content": "<stable>",
        "version": 5,
    }


def test_create_page_records_snapshot_when_successful() -> None:
    client = Mock()
    client.create_page.return_value = {"id": "abc", "version": 12}
    registry = PageRollbackRegistry()
    publisher = _make_publisher(client, registry)

    payload = {"title": "Test", "content": "<generated>"}

    result = publisher.create_page(payload)

    assert result == {"id": "abc", "version": 12}
    snapshot = registry.latest_snapshot("abc")
    assert snapshot is not None
    assert snapshot.content == "<generated>"
    assert snapshot.version == 12


def test_create_page_rolls_back_when_snapshot_available() -> None:
    client = Mock()
    client.create_page.side_effect = RuntimeError("create failed")
    client.update_page.return_value = {"id": "abc"}
    registry = PageRollbackRegistry()
    registry.record_snapshot(page_id="abc", content="<previous>", version=7)
    publisher = _make_publisher(client, registry)

    payload = {"id": "abc", "content": "<generated>"}

    with pytest.raises(RollbackError) as exc_info:
        publisher.create_page(payload)

    assert "create failed" in str(exc_info.value.original_error)
    client.update_page.assert_called_with(
        {"id": "abc", "content": "<previous>", "version": 7},
    )


def test_create_page_failure_without_snapshot_propagates_original() -> None:
    client = Mock()
    client.create_page.side_effect = RuntimeError("create failed")
    registry = PageRollbackRegistry()
    publisher = _make_publisher(client, registry)

    payload = {"id": "missing", "content": "<generated>"}

    with pytest.raises(RuntimeError, match="create failed"):
        publisher.create_page(payload)

    client.update_page.assert_not_called()
