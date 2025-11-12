"""
Rule matching engine for mapping code changes to Confluence pages.

Implements path/module selector matching with glob and regular expression support.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import fnmatch
import re
from pathlib import PurePosixPath
from typing import Iterable, Sequence  # noqa: UP035


class SelectorKind(Enum):
    """Kinds of selector patterns that a rule may use."""

    GLOB = "glob"
    REGEX = "regex"


@dataclass(frozen=True, slots=True)
class RuleDefinition:
    """In-memory representation of a rule that can be evaluated by the engine."""

    id: int
    name: str
    selector: str
    space_key: str
    page_id: str
    template_id: int | None = None
    auto_approve: bool = False


class RuleEngine:
    """Evaluates rule selectors against file paths or module identifiers."""

    def __init__(self, rules: Iterable[RuleDefinition] | None = None) -> None:
        self._rules: list[
            tuple[RuleDefinition, tuple[SelectorKind, str | re.Pattern[str]]]
        ] = []
        if rules:
            self.load_rules(rules)

    def load_rules(self, rules: Iterable[RuleDefinition]) -> None:
        """Replace the current rule set with a new collection."""
        self._rules.clear()
        for rule in rules:
            self.add_rule(rule)

    def add_rule(self, rule: RuleDefinition) -> None:
        """Add a rule to the engine with a compiled selector."""
        compiled = self._compile_selector(rule.selector)
        self._rules.append((rule, compiled))

    def match(self, target: str) -> Sequence[RuleDefinition]:
        """
        Return every rule whose selector matches the provided target.

        Parameters
        ----------
        target:
            A file path or module identifier to evaluate. Paths are normalized
            to POSIX style to ensure consistent matching across operating systems.
        """
        normalized = self._normalize_target(target)
        matches: list[RuleDefinition] = []
        for rule, (selector_kind, compiled) in self._rules:
            if selector_kind is SelectorKind.GLOB:
                pattern = compiled if isinstance(compiled, str) else compiled.pattern
                if fnmatch.fnmatch(normalized, pattern):
                    matches.append(rule)
            else:
                assert isinstance(compiled, re.Pattern)
                if compiled.search(normalized):
                    matches.append(rule)
        return matches

    @staticmethod
    def _normalize_target(target: str) -> str:
        """Normalize a file path or module name to POSIX form for matching."""
        if not target:
            return ""
        # PurePosixPath will convert Windows backslashes to forward slashes.
        return str(PurePosixPath(target))

    @staticmethod
    def _compile_selector(selector: str) -> tuple[SelectorKind, str | re.Pattern[str]]:
        """Compile the selector into a form optimized for matching."""
        kind, pattern = RuleEngine._determine_selector(selector)
        if kind is SelectorKind.REGEX:
            return kind, re.compile(pattern)
        return kind, pattern

    @staticmethod
    def _determine_selector(selector: str) -> tuple[SelectorKind, str]:
        """
        Determine the selector kind and raw pattern from a selector string.

        Supported prefixes:
            - ``regex:`` or ``re:`` to indicate a regular expression.
            - ``glob:`` to explicitly mark a glob pattern.
        If no prefix is provided the selector defaults to glob matching.
        """
        if selector.startswith("regex:"):
            return SelectorKind.REGEX, selector[len("regex:") :]
        if selector.startswith("re:"):
            return SelectorKind.REGEX, selector[len("re:") :]
        if selector.startswith("glob:"):
            return SelectorKind.GLOB, selector[len("glob:") :]
        return SelectorKind.GLOB, selector


__all__ = ["RuleDefinition", "RuleEngine", "SelectorKind"]
