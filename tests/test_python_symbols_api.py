"""Integration tests for Python symbol API endpoints."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from db.models import PythonSymbol, Run
from db.session import SessionLocal


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_list_python_symbols_endpoint(client: TestClient):
    """Ensure the endpoint returns persisted symbol metadata."""
    session = SessionLocal()
    try:
        run = Run(
            repo="test/repo",
            branch="main",
            commit_sha="abc123",
            started_at=datetime.utcnow(),
            status="Awaiting Review",
            correlation_id="corr-123",
        )
        session.add(run)
        session.commit()

        symbol = PythonSymbol(
            run_id=run.id,
            file_path="src/example.py",
            symbol_name="foo",
            qualified_name="src/example.py::function::foo@3",
            symbol_type="function",
            docstring="Example function.",
            lineno=3,
            symbol_metadata={"decorators": [], "is_public": True},
        )
        session.add(symbol)
        session.commit()

        response = client.get(f"/api/v1/runs/{run.id}/python-symbols")
        assert response.status_code == 200

        payload = response.json()
        assert "items" in payload
        assert len(payload["items"]) == 1
        item = payload["items"][0]
        assert item["symbol_name"] == "foo"
        assert item["docstring"] == "Example function."
        assert item["symbol_metadata"]["is_public"] is True
    finally:
        session.query(PythonSymbol).delete()
        session.query(Run).delete()
        session.commit()
        session.close()

