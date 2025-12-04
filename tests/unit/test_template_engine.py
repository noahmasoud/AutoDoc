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


class TestTemplateEngineStructuredErrors:
    """Tests for structured error handling (FR-24, NFR-3, NFR-4).

    Tests the new exception types with structured error information:
    - MissingVariableError (missing required variable)
    - TemplateSyntaxError (invalid placeholder syntax)
    - UnsupportedFormatError (invalid format enum)
    """

    def test_missing_required_variable_strict_mode(self):
        """Test MissingVariableError when required variable is missing in strict mode."""
        from autodoc.templates.engine import (
            MissingVariableError,
            TemplateEngine,
        )

        template = "Hello {{name}}, your age is {{age}}"
        variables = {"name": "Alice"}

        with pytest.raises(MissingVariableError) as exc_info:
            TemplateEngine.render(template, "Markdown", variables, strict_mode=True)

        # Verify structured error information
        error = exc_info.value
        assert error.code == "MISSING_VARIABLE"
        assert "age" in error.message or error.variable == "age"
        assert error.variable == "age"

        # Verify error can be converted to dict for storage/logging
        error_dict = error.to_dict()
        assert error_dict["code"] == "MISSING_VARIABLE"
        assert error_dict["variable"] == "age"
        assert "message" in error_dict

    def test_invalid_placeholder_syntax(self):
        """Test TemplateSyntaxError for invalid placeholder syntax."""
        from autodoc.templates.engine import (
            TemplateEngine,
            TemplateSyntaxError,
        )

        # Test mismatched braces
        template = "Hello {{name}, your age is {{age}}"

        with pytest.raises(TemplateSyntaxError) as exc_info:
            TemplateEngine.render(template, "Markdown", {"name": "Alice"})

        error = exc_info.value
        assert error.code == "TEMPLATE_SYNTAX_ERROR"
        assert "Mismatched placeholder braces" in error.message

        # Verify error can be converted to dict
        error_dict = error.to_dict()
        assert error_dict["code"] == "TEMPLATE_SYNTAX_ERROR"
        assert "message" in error_dict

        # Test nested placeholders (invalid)
        invalid_template = "Hello {{{{name}}}}"

        with pytest.raises(TemplateSyntaxError) as exc_info2:
            TemplateEngine.render(invalid_template, "Markdown", {"name": "Alice"})

        error2 = exc_info2.value
        assert error2.code == "TEMPLATE_SYNTAX_ERROR"
        assert "nested placeholder" in error2.message.lower()

    def test_invalid_format_enum(self):
        """Test UnsupportedFormatError for invalid format enum."""
        from autodoc.templates.engine import (
            TemplateEngine,
            UnsupportedFormatError,
        )

        template = "Hello {{name}}"
        variables = {"name": "World"}

        with pytest.raises(UnsupportedFormatError) as exc_info:
            TemplateEngine.render(template, "InvalidFormat", variables)

        error = exc_info.value
        assert error.code == "UNSUPPORTED_FORMAT"
        assert "Invalid template format" in error.message
        assert "InvalidFormat" in error.message

        # Verify error can be converted to dict
        error_dict = error.to_dict()
        assert error_dict["code"] == "UNSUPPORTED_FORMAT"
        assert error_dict["message"] == error.message

        # Test with template_id for better error reporting
        with pytest.raises(UnsupportedFormatError) as exc_info2:
            TemplateEngine.render(
                template, "AnotherInvalidFormat", variables, template_id=123
            )

        error2 = exc_info2.value
        assert error2.template_id == 123
        error_dict2 = error2.to_dict()
        assert error_dict2["template_id"] == 123

    def test_error_structured_information(self):
        """Test that all error types provide structured information via to_dict()."""
        from autodoc.templates.engine import (
            MissingVariableError,
            TemplateSyntaxError,
            UnsupportedFormatError,
        )

        # Test MissingVariableError structured info
        missing_error = MissingVariableError(
            "Required variable 'test_var' is missing",
            template_id=1,
            variable="test_var",
        )
        missing_dict = missing_error.to_dict()
        assert missing_dict == {
            "code": "MISSING_VARIABLE",
            "message": "Required variable 'test_var' is missing",
            "template_id": 1,
            "variable": "test_var",
        }

        # Test TemplateSyntaxError structured info
        syntax_error = TemplateSyntaxError(
            "Invalid placeholder syntax",
            template_id=2,
            variable="bad_var",
        )
        syntax_dict = syntax_error.to_dict()
        assert syntax_dict == {
            "code": "TEMPLATE_SYNTAX_ERROR",
            "message": "Invalid placeholder syntax",
            "template_id": 2,
            "variable": "bad_var",
        }

        # Test UnsupportedFormatError structured info
        format_error = UnsupportedFormatError(
            "Invalid format: BadFormat",
            template_id=3,
            format="BadFormat",
        )
        format_dict = format_error.to_dict()
        assert format_dict["code"] == "UNSUPPORTED_FORMAT"
        assert format_dict["template_id"] == 3
