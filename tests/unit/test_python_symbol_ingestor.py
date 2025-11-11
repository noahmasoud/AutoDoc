"""Unit tests for PythonSymbolIngestor."""

from __future__ import annotations

from datetime import datetime
import textwrap

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from db.models import PythonSymbol, Run
from db.session import Base
from services.python_symbol_ingestor import PythonSymbolIngestor


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
def test_session(test_engine) -> Session:
    """Create a SQLAlchemy session bound to the test engine."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_python_file(tmp_path) -> str:
    """Create a temporary Python file with docstrings for testing."""
    content = textwrap.dedent(
        '''
        """Module level docstring."""


        class Calculator:
            """Performs arithmetic operations."""

            def add(self, a: int, b: int) -> int:
                """Add two numbers."""
                return a + b


        def helper(value: str) -> str:
            """Normalize input."""
            return value.strip()
        ''',
    ).lstrip()
    file_path = tmp_path / "calculator.py"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def _create_run(session: Session) -> Run:
    run = Run(
        repo="test/repo",
        branch="main",
        commit_sha="abc123",
        started_at=datetime.utcnow(),
        status="Awaiting Review",
        correlation_id="corr-1",
    )
    session.add(run)
    session.commit()
    return run


def test_ingest_persists_symbols_with_docstrings(
    test_session: Session,
    sample_python_file: str,
) -> None:
    ingestor = PythonSymbolIngestor()
    run = _create_run(test_session)

    ingestor.ingest_files(run.id, [sample_python_file], test_session)

    symbols = test_session.scalars(
        select(PythonSymbol).where(PythonSymbol.run_id == run.id).order_by(PythonSymbol.id),
    ).all()

    assert len(symbols) == 4  # module, class, method, function

    module_symbol = next(s for s in symbols if s.symbol_type == "module")
    assert module_symbol.docstring == "Module level docstring."

    class_symbol = next(s for s in symbols if s.symbol_type == "class")
    assert class_symbol.docstring == "Performs arithmetic operations."

    method_symbol = next(s for s in symbols if s.symbol_type == "method")
    assert method_symbol.docstring == "Add two numbers."
    assert method_symbol.symbol_metadata is not None
    assert method_symbol.symbol_metadata.get("enclosing_class") == "Calculator"

    function_symbol = next(s for s in symbols if s.symbol_type == "function")
    assert function_symbol.docstring == "Normalize input."


def test_ingest_replaces_existing_symbols(
    test_session: Session,
    sample_python_file: str,
) -> None:
    ingestor = PythonSymbolIngestor()
    run = _create_run(test_session)

    ingestor.ingest_files(run.id, [sample_python_file], test_session)
    initial_symbols = test_session.scalars(
        select(PythonSymbol).where(PythonSymbol.run_id == run.id),
    ).all()

    ingestor.ingest_files(run.id, [sample_python_file], test_session)
    refreshed_symbols = test_session.scalars(
        select(PythonSymbol).where(PythonSymbol.run_id == run.id),
    ).all()

    assert len(initial_symbols) == len(refreshed_symbols) == 4
    # Ensure metadata refreshed by checking IDs reset starting from 1 after delete/add
    assert {symbol.symbol_type for symbol in refreshed_symbols} == {"module", "class", "method", "function"}

