"""
Integration tests for phase policy enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import get_session, Base

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_client(db_session):
    """Create a test client that uses the test database."""
    def override_get_session():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as client:
        yield client

def test_create_task_policy_denied(test_client):
    # Create a project
    response = test_client.post("/projects/", json={"name": "Test Project"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Attempt to create a task with an agent not allowed in the discovery phase
    response = test_client.post(
        f"/projects/{project_id}/tasks",
        json={"agent_type": "coder", "instructions": "implement feature"}
    )
    assert response.status_code == 400
    assert "Agent 'coder' is not allowed in the 'discovery' phase." in response.json()["detail"]

def test_create_task_policy_needs_clarification(test_client):
    # Create a project
    response = test_client.post("/projects/", json={"name": "Test Project"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Attempt to create a task with a mismatched prompt
    response = test_client.post(
        f"/projects/{project_id}/tasks",
        json={"agent_type": "analyst", "instructions": "write code"}
    )
    assert response.status_code == 400
    assert "Instructions do not seem to match the 'discovery' phase." in response.json()["detail"]

def test_create_task_policy_allowed(test_client):
    # Create a project
    response = test_client.post("/projects/", json={"name": "Test Project"})
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Attempt to create a valid task
    response = test_client.post(
        f"/projects/{project_id}/tasks",
        json={"agent_type": "analyst", "instructions": "gather requirements"}
    )
    assert response.status_code == 201
