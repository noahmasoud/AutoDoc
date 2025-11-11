"""Unit tests for change detector service."""

import pytest

from schemas.changes import (
    RunArtifact,
    SymbolData,
    SignatureInfo,
    ParameterInfo,
)
from services.change_detector import (
    detect_changes,
    get_breaking_changes_summary,
    _create_symbol_map,
    _get_symbol_key,
    _parameters_differ,
    _is_breaking_change,
)


class TestDetectChanges:
    """Test suite for detect_changes function."""

    @pytest.mark.unit
    def test_detect_changes_no_previous_artifact(self):
        """Test detecting changes when no previous artifact exists."""
        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="test_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="test_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        current_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[current_symbol],
        )

        changes = detect_changes(None, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "added"
        assert changes[0].symbol_name == "test_func"
        assert changes[0].signature_before is None
        assert changes[0].signature_after is not None
        assert changes[0].is_breaking is False

    @pytest.mark.unit
    def test_detect_changes_added_symbol(self):
        """Test detecting an added symbol."""
        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[],
        )

        new_symbol = SymbolData(
            file_path="test.py",
            symbol_name="new_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="new_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="int",
            ),
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[new_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "added"
        assert changes[0].symbol_name == "new_func"
        assert changes[0].is_breaking is False

    @pytest.mark.unit
    def test_detect_changes_removed_symbol(self):
        """Test detecting a removed symbol."""
        removed_symbol = SymbolData(
            file_path="test.py",
            symbol_name="old_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="old_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[removed_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "removed"
        assert changes[0].symbol_name == "old_func"
        assert changes[0].is_breaking is True  # Removals are always breaking

    @pytest.mark.unit
    def test_detect_changes_no_modifications(self):
        """Test when symbols haven't changed."""
        symbol = SymbolData(
            file_path="test.py",
            symbol_name="unchanged_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="unchanged_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="int",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 0

    @pytest.mark.unit
    def test_detect_changes_modified_return_type(self):
        """Test detecting a modified return type (breaking change)."""
        previous_symbol = SymbolData(
            file_path="test.py",
            symbol_name="modified_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="modified_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="modified_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="modified_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="str",  # Changed return type
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True  # Return type change is breaking

    @pytest.mark.unit
    def test_detect_changes_parameter_added(self):
        """Test detecting a parameter addition (non-breaking)."""
        previous_symbol = SymbolData(
            file_path="test.py",
            symbol_name="add_param_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="add_param_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="add_param_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="add_param_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="None",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True  # Parameter addition is breaking

    @pytest.mark.unit
    def test_detect_changes_parameter_removed(self):
        """Test detecting a parameter removal (breaking)."""
        previous_symbol = SymbolData(
            file_path="test.py",
            symbol_name="remove_param_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="remove_param_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="None",
            ),
        )

        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="remove_param_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="remove_param_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True  # Parameter removal is breaking

    @pytest.mark.unit
    def test_detect_changes_docstring_changed(self):
        """Test detecting a docstring change (non-breaking)."""
        previous_symbol = SymbolData(
            file_path="test.py",
            symbol_name="doc_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="doc_func",
                parameters=[],
                return_annotation="None",
            ),
            docstring="Old docstring",
        )

        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="doc_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="doc_func",
                parameters=[],
                return_annotation="None",
            ),
            docstring="New docstring",
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is False  # Docstring change is not breaking

    @pytest.mark.unit
    def test_detect_changes_complex_scenario(self):
        """Test detecting multiple types of changes simultaneously."""
        # Previous: func1, func2, old_func
        previous_symbols = [
            SymbolData(
                file_path="test.py",
                symbol_name="func1",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func1",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="int",
                ),
            ),
            SymbolData(
                file_path="test.py",
                symbol_name="func2",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func2",
                    parameters=[],
                    return_annotation="str",
                ),
            ),
            SymbolData(
                file_path="test.py",
                symbol_name="old_func",
                symbol_type="function",
                signature=SignatureInfo(
                    name="old_func",
                    parameters=[],
                    return_annotation="None",
                ),
            ),
        ]

        # Current: func1 (modified), new_func
        current_symbols = [
            SymbolData(
                file_path="test.py",
                symbol_name="func1",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func1",
                    parameters=[
                        ParameterInfo(name="x", annotation="str"),  # Type changed
                    ],
                    return_annotation="int",
                ),
            ),
            SymbolData(
                file_path="test.py",
                symbol_name="func2",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func2",
                    parameters=[],
                    return_annotation="str",
                ),
            ),
            SymbolData(
                file_path="test.py",
                symbol_name="new_func",
                symbol_type="function",
                signature=SignatureInfo(
                    name="new_func",
                    parameters=[],
                    return_annotation="None",
                ),
            ),
        ]

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=previous_symbols,
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=current_symbols,
        )

        changes = detect_changes(previous_artifact, current_artifact)

        # Should detect:
        # - 1 removal (old_func)
        # - 1 addition (new_func)
        # - 1 modification (func1 parameter type changed)
        assert len(changes) == 3

        # Find each change type
        addition = next(c for c in changes if c.change_type == "added")
        removal = next(c for c in changes if c.change_type == "removed")
        modification = next(c for c in changes if c.change_type == "modified")

        assert addition.symbol_name == "new_func"
        assert removal.symbol_name == "old_func"
        assert modification.symbol_name == "func1"
        assert modification.is_breaking is True  # Parameter type change is breaking


