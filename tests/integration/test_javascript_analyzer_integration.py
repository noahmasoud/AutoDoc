"""Integration tests for JavaScript analyzer."""

from unittest.mock import Mock, patch

import pytest

from services.javascript_analyzer import JavaScriptAnalyzer


class TestJavaScriptAnalyzerIntegration:
    """Integration tests for JavaScriptAnalyzer."""

    @pytest.mark.integration
    @patch("services.javascript_parser.subprocess.run")
    def test_analyze_no_javascript_files(self, mock_run):
        """Test analyzer with no JavaScript files."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = JavaScriptAnalyzer()

        changed_files = ["README.md", "Makefile", "setup.py"]
        result = analyzer.analyze_changed_files(changed_files, "run_001")

        assert result["files_processed"] == 0
        assert result["files_failed"] == 0
        assert len(result["files"]) == 0

    @pytest.mark.integration
    @patch("services.javascript_parser.subprocess.run")
    def test_analyze_mixed_file_types(self, mock_run):
        """Test analyzer with mixed file types."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = JavaScriptAnalyzer()

        changed_files = [
            "src/app.js",
            "src/styles.css",
            "README.md",
            "tests/test.jsx",
        ]

        # Mock the parser to avoid requiring Node.js
        with patch.object(analyzer.parser, "parse_file") as mock_parse:
            mock_ast = {
                "body": [
                    {
                        "type": "ClassDeclaration",
                        "id": {"name": "TestClass"},
                        "loc": {"start": {"line": 1}},
                        "decorators": [],
                    },
                ],
            }
            mock_parse.return_value = mock_ast

            with patch.object(
                analyzer.parser,
                "extract_public_symbols",
            ) as mock_extract:
                mock_extract.return_value = {
                    "classes": [{"name": "TestClass", "line": 1, "decorators": 0}],
                    "functions": [],
                    "interfaces": [],
                    "types": [],
                    "enums": [],
                }

                result = analyzer.analyze_changed_files(changed_files, "run_002")

                # Should only process .js and .jsx files
                assert result["files_processed"] == 2  # app.js and test.jsx
                assert len(result["files"]) == 2

    @pytest.mark.integration
    @patch("services.javascript_parser.subprocess.run")
    def test_analyze_with_parse_error(self, mock_run):
        """Test analyzer handles parse errors gracefully."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = JavaScriptAnalyzer()

        changed_files = ["src/app.js"]

        # Mock parser to raise ParseError
        with patch.object(analyzer.parser, "parse_file") as mock_parse:
            from services.javascript_parser import ParseError

            mock_parse.side_effect = ParseError("Syntax error")

            result = analyzer.analyze_changed_files(changed_files, "run_003")

            assert result["files_processed"] == 0
            assert result["files_failed"] == 1
            assert result["files"][0]["status"] == "failed"
            assert "error" in result["files"][0]

