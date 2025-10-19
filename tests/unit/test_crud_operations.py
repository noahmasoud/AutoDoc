"""
CRUD smoke tests for all five entities.

Tests basic Create, Read, Update, Delete operations for Run, Change, Rule, Template, Patch.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine, select, event
from sqlalchemy.orm import sessionmaker

from db.session import Base
from db.models import Run, Change, Rule, Template, Patch


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


class TestRunCRUD:
    """CRUD smoke tests for Run entity."""

    def test_create_run(self, test_session):
        """Test creating a Run."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123def456",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        assert run.id is not None
        assert run.repo == "test/repo"

    def test_read_run(self, test_session):
        """Test reading a Run."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        # Read by ID
        retrieved = test_session.get(Run, run.id)
        assert retrieved is not None
        assert retrieved.repo == "test/repo"
        assert retrieved.commit_sha == "abc123"

        # Read by query
        result = test_session.scalar(
            select(Run).where(Run.commit_sha == "abc123"),
        )
        assert result is not None
        assert result.id == run.id

    def test_update_run(self, test_session):
        """Test updating a Run."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        # Update
        run.status = "Success"
        run.completed_at = datetime.utcnow()
        test_session.commit()

        # Verify update
        retrieved = test_session.get(Run, run.id)
        assert retrieved.status == "Success"
        assert retrieved.completed_at is not None

    def test_delete_run(self, test_session):
        """Test deleting a Run."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        run_id = run.id

        # Delete
        test_session.delete(run)
        test_session.commit()

        # Verify deletion
        retrieved = test_session.get(Run, run_id)
        assert retrieved is None


class TestChangeCRUD:
    """CRUD smoke tests for Change entity."""

    def test_create_change(self, test_session):
        """Test creating a Change."""
        # Create parent run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        # Create change
        change = Change(
            run_id=run.id,
            file_path="src/main.py",
            symbol="my_function",
            change_type="added",
            signature_after={"name": "my_function", "params": ["arg1"]},
        )
        test_session.add(change)
        test_session.commit()

        assert change.id is not None
        assert change.run_id == run.id

    def test_read_change(self, test_session):
        """Test reading a Change."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        change = Change(
            run_id=run.id,
            file_path="src/main.py",
            symbol="my_function",
            change_type="modified",
        )
        test_session.add(change)
        test_session.commit()

        # Read by ID
        retrieved = test_session.get(Change, change.id)
        assert retrieved is not None
        assert retrieved.symbol == "my_function"

        # Read by query
        result = test_session.scalar(
            select(Change).where(Change.file_path == "src/main.py"),
        )
        assert result is not None

    def test_update_change(self, test_session):
        """Test updating a Change."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        change = Change(
            run_id=run.id,
            file_path="src/main.py",
            symbol="my_function",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Update
        change.change_type = "modified"
        change.signature_after = {"modified": True}
        test_session.commit()

        # Verify
        retrieved = test_session.get(Change, change.id)
        assert retrieved.change_type == "modified"

    def test_delete_change(self, test_session):
        """Test deleting a Change."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        change = Change(
            run_id=run.id,
            file_path="src/main.py",
            symbol="my_function",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        change_id = change.id

        # Delete
        test_session.delete(change)
        test_session.commit()

        # Verify
        retrieved = test_session.get(Change, change_id)
        assert retrieved is None


class TestRuleCRUD:
    """CRUD smoke tests for Rule entity."""

    def test_create_rule(self, test_session):
        """Test creating a Rule."""
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            auto_approve=False,
        )
        test_session.add(rule)
        test_session.commit()

        assert rule.id is not None
        assert rule.name == "test_rule"

    def test_read_rule(self, test_session):
        """Test reading a Rule."""
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            auto_approve=True,
        )
        test_session.add(rule)
        test_session.commit()

        # Read by ID
        retrieved = test_session.get(Rule, rule.id)
        assert retrieved is not None
        assert retrieved.auto_approve is True

        # Read by name
        result = test_session.scalar(
            select(Rule).where(Rule.name == "test_rule"),
        )
        assert result is not None

    def test_update_rule(self, test_session):
        """Test updating a Rule."""
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            auto_approve=False,
        )
        test_session.add(rule)
        test_session.commit()

        # Update
        rule.auto_approve = True
        rule.selector = "**/*.py"
        test_session.commit()

        # Verify
        retrieved = test_session.get(Rule, rule.id)
        assert retrieved.auto_approve is True
        assert retrieved.selector == "**/*.py"

    def test_delete_rule(self, test_session):
        """Test deleting a Rule."""
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            auto_approve=False,
        )
        test_session.add(rule)
        test_session.commit()

        rule_id = rule.id

        # Delete
        test_session.delete(rule)
        test_session.commit()

        # Verify
        retrieved = test_session.get(Rule, rule_id)
        assert retrieved is None


