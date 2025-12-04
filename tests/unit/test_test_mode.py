"""
Tests for Test Mode functionality (SCRUM-51).

Verifies that when mode='TEST':
- Runs are created with TEST mode
- Patches are generated
- Confluence updates are skipped
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Run, Change, Rule, Patch, Base
from services.confluence_publisher import ConfluencePublisher


# Add these fixtures
@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


class TestRunModeField:
    """Test the mode field on Run model."""

    def test_run_defaults_to_production_mode(self, test_session: Session):
        """Test that Run mode defaults to PRODUCTION."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-123",
        )
        test_session.add(run)
        test_session.commit()

        assert run.mode == "PRODUCTION"

    def test_run_can_be_created_with_test_mode(self, test_session: Session):
        """Test that Run can be created with mode='TEST'."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-123",
            mode="TEST",
        )
        test_session.add(run)
        test_session.commit()

        assert run.mode == "TEST"

    def test_run_mode_constraint(self, test_session: Session):
        """Test that Run mode only accepts PRODUCTION or TEST."""
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-123",
            mode="INVALID",
        )
        test_session.add(run)

        with pytest.raises(Exception):  # SQLAlchemy will raise constraint violation
            test_session.commit()


class TestConfluencePublisherTestMode:
    """Test ConfluencePublisher behavior in TEST mode."""

    def test_update_page_skipped_in_test_mode(self):
        """Test that update_page is skipped when run_mode='TEST'."""
        mock_client = Mock()
        publisher = ConfluencePublisher(
            client=mock_client,
            run_mode="TEST"
        )

        payload = {"id": "12345", "content": "new content"}
        result = publisher.update_page(payload)

        # Should return test mode response
        assert result["id"] == "12345"
        assert result["status"] == "test_mode_skipped"

        # Should NOT call the actual client
        mock_client.update_page.assert_not_called()
        mock_client.get_page.assert_not_called()

    def test_create_page_skipped_in_test_mode(self):
        """Test that create_page is skipped when run_mode='TEST'."""
        mock_client = Mock()
        publisher = ConfluencePublisher(
            client=mock_client,
            run_mode="TEST"
        )

        payload = {"id": "12345", "content": "new page"}
        result = publisher.create_page(payload)

        # Should return test mode response
        assert result["id"] == "12345"
        assert result["status"] == "test_mode_skipped"

        # Should NOT call the actual client
        mock_client.create_page.assert_not_called()

    def test_update_page_executes_in_production_mode(self):
        """Test that update_page executes normally in PRODUCTION mode."""
        mock_client = Mock()
        mock_client.get_page.return_value = {
            "id": "12345",
            "content": "old content",
            "version": 1
        }
        mock_client.update_page.return_value = {
            "id": "12345",
            "content": "new content",
            "version": 2
        }

        publisher = ConfluencePublisher(
            client=mock_client,
            run_mode="PRODUCTION"
        )

        payload = {"id": "12345", "content": "new content"}
        result = publisher.update_page(payload)

        # Should call the actual client
        mock_client.get_page.assert_called_once_with("12345")
        mock_client.update_page.assert_called_once_with(payload)

        # Should return actual result
        assert result["version"] == 2

    def test_publisher_defaults_to_production_mode(self):
        """Test that ConfluencePublisher defaults to PRODUCTION mode."""
        mock_client = Mock()
        publisher = ConfluencePublisher(client=mock_client)

        assert publisher._run_mode == "PRODUCTION"


class TestTestModeIntegration:
    """Integration tests for test mode workflow."""

    def test_test_run_can_generate_patches(self, test_session: Session):
        """Test that patches can be generated for test runs."""
        # Create a TEST mode run
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            correlation_id="test-123",
            mode="TEST",
        )
        test_session.add(run)
        test_session.commit()

        # Create a rule
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Create a change
        change = Change(
            run_id=run.id,
            file_path="test.py",
            symbol="test_function",
            change_type="added",
        )
        test_session.add(change)
        test_session.commit()

        # Create a patch (simulating patch generation)
        patch = Patch(
            run_id=run.id,
            page_id="12345",
            diff_before="old",
            diff_after="new",
            status="Proposed",
        )
        test_session.add(patch)
        test_session.commit()

        # Verify patch was created
        assert patch.id is not None
        assert patch.run_id == run.id

        # Verify run is still in TEST mode
        assert run.mode == "TEST"
