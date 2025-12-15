"""Enhanced unit tests for Python symbol extraction + change detection.

Tests comprehensive symbol extraction and change detection scenarios:
- Public function extraction with various signatures
- Class and method extraction
- Change detection: added, removed, modified symbols
- Breaking vs non-breaking changes
- Parameter type changes, return type changes
- Signature modifications
"""

import pytest

from schemas.changes import (
    RunArtifact,
    SymbolData,
    SignatureInfo,
    ParameterInfo,
)
from services.change_detector import detect_changes
from services.python_symbol_ingestor import PythonSymbolIngestor
from db.models import Run, PythonSymbol
from db.session import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_con, _):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_session(test_engine):
    """Create a SQLAlchemy session bound to the test engine."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestPythonSymbolExtraction:
    """Comprehensive tests for Python symbol extraction."""

    def test_extract_public_function_signature(self, test_session, tmp_path):
        """Test extracting public function with full signature."""
        code = '''
def public_function(name: str, age: int = 0) -> dict:
    """A public function with type hints.
    
    Args:
        name: Person's name
        age: Person's age
        
    Returns:
        Dictionary with name and age
    """
    return {"name": name, "age": age}
'''
        file_path = tmp_path / "test_api.py"
        file_path.write_text(code)

        ingestor = PythonSymbolIngestor()
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="test-1",
        )
        test_session.add(run)
        test_session.commit()

        ingestor.ingest_files(run.id, [str(file_path)], test_session)
        test_session.commit()

        symbols = (
            test_session.query(PythonSymbol).filter(PythonSymbol.run_id == run.id).all()
        )

        # Should extract module + function
        assert len(symbols) >= 1
        func_symbol = next((s for s in symbols if s.symbol_type == "function"), None)
        assert func_symbol is not None
        assert func_symbol.symbol_name == "public_function"
        assert func_symbol.docstring is not None
        assert "A public function" in func_symbol.docstring

        # Verify signature metadata
        metadata = func_symbol.symbol_metadata
        assert metadata is not None
        assert metadata.get("is_public") is True

    def test_extract_class_with_methods(self, test_session, tmp_path):
        """Test extracting class with multiple methods."""
        code = '''
class APIClient:
    """HTTP API client."""
    
    def __init__(self, base_url: str):
        """Initialize client."""
        self.base_url = base_url
    
    def get(self, endpoint: str) -> dict:
        """GET request."""
        return {}
    
    def post(self, endpoint: str, data: dict) -> dict:
        """POST request."""
        return {}
'''
        file_path = tmp_path / "client.py"
        file_path.write_text(code)

        ingestor = PythonSymbolIngestor()
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="test-2",
        )
        test_session.add(run)
        test_session.commit()

        ingestor.ingest_files(run.id, [str(file_path)], test_session)
        test_session.commit()

        symbols = (
            test_session.query(PythonSymbol).filter(PythonSymbol.run_id == run.id).all()
        )

        # Should extract: module + class + 3 methods
        assert len(symbols) >= 4

        class_symbol = next((s for s in symbols if s.symbol_type == "class"), None)
        assert class_symbol is not None
        assert class_symbol.symbol_name == "APIClient"

        methods = [s for s in symbols if s.symbol_type == "method"]
        assert len(methods) >= 3
        method_names = {m.symbol_name for m in methods}
        assert "__init__" in method_names or "get" in method_names

    def test_extract_private_vs_public(self, test_session, tmp_path):
        """Test distinguishing private vs public symbols."""
        code = """
def public_func():
    pass

def _private_func():
    pass

class PublicClass:
    pass

class _PrivateClass:
    pass
