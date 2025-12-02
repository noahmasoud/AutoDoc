"""Template engine for variable substitution in AutoDoc templates.

This module implements the core template rendering functionality that
underpins FR-10 and FR-20 by allowing template-driven patch generation
with placeholders for analyzer findings and metadata.

Per SRS 4.3: Confluence Mapping & Patch Generation.
"""

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from db.models import Template


class TemplateEngine:
    """Template engine for rendering templates with variable substitution.

    Supports simple variables ({{variable_name}}) and nested object access
    ({{object.property}}). Missing variables are left unchanged in the output.

    Example:
        >>> engine = TemplateEngine()
        >>> template = "Hello {{name}}!"
        >>> variables = {"name": "World"}
        >>> engine.render(template, variables, "Markdown")
        'Hello World!'
    """

    # Pattern to match {{variable}} or {{object.property}} placeholders
    PLACEHOLDER_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    def render(
        self,
        template_body: str,
        variables: dict[str, Any],
        format: str,  # noqa: A002
    ) -> str:
        """Render a template by substituting variables.

        Args:
            template_body: The template content with placeholders (e.g., {{name}})
            variables: Dictionary of variables to substitute
            format: Template format ("Markdown" or "Storage") - used for validation

        Returns:
            Rendered template with variables substituted

        Raises:
            ValueError: If format is not "Markdown" or "Storage"
        """
        if format not in ("Markdown", "Storage"):
            raise ValueError(
                f"Invalid template format: {format}. Must be 'Markdown' or 'Storage'"
            )

        def replace_placeholder(match: re.Match[str]) -> str:
            """Replace a single placeholder with its value."""
            placeholder = match.group(1).strip()
            value, found = self._get_nested_value(variables, placeholder)

            if not found:
                # Variable not found - leave placeholder unchanged
                return match.group(0)

            # Convert value to string (including None -> "None")
            return str(value)

        # Replace all placeholders
        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, template_body)

    def _get_nested_value(self, context: dict[str, Any], path: str) -> tuple[Any, bool]:
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
    ) -> str:
        """Render a Template entity with the given variables.

        This method integrates with the Template database entity, allowing
        stored templates to be rendered directly.

        Args:
            template: The Template entity from the database
            variables: Dictionary of variables to substitute

        Returns:
            Rendered template with variables substituted

        Raises:
            ValueError: If template format is not "Markdown" or "Storage"
        """
        return self.render(template.body, variables, template.format)
