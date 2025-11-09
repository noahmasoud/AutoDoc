"""Tests for change report generator module."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.change_report_generator import generate_change_report
from api.main import create_app


class TestChangeReportGenerator:
    """Test the generate_change_report function."""

    @pytest.mark.unit
    def test_generate_change_report_creates_file(self, tmp_path, monkeypatch):
        """Test that the function creates the change report JSON file."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = "test-run-123"
        diffs = {"added": ["line1"], "removed": [], "modified": []}
        findings = {"issues": [], "warnings": []}

        report_path = generate_change_report(run_id, diffs, findings)

        # Verify file exists
        assert Path(report_path).exists()
        assert Path(report_path).name == "change_report.json"

    @pytest.mark.unit
    def test_generate_change_report_json_keys(self, tmp_path, monkeypatch):
        """Test that the generated JSON contains all required keys."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = "test-run-456"
        diffs = {"added": ["line1"], "removed": ["line2"], "modified": []}
        findings = {"issues": ["issue1"], "warnings": ["warning1"]}

        report_path = generate_change_report(run_id, diffs, findings)

        # Read and parse JSON
        with Path(report_path).open("r", encoding="utf-8") as f:
            report = json.load(f)

        # Verify all required keys exist
        assert "run_id" in report
        assert "timestamp" in report
        assert "diff_summary" in report
        assert "analyzer_findings" in report

        # Verify values
        assert report["run_id"] == run_id
        assert report["diff_summary"] == diffs
        assert report["analyzer_findings"] == findings

    @pytest.mark.unit
    def test_generate_change_report_timestamp_format(self, tmp_path, monkeypatch):
        """Test that the timestamp is in valid ISO format."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = "test-run-789"
        diffs = {}
        findings = {}

        report_path = generate_change_report(run_id, diffs, findings)

        # Read and parse JSON
        with Path(report_path).open("r", encoding="utf-8") as f:
            report = json.load(f)

        # Verify timestamp is valid ISO format
        timestamp_str = report["timestamp"]
        try:
            # Parse ISO format timestamp (handle both Z and +00:00 formats)
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str.replace("Z", "+00:00")
            # datetime.fromisoformat() can parse ISO 8601 format
            parsed_timestamp = datetime.fromisoformat(timestamp_str)
            # Verify it's a valid datetime object
            assert isinstance(parsed_timestamp, datetime)
        except (ValueError, AttributeError) as e:
            pytest.fail(f"Timestamp is not in valid ISO format: {timestamp_str}. Error: {e}")

    @pytest.mark.unit
    def test_generate_change_report_creates_directory(self, tmp_path, monkeypatch):
        """Test that the function creates the artifacts directory if it doesn't exist."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = "test-run-dir"
        diffs = {}
        findings = {}

        # Verify artifacts directory doesn't exist initially
        artifacts_dir = tmp_path / "artifacts" / run_id
        assert not artifacts_dir.exists()

        report_path = generate_change_report(run_id, diffs, findings)

        # Verify directory was created
        assert artifacts_dir.exists()
        assert artifacts_dir.is_dir()

    @pytest.mark.unit
    def test_generate_change_report_handles_existing_directory(self, tmp_path, monkeypatch):
        """Test that the function works when the directory already exists."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = "test-run-existing"
        diffs = {}
        findings = {}

        # Create the directory beforehand
        artifacts_dir = tmp_path / "artifacts" / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Should not raise an error
        report_path = generate_change_report(run_id, diffs, findings)

        # Verify file was created
        assert Path(report_path).exists()


class TestChangeReportEndpoint:
    """Test the /api/runs/{run_id}/report endpoint."""

    @pytest.fixture
    def test_engine(self):
        """Create an in-memory SQLite database for testing."""
        from sqlalchemy import create_engine, event
        from db.session import Base
        from db.models import Run

        engine = create_engine("sqlite:///:memory:")

        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def enable_sqlite_fks(dbapi_con, connection_record):
            cursor = dbapi_con.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(engine)
        yield engine
        Base.metadata.drop_all(engine)

    @pytest.fixture
    def test_session(self, test_engine):
        """Create a test database session."""
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=test_engine)
        session = Session()
        yield session
        session.rollback()
        session.close()

    @pytest.fixture
    def sample_run(self, test_session):
        """Create a sample run for testing."""
        from db.models import Run
        from datetime import datetime, UTC

        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.now(UTC),
            status="Awaiting Review",
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()
        test_session.refresh(run)
        return run

    @pytest.fixture
    def client(self, test_session):
        """Create a test client for the FastAPI app with test database."""
        from unittest.mock import patch
        from db.session import get_db

        app = create_app()

        # Override get_db dependency to use test session
        def override_get_db():
            yield test_session

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

        app.dependency_overrides.clear()

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_generates_report(self, client, sample_run, tmp_path, monkeypatch):
        """Test that the endpoint generates a change report."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = sample_run.id
        payload = {
            "diffs": {"added": ["line1"], "removed": [], "modified": []},
            "findings": {"issues": [], "warnings": []},
        }

        response = client.post(
            f"/api/v1/runs/{run_id}/report",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert "report_path" in data
        assert Path(data["report_path"]).exists()

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_returns_valid_json_path(self, client, sample_run, tmp_path, monkeypatch):
        """Test that the endpoint returns a valid JSON file path."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = sample_run.id
        payload = {
            "diffs": {"added": ["line1"]},
            "findings": {"issues": []},
        }

        response = client.post(
            f"/api/v1/runs/{run_id}/report",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        report_path = Path(data["report_path"])

        # Verify file exists and is valid JSON
        assert report_path.exists()
        with report_path.open("r", encoding="utf-8") as f:
            report = json.load(f)
            assert "run_id" in report
            assert "timestamp" in report

    @pytest.mark.unit
    @pytest.mark.api
    def test_endpoint_returns_404_for_nonexistent_run(self, client, tmp_path, monkeypatch):
        """Test that the endpoint returns 404 for a non-existent run."""
        # Change to temporary directory
        monkeypatch.chdir(tmp_path)

        run_id = 99999  # Non-existent run ID
        payload = {
            "diffs": {},
            "findings": {},
        }

        response = client.post(
            f"/api/v1/runs/{run_id}/report",
            json=payload,
        )

        assert response.status_code == 404

