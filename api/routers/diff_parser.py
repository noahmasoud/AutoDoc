"""Diff parser router for comparing file contents."""

import difflib
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/diff", tags=["diff"])


class DiffRequest(BaseModel):
    """Request model for diff parsing."""

    old_file: str
    new_file: str


class ModifiedLine(BaseModel):
    """Model for a modified line."""

    line: int
    old: str
    new: str


class DiffResponse(BaseModel):
    """Response model for diff parsing."""

    added: list[str]
    removed: list[str]
    modified: list[ModifiedLine]


def parse_diff(old_code: str, new_code: str) -> dict[str, Any]:
    """Parse differences between two code strings."""
    if old_code == new_code:
        return _empty_diff_result()

    old_lines = _split_lines(old_code)
    new_lines = _split_lines(new_code)

    if not old_lines and not new_lines:
        return _empty_diff_result()

    diff = _build_unified_diff(old_lines, new_lines)
    return _collect_diff_changes(diff)


def _empty_diff_result() -> dict[str, Any]:
    return {"added": [], "removed": [], "modified": []}


def _split_lines(source: str) -> list[str]:
    return source.splitlines(keepends=True)


def _build_unified_diff(old_lines: list[str], new_lines: list[str]) -> list[str]:
    return list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="old",
            tofile="new",
            lineterm="",
            n=0,
        ),
    )


def _collect_diff_changes(diff: list[str]) -> dict[str, Any]:
    added: list[str] = []
    removed: list[str] = []
    modified: list[dict[str, Any]] = []
    pending_removals: list[tuple[int, str]] = []
    current_new_line = 0
    i = 0

    while i < len(diff):
        line = diff[i]

        if line.startswith(("+++", "---")):
            i += 1
            continue

        if line.startswith("@@"):
            current_new_line = _parse_hunk_header(line, current_new_line)
            _flush_pending_removals(pending_removals, removed)
            pending_removals = []
            i += 1
            continue

        if line.startswith("+") and not line.startswith("++"):
            i, current_new_line = _handle_added_line(
                line,
                pending_removals,
                added,
                removed,
                modified,
                i,
                current_new_line,
            )
            continue

        if line.startswith("-") and not line.startswith("--"):
            pending_removals.append((current_new_line, line[1:]))
            i += 1
            continue

        if line.startswith(" "):
            _flush_pending_removals(pending_removals, removed)
            pending_removals = []
            current_new_line += 1
            i += 1
            continue

        i += 1

    _flush_pending_removals(pending_removals, removed)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }


def _parse_hunk_header(line: str, current_line: int) -> int:
    parts = line.split("@@")
    if len(parts) < 2:
        return current_line

    hunk_info = parts[1].strip()
    plus_part = [p for p in hunk_info.split() if p.startswith("+")]
    if not plus_part:
        return current_line

    new_start_str = plus_part[0][1:].split(",")[0]
    try:
        return int(new_start_str) - 1
    except ValueError:
        return 0


def _handle_added_line(
    line: str,
    pending_removals: list[tuple[int, str]],
    added: list[str],
    removed: list[str],
    modified: list[dict[str, Any]],
    index: int,
    current_line: int,
) -> tuple[int, int]:
    content = line[1:]
    content_clean = content.rstrip("\n\r")

    if pending_removals:
        _, old_content = pending_removals.pop(0)
        old_content_clean = old_content.rstrip("\n\r")

        if old_content_clean == content_clean:
            return index + 1, current_line + 1

        if _is_similar_change(old_content_clean, content_clean):
            modified.append(
                {
                    "line": current_line + 1,
                    "old": old_content_clean,
                    "new": content_clean,
                },
            )
        else:
            removed.append(old_content_clean)
            added.append(content_clean)
            return index + 1, current_line + 1
    else:
        added.append(content_clean)

    return index + 1, current_line + 1


def _flush_pending_removals(
    pending_removals: list[tuple[int, str]],
    removed: list[str],
) -> None:
    for _, content in pending_removals:
        removed.append(content.rstrip("\n\r"))


def _is_similar_change(old: str, new: str) -> bool:
    if not old or not new:
        return False
    return old in new or new in old


@router.post("/parse", response_model=DiffResponse)
def parse_diff_endpoint(request: DiffRequest) -> DiffResponse:
    """Parse differences between two file contents.

    Args:
        request: Request containing old_file and new_file strings

    Returns:
        DiffResponse with added, removed, and modified lines
    """
    result = parse_diff(request.old_file, request.new_file)
    return DiffResponse(
        added=result["added"],
        removed=result["removed"],
        modified=[ModifiedLine(**m) for m in result["modified"]],
    )
