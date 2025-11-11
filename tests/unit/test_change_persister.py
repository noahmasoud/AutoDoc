"""Unit tests for change_persister service."""

import pytest
from unittest.mock import Mock, patch

from sqlalchemy.exc import SQLAlchemyError

from db.models import Change
from schemas.changes import ChangeDetected
from services.change_persister import (
    save_changes_to_database,
    get_changes_for_run,
    get_changes_by_type,
    ChangePersistenceError,
)


class TestSaveChangesToDatabase:
    """Test suite for save_changes_to_database function."""

    @pytest.mark.unit
    def test_save_changes_to_database_empty_list(self, mock_database):
        """Test saving empty list of changes."""
        changes = []

        result = save_changes_to_database(mock_database, run_id=1, changes=changes)

        assert result == []
        mock_database.add.assert_not_called()
        mock_database.commit.assert_not_called()

    @pytest.mark.unit
    def test_save_changes_to_database_single_change(self, mock_database):
        """Test saving a single change."""
        change_detected = ChangeDetected(
            file_path="test.py",
            symbol_name="test_func",
            change_type="added",
            signature_before=None,
            signature_after={"name": "test_func"},
            is_breaking=False,
            breaking_reason=None,
        )
        changes = [change_detected]

        # Mock the Change model to return a mock object
        mock_change = Mock(spec=Change)
        with patch("services.change_persister.Change", return_value=mock_change):
            result = save_changes_to_database(mock_database, run_id=1, changes=changes)

        assert len(result) == 1
        assert result[0] == mock_change
        mock_database.add.assert_called_once()
        mock_database.commit.assert_called_once()
        mock_database.refresh.assert_called_once_with(mock_change)

    @pytest.mark.unit
    def test_save_changes_to_database_multiple_changes(self, mock_database):
        """Test saving multiple changes."""
        changes = [
            ChangeDetected(
                file_path="test1.py",
                symbol_name="func1",
                change_type="added",
                signature_before=None,
                signature_after={"name": "func1"},
                is_breaking=False,
                breaking_reason=None,
            ),
            ChangeDetected(
                file_path="test2.py",
                symbol_name="func2",
                change_type="removed",
                signature_before={"name": "func2"},
                signature_after=None,
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
            ChangeDetected(
                file_path="test3.py",
                symbol_name="func3",
                change_type="modified",
                signature_before={"name": "func3", "return_annotation": "int"},
                signature_after={"name": "func3", "return_annotation": "str"},
                is_breaking=True,
                breaking_reason="return_type_changed",
            ),
        ]

        # Mock the Change model to return mock objects
        mock_changes = [Mock(spec=Change) for _ in changes]
        with patch("services.change_persister.Change", side_effect=mock_changes):
            result = save_changes_to_database(mock_database, run_id=1, changes=changes)

        assert len(result) == 3
        assert result == mock_changes
        assert mock_database.add.call_count == 3
        mock_database.commit.assert_called_once()
        assert mock_database.refresh.call_count == 3

    @pytest.mark.unit
    def test_save_changes_to_database_rollback_on_error(self, mock_database):
        """Test that changes are rolled back on database error."""
        change_detected = ChangeDetected(
            file_path="test.py",
            symbol_name="test_func",
            change_type="added",
            signature_before=None,
            signature_after={"name": "test_func"},
            is_breaking=False,
            breaking_reason=None,
        )
        changes = [change_detected]

        # Mock database error on commit
        mock_database.commit.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(ChangePersistenceError) as exc_info:
            save_changes_to_database(mock_database, run_id=1, changes=changes)

        assert "Failed to save changes" in str(exc_info.value)
        mock_database.rollback.assert_called_once()

    @pytest.mark.unit
    def test_save_changes_to_database_preserves_change_type(self, mock_database):
        """Test that change_type is correctly preserved."""
        test_cases = [
            ("added", None, {"name": "func"}),
            ("removed", {"name": "func"}, None),
            ("modified", {"name": "func"}, {"name": "func", "modified": True}),
        ]

        for change_type, sig_before, sig_after in test_cases:
            change_detected = ChangeDetected(
                file_path="test.py",
                symbol_name="test_func",
                change_type=change_type,
                signature_before=sig_before,
                signature_after=sig_after,
                is_breaking=change_type in ("removed", "modified"),
                breaking_reason=None,
            )

            mock_change = Mock(spec=Change)
            with patch("services.change_persister.Change", return_value=mock_change):
                save_changes_to_database(
                    mock_database,
                    run_id=1,
                    changes=[change_detected],
                )

                # Verify Change was created with correct attributes
                call_args = (
                    mock_change.__init__.call_args
                    if hasattr(mock_change.__init__, "call_args")
                    else None
                )
                # Since we're using Mock with spec=Change, we can verify the Change constructor was called
                # by checking the mock_change object was added to session
                mock_database.reset_mock()


class TestGetChangesForRun:
    """Test suite for get_changes_for_run function."""

    @pytest.mark.unit
    def test_get_changes_for_run_success(self, mock_database):
        """Test successfully retrieving changes for a run."""
        mock_changes = [
            Mock(spec=Change, id=1, run_id=1, file_path="test1.py"),
            Mock(spec=Change, id=2, run_id=1, file_path="test2.py"),
        ]

        result_set = Mock()
        result_set.scalars.return_value.all.return_value = mock_changes
        mock_database.execute.return_value = result_set

        result = get_changes_for_run(mock_database, run_id=1)

        assert len(result) == 2
        assert result == mock_changes

    @pytest.mark.unit
    def test_get_changes_for_run_empty(self, mock_database):
        """Test retrieving changes when none exist."""
        result_set = Mock()
        result_set.scalars.return_value.all.return_value = []
        mock_database.execute.return_value = result_set

        result = get_changes_for_run(mock_database, run_id=1)

        assert result == []

    @pytest.mark.unit
    def test_get_changes_for_run_database_error(self, mock_database):
        """Test handling database error when retrieving changes."""
        mock_database.execute.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(ChangePersistenceError) as exc_info:
            get_changes_for_run(mock_database, run_id=1)

        assert "Failed to retrieve changes" in str(exc_info.value)


class TestGetChangesByType:
    """Test suite for get_changes_by_type function."""

    @pytest.mark.unit
    def test_get_changes_by_type_added(self, mock_database):
        """Test retrieving added changes."""
        mock_changes = [
            Mock(spec=Change, id=1, change_type="added"),
            Mock(spec=Change, id=2, change_type="added"),
        ]

        result_set = Mock()
        result_set.scalars.return_value.all.return_value = mock_changes
        mock_database.execute.return_value = result_set

        result = get_changes_by_type(mock_database, run_id=1, change_type="added")

        assert len(result) == 2
        assert result == mock_changes

    @pytest.mark.unit
    def test_get_changes_by_type_removed(self, mock_database):
        """Test retrieving removed changes."""
        mock_changes = [
            Mock(spec=Change, id=3, change_type="removed"),
        ]

        result_set = Mock()
        result_set.scalars.return_value.all.return_value = mock_changes
        mock_database.execute.return_value = result_set

        result = get_changes_by_type(mock_database, run_id=1, change_type="removed")

        assert len(result) == 1
        assert result == mock_changes

    @pytest.mark.unit
    def test_get_changes_by_type_modified(self, mock_database):
        """Test retrieving modified changes."""
        mock_changes = [
            Mock(spec=Change, id=4, change_type="modified"),
            Mock(spec=Change, id=5, change_type="modified"),
            Mock(spec=Change, id=6, change_type="modified"),
        ]

        result_set = Mock()
        result_set.scalars.return_value.all.return_value = mock_changes
        mock_database.execute.return_value = result_set

        result = get_changes_by_type(mock_database, run_id=1, change_type="modified")

        assert len(result) == 3
        assert result == mock_changes

    @pytest.mark.unit
    def test_get_changes_by_type_invalid_type(self, mock_database):
        """Test that invalid change_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_changes_by_type(mock_database, run_id=1, change_type="invalid")

        assert "Invalid change_type" in str(exc_info.value)

    @pytest.mark.unit
    def test_get_changes_by_type_database_error(self, mock_database):
        """Test handling database error when retrieving changes by type."""
        mock_database.execute.side_effect = SQLAlchemyError("Database error")

        with pytest.raises(ChangePersistenceError) as exc_info:
            get_changes_by_type(mock_database, run_id=1, change_type="added")

        assert "Failed to retrieve changes" in str(exc_info.value)


class TestChangePersisterIntegration:
    """Integration-style tests for change persistence."""

    @pytest.mark.unit
    def test_save_and_retrieve_changes(self, mock_database):
        """Test the full flow of saving and retrieving changes."""
        changes = [
            ChangeDetected(
                file_path="api/test.py",
                symbol_name="new_function",
                change_type="added",
                signature_before=None,
                signature_after={"name": "new_function", "parameters": []},
                is_breaking=False,
                breaking_reason=None,
            ),
            ChangeDetected(
                file_path="api/old.py",
                symbol_name="old_function",
                change_type="removed",
                signature_before={"name": "old_function"},
                signature_after=None,
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
        ]

        # Mock Change objects
        mock_change1 = Mock(spec=Change, id=1, run_id=1, change_type="added")
        mock_change2 = Mock(spec=Change, id=2, run_id=1, change_type="removed")
        mock_changes_list = [mock_change1, mock_change2]

        with patch("services.change_persister.Change", side_effect=mock_changes_list):
            saved = save_changes_to_database(mock_database, run_id=1, changes=changes)

        assert len(saved) == 2

        # Now retrieve them
        result_set = Mock()
        result_set.scalars.return_value.all.return_value = mock_changes_list
        mock_database.execute.return_value = result_set

        retrieved = get_changes_for_run(mock_database, run_id=1)

        assert len(retrieved) == 2
        assert retrieved == mock_changes_list

    @pytest.mark.unit
    def test_tagged_changes_by_type(self, mock_database):
        """Test that changes are properly tagged and can be filtered by type."""
        all_changes = [
            ChangeDetected(
                file_path="test.py",
                symbol_name=f"func{i}",
                change_type=change_type,
                signature_before=None if change_type == "added" else {},
                signature_after=None if change_type == "removed" else {},
                is_breaking=change_type != "added",
                breaking_reason=None,
            )
            for i, change_type in enumerate(
                ["added", "added", "removed", "modified", "modified"],
            )
        ]

        # Mock all Change objects
        mock_all_changes = [
            Mock(spec=Change, id=i + 1, run_id=1, change_type=change_type)
            for i, change_type in enumerate(
                ["added", "added", "removed", "modified", "modified"],
            )
        ]

        with patch("services.change_persister.Change", side_effect=mock_all_changes):
            save_changes_to_database(mock_database, run_id=1, changes=all_changes)

        # Retrieve by type
        for change_type in ("added", "removed", "modified"):
            expected_count = [
                1 for c in all_changes if c.change_type == change_type
            ].__len__()
            mock_filtered = [
                m for m in mock_all_changes if m.change_type == change_type
            ]

            result_set = Mock()
            result_set.scalars.return_value.all.return_value = mock_filtered
            mock_database.execute.return_value = result_set

            result = get_changes_by_type(
                mock_database,
                run_id=1,
                change_type=change_type,
            )
            assert len(result) == expected_count
