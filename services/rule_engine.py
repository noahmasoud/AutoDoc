"""Rule engine for mapping source code files to Confluence pages.

This module provides functionality to match file paths against rules using
glob or regex patterns, resolve target pages with precedence handling, and
validate rule configurations.
"""

import fnmatch
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db.models import Rule


class RuleEngineError(Exception):
    """Base exception for rule engine errors."""


class InvalidSelectorError(RuleEngineError):
    """Raised when a selector pattern is invalid."""


class InvalidTargetError(RuleEngineError):
    """Raised when a rule target (page_id or space_key) is invalid."""


def is_glob_pattern(pattern: str) -> bool:
    """Detect if pattern is a glob pattern vs regex.

    A pattern is considered glob if it contains glob wildcards (* or ?)
    and doesn't contain regex-specific metacharacters that would indicate
    it's meant to be a regex pattern.

    Args:
        pattern: The pattern string to check

    Returns:
        True if pattern appears to be glob, False if regex
    """
    # Check for glob wildcards
    has_glob_wildcards = "*" in pattern or "?" in pattern

    # Check for regex-specific metacharacters that indicate regex intent
    # Check for literal characters in the pattern string (not regex matching)
    has_regex_indicators = (
        "^" in pattern  # Start anchor
        or "$" in pattern  # End anchor
        or "[" in pattern  # Character class
        or "{" in pattern  # Quantifier
        or "(" in pattern  # Group
        or "|" in pattern  # Alternation
        or "+" in pattern  # One or more
        or ".*" in pattern  # Dot-asterisk (common regex pattern)
        or (pattern.count("?") > 0 and "\\?" not in pattern)  # Unescaped ?
    )

    # If it has regex indicators, it's definitely regex
    if has_regex_indicators:
        return False

    # If it has glob wildcards and no regex indicators, it's glob
    if has_glob_wildcards:
        return True

    # Default: treat as literal string (will match exactly)
    return True


def match_glob(file_path: str, pattern: str) -> bool:
    """Match a file path against a glob pattern.

    Supports standard glob patterns including:
    - * matches any sequence of characters
    - ? matches any single character
    - ** matches any directory (recursive)

    Args:
        file_path: The file path to match
        pattern: The glob pattern

    Returns:
        True if the path matches the pattern, False otherwise
    """
    # Handle recursive glob pattern (**)
    if "**" in pattern:
        # Convert ** pattern to regex for recursive matching
        # ** matches zero or more directories
        # Escape special regex chars but keep ** and * wildcards
        regex_pattern = pattern.replace("**", "__RECURSIVE__")
        regex_pattern = re.escape(regex_pattern)
        # Replace __RECURSIVE__ with pattern that matches zero or more directory segments
        # (.*/)? matches zero or more directories with trailing slash
        # But we need to handle the case where ** is followed by / or *
        regex_pattern = regex_pattern.replace("__RECURSIVE__/", "(.*/)?")
        regex_pattern = regex_pattern.replace("__RECURSIVE__", "(.*/)?")
        regex_pattern = regex_pattern.replace(r"\*", ".*")
        regex_pattern = regex_pattern.replace(r"\?", ".")
        # Match from start of path
        regex_pattern = "^" + regex_pattern + "$"
        return bool(re.match(regex_pattern, file_path))

    # Use fnmatch for standard glob patterns
    return fnmatch.fnmatch(file_path, pattern)


def match_regex(file_path: str, pattern: str) -> bool:
    """Match a file path against a regex pattern.

    Args:
        file_path: The file path to match
        pattern: The regex pattern

    Returns:
        True if the path matches the pattern, False otherwise

    Raises:
        InvalidSelectorError: If the regex pattern is invalid
    """
    try:
        compiled = re.compile(pattern)
        return bool(compiled.search(file_path))
    except re.error as e:
        raise InvalidSelectorError(f"Invalid regex pattern: {pattern}") from e


def validate_selector(selector: str) -> bool:
    """Validate selector format (glob or regex).

    Args:
        selector: The selector pattern to validate

    Returns:
        True if selector is valid

    Raises:
        InvalidSelectorError: If selector is invalid
    """
    if not selector or not selector.strip():
        raise InvalidSelectorError("Selector cannot be empty")

    # Try to determine if it's glob or regex
    if is_glob_pattern(selector):
        # For glob, just check it's not empty (fnmatch will handle validation)
        return True
    # For regex, try to compile it
    try:
        re.compile(selector)
        return True
    except re.error as e:
        raise InvalidSelectorError(f"Invalid regex pattern: {selector}") from e


def match_file_to_rules(file_path: str, rules: list["Rule"]) -> list["Rule"]:
    """Match a file path against all rules and return matching rules.

    Args:
        file_path: The file path to match
        rules: List of rules to test against

    Returns:
        List of matching rules, sorted by priority (ascending) then by ID (ascending)
    """
    matching_rules = []

    for rule in rules:
        try:
            selector = rule.selector.strip()
            
            # Handle regex: prefix
            if selector.lower().startswith("regex:"):
                pattern = selector[6:].strip()  # Remove "regex:" prefix
                matches = match_regex(file_path, pattern)
            elif is_glob_pattern(selector):
                matches = match_glob(file_path, selector)
            else:
                # Try as regex if it looks like regex
                matches = match_regex(file_path, selector)

            if matches:
                matching_rules.append(rule)
        except InvalidSelectorError:
            # Skip invalid selectors, but don't fail the entire operation
            continue

    # Sort by priority (ascending, lower = higher priority), then by ID (ascending)
    matching_rules.sort(key=lambda r: (r.priority, r.id))

    return matching_rules


def resolve_target_page(file_path: str, rules: list["Rule"]) -> "Rule | None":
    """Resolve the target page for a file path using rule precedence.

    Returns the highest priority matching rule (lowest priority value).
    If multiple rules have the same priority, the one with the lowest ID wins.

    Args:
        file_path: The file path to match
        rules: List of rules to test against

    Returns:
        The matching rule with highest priority, or None if no rules match

    Raises:
        InvalidTargetError: If the resolved rule has invalid target configuration
    """
    matching_rules = match_file_to_rules(file_path, rules)

    if not matching_rules:
        return None

    # Get the first rule (highest priority due to sorting)
    rule = matching_rules[0]

    # Validate target configuration
    if not rule.page_id or not rule.page_id.strip():
        raise InvalidTargetError(
            f"Rule '{rule.name}' (ID: {rule.id}) has empty page_id"
        )
    if not rule.space_key or not rule.space_key.strip():
        raise InvalidTargetError(
            f"Rule '{rule.name}' (ID: {rule.id}) has empty space_key"
        )

    return rule


def validate_rule_target(rule: "Rule") -> bool:
    """Validate that a rule has valid target configuration.

    Args:
        rule: The rule to validate

    Returns:
        True if rule target is valid

    Raises:
        InvalidTargetError: If rule target is invalid
    """
    if not rule.page_id or not rule.page_id.strip():
        raise InvalidTargetError(
            f"Rule '{rule.name}' (ID: {rule.id}) has empty page_id"
        )
    if not rule.space_key or not rule.space_key.strip():
        raise InvalidTargetError(
            f"Rule '{rule.name}' (ID: {rule.id}) has empty space_key"
        )
    return True
