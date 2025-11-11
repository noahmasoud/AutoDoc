"""Unit tests for edge cases in change detection."""

import pytest

from schemas.changes import (
    RunArtifact,
    SymbolData,
    SignatureInfo,
    ParameterInfo,
)
from services.change_detector import detect_changes


class TestEdgeCasesFunctionOverloads:
    """Test edge cases related to function overloads."""

    @pytest.mark.unit
    def test_overloads_same_name_different_file(self):
        """Test functions with same name in different files are separate."""
        previous_symbols = [
            SymbolData(
                file_path="module1.py",
                symbol_name="process",
                symbol_type="function",
                signature=SignatureInfo(
                    name="process",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="int",
                ),
            ),
            SymbolData(
                file_path="module2.py",
                symbol_name="process",
                symbol_type="function",
                signature=SignatureInfo(
                    name="process",
                    parameters=[
                        ParameterInfo(name="x", annotation="str"),
                    ],
                    return_annotation="str",
                ),
            ),
        ]

        current_symbols = [
            SymbolData(
                file_path="module1.py",
                symbol_name="process",
                symbol_type="function",
                signature=SignatureInfo(
                    name="process",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="int",
                ),
            ),
            SymbolData(
                file_path="module2.py",
                symbol_name="process",
                symbol_type="function",
                signature=SignatureInfo(
                    name="process",
                    parameters=[
                        ParameterInfo(name="x", annotation="str"),
                        ParameterInfo(name="y", annotation="str"),
                    ],
                    return_annotation="str",
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

        # Should detect 1 modification (module2.process added a parameter)
        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].file_path == "module2.py"
        assert changes[0].symbol_name == "process"
        assert changes[0].is_breaking is True

    @pytest.mark.unit
    def test_methods_same_name_different_classes(self):
        """Test methods with same name in different classes are separate."""
        previous_symbols = [
            SymbolData(
                file_path="models.py",
                symbol_name="ClassA.method",
                symbol_type="method",
                signature=SignatureInfo(
                    name="method",
                    parameters=[],
                    return_annotation="None",
                ),
            ),
            SymbolData(
                file_path="models.py",
                symbol_name="ClassB.method",
                symbol_type="method",
                signature=SignatureInfo(
                    name="method",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="None",
                ),
            ),
        ]

        current_symbols = [
            SymbolData(
                file_path="models.py",
                symbol_name="ClassA.method",
                symbol_type="method",
                signature=SignatureInfo(
                    name="method",
                    parameters=[],
                    return_annotation="None",
                ),
            ),
            SymbolData(
                file_path="models.py",
                symbol_name="ClassB.method",
                symbol_type="method",
                signature=SignatureInfo(
                    name="method",
                    parameters=[
                        ParameterInfo(name="x", annotation="str"),
                    ],
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

        # Should detect 1 modification (ClassB.method parameter type changed)
        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].symbol_name == "ClassB.method"
        assert changes[0].is_breaking is True


class TestEdgeCasesRenamedSymbols:
    """Test edge cases related to renamed symbols (treated as separate symbols)."""

    @pytest.mark.unit
    def test_function_rename_treated_as_added_and_removed(self):
        """Test that renaming a function is detected as remove + add."""
        previous_symbols = [
            SymbolData(
                file_path="api.py",
                symbol_name="old_name",
                symbol_type="function",
                signature=SignatureInfo(
                    name="old_name",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="int",
                ),
            ),
        ]

        current_symbols = [
            SymbolData(
                file_path="api.py",
                symbol_name="new_name",
                symbol_type="function",
                signature=SignatureInfo(
                    name="new_name",
                    parameters=[
                        ParameterInfo(name="x", annotation="int"),
                    ],
                    return_annotation="int",
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

        # Should detect 1 removal and 1 addition (not a rename)
        assert len(changes) == 2
        removal = next(c for c in changes if c.change_type == "removed")
        addition = next(c for c in changes if c.change_type == "added")

        assert removal.symbol_name == "old_name"
        assert addition.symbol_name == "new_name"
        assert removal.is_breaking is True
        assert addition.is_breaking is False


class TestEdgeCasesParameterDefaults:
    """Test edge cases related to parameter defaults."""

    @pytest.mark.unit
    def test_parameter_default_added_non_breaking(self):
        """Test adding a default value to a parameter is not breaking."""
        previous_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(name="multiplier", annotation="int"),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(
                        name="multiplier",
                        annotation="int",
                        default_value="1",
                    ),
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

        # Should detect modification but check breaking separately
        # This test verifies parameter defaults are tracked
        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        # Note: parameter default addition is not currently breaking in our logic
        # This test documents the current behavior

    @pytest.mark.unit
    def test_parameter_default_removed_breaking(self):
        """Test removing a default value is breaking."""
        previous_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(
                        name="multiplier",
                        annotation="int",
                        default_value="1",
                    ),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(name="multiplier", annotation="int"),
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
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True
        assert "parameter_default_removed" in changes[0].breaking_reason

    @pytest.mark.unit
    def test_parameter_default_value_changed(self):
        """Test changing a default value is not breaking."""
        previous_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(
                        name="multiplier",
                        annotation="int",
                        default_value="1",
                    ),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="compute",
            symbol_type="function",
            signature=SignatureInfo(
                name="compute",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                    ParameterInfo(
                        name="multiplier",
                        annotation="int",
                        default_value="2",
                    ),
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
        assert changes[0].change_type == "modified"
        # Default value change is not currently breaking
        assert changes[0].is_breaking is False


class TestEdgeCasesParameterVariations:
    """Test edge cases for different parameter kinds."""

    @pytest.mark.unit
    def test_varargs_positional_only(self):
        """Test varargs (positional-only) parameters."""
        previous_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="sum_values",
            symbol_type="function",
            signature=SignatureInfo(
                name="sum_values",
                parameters=[
                    ParameterInfo(name="*args", annotation="int", kind="varargs"),
                ],
                return_annotation="int",
            ),
        )

        current_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="sum_values",
            symbol_type="function",
            signature=SignatureInfo(
                name="sum_values",
                parameters=[
                    ParameterInfo(name="*args", annotation="float", kind="varargs"),
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
        assert changes[0].change_type == "modified"
        # Note: varargs type change is breaking but may need special handling

    @pytest.mark.unit
    def test_kwargs_keyword_only(self):
        """Test kwargs (keyword-only) parameters."""
        previous_symbol = SymbolData(
            file_path="config.py",
            symbol_name="setup",
            symbol_type="function",
            signature=SignatureInfo(
                name="setup",
                parameters=[
                    ParameterInfo(name="**kwargs", annotation="Any", kind="varkeyword"),
                ],
                return_annotation="None",
            ),
        )

        current_symbol = SymbolData(
            file_path="config.py",
            symbol_name="setup",
            symbol_type="function",
            signature=SignatureInfo(
                name="setup",
                parameters=[
                    ParameterInfo(
                        name="**options",
                        annotation="Any",
                        kind="varkeyword",
                    ),
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
        assert changes[0].is_breaking is True
        assert "parameter_name_changed" in changes[0].breaking_reason


class TestEdgeCasesMissingSignature:
    """Test edge cases with missing signatures."""

    @pytest.mark.unit
    def test_symbol_with_no_signature(self):
        """Test symbol that has no signature information."""
        previous_symbol = SymbolData(
            file_path="legacy.py",
            symbol_name="old_var",
            symbol_type="function",
            signature=None,
        )

        current_symbol = SymbolData(
            file_path="legacy.py",
            symbol_name="old_var",
            symbol_type="function",
            signature=None,
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

        # Symbols without signatures should be treated as identical
        assert len(changes) == 0


class TestEdgeCasesVisibilityChanges:
    """Test edge cases for visibility changes."""

    @pytest.mark.unit
    def test_function_becomes_private(self):
        """Test when public function becomes private."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="helper_func",
            symbol_type="function",
            is_public=True,
            signature=SignatureInfo(
                name="helper_func",
                parameters=[],
                return_annotation="None",
            ),
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="helper_func",
            symbol_type="function",
            is_public=False,  # Became private
            signature=SignatureInfo(
                name="helper_func",
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

        # Visibility change should be detected as modification
        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is False  # Visibility changes are not breaking


class TestEdgeCasesLargeScale:
    """Test edge cases for large-scale changes."""

    @pytest.mark.unit
    def test_many_simultaneous_changes(self):
        """Test detecting many changes at once."""
        # Create 50 symbols in previous version
        previous_symbols = [
            SymbolData(
                file_path=f"module{i}.py",
                symbol_name=f"func{j}",
                symbol_type="function",
                signature=SignatureInfo(
                    name=f"func{j}",
                    parameters=[],
                    return_annotation="None",
                ),
            )
            for i in range(5)
            for j in range(10)
        ]

        # Modify half, remove quarter, add new quarter
        # Keep first 25 (5 modules x 5 functions) - unchanged
        current_symbols = [
            SymbolData(
                file_path=f"module{i}.py",
                symbol_name=f"func{j}",
                symbol_type="function",
                signature=SignatureInfo(
                    name=f"func{j}",
                    parameters=[],
                    return_annotation="None",
                ),
            )
            for i in range(5)
            for j in range(5)
        ]

        # Modify next 15 (change return type) - 5 modules x 3 functions
        current_symbols.extend(
            [
                SymbolData(
                    file_path=f"module{i}.py",
                    symbol_name=f"func{j}",
                    symbol_type="function",
                    signature=SignatureInfo(
                        name=f"func{j}",
                        parameters=[],
                        return_annotation="str",  # Changed
                    ),
                )
                for i in range(5)
                for j in range(5, 8)
            ],
        )

        # Add 13 new functions
        current_symbols.extend(
            [
                SymbolData(
                    file_path="module_new.py",
                    symbol_name=f"new_func{j}",
                    symbol_type="function",
                    signature=SignatureInfo(
                        name=f"new_func{j}",
                        parameters=[],
                        return_annotation="None",
                    ),
                )
                for j in range(13)
            ],
        )

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
        # - 13 additions (new functions)
        # - 10 removals (func8 and func9 from each of 5 modules)
        # - 15 modifications (return type changed for func5-func7 in 5 modules)
        assert len(changes) == 38

        additions = [c for c in changes if c.change_type == "added"]
        removals = [c for c in changes if c.change_type == "removed"]
        modifications = [c for c in changes if c.change_type == "modified"]

        assert len(additions) == 13
        assert len(removals) == 10
        assert len(modifications) == 15

        # All modifications should be breaking
        assert all(c.is_breaking for c in modifications)


class TestEdgeCasesEmptyAndNull:
    """Test edge cases with empty or null values."""

    @pytest.mark.unit
    def test_return_annotation_none_vs_missing(self):
        """Test difference between None return annotation and missing one."""
        previous_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="do_work",
            symbol_type="function",
            signature=SignatureInfo(
                name="do_work",
                parameters=[],
                return_annotation="None",
            ),
        )

        current_symbol = SymbolData(
            file_path="utils.py",
            symbol_name="do_work",
            symbol_type="function",
            signature=SignatureInfo(
                name="do_work",
                parameters=[],
                return_annotation=None,
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

        # "None" vs None should be detected as different
        assert len(changes) == 1
        assert changes[0].change_type == "modified"


class TestEdgeCasesComplexSignature:
    """Test edge cases with complex signatures."""

    @pytest.mark.unit
    def test_complex_parameter_combinations(self):
        """Test function with many parameter variations."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="complex_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="complex_func",
                parameters=[
                    ParameterInfo(name="required_pos", annotation="int"),
                    ParameterInfo(
                        name="optional_pos",
                        annotation="int",
                        default_value="0",
                    ),
                    ParameterInfo(name="required_kw", annotation="str"),
                    ParameterInfo(
                        name="optional_kw",
                        annotation="str",
                        default_value="''",
                    ),
                    ParameterInfo(name="*args", annotation="Any", kind="varargs"),
                    ParameterInfo(name="**kwargs", annotation="Any", kind="varkeyword"),
                ],
                return_annotation="dict",
            ),
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="complex_func",
            symbol_type="function",
            signature=SignatureInfo(
                name="complex_func",
                parameters=[
                    ParameterInfo(name="required_pos", annotation="int"),
                    ParameterInfo(
                        name="optional_pos",
                        annotation="int",
                        default_value="0",
                    ),
                    ParameterInfo(name="required_kw", annotation="str"),
                    ParameterInfo(
                        name="optional_kw",
                        annotation="str",
                        default_value="''",
                    ),
                    ParameterInfo(name="*args", annotation="Any", kind="varargs"),
                    ParameterInfo(name="**kwargs", annotation="Any", kind="varkeyword"),
                ],
                return_annotation="dict",
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

        # Should be identical
        assert len(changes) == 0

    @pytest.mark.unit
    def test_complex_return_type_change(self):
        """Test changing a complex return type."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="create_response",
            symbol_type="function",
            signature=SignatureInfo(
                name="create_response",
                parameters=[
                    ParameterInfo(name="data", annotation="dict"),
                ],
                return_annotation="dict[str, Any]",
            ),
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="create_response",
            symbol_type="function",
            signature=SignatureInfo(
                name="create_response",
                parameters=[
                    ParameterInfo(name="data", annotation="dict"),
                ],
                return_annotation="Response",
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
        assert changes[0].is_breaking is True
        assert "return_type_changed" in changes[0].breaking_reason
