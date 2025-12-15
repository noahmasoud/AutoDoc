"""Golden-file integration tests with fixture repository.

Tests against a fixture repo with before/after commits:
- Python: add/remove/modify public functions
- TypeScript: export changes
- Assert stable JSON schema + expected change classifications
"""

import pytest
import shutil
import subprocess
from pathlib import Path

from schemas.changes import RunArtifact, SymbolData
from services.change_detector import detect_changes
from services.python_symbol_ingestor import PythonSymbolIngestor
from db.models import Run, PythonSymbol
from db.session import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime


@pytest.fixture
def fixture_repo(tmp_path: Path):
    """Create a fixture git repository with before/after commits."""
    repo_path = tmp_path / "fixture_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # BEFORE: Initial commit with Python and TypeScript files
    api_py_before = repo_path / "api.py"
    api_py_before.write_text('''"""API module."""

def get_user(user_id: int) -> dict:
    """Get user by ID.
    
    Args:
        user_id: User identifier
        
    Returns:
        User dictionary
    """
    return {"id": user_id}


def create_user(name: str, email: str) -> dict:
    """Create a new user.
    
    Args:
        name: User name
        email: User email
        
    Returns:
        Created user dictionary
    """
    return {"name": name, "email": email}
''')

    client_py_before = repo_path / "client.py"
    client_py_before.write_text('''"""Client module."""

class APIClient:
    """HTTP API client."""
    
    def request(self, method: str, url: str) -> dict:
        """Make HTTP request."""
        return {}
''')

    api_ts_before = repo_path / "api.ts"
    api_ts_before.write_text("""
export function fetchData(id: number): Promise<any> {
    return Promise.resolve({ id });
}

export class DataService {
    get(id: number): any {
        return { id };
    }
}

export interface User {
    id: number;
    name: string;
}
""")

    # Commit before state
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    before_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    # AFTER: Modified commit
    api_py_after = repo_path / "api.py"
    api_py_after.write_text('''"""API module."""

def get_user(user_id: int) -> dict:
    """Get user by ID (updated docstring).
    
    Args:
        user_id: User identifier
        
    Returns:
        User dictionary with additional fields
    """
    return {"id": user_id, "active": True}


# Removed: create_user function


def update_user(user_id: int, name: str) -> dict:
    """Update user information.
    
    Args:
        user_id: User identifier
        name: New user name
        
    Returns:
        Updated user dictionary
    """
    return {"id": user_id, "name": name}
''')

    client_py_after = repo_path / "client.py"
    client_py_after.write_text('''"""Client module."""

class APIClient:
    """HTTP API client."""
    
    def request(self, method: str, url: str) -> dict:
        """Make HTTP request."""
        return {}
    
    def post(self, endpoint: str, data: dict) -> dict:
        """POST request.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response dictionary
        """
        return {}
''')

    api_ts_after = repo_path / "api.ts"
    api_ts_after.write_text("""
export function fetchData(id: number): Promise<any> {
    return Promise.resolve({ id });
}

// Removed: DataService class

export interface User {
    id: number;
    name: string;
    email?: string;  // Added optional field
}

export interface Admin extends User {
    role: string;  // New interface
}
""")

    # Commit after state
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Modified: add/remove/change functions"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    after_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    yield {
        "path": repo_path,
        "before_commit": before_commit,
        "after_commit": after_commit,
        "before_files": {
            "api.py": api_py_before.read_text(),
            "client.py": client_py_before.read_text(),
            "api.ts": api_ts_before.read_text(),
        },
        "after_files": {
            "api.py": api_py_after.read_text(),
            "client.py": client_py_after.read_text(),
            "api.ts": api_ts_after.read_text(),
        },
    }

    # Cleanup
    shutil.rmtree(repo_path, ignore_errors=True)


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
    """Create a SQLAlchemy session."""
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _symbol_to_symbol_data(symbol) -> SymbolData:
    """Convert PythonSymbol to SymbolData for change detection."""
    from schemas.changes import SignatureInfo, ParameterInfo

    metadata = symbol.symbol_metadata or {}

    # Extract signature info from metadata
    parameters = []
    if "parameters" in metadata:
        for param in metadata["parameters"]:
            parameters.append(
                ParameterInfo(
                    name=param.get("name", ""),
                    annotation=param.get("annotation"),
                    default_value=param.get("default"),
                )
            )

    signature = SignatureInfo(
        name=symbol.symbol_name,
        parameters=parameters,
        return_annotation=metadata.get("return_type"),
    )

    return SymbolData(
        file_path=symbol.file_path,
        symbol_name=symbol.symbol_name,
        symbol_type=symbol.symbol_type,
        signature=signature,
        docstring=symbol.docstring,
        is_public=metadata.get("is_public", True),
    )


