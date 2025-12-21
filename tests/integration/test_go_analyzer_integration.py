"""Integration tests for Go analyzer."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services.go_analyzer import GoAnalyzer


class TestGoAnalyzerIntegration:
    """Integration tests for GoAnalyzer."""

    @pytest.mark.integration
    @patch("services.go_parser.subprocess.run")
    def test_analyze_no_go_files(self, mock_run):
        """Test analyzer with no Go files."""
        # Mock Go check
        mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")

        with patch.object(Path, "exists", return_value=True):
            analyzer = GoAnalyzer()

            changed_files = ["README.md", "Makefile", "setup.py"]
            result = analyzer.analyze_changed_files(changed_files, "run_001")

            assert result["files_processed"] == 0
            assert result["files_failed"] == 0
            assert len(result["files"]) == 0

    @pytest.mark.integration
    @patch("services.go_parser.subprocess.run")
    def test_analyze_mixed_file_types(self, mock_run):
        """Test analyzer with mixed file types."""
        # Mock Go check
        mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")

        with patch.object(Path, "exists", return_value=True):
            analyzer = GoAnalyzer()

            changed_files = [
                "src/main.go",
                "src/utils.go",
                "README.md",
                "tests/test.go",
            ]

            # Mock the parser to avoid requiring Go compiler
            with patch.object(analyzer.parser, "parse_file") as mock_parse:
                mock_ast = {
                    "package": "main",
                    "body": [
                        {
                            "type": "FunctionDeclaration",
                            "name": "main",
                            "line": 1,
                        },
                    ],
                }
                mock_parse.return_value = mock_ast

                with patch.object(
                    analyzer.parser,
                    "extract_public_symbols",
                ) as mock_extract:
                    mock_extract.return_value = {
                        "functions": [{"name": "main", "line": 1}],
                        "types": [],
                        "interfaces": [],
                        "structs": [],
                        "consts": [],
                        "vars": [],
                    }

                    result = analyzer.analyze_changed_files(changed_files, "run_002")

                    # Should only process .go files
                    assert result["files_processed"] == 3  # main.go, utils.go, test.go
                    assert len(result["files"]) == 3

    @pytest.mark.integration
    @patch("services.go_parser.subprocess.run")
    def test_analyze_with_parse_error(self, mock_run):
        """Test analyzer handles parse errors gracefully."""
        # Mock Go check
        mock_run.return_value = Mock(returncode=0, stdout="go version go1.21.0\n")

        with patch.object(Path, "exists", return_value=True):
            analyzer = GoAnalyzer()

            changed_files = ["src/main.go"]

            # Mock parser to raise ParseError
            with patch.object(analyzer.parser, "parse_file") as mock_parse:
                from services.go_parser import ParseError

                mock_parse.side_effect = ParseError("Syntax error")

                result = analyzer.analyze_changed_files(changed_files, "run_003")

                assert result["files_processed"] == 0
                assert result["files_failed"] == 1
                assert result["files"][0]["status"] == "failed"
                assert "error" in result["files"][0]

