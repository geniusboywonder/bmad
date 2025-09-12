"""Integration tests for Sprint 3 API endpoints."""

import pytest
import json
import asyncio
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.models.agent import AgentType, AgentStatus


class TestAgentStatusAPIIntegration:
    """Integration tests for Agent Status API - S3-INT-005, S3-INT-006, S3-INT-007, S3-INT-008."""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI app."""
        return TestClient(app)
    
    def test_get_all_agent_statuses_success(self, client):
        """Test GET /api/v1/agents/status returns all agents - S3-INT-005."""
        response = client.get("/api/v1/agents/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return status for all agent types
        expected_agents = [agent.value for agent in AgentType]
        assert len(data) == len(expected_agents)
        
        for agent_type in expected_agents:
            assert agent_type in data
            agent_status = data[agent_type]
            assert "agent_type" in agent_status
            assert "status" in agent_status
            assert "last_activity" in agent_status
            assert agent_status["agent_type"] == agent_type
    
    def test_get_specific_agent_status_success(self, client):
        """Test GET /api/v1/agents/status/{agent_type} returns agent - S3-INT-006."""
        agent_type = AgentType.ANALYST.value
        response = client.get(f"/api/v1/agents/status/{agent_type}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["agent_type"] == agent_type
        assert "status" in data
        assert "last_activity" in data
        assert "current_task_id" in data
        assert "error_message" in data
    
    def test_get_specific_agent_status_invalid_agent_type(self, client):
        """Test GET with invalid agent type returns 422 - S3-INT-008."""
        response = client.get("/api/v1/agents/status/invalid_agent")
        
        # FastAPI should return 422 for invalid enum value
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_reset_agent_status_success(self, client):
        """Test POST /api/v1/agents/status/{agent_type}/reset works - S3-INT-007.""" 
        agent_type = AgentType.TESTER.value
        
        with patch('app.api.agents.get_session') as mock_get_session:
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            response = client.post(f"/api/v1/agents/status/{agent_type}/reset")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "message" in data
            assert agent_type in data["message"]
            assert data["agent_type"] == agent_type
            assert data["status"] == "idle"
    
    def test_reset_agent_status_invalid_agent_type(self, client):
        """Test POST reset with invalid agent type returns 422 - S3-INT-008."""
        response = client.post("/api/v1/agents/status/invalid_agent/reset")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_agent_status_history_endpoint(self, client):
        """Test GET /api/v1/agents/status-history/{agent_type} works."""
        agent_type = AgentType.CODER.value
        
        with patch('app.api.agents.get_session') as mock_get_session:
            mock_db = Mock()
            mock_query = Mock()
            mock_record = Mock()
            
            # Configure mock database response
            mock_record.agent_type = agent_type
            mock_record.status = AgentStatus.WORKING.value
            mock_record.current_task_id = str(uuid4())
            mock_record.last_activity = datetime.now()
            mock_record.error_message = None
            mock_record.updated_at = datetime.now()
            
            mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_record]
            mock_db.query.return_value = mock_query
            mock_get_session.return_value = mock_db
            
            response = client.get(f"/api/v1/agents/status-history/{agent_type}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert isinstance(data, list)
            if data:  # If records returned
                record = data[0]
                assert "agent_type" in record
                assert "status" in record
                assert "updated_at" in record


class TestArtifactAPIIntegration:
    """Integration tests for Artifact Management API - S3-INT-014, S3-INT-015, S3-INT-016, S3-INT-017."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_project_id(self):
        return uuid4()
    
    def test_generate_artifacts_success(self, client, sample_project_id):
        """Test POST /api/v1/artifacts/{project_id}/generate works - S3-INT-014."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock artifact service
            mock_artifacts = [Mock(), Mock(), Mock()]  # 3 artifacts
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/test.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            response = client.post(f"/api/v1/artifacts/{sample_project_id}/generate")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == str(sample_project_id)
            assert data["status"] == "success"
            assert data["artifact_count"] == 3
            assert "Generated 3 artifacts successfully" in data["message"]
    
    def test_generate_artifacts_project_not_found(self, client, sample_project_id):
        """Test artifact generation with non-existent project returns 404."""
        with patch('app.api.artifacts.get_session') as mock_get_session:
            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_session.return_value = mock_db
            
            response = client.post(f"/api/v1/artifacts/{sample_project_id}/generate")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]
    
    def test_get_artifact_summary_success(self, client, sample_project_id):
        """Test GET /api/v1/artifacts/{project_id}/summary shows info - S3-INT-016."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock artifact service
            mock_artifact_1 = Mock()
            mock_artifact_1.name = "main.py"
            mock_artifact_1.file_type = "py"
            mock_artifact_1.created_at = datetime.now()
            
            mock_artifact_2 = Mock()
            mock_artifact_2.name = "README.md"
            mock_artifact_2.file_type = "md"
            mock_artifact_2.created_at = datetime.now()
            
            mock_artifacts = [mock_artifact_1, mock_artifact_2]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            
            # Mock ZIP file exists
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/summary")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == str(sample_project_id)
            assert data["project_name"] == "Test Project"
            assert data["artifact_count"] == 2
            assert data["download_available"] is True
            assert len(data["artifacts"]) == 2
            
            # Check artifact details
            assert data["artifacts"][0]["name"] == "main.py"
            assert data["artifacts"][0]["file_type"] == "py"
    
    def test_download_artifacts_success(self, client, sample_project_id):
        """Test GET /api/v1/artifacts/{project_id}/download serves ZIP - S3-INT-015."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service, \
             patch('app.api.artifacts.FileResponse') as mock_file_response:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock ZIP file exists
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            # Mock FileResponse
            mock_file_response.return_value = Mock()
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/download")
            
            # FileResponse doesn't work well with TestClient, check that it was called
            assert mock_file_response.called
            call_args = mock_file_response.call_args
            assert call_args[1]["filename"] == "Test_Project_artifacts.zip"
            assert call_args[1]["media_type"] == "application/zip"
    
    def test_download_artifacts_generates_if_missing(self, client, sample_project_id):
        """Test download generates artifacts if ZIP doesn't exist."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service, \
             patch('app.api.artifacts.FileResponse') as mock_file_response:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock ZIP file doesn't exist initially
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = False
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            # Mock artifact generation
            mock_artifacts = [Mock()]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/test.zip")
            
            # Mock FileResponse
            mock_file_response.return_value = Mock()
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/download")
            
            # Verify artifact generation was triggered
            mock_artifact_service.generate_project_artifacts.assert_called_once()
            mock_artifact_service.create_project_zip.assert_called_once()
    
    def test_cleanup_artifacts_success(self, client, sample_project_id):
        """Test DELETE /api/v1/artifacts/{project_id}/artifacts cleans - S3-INT-017."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock ZIP file exists
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_zip_path.unlink = Mock()
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            response = client.delete(f"/api/v1/artifacts/{sample_project_id}/artifacts")
            
            assert response.status_code == 200
            data = response.json()
            assert f"Artifacts cleaned up for project {sample_project_id}" in data["message"]
            
            # Verify cleanup was called
            mock_zip_path.unlink.assert_called_once()
    
    def test_cleanup_old_artifacts_admin(self, client):
        """Test POST /api/v1/artifacts/cleanup-old admin endpoint."""
        with patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            mock_artifact_service.cleanup_old_artifacts = Mock()
            
            response = client.post("/api/v1/artifacts/cleanup-old?max_age_hours=48")
            
            assert response.status_code == 200
            data = response.json()
            assert "Cleaned up artifacts older than 48 hours" in data["message"]
            
            # Verify cleanup was called with correct parameter
            mock_artifact_service.cleanup_old_artifacts.assert_called_once_with(48)


class TestProjectCompletionAPIIntegration:
    """Integration tests for Project Completion API."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_project_id(self):
        return uuid4()
    
    def test_get_completion_status_success(self, client, sample_project_id):
        """Test GET /api/v1/projects/{project_id}/completion works."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock completion service response
            mock_status = {
                "project_id": str(sample_project_id),
                "project_name": "Test Project",
                "completion_percentage": 75.0,
                "total_tasks": 4,
                "completed_tasks": 3,
                "is_complete": False
            }
            mock_completion_service.get_project_completion_status = AsyncMock(return_value=mock_status)
            
            response = client.get(f"/api/v1/projects/{sample_project_id}/completion")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == str(sample_project_id)
            assert data["completion_percentage"] == 75.0
            assert data["total_tasks"] == 4
            assert data["completed_tasks"] == 3
            assert data["is_complete"] is False
    
    def test_get_completion_status_project_not_found(self, client, sample_project_id):
        """Test completion status with non-existent project returns 404."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock service returns error
            mock_completion_service.get_project_completion_status = AsyncMock(
                return_value={"error": "Project not found"}
            )
            
            response = client.get(f"/api/v1/projects/{sample_project_id}/completion")
            
            assert response.status_code == 404
    
    def test_check_project_completion_success(self, client, sample_project_id):
        """Test POST /api/v1/projects/{project_id}/check-completion works."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock completion check returns True
            mock_completion_service.check_project_completion = AsyncMock(return_value=True)
            
            response = client.post(f"/api/v1/projects/{sample_project_id}/check-completion")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == str(sample_project_id)
            assert data["is_complete"] is True
            assert "and completed" in data["message"]
    
    def test_check_project_completion_not_complete(self, client, sample_project_id):
        """Test check completion when project is not complete."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock completion check returns False
            mock_completion_service.check_project_completion = AsyncMock(return_value=False)
            
            response = client.post(f"/api/v1/projects/{sample_project_id}/check-completion")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["is_complete"] is False
            assert "Project completion checked" in data["message"]
            assert "and completed" not in data["message"]
    
    def test_force_project_completion_success(self, client, sample_project_id):
        """Test POST /api/v1/projects/{project_id}/force-complete works."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock force completion succeeds
            mock_completion_service.force_project_completion = AsyncMock(return_value=True)
            
            response = client.post(f"/api/v1/projects/{sample_project_id}/force-complete")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["project_id"] == str(sample_project_id)
            assert data["status"] == "completed"
            assert "forced to completion" in data["message"]
    
    def test_force_project_completion_failure(self, client, sample_project_id):
        """Test force completion failure returns 400."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service:
            
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Mock force completion fails
            mock_completion_service.force_project_completion = AsyncMock(return_value=False)
            
            response = client.post(f"/api/v1/projects/{sample_project_id}/force-complete")
            
            assert response.status_code == 400
            data = response.json()
            assert "Failed to force project completion" in data["detail"]