class TestUtilityFunctions:
    """Test suite for utility functions."""

    @pytest.mark.unit
    def test_get_symbol_key(self):
        """Test symbol key generation."""
        symbol = SymbolData(
            file_path="path/to/file.py",
            symbol_name="my_function",
            symbol_type="function",
        )

        key = _get_symbol_key(symbol)
        assert key == "path/to/file.py:my_function:function"

    @pytest.mark.unit
    def test_create_symbol_map(self):
        """Test creating symbol map."""
        symbols = [
            SymbolData(
                file_path="test.py",
                symbol_name="func1",
                symbol_type="function",
            ),
            SymbolData(
                file_path="test.py",
                symbol_name="func2",
                symbol_type="function",
            ),
        ]

        symbol_map = _create_symbol_map(symbols)
        assert len(symbol_map) == 2
        assert "test.py:func1:function" in symbol_map
        assert "test.py:func2:function" in symbol_map

    @pytest.mark.unit
    def test_parameters_differ_name(self):
        """Test parameter comparison - different names."""
        param1 = ParameterInfo(name="x", annotation="int")
        param2 = ParameterInfo(name="y", annotation="int")

        assert _parameters_differ(param1, param2) is True

    @pytest.mark.unit
    def test_parameters_differ_annotation(self):
        """Test parameter comparison - different annotations."""
        param1 = ParameterInfo(name="x", annotation="int")
        param2 = ParameterInfo(name="x", annotation="str")

        assert _parameters_differ(param1, param2) is True

    @pytest.mark.unit
    def test_parameters_differ_default(self):
        """Test parameter comparison - different default values."""
        param1 = ParameterInfo(name="x", annotation="int", default_value="0")
        param2 = ParameterInfo(name="x", annotation="int", default_value="1")

        assert _parameters_differ(param1, param2) is True

    @pytest.mark.unit
    def test_parameters_same(self):
        """Test parameter comparison - same parameters."""
        param1 = ParameterInfo(name="x", annotation="int")
        param2 = ParameterInfo(name="x", annotation="int")

        assert _parameters_differ(param1, param2) is False

    @pytest.mark.unit
    def test_is_breaking_change_return_type(self):
        """Test breaking change detection - return type change."""
        prev_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[],
                return_annotation="int",
            ),
        )

        curr_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[],
                return_annotation="str",
            ),
        )

        assert _is_breaking_change(prev_symbol, curr_symbol) is True

    @pytest.mark.unit
    def test_is_breaking_change_param_removed(self):
        """Test breaking change detection - parameter removed."""
        prev_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="None",
            ),
        )

        curr_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[],
                return_annotation="None",
            ),
        )

        assert _is_breaking_change(prev_symbol, curr_symbol) is True

    @pytest.mark.unit
    def test_is_breaking_change_param_type_changed(self):
        """Test breaking change detection - parameter type changed."""
        prev_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="None",
            ),
        )

        curr_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[
                    ParameterInfo(name="x", annotation="str"),
                ],
                return_annotation="None",
            ),
        )

        assert _is_breaking_change(prev_symbol, curr_symbol) is True

    @pytest.mark.unit
    def test_is_breaking_change_non_breaking(self):
        """Test breaking change detection - non-breaking docstring change."""
        prev_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[],
                return_annotation="None",
            ),
            docstring="Old doc",
        )

        curr_symbol = SymbolData(
            file_path="test.py",
            symbol_name="func",
            symbol_type="function",
            signature=SignatureInfo(
                name="func",
                parameters=[],
                return_annotation="None",
            ),
            docstring="New doc",
        )

        assert _is_breaking_change(prev_symbol, curr_symbol) is False


