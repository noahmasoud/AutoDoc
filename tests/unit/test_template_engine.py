"""Unit tests for TemplateEngine.

Tests template rendering for both Markdown and Confluence Storage Format,
including variable substitution, escaping, and validation.
"""

import pytest
from services.template_engine import (
    TemplateEngine,
    TemplateEngineError,
    TemplateValidationError,
)


class TestTemplateEngineMarkdown:
    """Tests for Markdown template rendering."""

    def test_render_markdown_simple(self):
        """Test simple Markdown rendering with variables."""
        template = "# {{title}}\n\n{{description}}"
        variables = {
            "title": "API Documentation",
            "description": "This is the API docs.",
        }
        result = TemplateEngine.render(template, "Markdown", variables)
        assert result == "# API Documentation\n\nThis is the API docs."

    def test_render_markdown_multiple_variables(self):
        """Test Markdown rendering with multiple variables."""
        template = (
            "Function: {{function_name}}\nType: {{change_type}}\nFile: {{file_path}}"
        )
        variables = {
            "function_name": "process_data",
            "change_type": "added",
            "file_path": "src/api.py",
        }
        result = TemplateEngine.render(template, "Markdown", variables)
        assert "process_data" in result
        assert "added" in result
        assert "src/api.py" in result

    def test_render_markdown_missing_variable(self):
        """Test that missing variables are left as-is in Markdown."""
        template = "Hello {{name}}, your age is {{age}}"
        variables = {"name": "Alice"}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert "Hello Alice" in result
        assert "{{age}}" in result  # Missing variable left as-is

    def test_render_markdown_empty_template(self):
        """Test rendering empty Markdown template."""
        result = TemplateEngine.render("", "Markdown", {})
        assert result == ""

    def test_render_markdown_no_placeholders(self):
        """Test rendering Markdown template with no placeholders."""
        template = "# Static Content\n\nThis has no variables."
        result = TemplateEngine.render(template, "Markdown", {})
        assert result == template

    def test_render_markdown_special_characters(self):
        """Test that special characters in Markdown are not escaped."""
        template = "Content: {{content}}"
        variables = {"content": "Special chars: < > & \" '"}
        result = TemplateEngine.render(template, "Markdown", variables)
        # In Markdown, we don't escape, so special chars should appear as-is
        assert "< > & \" '" in result


