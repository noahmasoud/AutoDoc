"""Rule matching service with priority ordering and conflict resolution."""

import fnmatch
import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from db.models import Rule

logger = logging.getLogger(__name__)


class RuleMatch:
    """Represents a matched rule for a file."""

    def __init__(self, rule: "Rule", file_path: str) -> None:
        """Initialize a rule match.

        Args:
            rule: The matched rule
            file_path: The file path that matched
        """
        self.rule = rule
        self.file_path = file_path

    def __repr__(self) -> str:
        return f"RuleMatch(rule_id={self.rule.id}, rule_name={self.rule.name}, file_path={self.file_path})"


class RuleMatcher:
    """Service for matching rules to files with priority ordering."""

    @staticmethod
    def match_rules_to_file(file_path: str, rules: list["Rule"]) -> list[RuleMatch]:
        """Match rules to a file path, ordered by priority (higher priority first).

        Args:
            file_path: The file path to match against
            rules: List of rules to check

        Returns:
            List of matched rules, ordered by priority (descending), then by rule ID
        """
        matches: list[RuleMatch] = []

        for rule in rules:
            if RuleMatcher._matches_selector(file_path, rule.selector):
                matches.append(RuleMatch(rule, file_path))
                logger.debug(
                    "Rule '%s' (id=%d, priority=%d) matched file '%s'",
                    rule.name,
                    rule.id,
                    rule.priority,
                    file_path,
                )

        # Sort by priority (descending), then by rule ID (ascending) for stability
        matches.sort(key=lambda m: (-m.rule.priority, m.rule.id))

        if matches:
            logger.info(
                "File '%s' matched %d rule(s): %s",
                file_path,
                len(matches),
                [f"{m.rule.name}(priority={m.rule.priority})" for m in matches],
            )

        return matches

    @staticmethod
    def get_primary_rule(file_path: str, rules: list["Rule"]) -> Optional["Rule"]:
        """Get the highest priority rule for a file.

        Args:
            file_path: The file path to match against
            rules: List of rules to check

        Returns:
            The highest priority rule, or None if no match
        """
        matches = RuleMatcher.match_rules_to_file(file_path, rules)
        return matches[0].rule if matches else None

    @staticmethod
    def resolve_conflicting_rules(
        matches: list[RuleMatch],
    ) -> list[RuleMatch]:
        """Resolve conflicts when multiple rules match the same file.

        Strategy:
        - Rules with the same priority are kept (all applied)
        - If priorities differ, only the highest priority rules are kept
        - Rules are grouped by priority and the highest group is returned

        Args:
            matches: List of rule matches (should be pre-sorted by priority)

        Returns:
            List of resolved rule matches (highest priority group only)
        """
        if not matches:
            return []

        # Group matches by priority
        priority_groups: dict[int, list[RuleMatch]] = {}
        for match in matches:
            priority = match.rule.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(match)

        # Get the highest priority
        max_priority = max(priority_groups.keys())

        # Return all rules with the highest priority
        resolved = priority_groups[max_priority]

        if len(matches) > len(resolved):
            logger.info(
                "Resolved %d rule matches to %d highest priority rule(s) (priority=%d)",
                len(matches),
                len(resolved),
                max_priority,
            )

        return resolved

    @staticmethod
    def _matches_selector(file_path: str, selector: str) -> bool:
        """Check if a file path matches a selector pattern.

        Supports glob patterns (e.g., '*.py', '**/*.ts', 'src/api/**').

        Args:
            file_path: The file path to check
            selector: The glob pattern selector

        Returns:
            True if the file path matches the selector
        """
        # Normalize paths for matching
        normalized_path = file_path.replace("\\", "/")
        return fnmatch.fnmatch(normalized_path, selector) or fnmatch.fnmatch(
            normalized_path, f"**/{selector}"
        )
