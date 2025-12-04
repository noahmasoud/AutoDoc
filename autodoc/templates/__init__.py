"""Template engine module for AutoDoc.

Provides template rendering with variable substitution for generating
Confluence documentation patches.
"""

from autodoc.templates.engine import (
    MissingVariableError,
    TemplateEngine,
    TemplateError,
    TemplateSyntaxError,
    UnsupportedFormatError,
)

# Alias for backwards compatibility
TemplateEngineError = TemplateError
TemplateValidationError = TemplateSyntaxError

__all__ = [
    "MissingVariableError",
    "TemplateEngine",
    "TemplateEngineError",
    "TemplateError",
    "TemplateSyntaxError",
    "TemplateValidationError",
    "UnsupportedFormatError",
]
