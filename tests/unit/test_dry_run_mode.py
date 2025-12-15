"""Unit tests for dry-run mode functionality.

Tests verify that:
1. Confluence API clients are not invoked when is_dry_run=True
2. Patch artifacts are still generated in dry-run mode
3. Patches are persisted in the database
4. Run metadata correctly indicates dry-run status
"""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Change, Patch, Rule, Run
from db.session import Base
from services.patches_artifact_exporter import export_patches_artifact
from services.patch_generator import generate_patches_for_run


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database for testing."""
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
def test_session(test_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()

    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_run(test_session):
    """Create a sample run for testing."""
    run = Run(
        repo="test/repo",
        branch="main",
        commit_sha="abc123def456",
        started_at=datetime.now(UTC),
        status="Awaiting Review",
        correlation_id="test-correlation-id",
        is_dry_run=False,  # Default to False
    )
    test_session.add(run)
    test_session.commit()
    test_session.refresh(run)
    return run


@pytest.fixture
def sample_rule(test_session):
    """Create a sample rule for testing."""
    rule = Rule(
        name="test_rule",
        selector="*.py",
        space_key="TEST",
        page_id="12345",
        priority=0,
    )
    test_session.add(rule)
    test_session.commit()
    test_session.refresh(rule)
    return rule


@pytest.fixture
def sample_changes(test_session, sample_run):
    """Create sample changes for testing."""
    changes = [
        Change(
            run_id=sample_run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
            signature_after={"name": "process_request", "params": ["request"]},
        ),
        Change(
            run_id=sample_run.id,
            file_path="src/api.py",
            symbol="handle_error",
            change_type="modified",
            signature_before={"name": "handle_error", "params": ["error"]},
            signature_after={"name": "handle_error", "params": ["error", "context"]},
        ),
    ]
    test_session.add_all(changes)
    test_session.commit()
    return changes


class TestDryRunMode:
    """Test suite for dry-run mode functionality."""

    def test_patch_generation_in_dry_run_mode(
        self, test_session, sample_run, sample_rule, sample_changes
    ):
        """Test that patches are generated in dry-run mode."""
        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, sample_run.id)

        # Verify patches were created
        assert len(patches) == 1
        assert patches[0].run_id == sample_run.id
        assert patches[0].page_id == sample_rule.page_id
        assert patches[0].status == "Proposed"

    def test_patches_persisted_in_dry_run_mode(
        self, test_session, sample_run, sample_rule, sample_changes
    ):
        """Test that patches are persisted in database in dry-run mode."""
        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, sample_run.id)

        # Verify patches are in database
        from sqlalchemy import select

        db_patches = (
            test_session.execute(select(Patch).where(Patch.run_id == sample_run.id))
            .scalars()
            .all()
        )
        assert len(db_patches) == 1
        assert db_patches[0].id == patches[0].id

    @patch("api.routers.patches.ConfluenceClient")
    @patch("api.routers.patches.ConfluencePublisher")
    def test_patch_apply_skips_confluence_in_dry_run_mode(
        self, mock_publisher_class, mock_client_class, test_session, sample_run
    ):
        """Test that Confluence REST calls are skipped when is_dry_run=True."""
        from api.routers.patches import apply_patch

        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Create a patch
        patch_obj = Patch(
            run_id=sample_run.id,
            page_id="12345",
            diff_before="Before content",
            diff_after="After content",
            status="Proposed",
        )
        test_session.add(patch_obj)
        test_session.commit()
        test_session.refresh(patch_obj)

        # Apply patch directly (bypassing FastAPI dependency injection)
        result = apply_patch(patch_obj.id, approved_by="test_user", db=test_session)

        # Verify Confluence client was NOT instantiated
        mock_client_class.assert_not_called()
        mock_publisher_class.assert_not_called()

        # Verify patch status was updated
        assert result.status == "Applied"
        assert result.approved_by == "test_user"
        assert result.applied_at is not None

    @patch("api.routers.patches.ConfluenceClient")
    @patch("api.routers.patches.ConfluencePublisher")
    def test_patch_apply_calls_confluence_in_normal_mode(
        self,
        mock_publisher_class,
        mock_client_class,
        test_session,
        sample_run,
        sample_rule,
    ):
        """Test that Confluence REST calls are made when is_dry_run=False."""
        from api.routers.patches import apply_patch
        from db.models import Connection
        from core.encryption import encrypt_token

        # Ensure run is NOT in dry-run mode
        sample_run.is_dry_run = False
        test_session.commit()

        # Create a Connection object (required for apply_patch)
        connection = Connection(
            confluence_base_url="https://test.atlassian.net",
            space_key="TEST",
            encrypted_token=encrypt_token("test-token"),
        )
        test_session.add(connection)
        test_session.commit()

        # Create a patch
        patch_obj = Patch(
            run_id=sample_run.id,
            page_id=sample_rule.page_id,
            diff_before="Before content",
            diff_after="After content",
            status="Proposed",
        )
        test_session.add(patch_obj)
        test_session.commit()
        test_session.refresh(patch_obj)

        # Mock Confluence client and publisher
        mock_client = Mock()
        mock_client.get_page.return_value = {
            "id": sample_rule.page_id,
            "version": {"number": 1},
        }
        mock_client.update_page.return_value = {
            "id": sample_rule.page_id,
            "version": 2,
        }
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client

        mock_publisher = Mock()
        mock_publisher.update_page.return_value = {
            "id": sample_rule.page_id,
            "version": 2,
        }
        mock_publisher_class.return_value = mock_publisher

        # Apply patch directly (bypassing FastAPI dependency injection)
        result = apply_patch(patch_obj.id, approved_by="test_user", db=test_session)

        # Verify Confluence client was instantiated
        mock_client_class.assert_called_once()
        mock_publisher_class.assert_called_once_with(mock_client)

        # Verify update_page was called on the client (not publisher, as the code calls client.update_page directly)
        mock_client.update_page.assert_called_once()

        # Verify patch status was updated
        assert result.status == "Applied"
        assert result.approved_by == "test_user"
        assert result.applied_at is not None

    def test_patches_artifact_exported_in_dry_run_mode(
        self, test_session, sample_run, sample_rule, sample_changes
    ):
        """Test that patches are exported as JSON artifact in dry-run mode."""
        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, sample_run.id)
        assert len(patches) > 0

        # Export patches artifact
        artifact_path = export_patches_artifact(test_session, sample_run.id)

        # Verify artifact file exists
        assert Path(artifact_path).exists()

        # Verify artifact content
        import json

        with Path(artifact_path).open(encoding="utf-8") as f:
            artifact_data = json.load(f)

        assert artifact_data["run_id"] == sample_run.id
        assert artifact_data["is_dry_run"] is True
        assert artifact_data["patches_count"] == len(patches)
        assert len(artifact_data["patches"]) == len(patches)
        assert artifact_data["patches"][0]["id"] == patches[0].id

    def test_change_report_includes_dry_run_flag(self, test_session, sample_run):
        """Test that change report includes is_dry_run flag."""
        from services.change_report_generator import generate_change_report

        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Generate change report
        report_path = generate_change_report(
            run_id=str(sample_run.id),
            diffs={"test.py": {"added": ["line1"], "removed": [], "modified": []}},
            findings={"test.py": []},
            is_dry_run=True,
        )

        # Verify report content
        import json

        with Path(report_path).open(encoding="utf-8") as f:
            report_data = json.load(f)

        assert report_data["run_id"] == str(sample_run.id)
        assert report_data["is_dry_run"] is True

    def test_run_out_schema_includes_dry_run_flag(self, test_session, sample_run):
        """Test that RunOut schema includes is_dry_run field."""
        from schemas.runs import RunOut

        # Set run to dry-run mode
        sample_run.is_dry_run = True
        test_session.commit()

        # Convert to schema
        run_out = RunOut.model_validate(sample_run)

        # Verify is_dry_run is included
        assert run_out.is_dry_run is True
        assert run_out.display_status == f"{sample_run.status} (Dry Run)"
        assert run_out.run_type_label == "Dry Run"

    def test_run_out_schema_normal_run(self, test_session, sample_run):
        """Test that RunOut schema correctly identifies normal runs."""
        from schemas.runs import RunOut

        # Ensure run is NOT in dry-run mode
        sample_run.is_dry_run = False
        test_session.commit()

        # Convert to schema
        run_out = RunOut.model_validate(sample_run)

        # Verify is_dry_run is False
        assert run_out.is_dry_run is False
        assert run_out.display_status == sample_run.status
        assert run_out.run_type_label == "Normal Run"

    @patch("autodoc.cli.main.SessionLocal")
    @patch("autodoc.cli.main.subprocess.run")
    def test_cli_creates_run_with_dry_run_flag(
        self, mock_subprocess, mock_session_local, test_session
    ):
        """Test that CLI creates run with is_dry_run flag set."""
        from autodoc.cli.main import create_run_from_cli
        from unittest.mock import MagicMock

        # Mock SessionLocal to return our test session
        mock_session_local.return_value = test_session

        # Mock git subprocess calls
        def mock_subprocess_side_effect(*args, **kwargs):
            if "rev-parse" in args[0]:
                # First commit, return non-zero (empty tree)
                result = MagicMock()
                result.returncode = 1
                return result
            if "diff" in args[0]:
                # Return empty list of changed files
                result = MagicMock()
                result.returncode = 0
                result.stdout = ""
                return result
            return MagicMock()

        mock_subprocess.side_effect = mock_subprocess_side_effect

        # Create run via CLI with --dry-run
        run_id = create_run_from_cli(
            commit_sha="abc123",
            repo="test/repo",
            branch="main",
            is_dry_run=True,
        )

        # Verify run exists and has is_dry_run=True
        run = test_session.get(Run, run_id)
        assert run is not None
        assert run.is_dry_run is True
        assert run.repo == "test/repo"
        assert run.commit_sha == "abc123"

    @patch("autodoc.cli.main.SessionLocal")
    @patch("autodoc.cli.main.subprocess.run")
    def test_cli_creates_run_without_dry_run_flag(
        self, mock_subprocess, mock_session_local, test_session
    ):
        """Test that CLI creates run with is_dry_run=False by default."""
        from autodoc.cli.main import create_run_from_cli
        from unittest.mock import MagicMock

        # Mock SessionLocal to return our test session
        mock_session_local.return_value = test_session

        # Mock git subprocess calls
        def mock_subprocess_side_effect(*args, **kwargs):
            if "rev-parse" in args[0]:
                # First commit, return non-zero (empty tree)
                result = MagicMock()
                result.returncode = 1
                return result
            if "diff" in args[0]:
                # Return empty list of changed files
                result = MagicMock()
                result.returncode = 0
                result.stdout = ""
                return result
            return MagicMock()

        mock_subprocess.side_effect = mock_subprocess_side_effect

        # Create run via CLI without --dry-run
        run_id = create_run_from_cli(
            commit_sha="abc123",
            repo="test/repo",
            branch="main",
            is_dry_run=False,
        )

        # Verify run exists and has is_dry_run=False
        run = test_session.get(Run, run_id)
        assert run is not None
        assert run.is_dry_run is False
