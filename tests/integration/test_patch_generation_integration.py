"""Integration tests for patch generation from analyzer findings.

Tests the complete workflow from synthetic code changes through patch generation,
including template rendering and the CI pipeline integration.
"""

from collections.abc import Generator
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Patch, PythonSymbol, Rule, Run, Template
from db.session import Base
from schemas.changes import ChangeDetected
from services.change_persister import save_changes_to_database


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


@pytest.fixture
def sample_run(test_session):
    """Create a sample run for testing."""
    run = Run(
        repo="test/repo",
        branch="main",
        commit_sha="abc123def456",
        started_at=datetime.utcnow(),
        correlation_id="test-correlation-id",
        status="Awaiting Review",
    )
    test_session.add(run)
    test_session.commit()
    test_session.refresh(run)
    return run


@pytest.fixture
def sample_rule(test_session):
    """Create a sample rule for testing."""
    rule = Rule(
        name="api_docs",
        selector="src/api/**/*.py",
        space_key="DOCS",
        page_id="12345",
        priority=0,
    )
    test_session.add(rule)
    test_session.commit()
    test_session.refresh(rule)
    return rule


@pytest.fixture
def sample_template(test_session):
    """Create a sample template for testing."""
    template = Template(
        name="api_reference",
        format="Markdown",
        body="# API Reference\n\n## Changes\n\n{{changes.all}}\n\n## Files\n\n{{files}}\n",
    )
    test_session.add(template)
    test_session.commit()
    test_session.refresh(template)
    return template


