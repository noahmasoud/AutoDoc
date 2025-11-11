"""Unit tests for artifact loader service."""

from datetime import datetime
from unittest.mock import MagicMock
import pytest

from db.models import Run, Change
from schemas.changes import RunArtifact, SymbolData, SignatureInfo
from services.artifact_loader import (
    load_run_artifact,
    load_artifact_from_run,
    ArtifactLoadError,
    _change_to_symbol_data,
    _parse_signature,
)


class TestLoadRunArtifact:
    """Test suite for load_run_artifact function."""

    @pytest.mark.unit
    def test_load_run_artifact_success(self):
        """Test successfully loading a run artifact."""
        # Create mock database session
        db = MagicMock()

        # Create mock run
        mock_run = Run(
            id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.now(),
            completed_at=None,
            status="Awaiting Review",
            correlation_id="corr-123",
        )

        # Create mock change with signature data
        mock_change = Change(
            id=1,
            run_id=1,
            file_path="test_file.py",
            symbol="test_function",
            change_type="added",
            signature_before=None,
            signature_after={
                "name": "test_function",
                "parameters": [
                    {"name": "param1", "annotation": "str", "kind": "pos"},
                ],
                "return_annotation": "int",
                "line_start": 1,
                "line_end": 10,
                "symbol_type": "function",
                "docstring": "Test function",
                "is_public": True,
            },
        )

        db.get.return_value = mock_run
        db.execute.return_value.scalars.return_value.all.return_value = [mock_change]

        # Load artifact
        artifact = load_run_artifact(db, 1)

        # Verify results
        assert isinstance(artifact, RunArtifact)
        assert artifact.run_id == 1
        assert artifact.repo == "test/repo"
        assert artifact.branch == "main"
        assert artifact.commit_sha == "abc123"
        assert len(artifact.symbols) == 1
        assert artifact.symbols[0].symbol_name == "test_function"

    @pytest.mark.unit
    def test_load_run_artifact_not_found(self):
        """Test loading a non-existent run."""
        db = MagicMock()
        db.get.return_value = None

        with pytest.raises(ArtifactLoadError, match="Run 999 not found"):
            load_run_artifact(db, 999)

    @pytest.mark.unit
    def test_load_run_artifact_no_changes(self):
        """Test loading a run with no changes."""
        db = MagicMock()

        mock_run = Run(
            id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.now(),
            completed_at=None,
            status="Awaiting Review",
            correlation_id="corr-123",
        )

        db.get.return_value = mock_run
        db.execute.return_value.scalars.return_value.all.return_value = []

        artifact = load_run_artifact(db, 1)

        assert isinstance(artifact, RunArtifact)
        assert len(artifact.symbols) == 0


class TestLoadArtifactFromRun:
    """Test suite for load_artifact_from_run function."""

    @pytest.mark.unit
    def test_load_artifact_from_run_success(self):
        """Test successfully loading artifact from Run object."""
        db = MagicMock()

        mock_run = Run(
            id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.now(),
            completed_at=None,
            status="Awaiting Review",
            correlation_id="corr-123",
        )

        mock_change = Change(
            id=1,
            run_id=1,
            file_path="test_file.py",
            symbol="test_function",
            change_type="added",
            signature_before=None,
            signature_after={
                "name": "test_function",
                "parameters": [],
                "return_annotation": "None",
                "symbol_type": "function",
            },
        )

        db.execute.return_value.scalars.return_value.all.return_value = [mock_change]

        artifact = load_artifact_from_run(db, mock_run)

        assert isinstance(artifact, RunArtifact)
        assert artifact.run_id == 1
        assert len(artifact.symbols) == 1


