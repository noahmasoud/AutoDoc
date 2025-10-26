"""Integration tests for TypeScript analyzer."""

from unittest.mock import Mock, patch

import pytest

from services.typescript_analyzer import TypeScriptAnalyzer


class TestTypeScriptAnalyzerIntegration:
    """Integration tests for TypeScriptAnalyzer."""

    @pytest.mark.integration
    @patch("services.typescript_parser.subprocess.run")
    def test_analyze_no_typescript_files(self, mock_run):
        """Test analyzer with no TypeScript files."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = TypeScriptAnalyzer()

        changed_files = ["README.md", "Makefile", "setup.py"]
        result = analyzer.analyze_changed_files(changed_files, "run_001")

        assert result["files_processed"] == 0
        assert result["files_failed"] == 0
        assert len(result["files"]) == 0

    @pytest.mark.integration
    @patch("services.typescript_parser.subprocess.run")
    def test_analyze_mixed_file_types(self, mock_run):
        """Test analyzer with mixed file types."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = TypeScriptAnalyzer()

        changed_files = [
            "src/app.ts",
            "src/styles.css",
            "README.md",
            "tests/test.ts",
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

                # Should only process .ts files
                assert result["files_processed"] == 2  # app.ts and test.ts
                assert len(result["files"]) == 2

    @pytest.mark.integration
    @patch("services.typescript_parser.subprocess.run")
    def test_analyze_with_parse_error(self, mock_run):
        """Test analyzer handles parse errors gracefully."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = TypeScriptAnalyzer()

        changed_files = ["src/app.ts"]

        # Mock parser to raise ParseError
        with patch.object(analyzer.parser, "parse_file") as mock_parse:
            from services.typescript_parser import ParseError

            mock_parse.side_effect = ParseError("Syntax error")

            result = analyzer.analyze_changed_files(changed_files, "run_003")

            assert result["files_processed"] == 0
            assert result["files_failed"] == 1
            assert result["files"][0]["status"] == "failed"
            assert "error" in result["files"][0]

    @pytest.mark.integration
    @patch("services.typescript_parser.subprocess.run")
    def test_analyze_extracts_symbols(self, mock_run):
        """Test analyzer extracts symbols correctly."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = TypeScriptAnalyzer()

        changed_files = ["src/service.ts"]

        with patch.object(analyzer.parser, "parse_file") as mock_parse:
            mock_parse.return_value = {"body": []}

            with patch.object(
                analyzer.parser,
                "extract_public_symbols",
            ) as mock_extract:
                mock_extract.return_value = {
                    "classes": [
                        {"name": "ServiceClass", "line": 1, "decorators": 0},
                    ],
                    "functions": [
                        {"name": "getData", "line": 10, "async": True},
                    ],
                    "interfaces": [
                        {"name": "IData", "line": 5},
                    ],
                    "types": [],
                    "enums": [
                        {"name": "Status", "line": 20},
                    ],
                }

                result = analyzer.analyze_changed_files(changed_files, "run_004")

                assert result["files_processed"] == 1
                assert result["symbols_extracted"]["classes"] == 1
                assert result["symbols_extracted"]["functions"] == 1
                assert result["symbols_extracted"]["interfaces"] == 1
                assert result["symbols_extracted"]["enums"] == 1

    @pytest.mark.integration
    @patch("services.typescript_parser.subprocess.run")
    def test_is_typescript_file(self, mock_run):
        """Test TypeScript file detection."""
        # Mock Node.js check
        mock_run.return_value = Mock(returncode=0, stdout="v18.0.0\n")

        analyzer = TypeScriptAnalyzer()

        # Test file filtering by checking results
        ts_files = ["file.ts", "file.tsx", "file.js", "file.py", "file.TS"]
        result = analyzer.analyze_changed_files(ts_files, "run_006")
        # Should process 3 TypeScript files (.ts, .tsx, .TS)
        assert result["files_processed"] == 0  # Mock parser won't parse
        assert len(result["files"]) == 3  # Only TS files processed
