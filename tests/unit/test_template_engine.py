"""Unit tests for template engine.

Tests variable substitution including simple variables, nested objects,
and handling of missing variables.
"""

import pytest

from autodoc.templates.engine import TemplateEngine
from db.models import Template


class TestTemplateEngine:
    """Tests for TemplateEngine class."""

    def test_simple_variable_substitution(self):
        """Test simple variable substitution."""
        engine = TemplateEngine()
        template = "Hello {{name}}!"
        variables = {"name": "World"}
        result = engine.render(template, variables, "Markdown")
        assert result == "Hello World!"

    def test_multiple_simple_variables(self):
        """Test multiple simple variables in one template."""
        engine = TemplateEngine()
        template = "{{greeting}}, {{name}}! Welcome to {{project}}."
        variables = {
            "greeting": "Hello",
            "name": "AutoDoc",
            "project": "Documentation",
        }
        result = engine.render(template, variables, "Markdown")
        assert result == "Hello, AutoDoc! Welcome to Documentation."

    def test_nested_object_access(self):
        """Test nested object access using dot notation."""
        engine = TemplateEngine()
        template = "The function {{symbol.name}} is located at {{symbol.file_path}}."
        variables = {
            "symbol": {
                "name": "process_request",
                "file_path": "src/api.py",
            },
        }
        result = engine.render(template, variables, "Markdown")
        assert result == "The function process_request is located at src/api.py."

    def test_multiple_levels_of_nesting(self):
        """Test multiple levels of nested object access."""
        engine = TemplateEngine()
        template = "{{change.symbol.name}} was {{change.type}} in {{change.file.path}}."
        variables = {
            "change": {
                "symbol": {"name": "handle_error"},
                "type": "added",
                "file": {"path": "src/api.py"},
            },
        }
        result = engine.render(template, variables, "Markdown")
        assert result == "handle_error was added in src/api.py."

    def test_missing_variable_unchanged(self):
        """Test that missing variables leave placeholder unchanged."""
        engine = TemplateEngine()
        template = "Hello {{name}}, your status is {{status}}."
        variables = {"name": "World"}
        result = engine.render(template, variables, "Markdown")
        assert result == "Hello World, your status is {{status}}."

    def test_all_variables_missing(self):
        """Test template with all variables missing."""
        engine = TemplateEngine()
        template = "{{missing1}} and {{missing2}}"
        variables = {}
        result = engine.render(template, variables, "Markdown")
        assert result == "{{missing1}} and {{missing2}}"

    def test_nested_path_partially_missing(self):
        """Test nested path where intermediate key is missing."""
        engine = TemplateEngine()
        template = "Value: {{obj.missing.property}}"
        variables = {"obj": {"other": "value"}}
        result = engine.render(template, variables, "Markdown")
        assert result == "Value: {{obj.missing.property}}"

    def test_nested_path_invalid_type(self):
        """Test nested path where intermediate value is not a dict."""
        engine = TemplateEngine()
        template = "Value: {{obj.property}}"
        variables = {"obj": "not_a_dict"}
        result = engine.render(template, variables, "Markdown")
        assert result == "Value: {{obj.property}}"

    def test_format_validation_markdown(self):
        """Test that Markdown format is accepted."""
        engine = TemplateEngine()
        template = "{{name}}"
        variables = {"name": "test"}
        result = engine.render(template, variables, "Markdown")
        assert result == "test"

    def test_format_validation_storage(self):
        """Test that Storage format is accepted."""
        engine = TemplateEngine()
        template = "{{name}}"
        variables = {"name": "test"}
        result = engine.render(template, variables, "Storage")
        assert result == "test"

    def test_format_validation_invalid(self):
        """Test that invalid format raises ValueError."""
        engine = TemplateEngine()
        template = "{{name}}"
        variables = {"name": "test"}
        with pytest.raises(ValueError, match="Invalid template format"):
            engine.render(template, variables, "InvalidFormat")

    def test_numeric_values(self):
        """Test that numeric values are converted to strings."""
        engine = TemplateEngine()
        template = "Line {{lineno}} has {{count}} changes."
        variables = {"lineno": 42, "count": 5}
        result = engine.render(template, variables, "Markdown")
        assert result == "Line 42 has 5 changes."

    def test_boolean_values(self):
        """Test that boolean values are converted to strings."""
        engine = TemplateEngine()
        template = "Auto-approve: {{auto_approve}}"
        variables = {"auto_approve": True}
        result = engine.render(template, variables, "Markdown")
        assert result == "Auto-approve: True"

    def test_none_value(self):
        """Test that None values are converted to string 'None'."""
        engine = TemplateEngine()
        template = "Value: {{value}}"
        variables = {"value": None}
        result = engine.render(template, variables, "Markdown")
        assert result == "Value: None"

    def test_empty_template(self):
        """Test rendering empty template."""
        engine = TemplateEngine()
        template = ""
        variables = {"name": "test"}
        result = engine.render(template, variables, "Markdown")
        assert result == ""

    def test_template_with_no_placeholders(self):
        """Test template with no placeholders."""
        engine = TemplateEngine()
        template = "This is a static template with no variables."
        variables = {"name": "test"}
        result = engine.render(template, variables, "Markdown")
        assert result == "This is a static template with no variables."

    def test_whitespace_in_placeholder(self):
        """Test that whitespace in placeholder is trimmed."""
        engine = TemplateEngine()
        template = "Hello {{  name  }}!"
        variables = {"name": "World"}
        result = engine.render(template, variables, "Markdown")
        assert result == "Hello World!"

    def test_render_template_entity(self):
        """Test rendering from Template entity."""
        engine = TemplateEngine()
        template_entity = Template(
            id=1,
            name="test_template",
            format="Markdown",
            body="Hello {{name}}!",
            variables=None,
        )
        variables = {"name": "World"}
        result = engine.render_template(template_entity, variables)
        assert result == "Hello World!"

    def test_render_template_entity_storage_format(self):
        """Test rendering from Template entity with Storage format."""
        engine = TemplateEngine()
        template_entity = Template(
            id=1,
            name="test_template",
            format="Storage",
            body="<p>{{content}}</p>",
            variables=None,
        )
        variables = {"content": "Hello World"}
        result = engine.render_template(template_entity, variables)
        assert result == "<p>Hello World</p>"

    def test_complex_nested_structure(self):
        """Test rendering with complex nested structure."""
        engine = TemplateEngine()
        template = """
# Change Summary

**Symbol:** {{symbol.name}}
**Type:** {{symbol.type}}
**Location:** {{symbol.file_path}}:{{symbol.lineno}}
**Description:** {{symbol.docstring}}
"""
        variables = {
            "symbol": {
                "name": "handle_error",
                "type": "function",
                "file_path": "src/api.py",
                "lineno": 42,
                "docstring": "Handles API errors gracefully",
            },
        }
        result = engine.render(template, variables, "Markdown")
        assert "**Symbol:** handle_error" in result
        assert "**Type:** function" in result
        assert "**Location:** src/api.py:42" in result
        assert "**Description:** Handles API errors gracefully" in result
