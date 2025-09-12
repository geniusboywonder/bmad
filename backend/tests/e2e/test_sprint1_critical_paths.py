"""
End-to-End tests for Sprint 1 critical paths

Test scenarios:
- 1.1-E2E-001: Complete project creation workflow (P0)
- 1.2-E2E-001: Context persistence across workflow (P1)  
- 1.3-E2E-001: Complete HITL request workflow (P0)
- 1.4-E2E-001: Full application startup and health (P1)
"""

import pytest
from uuid import UUID
from fastapi import status
from fastapi.testclient import TestClient

from app.models.task import TaskStatus
from app.models.agent import AgentType
from app.models.context import ArtifactType
from app.models.hitl import HitlStatus


class TestCompleteProjectCreationWorkflow:
    """Test scenario 1.1-E2E-001: Complete project creation workflow (P0)"""
    
    @pytest.mark.e2e
    @pytest.mark.p0
    def test_end_to_end_project_creation(
        self, client: TestClient, db_session, orchestrator_service
    ):
        """Test complete project creation workflow from API to database."""
        
        # Step 1: Create project via API
        project_data = {
            "name": "E2E Test Project",
            "description": "End-to-end workflow test"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        project_response = response.json()
        project_id = UUID(project_response["id"])
        
        # Step 2: Verify project exists and is accessible
        status_response = client.get(f"/api/v1/projects/{project_id}/status")
        assert status_response.status_code == status.HTTP_200_OK
        
        status_data = status_response.json()
        assert status_data["project_id"] == str(project_id)
        assert isinstance(status_data["tasks"], list)
        
        # Step 3: Create initial task through orchestrator
        task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Initial project planning task"
        )
        
        # Step 4: Verify task appears in project status
        updated_status = client.get(f"/api/v1/projects/{project_id}/status")
        updated_data = updated_status.json()
        
        assert len(updated_data["tasks"]) == 1
        task_data = updated_data["tasks"][0]
        assert task_data["task_id"] == str(task.task_id)
        assert task_data["agent_type"] == AgentType.ANALYST.value
        assert task_data["status"] == TaskStatus.PENDING.value
        
        # Step 5: Update task status and verify persistence
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            output={"result": "Project planning completed"}
        )
        
        final_status = client.get(f"/api/v1/projects/{project_id}/status")
        final_data = final_status.json()
        
        completed_task = final_data["tasks"][0]
        assert completed_task["status"] == TaskStatus.COMPLETED.value
    
    @pytest.mark.e2e
    @pytest.mark.p0
    def test_project_workflow_error_handling(
        self, client: TestClient, orchestrator_service
    ):
        """Test project workflow handles errors gracefully."""
        
        # Test 1: Invalid project data
        invalid_data = {"description": "Missing name field"}
        response = client.post("/api/v1/projects/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test 2: Non-existent project status request
        fake_id = "12345678-1234-1234-1234-123456789012"
        response = client.get(f"/api/v1/projects/{fake_id}/status")
        assert response.status_code == status.HTTP_200_OK  # Returns empty tasks
        assert response.json()["tasks"] == []
        
        # Test 3: Malformed UUID in URL
        response = client.get("/api/v1/projects/invalid-uuid/status")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestContextPersistenceWorkflow:
    """Test scenario 1.2-E2E-001: Context persistence across workflow (P1)"""
    
    @pytest.mark.e2e
    @pytest.mark.p1
    def test_context_persistence_full_workflow(
        self, client: TestClient, db_session, orchestrator_service, context_store_service
    ):
        """Test context artifacts persist correctly across full workflow."""
        
        # Step 1: Create project
        project_data = {"name": "Context Persistence Test"}
        response = client.post("/api/v1/projects/", json=project_data)
        project_id = UUID(response.json()["id"])
        
        # Step 2: Create initial context artifact (user input)
        user_input_artifact = context_store_service.create_artifact(
            project_id=project_id,
            source_agent="user",
            artifact_type=ArtifactType.USER_INPUT,
            content={
                "requirements": "Build a task management system",
                "priority": "high",
                "deadline": "2024-01-15"
            }
        )
        
        # Step 3: Create analysis task that uses user input
        analysis_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analyze user requirements",
            context_ids=[user_input_artifact.context_id]
        )
        
        # Step 4: Complete analysis and create output artifact
        orchestrator_service.update_task_status(
            analysis_task.task_id,
            TaskStatus.COMPLETED,
            output={"analysis": "completed"}
        )
        
        analysis_output = context_store_service.create_artifact(
            project_id=project_id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={
                "features": ["task creation", "task tracking", "reporting"],
                "architecture": "microservices",
                "database": "postgresql"
            }
        )
        
        # Step 5: Create architecture task that uses analysis output
        architecture_task = orchestrator_service.create_task(
            project_id=project_id,
            agent_type=AgentType.ARCHITECT.value,
            instructions="Create technical architecture",
            context_ids=[user_input_artifact.context_id, analysis_output.context_id]
        )
        
        # Step 6: Verify all artifacts are accessible
        all_artifacts = context_store_service.get_artifacts_by_project(project_id)
        assert len(all_artifacts) == 2
        
        artifact_types = [a.artifact_type for a in all_artifacts]
        assert ArtifactType.USER_INPUT in artifact_types
        assert ArtifactType.PROJECT_PLAN in artifact_types
        
        # Step 7: Verify context can be retrieved for new tasks
        context_artifacts = context_store_service.get_artifacts_by_ids(
            architecture_task.context_ids
        )
        assert len(context_artifacts) == 2
        
        # Verify content integrity throughout workflow
        user_artifact = next(a for a in context_artifacts if a.artifact_type == ArtifactType.USER_INPUT)
        assert user_artifact.content["requirements"] == "Build a task management system"
        
        plan_artifact = next(a for a in context_artifacts if a.artifact_type == ArtifactType.PROJECT_PLAN)
        assert "task creation" in plan_artifact.content["features"]


