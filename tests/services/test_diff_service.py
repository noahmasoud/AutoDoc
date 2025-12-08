"""
Tests for DiffService - Patch Diff Preview Generation.
Tests verify correct diff output for:
- Single-line changes
- Multi-line insertions/deletions
- Edge cases
"""

import json
from services.diff import DiffService


class TestDiffServiceUnified:
    """Test unified diff generation."""

    def test_single_line_addition(self):
        """Test unified diff for adding a single line."""
        before = "line1\nline2"
        after = "line1\nline2\nline3"

        result = DiffService.generate_unified_diff(before, after)

        assert "+line3" in result
        assert "before" in result
        assert "after" in result

    def test_single_line_removal(self):
        """Test unified diff for removing a single line."""
        before = "line1\nline2\nline3"
        after = "line1\nline2"

        result = DiffService.generate_unified_diff(before, after)

        assert "-line3" in result

    def test_single_line_modification(self):
        """Test unified diff for modifying a single line."""
        before = "line1\nline2\nline3"
        after = "line1\nmodified line2\nline3"

        result = DiffService.generate_unified_diff(before, after)

        assert "-line2" in result
        assert "+modified line2" in result


class TestDiffServiceStructured:
    """Test structured diff generation."""

    def test_single_line_addition_structured(self):
        """Test structured diff for adding a single line."""
        before = "line1\nline2"
        after = "line1\nline2\nline3"

        result = DiffService.generate_structured_diff(before, after)

        assert result.total_added == 1
        assert result.total_removed == 0
        assert len(result.hunks) > 0

    def test_single_line_removal_structured(self):
        """Test structured diff for removing a single line."""
        before = "line1\nline2\nline3"
        after = "line1\nline2"

        result = DiffService.generate_structured_diff(before, after)

        assert result.total_added == 0
        assert result.total_removed == 1

    def test_multiple_line_insertions(self):
        """Test structured diff for multiple insertions."""
        before = "line1\nline2"
        after = "line1\nline2\nline3\nline4\nline5"

        result = DiffService.generate_structured_diff(before, after)

        assert result.total_added == 3
        assert result.total_removed == 0

    def test_multiple_line_deletions(self):
        """Test structured diff for multiple deletions."""
        before = "line1\nline2\nline3\nline4\nline5"
        after = "line1\nline2"

        result = DiffService.generate_structured_diff(before, after)

        assert result.total_added == 0
        assert result.total_removed == 3

    def test_mixed_changes(self):
        """Test structured diff with both additions and deletions."""
        before = "line1\nline2\nline3"
        after = "line1\nnew line\nline3"

        result = DiffService.generate_structured_diff(before, after)

        assert result.total_added >= 1
        assert result.total_removed >= 1


class TestDiffServiceCombined:
    """Test the combined generate_diffs method."""

    def test_generate_both_diffs(self):
        """Test generating both unified and structured diffs."""
        before = "line1\nline2"
        after = "line1\nmodified"

        unified, structured_json = DiffService.generate_diffs(before, after)

        # Check unified is a string
        assert isinstance(unified, str)
        assert "line1" in unified

        # Check structured is valid JSON
        structured = json.loads(structured_json)
        assert "hunks" in structured
        assert "total_added" in structured
        assert "total_removed" in structured


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_content(self):
        """Test diff with empty content."""
        unified, structured_json = DiffService.generate_diffs("", "")

        assert unified is not None
        structured = json.loads(structured_json)
        assert structured["total_added"] == 0
        assert structured["total_removed"] == 0

    def test_identical_content(self):
        """Test diff with identical content."""
        content = "line1\nline2\nline3"
        unified, structured_json = DiffService.generate_diffs(content, content)

        assert unified is not None
        structured = json.loads(structured_json)
        # Should have no additions or removals
        assert structured["total_added"] == 0
        assert structured["total_removed"] == 0