class TestAPIErrorHandling:
    """Test API error handling - S3-UNIT-021."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_agent_status_api_database_error_handling(self, client):
        """Test graceful handling of database errors in agent API."""
        agent_type = AgentType.ANALYST.value
        
        with patch('app.api.agents.get_session') as mock_get_session:
            # Mock database connection failure
            mock_get_session.side_effect = Exception("Database connection failed")
            
            response = client.get(f"/api/v1/agents/status-history/{agent_type}")
            
            # Should return 500 with graceful error message
            assert response.status_code == 500
            data = response.json()
            assert "Failed to fetch agent status history" in data["detail"]
    
    def test_artifact_api_invalid_uuid_handling(self, client):
        """Test handling of invalid UUID parameters."""
        invalid_project_id = "not-a-uuid"
        
        response = client.post(f"/api/v1/artifacts/{invalid_project_id}/generate")
        
        # FastAPI should return 422 for invalid UUID
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_artifact_api_service_error_handling(self, client):
        """Test graceful handling of service errors in artifact API."""
        sample_project_id = uuid4()
        
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Mock database returns project
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock artifact service error
            mock_artifact_service.generate_project_artifacts = AsyncMock(
                side_effect=Exception("Artifact generation failed")
            )
            
            response = client.post(f"/api/v1/artifacts/{sample_project_id}/generate")
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to generate project artifacts" in data["detail"]


class TestAPIInputValidation:
    """Test API input validation - S3-UNIT-021."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cleanup_old_artifacts_parameter_validation(self, client):
        """Test parameter validation for cleanup endpoint."""
        # Test with invalid parameter type
        response = client.post("/api/v1/artifacts/cleanup-old?max_age_hours=not_a_number")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_cleanup_old_artifacts_negative_hours(self, client):
        """Test cleanup with negative hours parameter."""
        with patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            mock_artifact_service.cleanup_old_artifacts = Mock()
            
            # Negative hours should still work (processed as 0 or handled gracefully)
            response = client.post("/api/v1/artifacts/cleanup-old?max_age_hours=-1")
            
            # API should handle gracefully
            if response.status_code == 200:
                mock_artifact_service.cleanup_old_artifacts.assert_called_once_with(-1)
            else:
                # Or reject with validation error
                assert response.status_code == 422


class TestAPIPerformance:
    """Test API performance scenarios - S3-UNIT-018."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_all_agent_statuses_performance(self, client):
        """Test performance of getting all agent statuses."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/agents/status")
        end_time = time.time()
        
        # Should respond quickly (under 1 second for in-memory data)
        response_time = end_time - start_time
        assert response_time < 1.0
        assert response.status_code == 200
    
    def test_artifact_generation_timeout_handling(self, client):
        """Test handling of long-running artifact generation."""
        sample_project_id = uuid4()
        
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Mock database
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Mock slow artifact generation (simulated)
            async def slow_generation(*args, **kwargs):
                await asyncio.sleep(0.1)  # Small delay for test
                return [Mock(), Mock()]
            
            mock_artifact_service.generate_project_artifacts = slow_generation
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/test.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            response = client.post(f"/api/v1/artifacts/{sample_project_id}/generate")
            
            # Should handle async operations correctly
            assert response.status_code == 200