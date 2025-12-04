"""Service for generating diffs between before/after content.

Implements FR-15: UI shall provide diff preview (before/after).
Generates both unified diff strings and structured diff models for side-by-side UI.
"""

import difflib
import json
import logging
from dataclasses import dataclass, asdict
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class DiffLine:
    """Represents a single line in a diff with its type and content."""

    type: Literal["added", "removed", "unchanged", "context"]
    content: str
    line_number_before: int | None = None
    line_number_after: int | None = None


@dataclass
class DiffHunk:
    """Represents a hunk (block) of changes in a diff."""

    start_before: int
    start_after: int
    lines: list[DiffLine]


@dataclass
class StructuredDiff:
    """Structured representation of a diff for side-by-side UI."""

    hunks: list[DiffHunk]
    total_added: int
    total_removed: int
    total_unchanged: int


class DiffService:
    """Service for generating diffs between before and after content."""

    @staticmethod
    def generate_unified_diff(
        before_content: str,
        after_content: str,
        from_file: str = "before",
        to_file: str = "after",
        context_lines: int = 3,
    ) -> str:
        """Generate a unified diff string.

        Args:
            before_content: The original content
            after_content: The modified content
            from_file: Label for the 'before' file (default: "before")
            to_file: Label for the 'after' file (default: "after")
            context_lines: Number of context lines to include around changes

        Returns:
            Unified diff string in standard diff format
        """
        before_lines = before_content.splitlines(keepends=True)
        after_lines = after_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=from_file,
            tofile=to_file,
            n=context_lines,
            lineterm="",
        )

        return "".join(diff)

    @staticmethod
    def generate_structured_diff(
        before_content: str,
        after_content: str,
        context_lines: int = 3,
    ) -> StructuredDiff:
        """Generate a structured diff model for side-by-side UI.

        Args:
            before_content: The original content
            after_content: The modified content
            context_lines: Number of context lines to include around changes

        Returns:
            StructuredDiff object with hunks and line-by-line changes
        """
        before_lines = before_content.splitlines(keepends=False)
        after_lines = after_content.splitlines(keepends=False)

        # Use SequenceMatcher to find differences
        matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
        hunks = []
        total_added = 0
        total_removed = 0
        total_unchanged = 0

        # Track current line numbers
        before_line_num = 1
        after_line_num = 1

        current_hunk_lines: list[DiffLine] = []
        current_hunk_start_before = 1
        current_hunk_start_after = 1
        in_hunk = False

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                # Unchanged lines - add as context if we're in a hunk
                equal_lines = before_lines[i1:i2]
                total_unchanged += len(equal_lines)

                if in_hunk:
                    # Add context lines to current hunk
                    for line in equal_lines:
                        current_hunk_lines.append(
                            DiffLine(
                                type="unchanged",
                                content=line,
                                line_number_before=before_line_num,
                                line_number_after=after_line_num,
                            )
                        )
                        before_line_num += 1
                        after_line_num += 1

                    # If we have enough context, close this hunk
                    if len(equal_lines) > context_lines * 2:
                        # Close current hunk
                        hunks.append(
                            DiffHunk(
                                start_before=current_hunk_start_before,
                                start_after=current_hunk_start_after,
                                lines=current_hunk_lines,
                            )
                        )
                        current_hunk_lines = []
                        in_hunk = False
                else:
                    # Not in a hunk, just advance line numbers
                    before_line_num += len(equal_lines)
                    after_line_num += len(equal_lines)

            elif tag == "delete":
                # Removed lines
                if not in_hunk:
                    # Start a new hunk with context before
                    context_start = max(0, i1 - context_lines)
                    context_before = before_lines[context_start:i1]
                    context_after = after_lines[
                        max(0, j1 - context_lines) : j1
                    ]

                    # Add context lines
                    for idx, line in enumerate(context_before):
                        current_hunk_lines.append(
                            DiffLine(
                                type="context",
                                content=line,
                                line_number_before=context_start + idx + 1,
                                line_number_after=max(0, j1 - context_lines) + idx + 1,
                            )
                        )

                    current_hunk_start_before = context_start + 1
                    current_hunk_start_after = max(0, j1 - context_lines) + 1
                    in_hunk = True

                # Add removed lines
                for line in before_lines[i1:i2]:
                    current_hunk_lines.append(
                        DiffLine(
                            type="removed",
                            content=line,
                            line_number_before=before_line_num,
                            line_number_after=None,
                        )
                    )
                    before_line_num += 1
                    total_removed += 1

            elif tag == "insert":
                # Added lines
                if not in_hunk:
                    # Start a new hunk with context before
                    context_start = max(0, i1 - context_lines)
                    context_before = before_lines[context_start:i1]
                    context_after = after_lines[
                        max(0, j1 - context_lines) : j1
                    ]

                    # Add context lines
                    for idx, line in enumerate(context_before):
                        current_hunk_lines.append(
                            DiffLine(
                                type="context",
                                content=line,
                                line_number_before=context_start + idx + 1,
                                line_number_after=max(0, j1 - context_lines) + idx + 1,
                            )
                        )

                    current_hunk_start_before = context_start + 1
                    current_hunk_start_after = max(0, j1 - context_lines) + 1
                    in_hunk = True

                # Add added lines
                for line in after_lines[j1:j2]:
                    current_hunk_lines.append(
                        DiffLine(
                            type="added",
                            content=line,
                            line_number_before=None,
                            line_number_after=after_line_num,
                        )
                    )
                    after_line_num += 1
                    total_added += 1

            elif tag == "replace":
                # Modified lines (delete + insert)
                if not in_hunk:
                    # Start a new hunk with context before
                    context_start = max(0, i1 - context_lines)
                    context_before = before_lines[context_start:i1]
                    context_after = after_lines[
                        max(0, j1 - context_lines) : j1
                    ]

                    # Add context lines
                    for idx, line in enumerate(context_before):
                        current_hunk_lines.append(
                            DiffLine(
                                type="context",
                                content=line,
                                line_number_before=context_start + idx + 1,
                                line_number_after=max(0, j1 - context_lines) + idx + 1,
                            )
                        )

                    current_hunk_start_before = context_start + 1
                    current_hunk_start_after = max(0, j1 - context_lines) + 1
                    in_hunk = True

                # Add removed lines
                for line in before_lines[i1:i2]:
                    current_hunk_lines.append(
                        DiffLine(
                            type="removed",
                            content=line,
                            line_number_before=before_line_num,
                            line_number_after=None,
                        )
                    )
                    before_line_num += 1
                    total_removed += 1

                # Add added lines
                for line in after_lines[j1:j2]:
                    current_hunk_lines.append(
                        DiffLine(
                            type="added",
                            content=line,
                            line_number_before=None,
                            line_number_after=after_line_num,
                        )
                    )
                    after_line_num += 1
                    total_added += 1

        # Close any remaining hunk
        if in_hunk and current_hunk_lines:
            hunks.append(
                DiffHunk(
                    start_before=current_hunk_start_before,
                    start_after=current_hunk_start_after,
                    lines=current_hunk_lines,
                )
            )

        # If no hunks but content exists, create a single unchanged hunk
        if not hunks and before_lines:
            hunks.append(
                DiffHunk(
                    start_before=1,
                    start_after=1,
                    lines=[
                        DiffLine(
                            type="unchanged",
                            content=line,
                            line_number_before=idx + 1,
                            line_number_after=idx + 1,
                        )
                        for idx, line in enumerate(before_lines)
                    ],
                )
            )
            total_unchanged = len(before_lines)

        return StructuredDiff(
            hunks=hunks,
            total_added=total_added,
            total_removed=total_removed,
            total_unchanged=total_unchanged,
        )

    @staticmethod
    def generate_diffs(
        before_content: str,
        after_content: str,
        from_file: str = "before",
        to_file: str = "after",
        context_lines: int = 3,
    ) -> tuple[str, str]:
        """Generate both unified and structured diffs.

        Args:
            before_content: The original content
            after_content: The modified content
            from_file: Label for the 'before' file
            to_file: Label for the 'after' file
            context_lines: Number of context lines to include

        Returns:
            Tuple of (unified_diff_string, structured_diff_json_string)
        """
        unified_diff = DiffService.generate_unified_diff(
            before_content, after_content, from_file, to_file, context_lines
        )

        structured_diff = DiffService.generate_structured_diff(
            before_content, after_content, context_lines
        )

        # Serialize structured diff to JSON
        # Convert dataclasses to dicts recursively
        def dataclass_to_dict(obj):
            if isinstance(obj, (DiffLine, DiffHunk, StructuredDiff)):
                result = asdict(obj)
                # Recursively convert nested dataclasses
                if isinstance(obj, StructuredDiff):
                    result["hunks"] = [
                        dataclass_to_dict(hunk) for hunk in obj.hunks
                    ]
                elif isinstance(obj, DiffHunk):
                    result["lines"] = [
                        dataclass_to_dict(line) for line in obj.lines
                    ]
                return result
            return obj

        structured_diff_dict = dataclass_to_dict(structured_diff)
        structured_diff_json = json.dumps(structured_diff_dict, indent=2)

        return unified_diff, structured_diff_json

