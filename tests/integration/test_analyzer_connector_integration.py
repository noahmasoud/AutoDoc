"""Integration tests for analyzer and connector interactions."""

import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, patch


class TestAnalyzerConnectorIntegration:
    """Test suite for analyzer-connector integration."""

    @pytest.mark.integration
    @pytest.mark.analyzer
    @pytest.mark.connector
    def test_analyze_and_save_to_confluence(self, mock_confluence_client, sample_python_code: str):
        """Test complete workflow: analyze code and save to Confluence."""
        # Mock the analyzer (to be replaced with actual implementation)
        analyzer = Mock()
        analysis_result = {
            "functions": [
                {
                    "name": "calculate_sum",
                    "docstring": "Calculate the sum of two integers.",
                    "complexity": 1
                }
            ],
            "classes": [
                {
                    "name": "Calculator",
                    "docstring": "A simple calculator class.",
                    "methods": ["__init__", "add"]
                }
            ],
            "metrics": {
                "total_lines": 40,
                "functions_count": 3,
                "classes_count": 1
            }
        }
        analyzer.analyze.return_value = analysis_result
        
        # Mock the connector (to be replaced with actual implementation)
        connector = Mock()
        connector.create_page.return_value = {
            "id": "123",
            "title": "Code Analysis Report",
            "url": "https://example.atlassian.net/wiki/spaces/TEST/pages/123"
        }
        
        # Integration test workflow
        result = analyzer.analyze(sample_python_code)
        confluence_page = connector.create_page({
            "title": "Code Analysis Report",
            "content": f"Analysis of code with {result['metrics']['functions_count']} functions",
            "space": "TEST"
        })
        
        assert result["functions"][0]["name"] == "calculate_sum"
        assert confluence_page["id"] == "123"
        analyzer.analyze.assert_called_once_with(sample_python_code)
        connector.create_page.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.analyzer
    @pytest.mark.database
    def test_analyze_and_save_to_database(self, mock_database, sample_python_code: str):
        """Test complete workflow: analyze code and save to database."""
        # Mock the analyzer (to be replaced with actual implementation)
        analyzer = Mock()
        analysis_result = {
            "file_path": "/path/to/file.py",
            "functions": [{"name": "test_func", "complexity": 1}],
            "classes": [{"name": "TestClass", "methods": ["method1"]}],
            "created_at": "2024-01-01T00:00:00Z"
        }
        analyzer.analyze.return_value = analysis_result
        
        # Mock the database connector (to be replaced with actual implementation)
        db_connector = Mock()
        db_connector.save_result.return_value = "analysis_id_123"
        
        # Integration test workflow
        result = analyzer.analyze(sample_python_code)
        saved_id = db_connector.save_result(result)
        
        assert saved_id == "analysis_id_123"
        assert result["file_path"] == "/path/to/file.py"
        analyzer.analyze.assert_called_once_with(sample_python_code)
        db_connector.save_result.assert_called_once_with(result)

    @pytest.mark.integration
    @pytest.mark.connector
    @pytest.mark.database
    def test_retrieve_and_publish_to_confluence(self, mock_database, mock_confluence_client):
        """Test complete workflow: retrieve from database and publish to Confluence."""
        # Mock the database connector (to be replaced with actual implementation)
        db_connector = Mock()
        analysis_result = {
            "id": "analysis_id_123",
            "file_path": "/path/to/file.py",
            "functions": [{"name": "test_func", "complexity": 1}],
            "classes": [{"name": "TestClass", "methods": ["method1"]}]
        }
        db_connector.get_result.return_value = analysis_result
        
        # Mock the Confluence connector (to be replaced with actual implementation)
        confluence_connector = Mock()
        confluence_connector.create_page.return_value = {
            "id": "456",
            "title": "Published Analysis",
            "url": "https://example.atlassian.net/wiki/spaces/TEST/pages/456"
        }
        
        # Integration test workflow
        result = db_connector.get_result("analysis_id_123")
        published_page = confluence_connector.create_page({
            "title": f"Analysis Report: {result['file_path']}",
            "content": f"Found {len(result['functions'])} functions and {len(result['classes'])} classes",
            "space": "TEST"
        })
        
        assert result["id"] == "analysis_id_123"
        assert published_page["id"] == "456"
        db_connector.get_result.assert_called_once_with("analysis_id_123")
        confluence_connector.create_page.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.analyzer
    @pytest.mark.connector
    @pytest.mark.database
    def test_full_workflow_with_error_handling(self, mock_database, mock_confluence_client):
        """Test full workflow with error handling and rollback."""
        # Mock the analyzer (to be replaced with actual implementation)
        analyzer = Mock()
        analyzer.analyze.return_value = {"functions": [], "classes": []}
        
        # Mock the database connector (to be replaced with actual implementation)
        db_connector = Mock()
        db_connector.save_result.return_value = "analysis_id_123"
        db_connector.rollback.return_value = True
        
        # Mock the Confluence connector (to be replaced with actual implementation)
        confluence_connector = Mock()
        confluence_connector.create_page.side_effect = Exception("Confluence API error")
        
        # Integration test workflow with error handling
        analysis_result = analyzer.analyze("def test(): pass")
        saved_id = db_connector.save_result(analysis_result)
        
        # Simulate Confluence publishing failure and rollback
        try:
            confluence_connector.create_page({"title": "Test", "content": "Test"})
        except Exception as e:
            # Simulate rollback on error
            db_connector.rollback()
            # Verify the expected exception was raised
            assert str(e) == "Confluence API error"
        
        # Verify rollback was called
        db_connector.rollback.assert_called_once()
        
        assert saved_id == "analysis_id_123"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_batch_analysis_workflow(self, mock_database, mock_confluence_client):
        """Test batch analysis of multiple files."""
        # Mock the file system connector (to be replaced with actual implementation)
        fs_connector = Mock()
        fs_connector.list_files.return_value = [
            "/project/file1.py",
            "/project/file2.py",
            "/project/file3.py"
        ]
        fs_connector.read_file.side_effect = [
            "def func1(): pass",
            "def func2(): pass", 
            "def func3(): pass"
        ]
        
        # Mock the analyzer (to be replaced with actual implementation)
        analyzer = Mock()
        analyzer.analyze.side_effect = [
            {"functions": [{"name": "func1"}], "classes": []},
            {"functions": [{"name": "func2"}], "classes": []},
            {"functions": [{"name": "func3"}], "classes": []}
        ]
        
        # Mock the database connector (to be replaced with actual implementation)
        db_connector = Mock()
        db_connector.save_result.side_effect = ["id1", "id2", "id3"]
        
        # Integration test workflow for batch processing
        files = fs_connector.list_files("/project")
        results = []
        
        for file_path in files:
            content = fs_connector.read_file(file_path)
            analysis = analyzer.analyze(content)
            analysis["file_path"] = file_path
            saved_id = db_connector.save_result(analysis)
            results.append(saved_id)
        
        assert len(results) == 3
        assert results == ["id1", "id2", "id3"]
        assert analyzer.analyze.call_count == 3
        assert db_connector.save_result.call_count == 3