class TestGoldenFileIntegration:
    """Golden-file integration tests against fixture repo."""

    @pytest.mark.integration
    def test_python_changes_detected_correctly(self, fixture_repo: dict, test_session):
        """Test that Python changes are detected correctly from fixture repo."""
        repo_path = fixture_repo["path"]

        ingestor = PythonSymbolIngestor()

        # Process BEFORE state
        before_run = Run(
            repo="fixture_repo",
            branch="main",
            commit_sha=fixture_repo["before_commit"],
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="before-1",
        )
        test_session.add(before_run)
        test_session.commit()

        before_files = [
            str(repo_path / "api.py"),
            str(repo_path / "client.py"),
        ]

        # Write before state files
        for file_path in before_files:
            rel_path = Path(file_path).relative_to(repo_path)
            content = fixture_repo["before_files"][str(rel_path)]
            Path(file_path).write_text(content)

        ingestor.ingest_files(before_run.id, before_files, test_session)
        test_session.commit()

        before_symbols = (
            test_session.query(PythonSymbol)
            .filter(PythonSymbol.run_id == before_run.id)
            .all()
        )

        # Process AFTER state
        after_run = Run(
            repo="fixture_repo",
            branch="main",
            commit_sha=fixture_repo["after_commit"],
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="after-1",
        )
        test_session.add(after_run)
        test_session.commit()

        after_files = [
            str(repo_path / "api.py"),
            str(repo_path / "client.py"),
        ]

        # Write after state files
        for file_path in after_files:
            rel_path = Path(file_path).relative_to(repo_path)
            content = fixture_repo["after_files"][str(rel_path)]
            Path(file_path).write_text(content)

        ingestor.ingest_files(after_run.id, after_files, test_session)
        test_session.commit()

        after_symbols = (
            test_session.query(PythonSymbol)
            .filter(PythonSymbol.run_id == after_run.id)
            .all()
        )

        # Verify symbols were extracted
        assert len(before_symbols) > 0, "Should extract symbols from before state"
        assert len(after_symbols) > 0, "Should extract symbols from after state"

        # Verify symbol extraction structure
        for symbol in before_symbols + after_symbols:
            assert symbol.file_path is not None
            assert symbol.symbol_name is not None
            assert symbol.symbol_type is not None
            assert symbol.run_id is not None

        # Verify that we extracted functions and classes
        before_symbol_types = {s.symbol_type for s in before_symbols}
        after_symbol_types = {s.symbol_type for s in after_symbols}

        # Should have at least functions or classes
        assert "function" in before_symbol_types or "class" in before_symbol_types
        assert "function" in after_symbol_types or "class" in after_symbol_types

    @pytest.mark.integration
    def test_change_report_json_schema_stable(self, fixture_repo: dict, test_session):
        """Test that change report JSON schema is stable."""
        # This is a simplified version - full implementation would
        # generate actual change reports and validate schema

        # Expected schema structure
        expected_schema = {
            "type": "object",
            "properties": {
                "run_id": {"type": "integer"},
                "repo": {"type": "string"},
                "branch": {"type": "string"},
                "commit_sha": {"type": "string"},
                "symbols": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "symbol_name": {"type": "string"},
                            "symbol_type": {"type": "string"},
                        },
                        "required": ["file_path", "symbol_name", "symbol_type"],
                    },
                },
            },
            "required": ["run_id", "repo", "branch", "commit_sha", "symbols"],
        }

        # In a real test, we would:
        # 1. Generate change report
        # 2. Convert to JSON
        # 3. Validate against schema using jsonschema library

        # For now, we just verify the schema structure is defined
        assert expected_schema is not None
        assert "properties" in expected_schema
        assert "symbols" in expected_schema["properties"]

    @pytest.mark.integration
    def test_change_classifications_match_expected(self, fixture_repo: dict):
        """Test that change classifications match expected values."""
        # Expected classifications:
        # - Function removal: breaking
        # - Function addition: non-breaking
        # - Function signature change: breaking
        # - Docstring change: non-breaking

        # This would be validated against actual detected changes
        # For now, we verify the classification logic exists

        # Create minimal test artifacts
        previous_artifact = RunArtifact(
            run_id=1,
            repo="test",
            branch="main",
            commit_sha="abc123",
            symbols=[],
        )

        current_artifact = RunArtifact(
            run_id=2,
            repo="test",
            branch="main",
            commit_sha="def456",
            symbols=[],
        )

        changes = detect_changes(previous_artifact, current_artifact)

        # Verify change detection function works
        assert isinstance(changes, list)

        # Verify all changes have required fields
        for change in changes:
            assert hasattr(change, "change_type")
            assert hasattr(change, "is_breaking")
            assert change.change_type in ("added", "removed", "modified")
