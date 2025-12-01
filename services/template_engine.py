"""Template engine for rendering Confluence documentation templates.

This module provides functionality to render templates with placeholders,
supporting both Markdown and Confluence Storage Format as specified in FR-10.
"""

import logging
import re
from typing import Any

from db.models import Template

logger = logging.getLogger(__name__)


class TemplateEngineError(Exception):
    """Base exception for template engine errors."""


class InvalidTemplateError(TemplateEngineError):
    """Raised when a template is invalid or cannot be rendered."""


class TemplateEngine:
    """Engine for rendering templates with variable substitution."""

    # Pattern to match template variables: {{variable_name}} or {{variable.name}}
    VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_.]+)\}\}")

    def __init__(self):
        """Initialize the template engine."""

    def render(
        self,
        template: Template,
        context: dict[str, Any],
    ) -> str:
        """Render a template with the provided context.

        Supports variable substitution using {{variable_name}} syntax.
        Variables can be nested using dot notation: {{variable.nested.property}}

        Args:
            template: The Template database record to render
            context: Dictionary of variables to substitute in the template

        Returns:
            Rendered template string with variables substituted

        Raises:
            InvalidTemplateError: If template rendering fails
        """
        try:
            if not template:
                raise InvalidTemplateError("Template cannot be None")

            if not template.body:
                raise InvalidTemplateError("Template body cannot be empty")

            # Start with the template body
            rendered = template.body

            # Find all variables in the template
            variables = self.VARIABLE_PATTERN.findall(rendered)

            # Substitute each variable
            for var_name in variables:
                value = self._get_context_value(context, var_name)
                placeholder = f"{{{{{var_name}}}}}"
                rendered = rendered.replace(placeholder, str(value))

            logger.debug(
                f"Rendered template '{template.name}' (format: {template.format})",
                extra={
                    "template_id": template.id,
                    "template_name": template.name,
                    "template_format": template.format,
                    "variables_found": len(variables),
                },
            )

            return rendered

        except InvalidTemplateError:
            raise
        except Exception as e:
            logger.exception(
                f"Error rendering template '{template.name}': {e}",
                extra={
                    "template_id": template.id if template else None,
                    "template_name": template.name if template else None,
                },
            )
            raise InvalidTemplateError(f"Failed to render template: {e}") from e

    def _get_context_value(self, context: dict[str, Any], var_path: str) -> Any:
        """Get a value from context using dot notation.

        Args:
            context: The context dictionary
            var_path: Variable path, e.g., "variable" or "variable.nested.property"

        Returns:
            The value from context, or empty string if not found
        """
        parts = var_path.split(".")
        current = context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    logger.warning(
                        f"Variable '{var_path}' not found in context, using empty string",
                        extra={"var_path": var_path, "missing_part": part},
                    )
                    return ""
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                logger.warning(
                    f"Variable '{var_path}' not found in context, using empty string",
                    extra={"var_path": var_path, "missing_part": part},
                )
                return ""

        return current if current is not None else ""

    def validate_template(self, template: Template) -> bool:
        """Validate that a template can be rendered.

        Checks that the template has a body and that the format is valid.

        Args:
            template: The Template to validate

        Returns:
            True if template is valid

        Raises:
            InvalidTemplateError: If template is invalid
        """
        if not template:
            raise InvalidTemplateError("Template cannot be None")

        if not template.body:
            raise InvalidTemplateError("Template body cannot be empty")

        if template.format not in ("Markdown", "Storage"):
            raise InvalidTemplateError(
                f"Invalid template format: {template.format}. Must be 'Markdown' or 'Storage'"
            )

        return True