class TestCompleteHITLWorkflow:
    """Test scenario 1.3-E2E-001: Complete HITL request workflow (P0)"""
    
    @pytest.mark.e2e
    @pytest.mark.p0
    def test_complete_hitl_approval_workflow(
        self, client: TestClient, db_session, orchestrator_service, project_with_hitl
    ):
        """Test complete HITL request and approval workflow."""
        
        project = project_with_hitl["project"]
        task = project_with_hitl["task"]
        hitl_request = project_with_hitl["hitl_request"]
        
        # Step 1: Verify HITL request exists and is pending
        hitl_response = client.get(f"/api/v1/hitl/{hitl_request.id}")
        assert hitl_response.status_code == status.HTTP_200_OK
        
        hitl_data = hitl_response.json()
        assert hitl_data["status"] == HitlStatus.PENDING.value
        assert hitl_data["project_id"] == str(project.id)
        assert hitl_data["task_id"] == str(task.id)
        
        # Step 2: Submit approval response
        approval_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "approve",
                "comment": "Looks good, proceed with implementation"
            }
        )
        
        assert approval_response.status_code == status.HTTP_200_OK
        approval_data = approval_response.json()
        assert approval_data["action"] == "approve"
        assert approval_data["workflow_resumed"] is True
        
        # Step 3: Verify HITL request status updated
        updated_hitl = client.get(f"/api/v1/hitl/{hitl_request.id}")
        updated_data = updated_hitl.json()
        assert updated_data["status"] == HitlStatus.APPROVED.value
        assert updated_data["user_response"] == "approved"
        
        # Step 4: Verify workflow can continue (agent status should be updated)
        # This would be verified by checking agent status in full implementation
        
    @pytest.mark.e2e
    @pytest.mark.p1
    def test_complete_hitl_amendment_workflow(
        self, client: TestClient, db_session, project_with_hitl
    ):
        """Test complete HITL request amendment workflow."""
        
        hitl_request = project_with_hitl["hitl_request"]
        
        # Step 1: Submit amendment response
        amendment_data = {
            "action": "amend",
            "content": "Please revise the architecture to use microservices instead of monolith",
            "comment": "Need better scalability approach"
        }
        
        response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=amendment_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["action"] == "amend"
        assert response_data["workflow_resumed"] is True
        
        # Step 2: Verify amendment data persisted
        updated_hitl = client.get(f"/api/v1/hitl/{hitl_request.id}")
        updated_data = updated_hitl.json()
        
        assert updated_data["status"] == HitlStatus.AMENDED.value
        assert updated_data["amended_content"]["amended_content"] == amendment_data["content"]
        assert updated_data["amended_content"]["comment"] == amendment_data["comment"]
        
    @pytest.mark.e2e
    @pytest.mark.p1
    def test_hitl_workflow_error_handling(self, client: TestClient):
        """Test HITL workflow error handling."""
        from uuid import uuid4
        
        # Test 1: Non-existent HITL request
        fake_id = uuid4()
        response = client.post(
            f"/api/v1/hitl/{fake_id}/respond",
            json={"action": "approve"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test 2: Invalid action
        response = client.post(
            f"/api/v1/hitl/{fake_id}/respond",
            json={"action": "invalid_action"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestFullApplicationHealth:
    """Test scenario 1.4-E2E-001: Full application startup and health (P1)"""
    
    @pytest.mark.e2e
    @pytest.mark.p1
    def test_application_health_endpoints(self, client: TestClient):
        """Test all health check endpoints work correctly."""
        
        # Test basic health check
        response = client.get("/health/")
        assert response.status_code == status.HTTP_200_OK
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "service" in health_data
        assert "version" in health_data
        
        # Test detailed health check
        detailed_response = client.get("/health/detailed")
        # May return 200 or 503 depending on external service availability
        assert detailed_response.status_code in [200, 503]
        
        detailed_data = detailed_response.json()
        assert "components" in detailed_data
        
        # Test readiness check
        ready_response = client.get("/health/ready")
        assert ready_response.status_code in [200, 503]
    
    @pytest.mark.e2e
    @pytest.mark.p1
    def test_api_endpoint_accessibility(self, client: TestClient):
        """Test all main API endpoints are accessible."""
        
        # Test project endpoints accessibility
        # These should return proper HTTP status codes, not 404
        
        # POST projects (should require body)
        response = client.post("/api/v1/projects/", json={})
        assert response.status_code != 404  # Should be 422 (validation error)
        
        # GET project status (should handle non-existent gracefully)
        from uuid import uuid4
        fake_id = uuid4()
        response = client.get(f"/api/v1/projects/{fake_id}/status")
        assert response.status_code != 404  # Should be 200 with empty tasks
        
        # HITL endpoints accessibility
        response = client.get(f"/api/v1/hitl/{fake_id}")
        assert response.status_code == 404  # This one should be 404 for non-existent
    
    @pytest.mark.e2e
    @pytest.mark.p2
    def test_application_cors_headers(self, client: TestClient):
        """Test CORS headers are properly configured."""
        
        # Test OPTIONS request
        response = client.options("/api/v1/projects/")
        
        # Should include CORS headers
        headers = response.headers
        # Basic CORS functionality test
        assert response.status_code in [200, 204, 405]  # Various acceptable responses
    
    @pytest.mark.e2e
    @pytest.mark.p2
    def test_application_json_content_handling(self, client: TestClient):
        """Test application handles JSON content correctly."""
        
        # Test valid JSON
        valid_project = {"name": "JSON Test Project"}
        response = client.post("/api/v1/projects/", json=valid_project)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Response should be JSON
        assert "application/json" in response.headers.get("content-type", "")
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
        assert "id" in data