class TestTemplateCRUD:
    """CRUD smoke tests for Template entity."""

    def test_create_template(self, test_session):
        """Test creating a Template."""
        template = Template(
            name="api_template",
            format="Markdown",
            body="# API Documentation\n{{content}}",
            variables={"version": "1.0"},
        )
        test_session.add(template)
        test_session.commit()

        assert template.id is not None
        assert template.name == "api_template"

    def test_read_template(self, test_session):
        """Test reading a Template."""
        template = Template(
            name="api_template",
            format="Markdown",
            body="# API\n{{content}}",
        )
        test_session.add(template)
        test_session.commit()

        # Read by ID
        retrieved = test_session.get(Template, template.id)
        assert retrieved is not None
        assert retrieved.format == "Markdown"

        # Read by name
        result = test_session.scalar(
            select(Template).where(Template.name == "api_template"),
        )
        assert result is not None

    def test_update_template(self, test_session):
        """Test updating a Template."""
        template = Template(
            name="api_template",
            format="Markdown",
            body="# API\n{{content}}",
        )
        test_session.add(template)
        test_session.commit()

        # Update
        template.body = "# Updated API\n{{content}}"
        template.variables = {"version": "2.0"}
        test_session.commit()

        # Verify
        retrieved = test_session.get(Template, template.id)
        assert "Updated" in retrieved.body
        assert retrieved.variables["version"] == "2.0"

    def test_delete_template(self, test_session):
        """Test deleting a Template."""
        template = Template(
            name="api_template",
            format="Markdown",
            body="# API\n{{content}}",
        )
        test_session.add(template)
        test_session.commit()

        template_id = template.id

        # Delete
        test_session.delete(template)
        test_session.commit()

        # Verify
        retrieved = test_session.get(Template, template_id)
        assert retrieved is None


class TestPatchCRUD:
    """CRUD smoke tests for Patch entity."""

    def test_create_patch(self, test_session):
        """Test creating a Patch."""
        # Create parent run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        # Create patch
        patch = Patch(
            run_id=run.id,
            page_id="page-12345",
            diff_before="Original content",
            diff_after="Updated content",
            status="Proposed",
        )
        test_session.add(patch)
        test_session.commit()

        assert patch.id is not None
        assert patch.run_id == run.id

    def test_read_patch(self, test_session):
        """Test reading a Patch."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        patch = Patch(
            run_id=run.id,
            page_id="page-12345",
            diff_before="Original",
            diff_after="Updated",
            status="Proposed",
        )
        test_session.add(patch)
        test_session.commit()

        # Read by ID
        retrieved = test_session.get(Patch, patch.id)
        assert retrieved is not None
        assert retrieved.status == "Proposed"

        # Read by query
        result = test_session.scalar(
            select(Patch).where(Patch.page_id == "page-12345"),
        )
        assert result is not None

    def test_update_patch(self, test_session):
        """Test updating a Patch."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        patch = Patch(
            run_id=run.id,
            page_id="page-12345",
            diff_before="Original",
            diff_after="Updated",
            status="Proposed",
        )
        test_session.add(patch)
        test_session.commit()

        # Update
        patch.status = "Approved"
        patch.approved_by = "user@example.com"
        test_session.commit()

        # Verify
        retrieved = test_session.get(Patch, patch.id)
        assert retrieved.status == "Approved"
        assert retrieved.approved_by == "user@example.com"

    def test_delete_patch(self, test_session):
        """Test deleting a Patch."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        patch = Patch(
            run_id=run.id,
            page_id="page-12345",
            diff_before="Original",
            diff_after="Updated",
            status="Proposed",
        )
        test_session.add(patch)
        test_session.commit()

        patch_id = patch.id

        # Delete
        test_session.delete(patch)
        test_session.commit()

        # Verify
        retrieved = test_session.get(Patch, patch_id)
        assert retrieved is None


class TestRelationships:
    """Test relationships between entities."""

    def test_run_changes_relationship(self, test_session):
        """Test Run -> Changes relationship."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Success",
            correlation_id="corr-123",
        )
        test_session.add(run)
        test_session.commit()

        change1 = Change(
            run_id=run.id,
            file_path="file1.py",
            symbol="func1",
            change_type="added",
        )
        change2 = Change(
            run_id=run.id,
            file_path="file2.py",
            symbol="func2",
            change_type="modified",
        )
        test_session.add_all([change1, change2])
        test_session.commit()

        # Access via relationship
        retrieved = test_session.get(Run, run.id)
        assert len(retrieved.changes) == 2
        assert retrieved.changes[0].symbol in ["func1", "func2"]

    def test_template_rules_relationship(self, test_session):
        """Test Template -> Rules relationship."""
        template = Template(
            name="api_template",
            format="Markdown",
            body="# API",
        )
        test_session.add(template)
        test_session.commit()

        rule1 = Rule(
            name="rule1",
            selector="*.py",
            space_key="DOCS",
            page_id="page-1",
            template_id=template.id,
            auto_approve=False,
        )
        rule2 = Rule(
            name="rule2",
            selector="*.js",
            space_key="DOCS",
            page_id="page-2",
            template_id=template.id,
            auto_approve=True,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        # Access via relationship
        retrieved = test_session.get(Template, template.id)
        assert len(retrieved.rules) == 2