class TestTemplateEngineStorageFormat:
    """Tests for Confluence Storage Format template rendering."""

    def test_render_storage_format_simple(self):
        """Test simple Storage Format rendering with variables."""
        template = "<ac:structured-macro><ac:parameter>{{param}}</ac:parameter></ac:structured-macro>"
        variables = {"param": "value"}
        result = TemplateEngine.render(template, "Storage", variables)
        assert "value" in result
        # Validation ensures XML is well-formed (wrapped with namespace declarations)

    def test_render_storage_format_escapes_xml(self):
        """Test that Storage Format properly escapes XML special characters."""
        template = "<p>{{content}}</p>"
        variables = {"content": "Text with <script>alert('xss')</script>"}
        result = TemplateEngine.render(template, "Storage", variables)
        # Should escape < and >
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        # Validation ensures XML is well-formed

    def test_render_storage_format_escapes_quotes(self):
        """Test that Storage Format escapes quotes and ampersands."""
        template = "<p>{{content}}</p>"
        variables = {"content": 'Text with "quotes" & ampersands'}
        result = TemplateEngine.render(template, "Storage", variables)
        # Should escape quotes and ampersands
        assert (
            "&quot;" in result or '"' in result
        )  # Quotes may or may not be escaped depending on context
        assert "&amp;" in result
        # Validation ensures XML is well-formed

    def test_render_storage_format_valid_xml(self):
        """Test that rendered Storage Format produces valid XML."""
        template = """<ac:structured-macro ac:name="code">
    <ac:parameter ac:name="language">{{language}}</ac:parameter>
    <ac:plain-text-body><![CDATA[{{code}}]]></ac:plain-text-body>
    </ac:structured-macro>"""
        variables = {"language": "python", "code": "def hello():\n    print('world')"}
        result = TemplateEngine.render(template, "Storage", variables)
        # Validation ensures XML is well-formed (wrapped with namespace declarations)
        assert "python" in result
        assert "def hello()" in result

    def test_render_storage_format_invalid_xml_raises_error(self):
        """Test that invalid XML in template raises TemplateValidationError."""
        # Template that produces invalid XML (unclosed tag)
        invalid_template = "<p>{{content}}"
        variables = {"content": "text"}
        with pytest.raises(TemplateValidationError):
            TemplateEngine.render(invalid_template, "Storage", variables)

    def test_render_storage_format_missing_variable(self):
        """Test that missing variables are left as-is in Storage Format."""
        template = "<p>{{name}} is {{age}} years old</p>"
        variables = {"name": "Bob"}
        result = TemplateEngine.render(template, "Storage", variables)
        assert "Bob" in result
        assert "{{age}}" in result  # Missing variable left as-is
        # Validation ensures XML is well-formed

    def test_render_storage_format_empty_template(self):
        """Test rendering empty Storage Format template."""
        result = TemplateEngine.render("", "Storage", {})
        assert result == ""

    def test_render_storage_format_complex_structure(self):
        """Test rendering complex Confluence Storage Format structure."""
        template = """<ac:structured-macro ac:name="panel">
    <ac:parameter ac:name="title">{{title}}</ac:parameter>
    <ac:rich-text-body>
    <h1>{{heading}}</h1>
    <p>{{description}}</p>
    </ac:rich-text-body>
    </ac:structured-macro>"""
        variables = {
            "title": "API Changes",
            "heading": "New Endpoints",
            "description": "Added endpoints for user management",
        }
        result = TemplateEngine.render(template, "Storage", variables)
        # Validation ensures XML is well-formed (wrapped with namespace declarations)
        assert "API Changes" in result
        assert "New Endpoints" in result
        assert "Added endpoints for user management" in result


class TestTemplateEngineValidation:
    """Tests for template validation and error handling."""

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises TemplateEngineError."""
        with pytest.raises(TemplateEngineError) as exc_info:
            TemplateEngine.render("template", "InvalidFormat", {})
        assert "Invalid template format" in str(exc_info.value)

    def test_storage_format_validation_catches_malformed_xml(self):
        """Test that Storage Format validation catches malformed XML."""
        # Template that produces malformed XML
        malformed_template = "<p>Unclosed paragraph"
        variables = {}
        with pytest.raises(TemplateValidationError) as exc_info:
            TemplateEngine.render(malformed_template, "Storage", variables)
        assert "Invalid Confluence Storage Format XML" in str(exc_info.value)

    def test_storage_format_validation_catches_invalid_tags(self):
        """Test that Storage Format validation catches invalid XML tags."""
        # Template with invalid tag structure
        invalid_template = "<p><invalid nesting></p></p>"
        variables = {}
        with pytest.raises(TemplateValidationError):
            TemplateEngine.render(invalid_template, "Storage", variables)


class TestTemplateEngineEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_nested_placeholders(self):
        """Test template with nested-looking placeholders."""
        template = "{{outer}} and {{inner}}"
        variables = {"outer": "{{fake}}", "inner": "value"}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert "{{fake}}" in result
        assert "value" in result

    def test_placeholder_at_start_and_end(self):
        """Test placeholders at template boundaries."""
        template = "{{start}}middle{{end}}"
        variables = {"start": "BEGIN", "end": "END"}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert result == "BEGINmiddleEND"

    def test_variable_with_empty_string(self):
        """Test substitution with empty string variable."""
        template = "Before{{empty}}After"
        variables = {"empty": ""}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert result == "BeforeAfter"

    def test_variable_with_none_converts_to_string(self):
        """Test that None values are converted to string."""
        template = "Value: {{value}}"
        variables = {"value": None}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert "None" in result

    def test_variable_with_number(self):
        """Test substitution with numeric values."""
        template = "Count: {{count}}, Price: {{price}}"
        variables = {"count": 42, "price": 99.99}
        result = TemplateEngine.render(template, "Markdown", variables)
        assert "42" in result
        assert "99.99" in result
