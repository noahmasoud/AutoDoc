"""Template engine for rendering Markdown and Confluence Storage Format templates.

This module provides template rendering functionality that supports both Markdown
and Confluence Storage Format (XML-based) templates with proper escaping and validation.

Per FR-10: Template-driven generation of content patches.
Per NFR-10: Output sanitization to prevent script injection.
"""

import logging
import re
import xml.etree.ElementTree as ET
from html import escape as html_escape
from typing import Any

logger = logging.getLogger(__name__)


class TemplateEngineError(Exception):
    """Base exception for template engine errors."""


class TemplateValidationError(TemplateEngineError):
    """Raised when template validation fails."""


class TemplateEngine:
    """Engine for rendering templates in Markdown or Confluence Storage Format.

    Supports placeholder substitution with proper escaping based on format.
    """

    # Pattern for placeholder variables: {{variable_name}}
    PLACEHOLDER_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    @classmethod
    def render(
        cls,
        template_body: str,
        format: str,  # noqa: A002
        variables: dict[str, Any],
    ) -> str:
        """Render a template with variable substitution.

        Args:
            template_body: The template body with {{variable}} placeholders
            format: Template format - "Markdown" or "Storage"
            variables: Dictionary of variable values to substitute

        Returns:
            Rendered template string

        Raises:
            TemplateEngineError: If rendering fails
            TemplateValidationError: If Storage Format output is invalid XML
        """
        if format not in ("Markdown", "Storage"):
            raise TemplateEngineError(
                f"Invalid template format: {format}. Must be 'Markdown' or 'Storage'"
            )

        # Perform placeholder substitution
        rendered = cls._substitute_placeholders(template_body, variables, format)

        # Validate Storage Format output
        if format == "Storage":
            cls._validate_storage_format(rendered)

        return rendered

    @classmethod
    def _substitute_placeholders(
        cls,
        template_body: str,
        variables: dict[str, Any],
        format: str,  # noqa: A002
    ) -> str:
        """Substitute placeholders in template body with variable values.

        Args:
            template_body: Template body with {{variable}} placeholders
            variables: Dictionary of variable values
            format: Template format for escaping

        Returns:
            Template with placeholders replaced
        """

        def replace_placeholder(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in variables:
                logger.warning(
                    f"Placeholder '{{{{{var_name}}}}}' not found in variables, leaving as-is",
                    extra={"variable": var_name},
                )
                return match.group(0)  # Return original placeholder

            value = str(variables[var_name])

            # Escape based on format
            if format == "Storage":
                # For Storage Format, escape XML/HTML characters
                return cls._escape_storage_format(value)
            # For Markdown, treat as plain text (no escaping needed for basic substitution)
            return value

        return cls.PLACEHOLDER_PATTERN.sub(replace_placeholder, template_body)

    @classmethod
    def _escape_storage_format(cls, value: str) -> str:
        """Escape a value for safe inclusion in Confluence Storage Format XML.

        Escapes XML/HTML special characters to prevent script injection (NFR-10).

        Args:
            value: Value to escape

        Returns:
            Escaped value safe for XML/HTML
        """
        # Use HTML escaping which handles: <, >, &, ", '
        return html_escape(value)

    @classmethod
    def _validate_storage_format(cls, rendered: str) -> None:
        """Validate that rendered Storage Format output is well-formed XML.

        Args:
            rendered: Rendered template output

        Raises:
            TemplateValidationError: If XML is not well-formed, with friendly error message
        """
        # Allow empty strings (valid for empty templates)
        if not rendered.strip():
            return

        try:
            # Confluence Storage Format uses namespaces (ac:, ri:, etc.)
            # We need to handle namespace prefixes. Try wrapping in a root element
            # with namespace declarations for validation
            wrapped_xml = (
                '<root xmlns:ac="http://atlassian.com/content" '
                'xmlns:ri="http://atlassian.com/rich">'
                f"{rendered}</root>"
            )
            ET.fromstring(wrapped_xml)
        except ET.ParseError as e:
            # If wrapping fails, try parsing directly (might work for simple XML)
            try:
                ET.fromstring(rendered)
            except ET.ParseError:
                # Provide a friendly error message
                error_msg = (
                    f"Invalid Confluence Storage Format XML: {e!s}. "
                    "Please ensure your template produces valid XML and that all "
                    "variable values are properly escaped."
                )
                raise TemplateValidationError(error_msg) from e
        except Exception as e:
            # Catch any other XML parsing errors
            error_msg = (
                f"Error validating Storage Format XML: {e!s}. "
                "Please check your template syntax."
            )
            raise TemplateValidationError(error_msg) from e
