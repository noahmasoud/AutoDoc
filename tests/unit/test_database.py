"""
Unit tests for database schema, models, and retention policy.

Tests per NFR-11: table creation, FK cascades, constraints, JSON fields, retention.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect, select, event, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from db.session import Base
from db.models import Run, Change, Rule, Template, Patch
from db.retention import (
    cleanup_old_runs,
    get_run_count,
    get_oldest_run_id,
    get_newest_run_id,
)


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


class TestSchemaCreation:
    """Test database schema creation and structure."""

    def test_all_tables_created(self, test_engine):
        """Test that all required tables are created."""
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()

        assert "runs" in tables
        assert "changes" in tables
        assert "rules" in tables
        assert "templates" in tables
        assert "patches" in tables

    def test_run_table_columns(self, test_engine):
        """Test Run table has all required columns."""
        inspector = inspect(test_engine)
        columns = {col["name"] for col in inspector.get_columns("runs")}

        required_columns = {
            "id",
            "repo",
            "branch",
            "commit_sha",
            "started_at",
            "completed_at",
            "status",
            "correlation_id",
        }
        assert required_columns.issubset(columns)

    def test_change_table_columns(self, test_engine):
        """Test Change table has all required columns."""
        inspector = inspect(test_engine)
        columns = {col["name"] for col in inspector.get_columns("changes")}

        required_columns = {
            "id",
            "run_id",
            "file_path",
            "symbol",
            "change_type",
            "signature_before",
            "signature_after",
        }
        assert required_columns.issubset(columns)

    def test_indexes_created(self, test_engine):
        """Test that required indexes are created."""
        inspector = inspect(test_engine)

        # Check run indexes
        run_indexes = {idx["name"] for idx in inspector.get_indexes("runs")}
        assert "ix_runs_commit_sha" in run_indexes

        # Check change indexes
        change_indexes = {idx["name"] for idx in inspector.get_indexes("changes")}
        assert "ix_changes_run_id" in change_indexes

        # Check patch indexes
        patch_indexes = {idx["name"] for idx in inspector.get_indexes("patches")}
        assert "ix_patches_run_id" in patch_indexes

        # Check rule indexes
        rule_indexes = {idx["name"] for idx in inspector.get_indexes("rules")}
        assert "ix_rules_name" in rule_indexes

        # Check template indexes
        template_indexes = {idx["name"] for idx in inspector.get_indexes("templates")}
        assert "ix_templates_name" in template_indexes

    def test_foreign_keys_created(self, test_engine):
        """Test that foreign key constraints are created."""
        inspector = inspect(test_engine)

        # Check Change foreign keys
        change_fks = inspector.get_foreign_keys("changes")
        assert len(change_fks) > 0
        assert change_fks[0]["referred_table"] == "runs"
        assert change_fks[0]["options"]["ondelete"] == "CASCADE"

        # Check Patch foreign keys
        patch_fks = inspector.get_foreign_keys("patches")
        assert len(patch_fks) > 0
        assert patch_fks[0]["referred_table"] == "runs"
        assert patch_fks[0]["options"]["ondelete"] == "CASCADE"

        # Check Rule foreign keys
        rule_fks = inspector.get_foreign_keys("rules")
        assert len(rule_fks) > 0
        assert rule_fks[0]["referred_table"] == "templates"


class TestConstraints:
    """Test database constraints and validations."""

    def test_run_status_constraint(self, test_session):
        """Test Run status check constraint."""
        valid_statuses = [
            "Awaiting Review",
            "Success",
            "Failed",
            "Manual Action Required",
            "Completed (no patches)",
        ]

        for status in valid_statuses:
            run = Run(
                repo="test/repo",
                branch="main",
                commit_sha="abc123",
                started_at=datetime.utcnow(),
                status=status,
                correlation_id="test-id",
            )
            test_session.add(run)
            test_session.commit()
            test_session.delete(run)
            test_session.commit()

    def test_change_type_constraint(self, test_session):
        """Test Change change_type check constraint."""
        # First create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="test-id",
        )
        test_session.add(run)
        test_session.commit()

        valid_types = ["added", "removed", "modified"]

        for change_type in valid_types:
            change = Change(
                run_id=run.id,
                file_path="test.py",
                symbol="test_func",
                change_type=change_type,
            )
            test_session.add(change)
            test_session.commit()
            test_session.delete(change)
            test_session.commit()

    def test_template_format_constraint(self, test_session):
        """Test Template format check constraint."""
        valid_formats = ["Markdown", "Storage"]

        for format_type in valid_formats:
            template = Template(
                name=f"test_template_{format_type}",
                format=format_type,
                body="Test body",
            )
            test_session.add(template)
            test_session.commit()
            test_session.delete(template)
            test_session.commit()

    def test_patch_status_constraint(self, test_session):
        """Test Patch status check constraint."""
        # First create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="test-id",
        )
        test_session.add(run)
        test_session.commit()

        valid_statuses = [
            "Proposed",
            "Approved",
            "Rejected",
            "Applied",
            "RolledBack",
        ]

        for status in valid_statuses:
            patch = Patch(
                run_id=run.id,
                page_id="page-123",
                diff_before="before",
                diff_after="after",
                status=status,
            )
            test_session.add(patch)
            test_session.commit()
            test_session.delete(patch)
            test_session.commit()

    def test_unique_constraints(self, test_session):
        """Test unique constraints on name fields."""
        # Test Rule name uniqueness
        rule1 = Rule(
            name="test_rule",
            selector="selector",
            space_key="SPACE",
            page_id="page-1",
            auto_approve=False,
        )
        test_session.add(rule1)
        test_session.commit()

        rule2 = Rule(
            name="test_rule",  # Duplicate name
            selector="selector2",
            space_key="SPACE",
            page_id="page-2",
            auto_approve=False,
        )
        test_session.add(rule2)

        with pytest.raises(IntegrityError):
            test_session.commit()

        test_session.rollback()

        # Test Template name uniqueness
        template1 = Template(
            name="test_template",
            format="Markdown",
            body="body",
        )
        test_session.add(template1)
        test_session.commit()

        template2 = Template(
            name="test_template",  # Duplicate name
            format="Storage",
            body="body2",
        )
        test_session.add(template2)

        with pytest.raises(IntegrityError):
            test_session.commit()


class TestCascadeDeletes:
    """Test CASCADE delete behavior per SRS requirements."""

    def test_run_delete_cascades_to_changes(self, test_session):
        """Test that deleting a Run cascades to Changes."""
        # Create run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="test-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create changes
        change1 = Change(
            run_id=run.id,
            file_path="test1.py",
            symbol="func1",
            change_type="added",
        )
        change2 = Change(
            run_id=run.id,
            file_path="test2.py",
            symbol="func2",
            change_type="modified",
        )
        test_session.add_all([change1, change2])
        test_session.commit()

        # Verify changes exist
        change_count = test_session.scalar(
            select(func.count()).select_from(Change),
        )
        assert change_count == 2

        # Delete run
        test_session.delete(run)
        test_session.commit()

        # Verify changes were cascaded
        change_count = test_session.scalar(
            select(func.count()).select_from(Change),
        )
        assert change_count == 0

    def test_run_delete_cascades_to_patches(self, test_session):
        """Test that deleting a Run cascades to Patches."""
        # Create run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="test-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create patches
        patch1 = Patch(
            run_id=run.id,
            page_id="page-1",
            diff_before="before1",
            diff_after="after1",
            status="Proposed",
        )
        patch2 = Patch(
            run_id=run.id,
            page_id="page-2",
            diff_before="before2",
            diff_after="after2",
            status="Approved",
        )
        test_session.add_all([patch1, patch2])
        test_session.commit()

        # Verify patches exist
        from sqlalchemy import func

        patch_count = test_session.scalar(
            select(func.count()).select_from(Patch),
        )
        assert patch_count == 2

        # Delete run
        test_session.delete(run)
        test_session.commit()

        # Verify patches were cascaded
        patch_count = test_session.scalar(
            select(func.count()).select_from(Patch),
        )
        assert patch_count == 0


class TestJSONFields:
    """Test JSON field functionality."""

    def test_change_signature_json_fields(self, test_session):
        """Test Change signature_before and signature_after JSON fields."""
        # Create run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="test-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create change with JSON data
        sig_before = {
            "name": "my_function",
            "params": ["arg1", "arg2"],
            "return_type": "str",
        }
        sig_after = {
            "name": "my_function",
            "params": ["arg1", "arg2", "arg3"],
            "return_type": "int",
        }

        change = Change(
            run_id=run.id,
            file_path="test.py",
            symbol="my_function",
            change_type="modified",
            signature_before=sig_before,
            signature_after=sig_after,
        )
        test_session.add(change)
        test_session.commit()

        # Retrieve and verify
        retrieved = test_session.get(Change, change.id)
        assert retrieved.signature_before == sig_before
        assert retrieved.signature_after == sig_after
        assert retrieved.signature_after["params"] == ["arg1", "arg2", "arg3"]

    def test_template_variables_json_field(self, test_session):
        """Test Template variables JSON field."""
        variables = {
            "title": "API Documentation",
            "version": "1.0",
            "authors": ["Alice", "Bob"],
        }

        template = Template(
            name="test_template",
            format="Markdown",
            body="# {{title}} v{{version}}",
            variables=variables,
        )
        test_session.add(template)
        test_session.commit()

        # Retrieve and verify
        retrieved = test_session.get(Template, template.id)
        assert retrieved.variables == variables
        assert retrieved.variables["authors"] == ["Alice", "Bob"]


class TestRetentionPolicy:
    """Test retention policy per SRS 7.2."""

    def create_test_runs(self, session, count: int):
        """Helper to create test runs."""
        runs = []
        base_time = datetime.utcnow() - timedelta(days=count)

        for i in range(count):
            run = Run(
                repo="test/repo",
                branch="main",
                commit_sha=f"commit-{i:03d}",
                started_at=base_time + timedelta(hours=i),
                status="Success",
                correlation_id=f"corr-{i:03d}",
            )
            runs.append(run)

        session.add_all(runs)
        session.commit()
        return runs

    def test_cleanup_keeps_exactly_100_runs(self, test_session):
        """Test that retention keeps exactly 100 most recent runs."""
        # Create 150 runs
        runs = self.create_test_runs(test_session, 150)

        # Verify 150 runs exist
        assert get_run_count(test_session) == 150

        # Run cleanup
        deleted = cleanup_old_runs(test_session, keep_count=100)

        # Verify 50 runs were deleted
        assert deleted == 50
        assert get_run_count(test_session) == 100

        # Verify the oldest 50 were deleted (correct ones kept)
        remaining_runs = test_session.scalars(
            select(Run).order_by(Run.started_at),
        ).all()

        # The first remaining run should be run #50
        assert remaining_runs[0].commit_sha == "commit-050"
        # The last remaining run should be run #149
        assert remaining_runs[-1].commit_sha == "commit-149"

    def test_cleanup_with_less_than_keep_count(self, test_session):
        """Test cleanup when fewer runs than keep_count exist."""
        # Create 50 runs
        self.create_test_runs(test_session, 50)

        # Run cleanup
        deleted = cleanup_old_runs(test_session, keep_count=100)

        # Nothing should be deleted
        assert deleted == 0
        assert get_run_count(test_session) == 50

    def test_cleanup_cascades_dependent_rows(self, test_session):
        """Test that cleanup cascades to Changes and Patches."""
        # Create 150 runs with changes and patches
        runs = self.create_test_runs(test_session, 150)

        # Add changes and patches to all runs
        for run in runs:
            change = Change(
                run_id=run.id,
                file_path="test.py",
                symbol="func",
                change_type="added",
            )
            patch = Patch(
                run_id=run.id,
                page_id="page-1",
                diff_before="before",
                diff_after="after",
                status="Proposed",
            )
            test_session.add_all([change, patch])

        test_session.commit()

        # Verify 150 changes and patches exist
        from sqlalchemy import func

        change_count = test_session.scalar(
            select(func.count()).select_from(Change),
        )
        patch_count = test_session.scalar(
            select(func.count()).select_from(Patch),
        )
        assert change_count == 150
        assert patch_count == 150

        # Run cleanup
        deleted = cleanup_old_runs(test_session, keep_count=100)
        assert deleted == 50

        # Verify changes and patches were cascaded
        change_count = test_session.scalar(
            select(func.count()).select_from(Change),
        )
        patch_count = test_session.scalar(
            select(func.count()).select_from(Patch),
        )
        assert change_count == 100
        assert patch_count == 100

    def test_cleanup_invalid_keep_count(self, test_session):
        """Test cleanup with invalid keep_count raises error."""
        with pytest.raises(ValueError):
            cleanup_old_runs(test_session, keep_count=0)

        with pytest.raises(ValueError):
            cleanup_old_runs(test_session, keep_count=-1)

    def test_get_run_count(self, test_session):
        """Test get_run_count helper function."""
        assert get_run_count(test_session) == 0

        self.create_test_runs(test_session, 10)
        assert get_run_count(test_session) == 10

    def test_get_oldest_newest_run_ids(self, test_session):
        """Test get_oldest_run_id and get_newest_run_id."""
        # Empty database
        assert get_oldest_run_id(test_session) is None
        assert get_newest_run_id(test_session) is None

        # Create runs
        runs = self.create_test_runs(test_session, 10)

        oldest_id = get_oldest_run_id(test_session)
        newest_id = get_newest_run_id(test_session)

        assert oldest_id == runs[0].id
        assert newest_id == runs[-1].id