class TestBreakingChangesSummary:
    """Test suite for get_breaking_changes_summary function."""

    @pytest.mark.unit
    def test_get_breaking_changes_summary_empty(self):
        """Test summary with no changes."""
        summary = get_breaking_changes_summary([])

        assert summary["total_changes"] == 0
        assert summary["breaking_count"] == 0
        assert summary["non_breaking_count"] == 0
        assert summary["breaking_percentage"] == 0.0
        assert summary["categories"] == {}
        assert summary["breaking_changes"] == []

    @pytest.mark.unit
    def test_get_breaking_changes_summary_mixed(self):
        """Test summary with mixed breaking and non-breaking changes."""
        from schemas.changes import ChangeDetected

        changes = [
            ChangeDetected(
                file_path="test.py",
                symbol_name="func1",
                change_type="added",
                signature_before=None,
                signature_after={},
                is_breaking=False,
                breaking_reason=None,
            ),
            ChangeDetected(
                file_path="test.py",
                symbol_name="func2",
                change_type="removed",
                signature_before={},
                signature_after=None,
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
            ChangeDetected(
                file_path="test.py",
                symbol_name="func3",
                change_type="modified",
                signature_before={},
                signature_after={},
                is_breaking=True,
                breaking_reason="return_type_changed",
            ),
        ]

        summary = get_breaking_changes_summary(changes)

        assert summary["total_changes"] == 3
        assert summary["breaking_count"] == 2
        assert summary["non_breaking_count"] == 1
        assert summary["breaking_percentage"] == pytest.approx(66.67, rel=1e-1)
        assert "symbol_removed" in summary["categories"]
        assert "return_type_changed" in summary["categories"]
        assert len(summary["breaking_changes"]) == 2

    @pytest.mark.unit
    def test_get_breaking_changes_summary_categories(self):
        """Test summary categorizes breaking changes correctly."""
        from schemas.changes import ChangeDetected

        changes = [
            ChangeDetected(
                file_path="test.py",
                symbol_name="func1",
                change_type="modified",
                signature_before={},
                signature_after={},
                is_breaking=True,
                breaking_reason="parameter_type_changed:x",
            ),
            ChangeDetected(
                file_path="test.py",
                symbol_name="func2",
                change_type="modified",
                signature_before={},
                signature_after={},
                is_breaking=True,
                breaking_reason="parameter_type_changed:y",
            ),
            ChangeDetected(
                file_path="test.py",
                symbol_name="func3",
                change_type="modified",
                signature_before={},
                signature_after={},
                is_breaking=True,
                breaking_reason="parameter_added",
            ),
        ]

        summary = get_breaking_changes_summary(changes)

        assert summary["breaking_count"] == 3
        assert summary["categories"]["parameter_type_changed"] == 2
        assert summary["categories"]["parameter_added"] == 1

    @pytest.mark.unit
    def test_get_breaking_changes_summary_all_breaking(self):
        """Test summary when all changes are breaking."""
        from schemas.changes import ChangeDetected

        changes = [
            ChangeDetected(
                file_path="test.py",
                symbol_name="func1",
                change_type="removed",
                signature_before={},
                signature_after=None,
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
            ChangeDetected(
                file_path="test.py",
                symbol_name="func2",
                change_type="removed",
                signature_before={},
                signature_after=None,
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
        ]

        summary = get_breaking_changes_summary(changes)

        assert summary["total_changes"] == 2
        assert summary["breaking_count"] == 2
        assert summary["non_breaking_count"] == 0
        assert summary["breaking_percentage"] == 100.0

    @pytest.mark.unit
    def test_breaking_reason_in_detected_changes(self):
        """Test that breaking reasons are correctly captured in detected changes."""
        previous_symbol = SymbolData(
            file_path="test.py",
            symbol_name="test_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="test_func",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="test.py",
            symbol_name="test_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="test_func",
                parameters=[
                    ParameterInfo(name="x", annotation="str"),
                ],
                return_annotation="int",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].is_breaking is True
        assert changes[0].breaking_reason is not None
        assert "parameter_type_changed" in changes[0].breaking_reason

    @pytest.mark.unit
    def test_breaking_reason_for_removed_symbol(self):
        """Test that removed symbols have correct breaking reason."""
        removed_symbol = SymbolData(
            file_path="test.py",
            symbol_name="old_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="old_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[removed_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "removed"
        assert changes[0].is_breaking is True
        assert changes[0].breaking_reason == "symbol_removed"
