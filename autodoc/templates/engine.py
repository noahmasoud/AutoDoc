"""Template engine for variable substitution in AutoDoc templates.

This module implements the core template rendering functionality that
underpins FR-10 and FR-20 by allowing template-driven patch generation
with placeholders for analyzer findings and metadata.

Per SRS 4.3: Confluence Mapping & Patch Generation.
Per FR-24 and NFR-3/NFR-4: Graceful error handling with structured error objects.
"""

import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from db.models import Template


class TemplateError(Exception):
    """Base exception for template engine errors.

    Provides structured error information for logging and UI display.
    Supports FR-24: UI displays run/patch status and error details.
    """

    def __init__(
        self,
        message: str,
        code: str,
        template_id: int | None = None,
        variable: str | None = None,
    ):
        """Initialize template error.

        Args:
            message: Human-readable error message
            code: Error code for programmatic handling
            template_id: Optional template ID associated with the error
            variable: Optional variable name associated with the error
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.template_id = template_id
        self.variable = variable

    def to_dict(self) -> dict[str, Any]:
        """Convert error to structured dictionary for logging/storage.

        Returns:
            Dictionary with error details
        """
        return {
            "code": self.code,
            "message": self.message,
            "template_id": self.template_id,
            "variable": self.variable,
        }


class TemplateSyntaxError(TemplateError):
    """Raised when template has invalid placeholder syntax."""

    def __init__(
        self,
        message: str,
        template_id: int | None = None,
        variable: str | None = None,
    ):
        super().__init__(message, "TEMPLATE_SYNTAX_ERROR", template_id, variable)


class MissingVariableError(TemplateError):
    """Raised when a required variable is missing from the context."""

    def __init__(
        self,
        message: str,
        template_id: int | None = None,
        variable: str | None = None,
    ):
        super().__init__(message, "MISSING_VARIABLE", template_id, variable)


class UnsupportedFormatError(TemplateError):
    """Raised when template format is not supported."""

    def __init__(
        self,
        message: str,
        template_id: int | None = None,
        format: str | None = None,  # noqa: A002
    ):
        super().__init__(message, "UNSUPPORTED_FORMAT", template_id, format)


class TemplateEngine:
    """Template engine for rendering templates with variable substitution.

    Supports simple variables ({{variable_name}}) and nested object access
    ({{object.property}}). Missing variables are left unchanged in the output.

    Per FR-24 and NFR-3/NFR-4: Graceful error handling with structured exceptions.

    Example:
        >>> engine = TemplateEngine()
        >>> template = "Hello {{name}}!"
        >>> variables = {"name": "World"}
        >>> engine.render(template, variables, "Markdown")
        'Hello World!'
    """

    # Pattern to match {{variable}} or {{object.property}} placeholders
    PLACEHOLDER_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    @classmethod
    def extract_variables(cls, template_body: str) -> dict[str, dict[str, Any]]:
        """Extract variable names from template body and create metadata structure.

        Finds all {{variable_name}} or {{object.property}} placeholders in the template
        and returns a dictionary structure suitable for the Template.variables field.

        Args:
            template_body: Template content to analyze

        Returns:
            Dictionary mapping variable names to metadata dictionaries with
            'description' field. Example:
            {
                "variable_name": {"description": "Variable: variable_name"},
                "object.property": {"description": "Variable: object.property"}
            }
        """
        variables: dict[str, dict[str, Any]] = {}

        # Find all placeholders
        matches = cls.PLACEHOLDER_PATTERN.findall(template_body)

        for placeholder in matches:
            var_name = placeholder.strip()

            # Skip empty placeholders (shouldn't happen, but be safe)
            if not var_name:
                continue

            # Only add if not already seen (deduplicate)
            if var_name not in variables:
                variables[var_name] = {
                    "description": f"Variable: {var_name}",
                }

        return variables

    @classmethod
    def render(
        cls,
        template_body: str,
        format: str,  # noqa: A002
        variables: dict[str, Any],
        template_id: int | None = None,
        strict_mode: bool = False,
    ) -> str:
        """Render a template by substituting variables.

        Catches low-level errors and wraps them as structured exceptions
        for graceful error handling (FR-24, NFR-3, NFR-4).

        Args:
            template_body: The template content with placeholders (e.g., {{name}})
            format: Template format ("Markdown" or "Storage") - used for validation
            variables: Dictionary of variables to substitute
            template_id: Optional template ID for error reporting
            strict_mode: If True, raise MissingVariableError for missing variables.
                        If False, leave missing variables unchanged (default).

        Returns:
            Rendered template with variables substituted

        Raises:
            UnsupportedFormatError: If format is not "Markdown" or "Storage"
            TemplateSyntaxError: If template has invalid placeholder syntax
            MissingVariableError: If strict_mode=True and a required variable is missing
        """
        try:
            # Validate format first
            if format not in ("Markdown", "Storage"):
                raise UnsupportedFormatError(
                    f"Invalid template format: {format}. Must be 'Markdown' or 'Storage'",
                    template_id=template_id,
                    format=format,
                )

            # Validate template syntax (check for malformed placeholders)
            cls._validate_template_syntax(template_body, template_id)

            def replace_placeholder(match: re.Match[str]) -> str:
                """Replace a single placeholder with its value."""
                try:
                    placeholder = match.group(1).strip()

                    # Validate placeholder syntax
                    if not placeholder:
                        raise TemplateSyntaxError(
                            "Empty placeholder found in template",
                            template_id=template_id,
                        )

                    value, found = cls._get_nested_value(variables, placeholder)

                    if not found:
                        if strict_mode:
                            raise MissingVariableError(
                                f"Required variable '{placeholder}' is missing from context",
                                template_id=template_id,
                                variable=placeholder,
                            )
                        # Variable not found - leave placeholder unchanged (non-strict)
                        return match.group(0)

                    # Convert value to string (including None -> "None")
                    return str(value)
                except (TemplateSyntaxError, MissingVariableError):
                    # Re-raise structured exceptions
                    raise
                except Exception as e:
                    # Wrap unexpected errors
                    raise TemplateSyntaxError(
                        f"Error processing placeholder: {e!s}",
                        template_id=template_id,
                        variable=match.group(1).strip() if match else None,
                    ) from e

            # Replace all placeholders
            try:
                rendered = cls.PLACEHOLDER_PATTERN.sub(
                    replace_placeholder, template_body
                )
            except re.error as e:
                # Invalid regex pattern (shouldn't happen with our pattern, but catch anyway)
                raise TemplateSyntaxError(
                    f"Invalid template pattern: {e!s}",
                    template_id=template_id,
                ) from e

            # Validate Storage Format XML after rendering
            if format == "Storage":
                cls._validate_storage_format(rendered, template_id)

            return rendered

        except (UnsupportedFormatError, TemplateSyntaxError, MissingVariableError):
            # Re-raise our structured exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors and wrap them
            raise TemplateSyntaxError(
                f"Unexpected error during template rendering: {e!s}",
                template_id=template_id,
            ) from e

    @classmethod
    def _validate_template_syntax(
        cls, template_body: str, template_id: int | None
    ) -> None:
        """Validate template syntax for common errors.

        Args:
            template_body: Template content to validate
            template_id: Optional template ID for error reporting

        Raises:
            TemplateSyntaxError: If template has invalid syntax
        """
        # Check for unclosed placeholders (e.g., {{ without }})
        open_braces = template_body.count("{{")
        close_braces = template_body.count("}}")

        if open_braces != close_braces:
            raise TemplateSyntaxError(
                f"Mismatched placeholder braces: found {open_braces} opening '{{{{' "
                f"but {close_braces} closing '}}'",
                template_id=template_id,
            )

        # Check for nested placeholders (e.g., {{{{var}}}} which is invalid)
        if "{{{{" in template_body or "}}}}" in template_body:
            raise TemplateSyntaxError(
                "Invalid nested placeholder syntax detected",
                template_id=template_id,
            )

    @classmethod
    def _validate_storage_format(cls, rendered: str, template_id: int | None) -> None:
        """Validate that rendered Storage Format output is well-formed XML.

        Args:
            rendered: Rendered template output
            template_id: Optional template ID for error reporting

        Raises:
            TemplateSyntaxError: If XML is not well-formed
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
                raise TemplateSyntaxError(
                    f"Invalid Confluence Storage Format XML: {e!s}. "
                    "Please ensure your template produces valid XML.",
                    template_id=template_id,
                ) from e
        except Exception as e:
            # Catch any other XML parsing errors
            raise TemplateSyntaxError(
                f"Error validating Storage Format XML: {e!s}",
                template_id=template_id,
            ) from e

    @classmethod
    def _get_nested_value(cls, context: dict[str, Any], path: str) -> tuple[Any, bool]:
        """Get a value from a nested dictionary using dot notation.

        Args:
            context: The variable context dictionary
            path: Dot-separated path (e.g., "symbol.name")

        Returns:
            Tuple of (value, found) where found indicates if the path exists.
            If found is False, the value is None and the variable is missing.
            If found is True, the value may be None (variable exists but is None).
        """
        parts = path.split(".")
        current: Any = context

        for part in parts:
            if not isinstance(current, dict):
                return (None, False)

            if part not in current:
                return (None, False)

            current = current[part]

        return (current, True)

    def render_template(
        self,
        template: "Template",
        variables: dict[str, Any],
        strict_mode: bool = False,
    ) -> str:
        """Render a Template entity with the given variables.

        This method integrates with the Template database entity, allowing
        stored templates to be rendered directly.

        Args:
            template: The Template entity from the database
            variables: Dictionary of variables to substitute
            strict_mode: If True, raise MissingVariableError for missing variables

        Returns:
            Rendered template with variables substituted

        Raises:
            UnsupportedFormatError: If template format is not "Markdown" or "Storage"
            TemplateSyntaxError: If template has invalid placeholder syntax
            MissingVariableError: If strict_mode=True and a required variable is missing
        """
        return self.__class__.render(
            template.body, template.format, variables, template.id, strict_mode
        )
