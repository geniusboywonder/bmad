"""Health check endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_detailed_health_check():
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    # This might return 503 if database/Redis are not available
    assert response.status_code in [200, 503]
    data = response.json()
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
    assert "celery" in data["components"]


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    # This might return 503 if services are not ready
    assert response.status_code in [200, 503]