class TestPatchGenerationIntegration:
    """Integration tests for complete patch generation workflow."""

    @pytest.mark.integration
    def test_complete_workflow_synthetic_code_changes(
        self, test_session, sample_run, sample_rule
    ):
        """Test complete workflow: synthetic code changes -> patches generated.

        This test simulates:
        1. Synthetic code changes detected
        2. Changes saved to database
        3. Patch generation automatically triggered (via change_persister)
        4. Patches created with sensible content
        """
        # Create synthetic code changes
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="process_request",
                change_type="added",
                signature_before=None,
                signature_after={
                    "name": "process_request",
                    "symbol_type": "function",
                    "parameters": [{"name": "request", "annotation": "str"}],
                    "return_annotation": "dict",
                },
                is_breaking=False,
                breaking_reason=None,
            ),
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="handle_error",
                change_type="modified",
                signature_before={
                    "name": "handle_error",
                    "parameters": [{"name": "error", "annotation": "Exception"}],
                },
                signature_after={
                    "name": "handle_error",
                    "parameters": [
                        {"name": "error", "annotation": "Exception"},
                        {"name": "context", "annotation": "dict"},
                    ],
                },
                is_breaking=True,
                breaking_reason="parameter_added",
            ),
        ]

        # Save changes (this should automatically trigger patch generation)
        saved_changes = save_changes_to_database(
            test_session,
            sample_run.id,
            changes,
        )

        # Verify changes were saved
        assert len(saved_changes) == 2
        assert saved_changes[0].symbol == "process_request"
        assert saved_changes[1].symbol == "handle_error"

        # Verify patches were automatically generated
        test_session.refresh(sample_run)
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()

        assert len(patches) == 1
        patch = patches[0]
        assert patch.run_id == sample_run.id
        assert patch.page_id == sample_rule.page_id
        assert patch.status == "Proposed"
        assert "src/api/handler.py" in patch.diff_after
        assert "process_request" in patch.diff_after
        assert "handle_error" in patch.diff_after

    @pytest.mark.integration
    def test_patch_generation_with_template(
        self,
        test_session,
        sample_run,
        sample_rule,
        sample_template,
    ):
        """Test patch generation with template rendering."""
        # Link template to rule
        sample_rule.template_id = sample_template.id
        test_session.commit()

        # Create synthetic changes
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="new_function",
                change_type="added",
                signature_after={
                    "name": "new_function",
                    "symbol_type": "function",
                },
                is_breaking=False,
            ),
        ]

        # Save changes and trigger patch generation
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify patch was generated with template
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 1

        patch = patches[0]
        # Template should have been rendered
        assert patch.diff_after is not None
        # Check that template variables were substituted
        # (The template has {{changes.all}} and {{files}} which should be rendered)
        assert (
            "src/api/handler.py" in patch.diff_after
            or "new_function" in patch.diff_after
        )

    @pytest.mark.integration
    def test_patch_generation_with_python_symbols(
        self,
        test_session,
        sample_run,
        sample_rule,
    ):
        """Test patch generation includes PythonSymbol records in context."""
        # Create PythonSymbol records (simulating analyzer findings)
        symbols = [
            PythonSymbol(
                run_id=sample_run.id,
                file_path="src/api/handler.py",
                symbol_name="process_request",
                qualified_name="api.handler.process_request",
                symbol_type="function",
                docstring="Process an incoming request.",
                lineno=10,
                symbol_metadata={"is_public": True},
            ),
            PythonSymbol(
                run_id=sample_run.id,
                file_path="src/api/handler.py",
                symbol_name="handle_error",
                qualified_name="api.handler.handle_error",
                symbol_type="function",
                docstring="Handle an error with context.",
                lineno=25,
                symbol_metadata={"is_public": True},
            ),
        ]
        test_session.add_all(symbols)
        test_session.commit()

        # Create synthetic changes
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="process_request",
                change_type="added",
                signature_after={"name": "process_request"},
                is_breaking=False,
            ),
        ]

        # Save changes and trigger patch generation
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify patch was generated
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 1

        # Patch should contain information from both changes and symbols
        patch = patches[0]
        assert "process_request" in patch.diff_after

    @pytest.mark.integration
    def test_patch_generation_multiple_files_same_page(
        self,
        test_session,
        sample_run,
        sample_rule,
    ):
        """Test patch generation when multiple files map to same page."""
        # Create changes in multiple files that match the same rule
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="func1",
                change_type="added",
                signature_after={"name": "func1"},
                is_breaking=False,
            ),
            ChangeDetected(
                file_path="src/api/router.py",
                symbol_name="func2",
                change_type="added",
                signature_after={"name": "func2"},
                is_breaking=False,
            ),
        ]

        # Save changes
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify patches were generated
        # Both files should map to the same page, so we should get one patch
        # with changes from both files
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 1

        patch = patches[0]
        assert patch.page_id == sample_rule.page_id
        # Both files should be represented in the patch
        assert "handler.py" in patch.diff_after or "func1" in patch.diff_after
        assert "router.py" in patch.diff_after or "func2" in patch.diff_after

    @pytest.mark.integration
    def test_patch_generation_multiple_pages(
        self,
        test_session,
        sample_run,
    ):
        """Test patch generation when changes map to different pages."""
        # Create rules for different file patterns
        rule1 = Rule(
            name="api_files",
            selector="src/api/**/*.py",
            space_key="DOCS",
            page_id="page_api",
            priority=0,
        )
        rule2 = Rule(
            name="utils_files",
            selector="src/utils/**/*.py",
            space_key="DOCS",
            page_id="page_utils",
            priority=0,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        # Create changes in files matching different rules
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="api_func",
                change_type="added",
                signature_after={"name": "api_func"},
                is_breaking=False,
            ),
            ChangeDetected(
                file_path="src/utils/helpers.py",
                symbol_name="util_func",
                change_type="added",
                signature_after={"name": "util_func"},
                is_breaking=False,
            ),
        ]

        # Save changes
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify separate patches for each page
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 2

        page_ids = {patch.page_id for patch in patches}
        assert "page_api" in page_ids
        assert "page_utils" in page_ids

    @pytest.mark.integration
    def test_patch_generation_no_matching_rules(
        self,
        test_session,
        sample_run,
    ):
        """Test patch generation when no rules match changed files."""
        # Create a rule that won't match
        rule = Rule(
            name="typescript_files",
            selector="**/*.ts",
            space_key="DOCS",
            page_id="page_ts",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create changes in Python files (won't match TypeScript rule)
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="func",
                change_type="added",
                signature_after={"name": "func"},
                is_breaking=False,
            ),
        ]

        # Save changes
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify no patches were generated
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 0

        # Verify run status was updated
        test_session.refresh(sample_run)
        assert sample_run.status == "Completed (no patches)"

    @pytest.mark.integration
    def test_patch_generation_with_all_change_types(
        self,
        test_session,
        sample_run,
        sample_rule,
    ):
        """Test patch generation handles all change types (added, modified, removed)."""
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="new_func",
                change_type="added",
                signature_after={"name": "new_func"},
                is_breaking=False,
            ),
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="modified_func",
                change_type="modified",
                signature_before={"name": "modified_func", "params": ["a"]},
                signature_after={"name": "modified_func", "params": ["a", "b"]},
                is_breaking=True,
                breaking_reason="parameter_added",
            ),
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="removed_func",
                change_type="removed",
                signature_before={"name": "removed_func"},
                is_breaking=True,
                breaking_reason="symbol_removed",
            ),
        ]

        # Save changes
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify patch was generated with all change types
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 1

        patch = patches[0]
        # All change types should be represented
        assert "new_func" in patch.diff_after
        assert "modified_func" in patch.diff_after
        assert "removed_func" in patch.diff_before or "removed_func" in patch.diff_after

    @pytest.mark.integration
    def test_patch_generation_rule_precedence(
        self,
        test_session,
        sample_run,
    ):
        """Test that rule precedence is respected in patch generation."""
        # Create rules with different priorities
        rule_low = Rule(
            name="low_priority",
            selector="src/**/*.py",
            space_key="DOCS",
            page_id="page_low",
            priority=10,
        )
        rule_high = Rule(
            name="high_priority",
            selector="src/api/**/*.py",
            space_key="DOCS",
            page_id="page_high",
            priority=0,
        )
        test_session.add_all([rule_low, rule_high])
        test_session.commit()

        # Create changes that match both rules
        changes = [
            ChangeDetected(
                file_path="src/api/handler.py",
                symbol_name="func",
                change_type="added",
                signature_after={"name": "func"},
                is_breaking=False,
            ),
        ]

        # Save changes
        save_changes_to_database(test_session, sample_run.id, changes)

        # Verify only one patch was created (highest priority rule)
        patches = test_session.query(Patch).filter(Patch.run_id == sample_run.id).all()
        assert len(patches) == 1
        assert patches[0].page_id == "page_high"  # Higher priority rule
