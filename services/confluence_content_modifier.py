"""Service for modifying Confluence Storage Format XML content.

This module provides utilities to modify Confluence page content using
different strategies: replace, append, and modify_section.
"""

import logging
import re
from typing import Literal

logger = logging.getLogger(__name__)


class ConfluenceContentModifier:
    """Modify Confluence Storage Format XML content using various strategies."""

    @staticmethod
    def replace(current_content: str, new_content: str) -> str:
        """Replace entire page content with new content.

        Args:
            current_content: Current page content (unused, kept for API consistency)
            new_content: New content to replace with

        Returns:
            New content string
        """
        return new_content

    @staticmethod
    def append(
        current_content: str,
        new_content: str,
        separator: str = "<hr/>",
    ) -> str:
        """Append new content to existing content with a separator.

        Args:
            current_content: Current page content
            new_content: Content to append
            separator: XML separator to insert between content (default: <hr/>)

        Returns:
            Combined content with separator
        """
        if not current_content.strip():
            return new_content

        return f"{current_content}{separator}{new_content}"

    @staticmethod
    def modify_section(
        current_content: str,
        marker: str,
        new_content: str,
        mode: Literal["replace", "append", "prepend"] = "replace",
    ) -> str:
        """Modify a specific section identified by an XML comment marker.

        The marker should be an XML comment like:
        <!-- AUTODOC_SECTION_NAME -->
        ...
        <!-- /AUTODOC_SECTION_NAME -->

        Args:
            current_content: Current page content
            marker: Section marker name (without <!-- -->)
            new_content: New content for the section
            mode: How to modify the section: "replace", "append", or "prepend"

        Returns:
            Modified content with updated section

        Raises:
            ValueError: If marker format is invalid or section not found
        """
        # Normalize marker (remove comment syntax if present)
        marker_clean = marker.strip()
        if marker_clean.startswith("<!--"):
            marker_clean = marker_clean[4:]
        if marker_clean.endswith("-->"):
            marker_clean = marker_clean[:-3]
        marker_clean = marker_clean.strip()

        # Create opening and closing markers
        open_marker = f"<!-- {marker_clean} -->"
        close_marker = f"<!-- /{marker_clean} -->"

        # Pattern to match the section (non-greedy to match first occurrence)
        pattern = re.compile(
            rf"({re.escape(open_marker)})(.*?)({re.escape(close_marker)})",
            re.DOTALL,
        )

        match = pattern.search(current_content)

        if not match:
            # Section not found - append it at the end
            logger.warning(
                f"Section marker '{marker_clean}' not found, appending new section at end",
            )
            separator = "<hr/>" if current_content.strip() else ""
            return f"{current_content}{separator}{open_marker}{new_content}{close_marker}"

        # Extract existing section content
        existing_section_content = match.group(2)

        # Apply mode
        if mode == "replace":
            updated_section = new_content
        elif mode == "append":
            updated_section = f"{existing_section_content}{new_content}"
        elif mode == "prepend":
            updated_section = f"{new_content}{existing_section_content}"
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'replace', 'append', or 'prepend'")

        # Replace the section
        replacement = f"{open_marker}{updated_section}{close_marker}"
        return pattern.sub(replacement, current_content, count=1)

    @staticmethod
    def apply_strategy(
        current_content: str,
        new_content: str,
        strategy: Literal["replace", "append", "modify_section"],
        **kwargs,
    ) -> str:
        """Apply the specified strategy to modify content.

        Args:
            current_content: Current page content
            new_content: New content to apply
            strategy: Strategy to use: "replace", "append", or "modify_section"
            **kwargs: Additional arguments:
                - separator: For "append" strategy (default: "<hr/>")
                - marker: For "modify_section" strategy (required)
                - mode: For "modify_section" strategy (default: "replace")

        Returns:
            Modified content

        Raises:
            ValueError: If required kwargs are missing or strategy is invalid
        """
        if strategy == "replace":
            return ConfluenceContentModifier.replace(current_content, new_content)
        elif strategy == "append":
            separator = kwargs.get("separator", "<hr/>")
            return ConfluenceContentModifier.append(current_content, new_content, separator)
        elif strategy == "modify_section":
            marker = kwargs.get("marker")
            if not marker:
                raise ValueError("marker is required for modify_section strategy")
            mode = kwargs.get("mode", "replace")
            return ConfluenceContentModifier.modify_section(
                current_content,
                marker,
                new_content,
                mode,
            )
        else:
            raise ValueError(
                f"Invalid strategy: {strategy}. Must be 'replace', 'append', or 'modify_section'",
            )

