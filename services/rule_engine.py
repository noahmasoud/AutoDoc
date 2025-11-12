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
            tuple[
                RuleDefinition,
                list[tuple[SelectorKind, str | re.Pattern[str]]],
            ]
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
        selectors = self._split_selector(rule.selector)
        compiled = [self._compile_selector(item) for item in selectors]
        self._rules.append((rule, compiled))

    def match(self, target: str) -> Sequence[RuleDefinition]:
        """
        Return every rule whose selectors match the provided target.

        Parameters
        ----------
        target:
            A file path or module identifier to evaluate. Paths are normalized
            to POSIX style to ensure consistent matching across operating systems.
        """
        normalized = self._normalize_target(target)
        matches: list[RuleDefinition] = []
        for rule, compiled_selectors in self._rules:
            for selector_kind, compiled in compiled_selectors:
                if selector_kind is SelectorKind.GLOB:
                    pattern = (
                        compiled if isinstance(compiled, str) else compiled.pattern
                    )
                    if fnmatch.fnmatch(normalized, pattern):
                        matches.append(rule)
                        break
                else:
                    assert isinstance(compiled, re.Pattern)
                    if compiled.search(normalized):
                        matches.append(rule)
                        break
        return matches

    @staticmethod
    def _normalize_target(target: str) -> str:
        """Normalize a file path or module name to POSIX form for matching."""
        if not target:
            return ""
        # PurePosixPath will convert Windows backslashes to forward slashes.
        return str(PurePosixPath(target))

    @staticmethod
    def _split_selector(selector: str) -> list[str]:
        """
        Split a selector string into individual selector expressions.

        Selectors can be separated by newlines or semicolons. Whitespace around
        each selector is ignored. If no separators are found the original
        selector is returned.
        """
        if not selector:
            return []
        normalized = selector.replace("\r\n", "\n").replace("\r", "\n")
        parts: list[str] = []
        for chunk in normalized.split("\n"):
            for piece in chunk.split(";"):
                text = piece.strip()
                if text:
                    parts.append(text)
        return parts or [selector]

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
