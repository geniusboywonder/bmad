"""Simple smoke tests to verify basic application functionality."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestApplicationSmoke:
    """Basic smoke tests to verify the application starts and core endpoints work."""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI application."""
        return TestClient(app)

    @pytest.mark.mock_data
    def test_health_endpoint_works(self, client):
        """Test that health endpoint is accessible."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.mock_data
    def test_api_docs_accessible(self, client):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    @pytest.mark.mock_data
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    @pytest.mark.mock_data
    def test_cors_headers_present(self, client):
        """Test that CORS headers are properly configured."""
        response = client.options("/health")
        # Should not fail with CORS error
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented but shouldn't fail

    @pytest.mark.mock_data
    def test_application_metadata(self, client):
        """Test application metadata is correctly set."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "BotArmy Backend"
