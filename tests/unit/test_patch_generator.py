"""Unit tests for patch generator service."""

from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Change, Rule, Run, Template
from db.session import Base
from services.patch_generator import (
    PatchGenerationError,
    generate_patches_for_run,
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
def test_session(test_engine) -> Generator:
    """Create a test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()

    yield session
    session.rollback()
    session.close()


class TestGeneratePatchesForRun:
    """Tests for generate_patches_for_run function."""

    def test_generate_patches_with_matching_rule(self, test_session):
        """Test patch generation when rules match changed files."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes
        change1 = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
            signature_after={"name": "process_request", "params": ["request"]},
        )
        change2 = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="handle_error",
            change_type="modified",
            signature_before={"name": "handle_error", "params": ["error"]},
            signature_after={"name": "handle_error", "params": ["error", "context"]},
        )
        test_session.add_all([change1, change2])
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patches were created
        assert len(patches) == 1
        assert patches[0].run_id == run.id
        assert patches[0].page_id == "12345"
        assert patches[0].status == "Proposed"
        assert "src/api.py" in patches[0].diff_after
        assert "process_request" in patches[0].diff_after
        assert "handle_error" in patches[0].diff_after

    def test_generate_patches_multiple_files(self, test_session):
        """Test patch generation for multiple files."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create rules
        rule1 = Rule(
            name="api_files",
            selector="src/api/*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        rule2 = Rule(
            name="utils_files",
            selector="src/utils/*.py",
            space_key="DOCS",
            page_id="222",
            priority=0,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        # Create changes for different files
        change1 = Change(
            run_id=run.id,
            file_path="src/api/handler.py",
            symbol="handle",
            change_type="added",
        )
        change2 = Change(
            run_id=run.id,
            file_path="src/utils/helpers.py",
            symbol="helper",
            change_type="modified",
        )
        test_session.add_all([change1, change2])
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patches were created for both files
        assert len(patches) == 2
        page_ids = {patch.page_id for patch in patches}
        assert "111" in page_ids
        assert "222" in page_ids

    def test_generate_patches_no_matching_rules(self, test_session):
        """Test patch generation when no rules match."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule that won't match
        rule = Rule(
            name="python_files",
            selector="*.ts",  # TypeScript, not Python
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes for Python files
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify no patches were created
        assert len(patches) == 0

        # Verify run status was updated
        test_session.refresh(run)
        assert run.status == "Completed (no patches)"

    def test_generate_patches_no_changes(self, test_session):
        """Test patch generation when run has no changes."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Generate patches (no changes exist)
        patches = generate_patches_for_run(test_session, run.id)

        # Verify no patches were created
        assert len(patches) == 0

    def test_generate_patches_no_rules(self, test_session):
        """Test patch generation when no rules exist."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches (no rules exist)
        patches = generate_patches_for_run(test_session, run.id)

        # Verify no patches were created
        assert len(patches) == 0

    def test_generate_patches_precedence(self, test_session):
        """Test that rule precedence is respected."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create rules with different priorities
        rule1 = Rule(
            name="low_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=10,
        )
        rule2 = Rule(
            name="high_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="222",
            priority=0,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify only one patch was created (highest priority rule)
        assert len(patches) == 1
        assert patches[0].page_id == "222"  # High priority rule

    def test_generate_patches_invalid_run(self, test_session):
        """Test patch generation with invalid run ID."""
        with pytest.raises(PatchGenerationError, match=r"Run.*not found"):
            generate_patches_for_run(test_session, 99999)

    def test_generate_patches_multiple_changes_same_file(self, test_session):
        """Test patch generation when multiple symbols change in same file."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create multiple changes in the same file
        change1 = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="func1",
            change_type="added",
        )
        change2 = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="func2",
            change_type="modified",
        )
        change3 = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="func3",
            change_type="removed",
        )
        test_session.add_all([change1, change2, change3])
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify only one patch was created (one per file)
        assert len(patches) == 1
        # Verify all changes are reflected in the patch
        assert "func1" in patches[0].diff_after
        assert "func2" in patches[0].diff_after
        assert "func3" in patches[0].diff_after

    def test_generate_patches_with_template(self, test_session):
        """Test patch generation using template when rule has template_id."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a template
        template = Template(
            name="api_changes_template",
            format="Markdown",
            body="# API Changes\n\nFile: {{file_path}}\nSymbol: {{symbol}}\nType: {{change_type}}",
        )
        test_session.add(template)
        test_session.commit()

        # Create a rule with template
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            template_id=template.id,
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patch was created with template content
        assert len(patches) == 1
        assert patches[0].page_id == "12345"
        # Verify template variables were substituted
        assert "src/api.py" in patches[0].diff_after
        assert "process_request" in patches[0].diff_after
        assert "added" in patches[0].diff_after
        # Verify template structure
        assert "# API Changes" in patches[0].diff_after

    def test_generate_patches_with_storage_format_template(self, test_session):
        """Test patch generation using Storage Format template."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a Storage Format template
        template = Template(
            name="storage_template",
            format="Storage",
            body="<p>File: {{file_path}}</p><p>Symbol: {{symbol}}</p>",
        )
        test_session.add(template)
        test_session.commit()

        # Create a rule with template
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            template_id=template.id,
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patch was created with template content
        assert len(patches) == 1
        # Verify template variables were substituted
        assert "src/api.py" in patches[0].diff_after
        assert "process_request" in patches[0].diff_after
        # Verify Storage Format structure
        assert "<p>" in patches[0].diff_after

    def test_generate_patches_fallback_when_no_template(self, test_session):
        """Test that patch generation falls back to simple format when no template."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule without template
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            template_id=None,
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patch was created with simple format
        assert len(patches) == 1
        # Verify simple format markers
        assert "# After Changes" in patches[0].diff_after
        assert "**File:**" in patches[0].diff_after
        assert (
            "*This patch was automatically generated by AutoDoc*"
            in patches[0].diff_after
        )

    def test_generate_patches_fallback_on_template_error(self, test_session):
        """Test that patch generation falls back when template rendering fails."""
        # Create a run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-correlation-id",
        )
        test_session.add(run)
        test_session.commit()

        # Create an invalid Storage Format template (malformed XML)
        template = Template(
            name="invalid_template",
            format="Storage",
            body="<p>Unclosed paragraph",  # Invalid XML
        )
        test_session.add(template)
        test_session.commit()

        # Create a rule with invalid template
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            template_id=template.id,
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes
        change = Change(
            run_id=run.id,
            file_path="src/api.py",
            symbol="process_request",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Generate patches (should fall back to simple format)
        patches = generate_patches_for_run(test_session, run.id)

        # Verify patch was created with fallback format
        assert len(patches) == 1
        # Verify simple format markers (fallback)
        assert "# After Changes" in patches[0].diff_after
        assert "**File:**" in patches[0].diff_after