"""
        file_path = tmp_path / "visibility.py"
        file_path.write_text(code)

        ingestor = PythonSymbolIngestor()
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="test-3",
        )
        test_session.add(run)
        test_session.commit()

        ingestor.ingest_files(run.id, [str(file_path)], test_session)
        test_session.commit()

        symbols = (
            test_session.query(PythonSymbol).filter(PythonSymbol.run_id == run.id).all()
        )

        # Check visibility in metadata (skip module symbols)
        for symbol in symbols:
            if symbol.symbol_type == "module":
                continue  # Module symbols don't have is_public metadata

            metadata = symbol.symbol_metadata or {}
            if symbol.symbol_name.startswith("_"):
                # Private symbols should have is_public=False in metadata
                assert metadata.get("is_public") is False
            else:
                # Public symbols should have is_public=True
                assert metadata.get("is_public") is True


class TestChangeDetection:
    """Comprehensive tests for change detection."""

    def test_detect_added_function(self):
        """Test detecting an added public function."""
        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[],
        )

        new_function = SymbolData(
            file_path="api.py",
            symbol_name="new_endpoint",
            symbol_type="function",
            signature=SignatureInfo(
                name="new_endpoint",
                parameters=[
                    ParameterInfo(name="id", annotation="int"),
                ],
                return_annotation="dict",
            ),
            is_public=True,
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[new_function],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "added"
        assert changes[0].symbol_name == "new_endpoint"
        assert changes[0].is_breaking is False  # Additions are not breaking

    def test_detect_removed_function(self):
        """Test detecting a removed public function (breaking change)."""
        removed_function = SymbolData(
            file_path="api.py",
            symbol_name="deprecated_endpoint",
            symbol_type="function",
            signature=SignatureInfo(
                name="deprecated_endpoint",
                parameters=[],
                return_annotation="dict",
            ),
            is_public=True,
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[removed_function],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "removed"
        assert changes[0].symbol_name == "deprecated_endpoint"
        assert changes[0].is_breaking is True  # Removals are always breaking

    def test_detect_parameter_type_change_breaking(self):
        """Test detecting parameter type change (breaking change)."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="process_data",
            symbol_type="function",
            signature=SignatureInfo(
                name="process_data",
                parameters=[
                    ParameterInfo(name="value", annotation="int"),
                ],
                return_annotation="int",
            ),
            is_public=True,
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="process_data",
            symbol_type="function",
            signature=SignatureInfo(
                name="process_data",
                parameters=[
                    ParameterInfo(name="value", annotation="str"),  # Type changed
                ],
                return_annotation="int",
            ),
            is_public=True,
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True
        assert changes[0].breaking_reason is not None
        assert (
            "parameter" in changes[0].breaking_reason.lower()
            or "type" in changes[0].breaking_reason.lower()
        )

    def test_detect_return_type_change_breaking(self):
        """Test detecting return type change (breaking change)."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="get_user",
            symbol_type="function",
            signature=SignatureInfo(
                name="get_user",
                parameters=[],
                return_annotation="dict",
            ),
            is_public=True,
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="get_user",
            symbol_type="function",
            signature=SignatureInfo(
                name="get_user",
                parameters=[],
                return_annotation="str",  # Return type changed
            ),
            is_public=True,
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True
        assert (
            "return" in changes[0].breaking_reason.lower()
            or "type" in changes[0].breaking_reason.lower()
        )

    def test_detect_parameter_removed_breaking(self):
        """Test detecting parameter removal (breaking change)."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="process",
            symbol_type="function",
            signature=SignatureInfo(
                name="process",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                    ParameterInfo(name="y", annotation="int"),
                ],
                return_annotation="int",
            ),
            is_public=True,
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="process",
            symbol_type="function",
            signature=SignatureInfo(
                name="process",
                parameters=[
                    ParameterInfo(name="x", annotation="int"),
                    # y parameter removed
                ],
                return_annotation="int",
            ),
            is_public=True,
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is True

    def test_detect_docstring_change_non_breaking(self):
        """Test detecting docstring change (non-breaking)."""
        previous_symbol = SymbolData(
            file_path="api.py",
            symbol_name="calculate",
            symbol_type="function",
            signature=SignatureInfo(
                name="calculate",
                parameters=[],
                return_annotation="int",
            ),
            docstring="Old docstring",
            is_public=True,
        )

        current_symbol = SymbolData(
            file_path="api.py",
            symbol_name="calculate",
            symbol_type="function",
            signature=SignatureInfo(
                name="calculate",
                parameters=[],
                return_annotation="int",
            ),
            docstring="New docstring",
            is_public=True,
        )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=[previous_symbol],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=[current_symbol],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].is_breaking is False  # Docstring changes are not breaking

    def test_detect_multiple_changes(self):
        """Test detecting multiple simultaneous changes."""
        previous_symbols = [
            SymbolData(
                file_path="api.py",
                symbol_name="func1",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func1",
                    parameters=[ParameterInfo(name="x", annotation="int")],
                    return_annotation="int",
                ),
                is_public=True,
            ),
            SymbolData(
                file_path="api.py",
                symbol_name="func2",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func2",
                    parameters=[],
                    return_annotation="str",
                ),
                is_public=True,
            ),
            SymbolData(
                file_path="api.py",
                symbol_name="old_func",
                symbol_type="function",
                signature=SignatureInfo(
                    name="old_func",
                    parameters=[],
                    return_annotation="None",
                ),
                is_public=True,
            ),
        ]

        current_symbols = [
            SymbolData(
                file_path="api.py",
                symbol_name="func1",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func1",
                    parameters=[
                        ParameterInfo(name="x", annotation="str")
                    ],  # Type changed
                    return_annotation="int",
                ),
                is_public=True,
            ),
            SymbolData(
                file_path="api.py",
                symbol_name="func2",
                symbol_type="function",
                signature=SignatureInfo(
                    name="func2",
                    parameters=[],
                    return_annotation="str",  # Unchanged
                ),
                is_public=True,
            ),
            SymbolData(
                file_path="api.py",
                symbol_name="new_func",
                symbol_type="function",
                signature=SignatureInfo(
                    name="new_func",
                    parameters=[],
                    return_annotation="dict",
                ),
                is_public=True,
            ),
        ]

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=previous_symbols,
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=current_symbols,
        )

        changes = detect_changes(previous_artifact, current_artifact)

        # Should detect: 1 removal, 1 addition, 1 modification
        assert len(changes) >= 2

        change_types = {c.change_type for c in changes}
        assert (
            "removed" in change_types
            or "added" in change_types
            or "modified" in change_types
        )

        # Verify at least one breaking change (removal or parameter type change)
        breaking_changes = [c for c in changes if c.is_breaking]
        assert len(breaking_changes) >= 1