class TestChangeToSymbolData:
    """Test suite for _change_to_symbol_data function."""

    @pytest.mark.unit
    def test_change_to_symbol_data_added(self):
        """Test converting 'added' change to symbol data."""
        change = Change(
            id=1,
            run_id=1,
            file_path="test.py",
            symbol="new_func",
            change_type="added",
            signature_before=None,
            signature_after={
                "name": "new_func",
                "parameters": [{"name": "x", "annotation": "int"}],
                "return_annotation": "str",
                "symbol_type": "function",
                "docstring": "New function",
                "is_public": True,
            },
        )

        result = _change_to_symbol_data(change)

        assert result is not None
        assert isinstance(result, SymbolData)
        assert result.symbol_name == "new_func"
        assert result.file_path == "test.py"
        assert result.symbol_type == "function"
        assert result.signature is not None
        assert result.signature.name == "new_func"

    @pytest.mark.unit
    def test_change_to_symbol_data_removed(self):
        """Test converting 'removed' change to symbol data."""
        change = Change(
            id=2,
            run_id=1,
            file_path="test.py",
            symbol="old_func",
            change_type="removed",
            signature_before={
                "name": "old_func",
                "parameters": [],
                "symbol_type": "function",
            },
            signature_after=None,
        )

        result = _change_to_symbol_data(change)

        assert result is not None
        assert result.symbol_name == "old_func"

    @pytest.mark.unit
    def test_change_to_symbol_data_modified(self):
        """Test converting 'modified' change to symbol data."""
        change = Change(
            id=3,
            run_id=1,
            file_path="test.py",
            symbol="modified_func",
            change_type="modified",
            signature_before={"name": "modified_func", "parameters": []},
            signature_after={
                "name": "modified_func",
                "parameters": [{"name": "new_param"}],
                "symbol_type": "function",
            },
        )

        result = _change_to_symbol_data(change)

        assert result is not None
        assert result.symbol_name == "modified_func"
        # Should use signature_after for modified
        assert len(result.signature.parameters) == 1

    @pytest.mark.unit
    def test_change_to_symbol_data_no_signature(self):
        """Test handling change with no signature data."""
        change = Change(
            id=4,
            run_id=1,
            file_path="test.py",
            symbol="incomplete",
            change_type="added",
            signature_before=None,
            signature_after=None,
        )

        result = _change_to_symbol_data(change)

        assert result is None


class TestParseSignature:
    """Test suite for _parse_signature function."""

    @pytest.mark.unit
    def test_parse_signature_complete(self):
        """Test parsing a complete signature."""
        signature_data = {
            "name": "test_func",
            "parameters": [
                {
                    "name": "param1",
                    "annotation": "str",
                    "default_value": None,
                    "kind": "pos",
                },
                {
                    "name": "param2",
                    "annotation": "int",
                    "default_value": "0",
                    "kind": "keyword",
                },
            ],
            "return_annotation": "bool",
            "line_start": 42,
            "line_end": 50,
        }

        result = _parse_signature(signature_data)

        assert result is not None
        assert isinstance(result, SignatureInfo)
        assert result.name == "test_func"
        assert len(result.parameters) == 2
        assert result.parameters[0].name == "param1"
        assert result.parameters[0].annotation == "str"
        assert result.return_annotation == "bool"
        assert result.line_start == 42
        assert result.line_end == 50

    @pytest.mark.unit
    def test_parse_signature_minimal(self):
        """Test parsing a minimal signature."""
        signature_data = {
            "name": "simple_func",
            "parameters": [],
        }

        result = _parse_signature(signature_data)

        assert result is not None
        assert result.name == "simple_func"
        assert len(result.parameters) == 0

    @pytest.mark.unit
    def test_parse_signature_empty(self):
        """Test parsing empty signature data."""
        result = _parse_signature({})

        assert result is not None
        assert result.name == ""
        assert len(result.parameters) == 0

    @pytest.mark.unit
    def test_parse_signature_malformed(self):
        """Test handling malformed signature data."""
        # Invalid structure should not crash but return None or partial data
        signature_data = None
        result = _parse_signature(signature_data)
        assert result is None
