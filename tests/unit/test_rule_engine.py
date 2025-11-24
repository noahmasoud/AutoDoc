"""Unit tests for rule engine service."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import Rule
from db.session import Base
from services.rule_engine import (
    InvalidSelectorError,
    InvalidTargetError,
    is_glob_pattern,
    match_file_to_rules,
    match_glob,
    match_regex,
    resolve_target_page,
    validate_rule_target,
    validate_selector,
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


class TestIsGlobPattern:
    """Tests for is_glob_pattern function."""

    def test_simple_glob_pattern(self):
        """Test simple glob patterns are detected."""
        assert is_glob_pattern("*.py") is True
        assert is_glob_pattern("**/*.ts") is True
        assert is_glob_pattern("src/**/*.py") is True

    def test_regex_pattern_detection(self):
        """Test regex patterns are detected."""
        assert is_glob_pattern("^src/.*\\.py$") is False
        assert is_glob_pattern("src/.*\\.(py|ts)") is False
        assert is_glob_pattern(".*\\.py") is False

    def test_literal_string(self):
        """Test literal strings default to glob."""
        assert is_glob_pattern("src/main.py") is True
        assert is_glob_pattern("exact_file.txt") is True


class TestMatchGlob:
    """Tests for match_glob function."""

    def test_simple_wildcard(self):
        """Test simple wildcard matching."""
        assert match_glob("test.py", "*.py") is True
        assert match_glob("test.txt", "*.py") is False
        assert match_glob("src/test.py", "*.py") is True

    def test_recursive_glob(self):
        """Test recursive glob pattern (**)."""
        assert match_glob("src/api/routes.py", "src/**/*.py") is True
        assert match_glob("src/api/v1/routes.py", "src/**/*.py") is True
        assert match_glob("src/routes.py", "src/**/*.py") is True
        assert match_glob("other/routes.py", "src/**/*.py") is False

    def test_single_char_wildcard(self):
        """Test single character wildcard (?)."""
        assert match_glob("test.py", "test?.py") is False
        assert match_glob("test1.py", "test?.py") is True
        assert match_glob("test12.py", "test?.py") is False

    def test_exact_match(self):
        """Test exact file path matching."""
        assert match_glob("src/main.py", "src/main.py") is True
        assert match_glob("src/main.py", "src/other.py") is False


class TestMatchRegex:
    """Tests for match_regex function."""

    def test_simple_regex(self):
        """Test simple regex patterns."""
        assert match_regex("src/api.py", r"src/.*\.py$") is True
        assert match_regex("src/api.ts", r"src/.*\.py$") is False

    def test_character_class(self):
        """Test regex with character classes."""
        assert match_regex("test1.py", r"test[0-9]\.py") is True
        assert match_regex("testa.py", r"test[0-9]\.py") is False

    def test_invalid_regex(self):
        """Test invalid regex raises error."""
        with pytest.raises(InvalidSelectorError, match="Invalid regex pattern"):
            match_regex("test.py", "[invalid")


class TestValidateSelector:
    """Tests for validate_selector function."""

    def test_valid_glob_selector(self):
        """Test valid glob selectors."""
        assert validate_selector("*.py") is True
        assert validate_selector("src/**/*.py") is True

    def test_valid_regex_selector(self):
        """Test valid regex selectors."""
        assert validate_selector(r"^src/.*\.py$") is True
        assert validate_selector(r"src/.*\.(py|ts)") is True

    def test_empty_selector(self):
        """Test empty selector raises error."""
        with pytest.raises(InvalidSelectorError, match="cannot be empty"):
            validate_selector("")
        with pytest.raises(InvalidSelectorError, match="cannot be empty"):
            validate_selector("   ")

    def test_invalid_regex_selector(self):
        """Test invalid regex selector raises error."""
        with pytest.raises(InvalidSelectorError):
            validate_selector("[invalid")


class TestMatchFileToRules:
    """Tests for match_file_to_rules function."""

    def test_single_matching_rule(self, test_session):
        """Test matching a single rule."""
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        matches = match_file_to_rules("test.py", [rule])
        assert len(matches) == 1
        assert matches[0].id == rule.id

    def test_no_matching_rules(self, test_session):
        """Test when no rules match."""
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        matches = match_file_to_rules("test.txt", [rule])
        assert len(matches) == 0

    def test_multiple_matching_rules_precedence(self, test_session):
        """Test precedence ordering when multiple rules match."""
        rule1 = Rule(
            name="low_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=10,
        )
        rule2 = Rule(
            name="high_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="456",
            priority=0,
        )
        rule3 = Rule(
            name="medium_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="789",
            priority=5,
        )
        test_session.add_all([rule1, rule2, rule3])
        test_session.commit()

        matches = match_file_to_rules("test.py", [rule1, rule2, rule3])
        assert len(matches) == 3
        # Should be sorted by priority (ascending)
        assert matches[0].priority == 0
        assert matches[1].priority == 5
        assert matches[2].priority == 10

    def test_tiebreaker_by_id(self, test_session):
        """Test that rule ID is used as tiebreaker for same priority."""
        rule1 = Rule(
            name="rule1",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        rule2 = Rule(
            name="rule2",
            selector="*.py",
            space_key="DOCS",
            page_id="456",
            priority=0,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        matches = match_file_to_rules("test.py", [rule2, rule1])
        assert len(matches) == 2
        # Lower ID should come first
        assert matches[0].id < matches[1].id

    def test_glob_and_regex_mixed(self, test_session):
        """Test matching with both glob and regex patterns."""
        glob_rule = Rule(
            name="glob_rule",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        regex_rule = Rule(
            name="regex_rule",
            selector=r"^src/.*\.py$",
            space_key="DOCS",
            page_id="456",
            priority=0,
        )
        test_session.add_all([glob_rule, regex_rule])
        test_session.commit()

        # Both should match src/test.py
        matches = match_file_to_rules("src/test.py", [glob_rule, regex_rule])
        assert len(matches) == 2

        # Only glob should match test.py (not in src/)
        matches = match_file_to_rules("test.py", [glob_rule, regex_rule])
        assert len(matches) == 1
        assert matches[0].name == "glob_rule"

    def test_invalid_selector_skipped(self, test_session):
        """Test that invalid selectors are skipped without failing."""
        valid_rule = Rule(
            name="valid",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        invalid_rule = Rule(
            name="invalid",
            selector="[invalid",
            space_key="DOCS",
            page_id="456",
            priority=0,
        )
        test_session.add_all([valid_rule, invalid_rule])
        test_session.commit()

        # Should still match valid rule, skip invalid one
        matches = match_file_to_rules("test.py", [valid_rule, invalid_rule])
        assert len(matches) == 1
        assert matches[0].name == "valid"


class TestResolveTargetPage:
    """Tests for resolve_target_page function."""

    def test_single_match(self, test_session):
        """Test resolving with single matching rule."""
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        resolved = resolve_target_page("test.py", [rule])
        assert resolved is not None
        assert resolved.id == rule.id

    def test_no_match_returns_none(self, test_session):
        """Test that None is returned when no rules match."""
        rule = Rule(
            name="python_files",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        resolved = resolve_target_page("test.txt", [rule])
        assert resolved is None

    def test_precedence_selection(self, test_session):
        """Test that highest priority rule is selected."""
        rule1 = Rule(
            name="low_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=10,
        )
        rule2 = Rule(
            name="high_priority",
            selector="*.py",
            space_key="DOCS",
            page_id="456",
            priority=0,
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        resolved = resolve_target_page("test.py", [rule1, rule2])
        assert resolved is not None
        assert resolved.priority == 0
        assert resolved.page_id == "456"

    def test_empty_page_id_raises_error(self, test_session):
        """Test that empty page_id raises InvalidTargetError."""
        rule = Rule(
            name="invalid",
            selector="*.py",
            space_key="DOCS",
            page_id="",  # Empty
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        with pytest.raises(InvalidTargetError, match="empty page_id"):
            resolve_target_page("test.py", [rule])

    def test_empty_space_key_raises_error(self, test_session):
        """Test that empty space_key raises InvalidTargetError."""
        rule = Rule(
            name="invalid",
            selector="*.py",
            space_key="",  # Empty
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        with pytest.raises(InvalidTargetError, match="empty space_key"):
            resolve_target_page("test.py", [rule])


class TestValidateRuleTarget:
    """Tests for validate_rule_target function."""

    def test_valid_target(self, test_session):
        """Test valid rule target passes validation."""
        rule = Rule(
            name="valid",
            selector="*.py",
            space_key="DOCS",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        assert validate_rule_target(rule) is True

    def test_empty_page_id_raises_error(self, test_session):
        """Test empty page_id raises error."""
        rule = Rule(
            name="invalid",
            selector="*.py",
            space_key="DOCS",
            page_id="",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        with pytest.raises(InvalidTargetError, match="empty page_id"):
            validate_rule_target(rule)

    def test_empty_space_key_raises_error(self, test_session):
        """Test empty space_key raises error."""
        rule = Rule(
            name="invalid",
            selector="*.py",
            space_key="",
            page_id="123",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        with pytest.raises(InvalidTargetError, match="empty space_key"):
            validate_rule_target(rule)

    def test_whitespace_only_raises_error(self, test_session):
        """Test whitespace-only values raise error."""
        rule = Rule(
            name="invalid",
            selector="*.py",
            space_key="   ",
            page_id="   ",
            priority=0,
        )
        test_session.add(rule)
        test_session.commit()

        with pytest.raises(InvalidTargetError):
            validate_rule_target(rule)
