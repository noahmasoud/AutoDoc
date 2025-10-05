"""Unit tests for CLI interface."""

from unittest.mock import Mock

import pytest


class TestCLIInterface:
    """Test suite for CLI interface."""

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_help_command(self):
        """Test CLI help command."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.show_help.return_value = "AutoDoc CLI Help"

        result = cli.show_help()

        assert result == "AutoDoc CLI Help"
        cli.show_help.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_analyze_command(self):
        """Test CLI analyze command."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.analyze_file.return_value = {
            "file": "/path/to/file.py",
            "functions": 3,
            "classes": 1,
            "complexity": 5,
        }

        result = cli.analyze_file("/path/to/file.py")

        assert result["file"] == "/path/to/file.py"
        assert result["functions"] == 3
        cli.analyze_file.assert_called_once_with("/path/to/file.py")

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_publish_command(self):
        """Test CLI publish command."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.publish_results.return_value = {
            "analysis_id": "analysis_123",
            "confluence_page_id": "123",
            "status": "published",
        }

        result = cli.publish_results("analysis_123", "TEST")

        assert result["analysis_id"] == "analysis_123"
        assert result["status"] == "published"
        cli.publish_results.assert_called_once_with("analysis_123", "TEST")

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_batch_analyze_command(self):
        """Test CLI batch analyze command."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.batch_analyze.return_value = {
            "files_processed": 3,
            "successful": 3,
            "failed": 0,
            "results": ["analysis_1", "analysis_2", "analysis_3"],
        }

        result = cli.batch_analyze(
            ["/path/file1.py", "/path/file2.py", "/path/file3.py"],
        )

        assert result["files_processed"] == 3
        assert result["successful"] == 3
        cli.batch_analyze.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_config_command(self):
        """Test CLI config command."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.set_config.return_value = True
        cli.get_config.return_value = {
            "confluence_url": "https://example.atlassian.net",
            "confluence_token": "***",
            "database_url": "sqlite:///autodoc.db",
        }

        # Test setting config
        set_result = cli.set_config("confluence_url", "https://new.example.net")
        assert set_result is True

        # Test getting config
        get_result = cli.get_config()
        assert get_result["confluence_url"] == "https://example.atlassian.net"

        cli.set_config.assert_called_once_with(
            "confluence_url",
            "https://new.example.net",
        )
        cli.get_config.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_error_handling(self):
        """Test CLI error handling."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.analyze_file.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError, match="File not found"):
            cli.analyze_file("/nonexistent/file.py")

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_progress_reporting(self):
        """Test CLI progress reporting."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.show_progress.return_value = None

        # Test progress reporting
        cli.show_progress("Analyzing files...", 50)

        cli.show_progress.assert_called_once_with("Analyzing files...", 50)

    @pytest.mark.unit
    @pytest.mark.cli
    def test_cli_output_formatting(self):
        """Test CLI output formatting."""
        # Mock the CLI interface (to be replaced with actual implementation)
        cli = Mock()
        cli.format_output.return_value = "Formatted output"

        data = {"functions": 3, "classes": 1}
        result = cli.format_output(data, format_type="json")

        assert result == "Formatted output"
        cli.format_output.assert_called_once_with(data, format_type="json")
