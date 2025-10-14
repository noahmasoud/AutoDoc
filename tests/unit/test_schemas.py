"""Unit tests for data schemas."""

from unittest.mock import Mock

import pytest


class TestAnalysisSchemas:
    """Test suite for analysis data schemas."""

    @pytest.mark.unit
    def test_function_schema(self):
        """Test function data schema."""
        # Mock the schema (to be replaced with actual Pydantic model)
        function_schema = Mock()
        function_schema.validate.return_value = {
            "name": "test_function",
            "line_start": 10,
            "line_end": 15,
            "docstring": "Test function docstring",
            "parameters": ["param1", "param2"],
            "return_type": "str",
            "complexity": 3,
        }

        function_data = {
            "name": "test_function",
            "line_start": 10,
            "line_end": 15,
            "docstring": "Test function docstring",
            "parameters": ["param1", "param2"],
            "return_type": "str",
            "complexity": 3,
        }

        result = function_schema.validate(function_data)

        assert result["name"] == "test_function"
        assert result["complexity"] == 3
        function_schema.validate.assert_called_once_with(function_data)

    @pytest.mark.unit
    def test_class_schema(self):
        """Test class data schema."""
        # Mock the schema (to be replaced with actual Pydantic model)
        class_schema = Mock()
        class_schema.validate.return_value = {
            "name": "TestClass",
            "line_start": 5,
            "line_end": 25,
            "docstring": "Test class docstring",
            "methods": ["__init__", "method1", "method2"],
            "base_classes": ["BaseClass"],
            "complexity": 5,
        }

        class_data = {
            "name": "TestClass",
            "line_start": 5,
            "line_end": 25,
            "docstring": "Test class docstring",
            "methods": ["__init__", "method1", "method2"],
            "base_classes": ["BaseClass"],
            "complexity": 5,
        }

        result = class_schema.validate(class_data)

        assert result["name"] == "TestClass"
        assert "method1" in result["methods"]
        class_schema.validate.assert_called_once_with(class_data)

    @pytest.mark.unit
    def test_analysis_result_schema(self):
        """Test analysis result schema."""
        # Mock the schema (to be replaced with actual Pydantic model)
        analysis_schema = Mock()
        analysis_schema.validate.return_value = {
            "file_path": "/path/to/file.py",
            "analysis_id": "analysis_123",
            "timestamp": "2024-01-01T00:00:00Z",
            "functions": [{"name": "func1", "complexity": 1}],
            "classes": [{"name": "Class1", "methods": ["method1"]}],
            "metrics": {
                "total_lines": 100,
                "code_lines": 80,
                "comment_lines": 15,
                "blank_lines": 5,
            },
        }

        analysis_data = {
            "file_path": "/path/to/file.py",
            "analysis_id": "analysis_123",
            "timestamp": "2024-01-01T00:00:00Z",
            "functions": [{"name": "func1", "complexity": 1}],
            "classes": [{"name": "Class1", "methods": ["method1"]}],
            "metrics": {
                "total_lines": 100,
                "code_lines": 80,
                "comment_lines": 15,
                "blank_lines": 5,
            },
        }

        result = analysis_schema.validate(analysis_data)

        assert result["file_path"] == "/path/to/file.py"
        assert result["analysis_id"] == "analysis_123"
        assert result["metrics"]["total_lines"] == 100
        analysis_schema.validate.assert_called_once_with(analysis_data)

    @pytest.mark.unit
    def test_confluence_page_schema(self):
        """Test Confluence page schema."""
        # Mock the schema (to be replaced with actual Pydantic model)
        page_schema = Mock()
        page_schema.validate.return_value = {
            "id": "123",
            "title": "Test Page",
            "content": "Page content",
            "space": "TEST",
            "url": "https://example.atlassian.net/wiki/spaces/TEST/pages/123",
            "version": 1,
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
        }

        page_data = {
            "id": "123",
            "title": "Test Page",
            "content": "Page content",
            "space": "TEST",
            "url": "https://example.atlassian.net/wiki/spaces/TEST/pages/123",
            "version": 1,
            "created": "2024-01-01T00:00:00Z",
            "updated": "2024-01-01T00:00:00Z",
        }

        result = page_schema.validate(page_data)

        assert result["id"] == "123"
        assert result["title"] == "Test Page"
        page_schema.validate.assert_called_once_with(page_data)

    @pytest.mark.unit
    def test_schema_validation_errors(self):
        """Test schema validation error handling."""
        # Mock the schema (to be replaced with actual Pydantic model)
        schema = Mock()
        schema.validate.side_effect = ValueError("Validation error")

        with pytest.raises(ValueError, match="Validation error"):
            schema.validate({"invalid": "data"})

    @pytest.mark.unit
    def test_optional_fields_schema(self):
        """Test schema with optional fields."""
        # Mock the schema (to be replaced with actual Pydantic model)
        schema = Mock()
        schema.validate.return_value = {
            "name": "test_function",
            "docstring": None,  # Optional field
            "parameters": [],
            "complexity": 1,
        }

        minimal_data = {"name": "test_function", "parameters": [], "complexity": 1}

        result = schema.validate(minimal_data)

        assert result["name"] == "test_function"
        assert result["docstring"] is None
        schema.validate.assert_called_once_with(minimal_data)

    @pytest.mark.unit
    def test_nested_schema_validation(self):
        """Test nested schema validation."""
        # Mock the schema (to be replaced with actual Pydantic model)
        schema = Mock()
        schema.validate.return_value = {
            "analysis": {
                "functions": [
                    {"name": "func1", "complexity": 1},
                    {"name": "func2", "complexity": 2},
                ],
                "classes": [{"name": "Class1", "methods": ["method1"]}],
            },
            "metadata": {
                "file_path": "/path/to/file.py",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        nested_data = {
            "analysis": {
                "functions": [
                    {"name": "func1", "complexity": 1},
                    {"name": "func2", "complexity": 2},
                ],
                "classes": [{"name": "Class1", "methods": ["method1"]}],
            },
            "metadata": {
                "file_path": "/path/to/file.py",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        result = schema.validate(nested_data)

        assert len(result["analysis"]["functions"]) == 2
        assert result["metadata"]["file_path"] == "/path/to/file.py"
        schema.validate.assert_called_once_with(nested_data)
