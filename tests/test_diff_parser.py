"""Tests for diff parser module."""

import pytest
from fastapi.testclient import TestClient

from api.routers.diff_parser import parse_diff
from api.main import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestParseDiffHelper:
    """Test the parse_diff helper function."""

    @pytest.mark.unit
    def test_parse_diff_one_added_line(self):
        """Test parsing diff with one added line."""
        old_code = "line1\nline2"
        new_code = "line1\nline2\nline3"

        result = parse_diff(old_code, new_code)

        assert result["added"] == ["line3"]
        assert result["removed"] == []
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_one_removed_line(self):
        """Test parsing diff with one removed line."""
        old_code = "line1\nline2\nline3"
        new_code = "line1\nline2"

        result = parse_diff(old_code, new_code)

        assert result["added"] == []
        assert result["removed"] == ["line3"]
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_one_changed_line(self):
        """Test parsing diff with one changed line."""
        old_code = "line1\nline2\nline3"
        new_code = "line1\nline2_modified\nline3"

        result = parse_diff(old_code, new_code)

        assert result["added"] == []
        assert result["removed"] == []
        assert len(result["modified"]) == 1
        assert result["modified"][0]["old"] == "line2"
        assert result["modified"][0]["new"] == "line2_modified"
        assert result["modified"][0]["line"] == 2  # Line numbers are 1-indexed in diff

    @pytest.mark.unit
    def test_parse_diff_empty_old_file(self):
        """Test parsing diff with empty old file."""
        old_code = ""
        new_code = "line1\nline2"

        result = parse_diff(old_code, new_code)

        assert result["added"] == ["line1", "line2"]
        assert result["removed"] == []
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_empty_new_file(self):
        """Test parsing diff with empty new file."""
        old_code = "line1\nline2"
        new_code = ""

        result = parse_diff(old_code, new_code)

        assert result["added"] == []
        assert result["removed"] == ["line1", "line2"]
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_identical_files(self):
        """Test parsing diff with identical files."""
        old_code = "line1\nline2"
        new_code = "line1\nline2"

        result = parse_diff(old_code, new_code)

        assert result["added"] == []
        assert result["removed"] == []
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_both_empty(self):
        """Test parsing diff with both files empty."""
        old_code = ""
        new_code = ""

        result = parse_diff(old_code, new_code)

        assert result["added"] == []
        assert result["removed"] == []
        assert result["modified"] == []

    @pytest.mark.unit
    def test_parse_diff_multiple_changes(self):
        """Test parsing diff with multiple types of changes."""
        old_code = "line1\nline2\nline3\nline4"
        new_code = "line1\nline2_modified\nline5\nline4"

        result = parse_diff(old_code, new_code)

        assert "line2_modified" in result["added"] or any(
            m["new"] == "line2_modified" for m in result["modified"]
        )
        # Either line3 is removed or line5 is added
        assert "line3" in result["removed"] or "line5" in result["added"]


class TestDiffParserEndpoint:
    """Test the /api/diff/parse endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_one_added_line(self, client):
        """Test endpoint with one added line."""
        response = client.post(
            "/api/diff/parse",
            json={"old_file": "line1\nline2", "new_file": "line1\nline2\nline3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == ["line3"]
        assert data["removed"] == []
        assert data["modified"] == []

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_one_removed_line(self, client):
        """Test endpoint with one removed line."""
        response = client.post(
            "/api/diff/parse",
            json={"old_file": "line1\nline2\nline3", "new_file": "line1\nline2"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == []
        assert data["removed"] == ["line3"]
        assert data["modified"] == []

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_one_changed_line(self, client):
        """Test endpoint with one changed line."""
        response = client.post(
            "/api/diff/parse",
            json={"old_file": "line1\nline2\nline3", "new_file": "line1\nline2_modified\nline3"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == []
        assert data["removed"] == []
        assert len(data["modified"]) == 1
        assert data["modified"][0]["old"] == "line2"
        assert data["modified"][0]["new"] == "line2_modified"

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_identical_files(self, client):
        """Test endpoint with identical files."""
        response = client.post(
            "/api/diff/parse",
            json={"old_file": "line1\nline2", "new_file": "line1\nline2"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == []
        assert data["removed"] == []
        assert data["modified"] == []

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_empty_files(self, client):
        """Test endpoint with empty files."""
        response = client.post(
            "/api/diff/parse",
            json={"old_file": "", "new_file": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["added"] == []
        assert data["removed"] == []
        assert data["modified"] == []

