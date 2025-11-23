"""Unit tests for rule matching with priority ordering."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Rule
from db.session import Base
from services.rule_matcher import RuleMatch, RuleMatcher


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


class TestRuleMatcher:
    """Test rule matching functionality."""

    def test_match_single_rule(self, test_session):
        """Test matching a single rule to a file."""
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="12345",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        matches = RuleMatcher.match_rules_to_file("src/main.py", [rule])
        assert len(matches) == 1
        assert matches[0].rule.id == rule.id
        assert matches[0].file_path == "src/main.py"

    def test_match_multiple_rules_different_priorities(self, test_session):
        """Test matching multiple rules with different priorities."""
        rule_low = Rule(
            name="all_python",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        rule_high = Rule(
            name="api_python",
            selector="api/*.py",
            space_key="DOCS",
            page_id="222",
            priority=10,
        )
        test_session.add_all([rule_low, rule_high])
        test_session.commit()

        # File matches both rules
        matches = RuleMatcher.match_rules_to_file("api/main.py", [rule_low, rule_high])
        assert len(matches) == 2
        # Higher priority rule should be first
        assert matches[0].rule.priority == 10
        assert matches[0].rule.id == rule_high.id
        assert matches[1].rule.priority == 0
        assert matches[1].rule.id == rule_low.id

    def test_resolve_conflicting_rules_keeps_highest_priority(self, test_session):
        """Test that conflict resolution keeps only highest priority rules."""
        rule_low = Rule(
            name="low_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        rule_medium = Rule(
            name="medium_priority",
            selector="src/*.py",
            space_key="DOCS",
            page_id="222",
            priority=5,
        )
        rule_high = Rule(
            name="high_priority",
            selector="src/api/*.py",
            space_key="DOCS",
            page_id="333",
            priority=10,
        )
        test_session.add_all([rule_low, rule_medium, rule_high])
        test_session.commit()

        matches = RuleMatcher.match_rules_to_file(
            "src/api/main.py", [rule_low, rule_medium, rule_high]
        )
        assert len(matches) == 3

        resolved = RuleMatcher.resolve_conflicting_rules(matches)
        # Should keep only highest priority rule
        assert len(resolved) == 1
        assert resolved[0].rule.priority == 10
        assert resolved[0].rule.id == rule_high.id

    def test_resolve_conflicting_rules_same_priority_keeps_all(self, test_session):
        """Test that rules with same priority are all kept."""
        rule1 = Rule(
            name="rule1",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=5,
        )
        rule2 = Rule(
            name="rule2",
            selector="src/*.py",
            space_key="DOCS",
            page_id="222",
            priority=5,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        matches = RuleMatcher.match_rules_to_file("src/main.py", [rule1, rule2])
        assert len(matches) == 2

        resolved = RuleMatcher.resolve_conflicting_rules(matches)
        # Should keep both rules with same priority
        assert len(resolved) == 2
        assert all(m.rule.priority == 5 for m in resolved)

    def test_get_primary_rule_returns_highest_priority(self, test_session):
        """Test that get_primary_rule returns the highest priority rule."""
        rule_low = Rule(
            name="low",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        rule_high = Rule(
            name="high",
            selector="api/*.py",
            space_key="DOCS",
            page_id="222",
            priority=10,
        )
        test_session.add_all([rule_low, rule_high])
        test_session.commit()

        primary = RuleMatcher.get_primary_rule("api/main.py", [rule_low, rule_high])
        assert primary is not None
        assert primary.priority == 10
        assert primary.id == rule_high.id

    def test_get_primary_rule_returns_none_when_no_match(self, test_session):
        """Test that get_primary_rule returns None when no rules match."""
        rule = Rule(
            name="test",
            selector="*.ts",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        primary = RuleMatcher.get_primary_rule("src/main.py", [rule])
        assert primary is None

    def test_selector_matching_glob_patterns(self, test_session):
        """Test that glob patterns are correctly matched."""
        rule = Rule(
            name="test",
            selector="**/*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        # Should match files at any depth
        assert len(RuleMatcher.match_rules_to_file("src/main.py", [rule])) == 1
        assert len(RuleMatcher.match_rules_to_file("src/api/main.py", [rule])) == 1
        assert len(RuleMatcher.match_rules_to_file("src/api/v1/main.py", [rule])) == 1

    def test_priority_ordering_stability(self, test_session):
        """Test that rules with same priority are ordered by ID for stability."""
        rule1 = Rule(
            name="rule1",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=5,
        )
        rule2 = Rule(
            name="rule2",
            selector="*.py",
            space_key="DOCS",
            page_id="222",
            priority=5,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        matches = RuleMatcher.match_rules_to_file("main.py", [rule1, rule2])
        assert len(matches) == 2
        # Should be ordered by ID (ascending) when priority is same
        assert matches[0].rule.id < matches[1].rule.id

    def test_empty_matches_resolution(self):
        """Test that resolving empty matches returns empty list."""
        resolved = RuleMatcher.resolve_conflicting_rules([])
        assert resolved == []

    def test_rule_match_repr(self, test_session):
        """Test RuleMatch string representation."""
        rule = Rule(
            name="test_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="111",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        match = RuleMatch(rule, "src/main.py")
        repr_str = repr(match)
        assert "RuleMatch" in repr_str
        assert str(rule.id) in repr_str
        assert "test_rule" in repr_str
        assert "src/main.py" in repr_str
