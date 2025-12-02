"""Integration tests for template API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from api.main import create_app
from db.models import Base, Template
from db.session import get_db


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
def test_session(test_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(test_session):
    """Create a test client with test database."""
    app = create_app()

    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestTemplateAPI:
    """Tests for template API endpoints."""

    def test_create_template(self, client, test_session):
        """Test creating a template."""
        response = client.post(
            "/api/v1/templates",
            json={
                "name": "test_template",
                "format": "Markdown",
                "body": "Hello {{name}}!",
                "variables": None,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_template"
        assert data["format"] == "Markdown"
        assert data["body"] == "Hello {{name}}!"

    def test_get_template(self, client, test_session):
        """Test getting a template."""
        # Create a template
        template = Template(
            name="test_template",
            format="Markdown",
            body="Hello {{name}}!",
            variables=None,
        )
        test_session.add(template)
        test_session.commit()

        response = client.get(f"/api/v1/templates/{template.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_template"
        assert data["body"] == "Hello {{name}}!"

    def test_preview_template_with_template_id(self, client, test_session):
        """Test preview endpoint with template_id."""
        # Create a template
        template = Template(
            name="test_template",
            format="Markdown",
            body="Hello {{name}}! Welcome to {{project}}.",
            variables=None,
        )
        test_session.add(template)
        test_session.commit()

        response = client.post(
            "/api/v1/templates/preview",
            json={
                "template_id": template.id,
                "variables": {"name": "World", "project": "AutoDoc"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rendered"] == "Hello World! Welcome to AutoDoc."
        assert data["template_id"] == template.id

    def test_preview_template_with_template_body(self, client):
        """Test preview endpoint with template body."""
        response = client.post(
            "/api/v1/templates/preview",
            json={
                "template_body": "The function {{symbol.name}} is in {{symbol.file_path}}.",
                "template_format": "Markdown",
                "variables": {
                    "symbol": {"name": "process_request", "file_path": "src/api.py"}
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rendered"] == "The function process_request is in src/api.py."
        assert data["template_id"] is None

    def test_preview_template_missing_variables(self, client, test_session):
        """Test preview with missing variables (should leave placeholders)."""
        template = Template(
            name="test_template",
            format="Markdown",
            body="Hello {{name}}, status is {{status}}.",
            variables=None,
        )
        test_session.add(template)
        test_session.commit()

        response = client.post(
            "/api/v1/templates/preview",
            json={
                "template_id": template.id,
                "variables": {"name": "World"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Hello World" in data["rendered"]
        assert "{{status}}" in data["rendered"]

    def test_preview_template_invalid_format(self, client):
        """Test preview with invalid template format."""
        response = client.post(
            "/api/v1/templates/preview",
            json={
                "template_body": "Hello {{name}}!",
                "template_format": "InvalidFormat",
                "variables": {"name": "World"},
            },
        )
        assert response.status_code == 400

    def test_preview_template_missing_required_fields(self, client):
        """Test preview with missing required fields."""
        # Missing both template_id and template_body
        response = client.post(
            "/api/v1/templates/preview",
            json={"variables": {"name": "World"}},
        )
        assert response.status_code == 400

    def test_preview_template_not_found(self, client):
        """Test preview with non-existent template_id."""
        response = client.post(
            "/api/v1/templates/preview",
            json={"template_id": 99999, "variables": {"name": "World"}},
        )
        assert response.status_code == 404

    def test_list_templates(self, client, test_session):
        """Test listing templates."""
        # Create multiple templates
        template1 = Template(
            name="template1",
            format="Markdown",
            body="Template 1",
            variables=None,
        )
        template2 = Template(
            name="template2",
            format="Storage",
            body="Template 2",
            variables=None,
        )
        test_session.add_all([template1, template2])
        test_session.commit()

        response = client.get("/api/v1/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [t["name"] for t in data]
        assert "template1" in names
        assert "template2" in names
