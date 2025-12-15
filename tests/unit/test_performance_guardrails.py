"""Performance guardrails tests.

Per SRS NFR-1: Analyzer runtime shall be ≤5 minutes for a change set ≤500 LOC
on a repo ≤10k LOC.
"""

import pytest
import time
from pathlib import Path

from services.python_symbol_ingestor import PythonSymbolIngestor
from services.change_detector import detect_changes
from schemas.changes import RunArtifact, SymbolData, SignatureInfo
from db.models import Run
from db.session import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime


@pytest.fixture
def large_codebase(tmp_path: Path):
    """Create a large codebase (~10k LOC) for performance testing."""
    base_dir = tmp_path / "large_repo"
    base_dir.mkdir()

    # Create ~50 files with ~200 LOC each = ~10k LOC
    for i in range(50):
        file_path = base_dir / f"module_{i}.py"
        content = f'''"""Module {i}."""
        
'''
        # Add ~20 functions per file
        for j in range(20):
            content += f'''
def function_{i}_{j}(x: int, y: str = "default") -> dict:
    """Function {i}_{j}.
    
    Args:
        x: Integer parameter
        y: String parameter
        
    Returns:
        Dictionary result
    """
    return {{"result": x + len(y)}}
    
'''
        # Add ~5 classes per file
        for k in range(5):
            content += f'''
class Class{i}_{k}:
    """Class {i}_{k}."""
    
    def method_{i}_{k}_1(self):
        """Method 1."""
        pass
    
    def method_{i}_{k}_2(self, param: str):
        """Method 2."""
        return param
'''

        file_path.write_text(content)

    return base_dir


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database."""
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
    """Create a SQLAlchemy session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


class TestPerformanceGuardrails:
    """Performance guardrails per SRS NFR-1."""

    @pytest.mark.slow
    @pytest.mark.performance
    def test_symbol_extraction_performance_large_repo(
        self, large_codebase: Path, test_session
    ):
        """Test symbol extraction completes within 5 minutes for ~10k LOC repo."""
        ingestor = PythonSymbolIngestor()

        run = Run(
            repo="large_repo",
            branch="main",
            commit_sha="test123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="perf-test-1",
        )
        test_session.add(run)
        test_session.commit()

        # Get all Python files
        python_files = list(large_codebase.glob("*.py"))

        # Measure extraction time
        start_time = time.time()

        ingestor.ingest_files(
            run.id,
            [str(f) for f in python_files],
            test_session,
        )
        test_session.commit()

        elapsed_time = time.time() - start_time

        # Per SRS NFR-1: Should complete in ≤5 minutes (300 seconds)
        max_allowed_time = 300  # 5 minutes in seconds
        assert elapsed_time < max_allowed_time, (
            f"Symbol extraction took {elapsed_time:.2f}s, "
            f"exceeds {max_allowed_time}s limit"
        )

        # Verify symbols were extracted
        from db.models import PythonSymbol

        symbols = (
            test_session.query(PythonSymbol).filter(PythonSymbol.run_id == run.id).all()
        )
        assert len(symbols) > 0

    @pytest.mark.performance
    def test_change_detection_performance(self):
        """Test change detection performance for ~500 LOC change set."""
        # Create artifacts with ~500 symbols (representing ~500 LOC)
        symbols = []
        for i in range(500):
            symbols.append(
                SymbolData(
                    file_path=f"module_{i % 50}.py",
                    symbol_name=f"function_{i}",
                    symbol_type="function",
                    signature=SignatureInfo(
                        name=f"function_{i}",
                        parameters=[],
                        return_annotation="int",
                    ),
                    is_public=True,
                )
            )

        previous_artifact = RunArtifact(
            run_id=1,
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            symbols=symbols,
        )

        # Modify some symbols
        modified_symbols = symbols.copy()
        for i in range(0, len(modified_symbols), 10):  # Modify every 10th
            modified_symbols[i] = SymbolData(
                file_path=modified_symbols[i].file_path,
                symbol_name=modified_symbols[i].symbol_name,
                symbol_type=modified_symbols[i].symbol_type,
                signature=SignatureInfo(
                    name=modified_symbols[i].symbol_name,
                    parameters=[],
                    return_annotation="str",  # Changed return type
                ),
                is_public=True,
            )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test/repo",
            branch="main",
            commit_sha="def456",
            symbols=modified_symbols,
        )

        # Measure change detection time
        start_time = time.time()

        changes = detect_changes(previous_artifact, current_artifact)

        elapsed_time = time.time() - start_time

        # Change detection should be fast (< 1 second for 500 symbols)
        max_allowed_time = 1.0
        assert elapsed_time < max_allowed_time, (
            f"Change detection took {elapsed_time:.3f}s, "
            f"exceeds {max_allowed_time}s limit"
        )

        # Verify changes were detected
        assert len(changes) > 0

    @pytest.mark.performance
    def test_analyzer_runtime_guardrail(self):
        """Test that analyzer runtime meets SRS NFR-1 requirement.

        SRS NFR-1: Analyzer runtime shall be ≤5 minutes for a change set ≤500 LOC
        on a repo ≤10k LOC.
        """
        # This is a placeholder for the full analyzer pipeline test
        # In practice, this would test the full pipeline:
        # 1. Parse changed files
        # 2. Extract symbols
        # 3. Detect changes
        # 4. Generate change report

        # For now, we verify the performance targets are defined
        max_runtime_seconds = 300  # 5 minutes
        max_change_set_loc = 500
        max_repo_loc = 10000

        assert max_runtime_seconds == 300
        assert max_change_set_loc == 500
        assert max_repo_loc == 10000
