"""
Rule selector matching utilities.

Supports simple glob patterns (including ** wildcards) and an optional
regular-expression mode when the selector starts with ``regex:``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import PurePosixPath
import fnmatch
import re


@lru_cache(maxsize=256)
def _compile_regex(pattern: str) -> re.Pattern[str]:
    """Compile and cache regular expressions used by regex selectors."""
    return re.compile(pattern)


def _normalize_path(path: str) -> str:
    """Normalize file paths to POSIX style for consistent matching."""
    return PurePosixPath(path).as_posix()


def match_rule(selector: str, file_path: str) -> bool:
    """
    Determine whether a rule selector matches a given file path.

    Args:
        selector: Glob or regex pattern. Prefix with ``regex:`` for regex mode.
        file_path: The path of the file being evaluated.

    Returns:
        True if the selector matches the path, False otherwise.
    """

    normalized_path = _normalize_path(file_path)

    if not selector:
        return False

    selector = selector.strip()

    if selector.lower().startswith("regex:"):
        pattern = selector[6:]
        if not pattern:
            return False
        regex = _compile_regex(pattern)
        return regex.search(normalized_path) is not None

    # Default glob mode. ``fnmatch`` already supports single/double wildcard usage.
    normalized_selector = _normalize_path(selector)
    return fnmatch.fnmatch(normalized_path, normalized_selector)


__all__ = ["match_rule"]

