"""Diff parser router for comparing file contents."""

import difflib
from typing import Dict, List, Any

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

    added: List[str]
    removed: List[str]
    modified: List[ModifiedLine]


def parse_diff(old_code: str, new_code: str) -> Dict[str, Any]:
    """Parse differences between two code strings.

    Uses difflib.unified_diff to compute line-by-line changes between the two files.

    Args:
        old_code: The original file content
        new_code: The modified file content

    Returns:
        Dictionary containing:
            - added: List of added lines
            - removed: List of removed lines
            - modified: List of dicts with line number, old, and new content
    """
    # Handle empty or identical files
    if old_code == new_code:
        return {"added": [], "removed": [], "modified": []}

    old_lines = old_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)

    # Handle empty files
    if not old_lines and not new_lines:
        return {"added": [], "removed": [], "modified": []}

    # Use unified_diff to compute differences as required
    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="old",
            tofile="new",
            lineterm="",
            n=0,  # Context lines (0 means no context, just changes)
        )
    )

    added: List[str] = []
    removed: List[str] = []
    modified: List[Dict[str, Any]] = []

    # Process the unified diff output
    pending_removals: List[tuple[int, str]] = []  # (line_num, content)
    current_new_line = 0

    i = 0
    while i < len(diff):
        line = diff[i]

        # Skip file headers
        if line.startswith("+++") or line.startswith("---"):
            i += 1
            continue

        # Process hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@"):
            # Parse hunk header to get starting line numbers
            parts = line.split("@@")
            if len(parts) >= 2:
                hunk_info = parts[1].strip()
                # Extract new file start line: +start,count
                plus_part = [p for p in hunk_info.split() if p.startswith("+")]
                if plus_part:
                    new_start_str = plus_part[0][1:].split(",")[0]
                    try:
                        current_new_line = int(new_start_str) - 1  # Convert to 0-indexed
                    except ValueError:
                        current_new_line = 0
            # Clear pending removals when starting a new hunk
            for _, content in pending_removals:
                removed.append(content.rstrip("\n\r"))
            pending_removals = []
            i += 1
            continue

        # Process diff lines
        if line.startswith("+") and not line.startswith("++"):
            # Added line
            content = line[1:]
            content_clean = content.rstrip("\n\r")
            # Check if preceded by removal (modification)
            if pending_removals:
                old_line_num, old_content = pending_removals.pop(0)
                modified.append(
                    {
                        "line": current_new_line + 1,  # 1-indexed for output
                        "old": old_content.rstrip("\n\r"),
                        "new": content_clean,
                    }
                )
            else:
                # Pure addition
                added.append(content_clean)
            current_new_line += 1
            i += 1
        elif line.startswith("-") and not line.startswith("--"):
            # Removed line - store it, might be part of modification
            content = line[1:]
            pending_removals.append((current_new_line, content))
            i += 1
        elif line.startswith(" "):
            # Unchanged line - flush any pending removals as pure removals
            for _, content in pending_removals:
                removed.append(content.rstrip("\n\r"))
            pending_removals = []
            current_new_line += 1
            i += 1
        else:
            i += 1

    # Handle any remaining pending removals at the end
    for _, content in pending_removals:
        removed.append(content.rstrip("\n\r"))

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
    }


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

