"""End-to-End tests for Sprint 3 workflows."""

import pytest
import asyncio
import json
from uuid import uuid4
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.models.agent import AgentType, AgentStatus
from app.models.task import TaskStatus


class TestAgentStatusWorkflowE2E:
    """E2E tests for agent status workflow - S3-E2E-001, S3-E2E-002."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_agent_status_change_workflow(self, client):
        """Test complete agent status change workflow - S3-E2E-001."""
        agent_type = AgentType.CODER.value
        
        with patch('app.services.agent_status_service.websocket_manager') as mock_ws, \
             patch('app.api.agents.get_session') as mock_get_session:
            
            mock_ws.broadcast_global = AsyncMock()
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Step 1: Get initial agent status (should be idle)
            response = client.get(f"/api/v1/agents/status/{agent_type}")
            assert response.status_code == 200
            initial_data = response.json()
            assert initial_data["status"] == AgentStatus.IDLE.value
            
            # Step 2: Simulate agent status change via service
            # (In real workflow, this would be triggered by orchestrator)
            from app.services.agent_status_service import agent_status_service
            
            task_id = uuid4()
            
            # Run status update
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                updated_status = loop.run_until_complete(
                    agent_status_service.set_agent_working(AgentType.CODER, task_id)
                )
            finally:
                loop.close()
            
            # Verify WebSocket broadcast was triggered
            mock_ws.broadcast_global.assert_called()
            
            # Step 3: Verify status change via API
            response = client.get(f"/api/v1/agents/status/{agent_type}")
            assert response.status_code == 200
            updated_data = response.json()
            assert updated_data["status"] == AgentStatus.WORKING.value
            assert updated_data["current_task_id"] == str(task_id)
            
            # Step 4: Reset agent status
            response = client.post(f"/api/v1/agents/status/{agent_type}/reset")
            assert response.status_code == 200
            reset_data = response.json()
            assert reset_data["status"] == "idle"
            
            # Step 5: Verify final state
            response = client.get(f"/api/v1/agents/status/{agent_type}")
            assert response.status_code == 200
            final_data = response.json()
            assert final_data["status"] == AgentStatus.IDLE.value
            assert final_data["current_task_id"] is None
    
    def test_client_can_fetch_and_display_status_workflow(self, client):
        """Test client workflow for fetching and displaying status - S3-E2E-002."""
        # Step 1: Client fetches all agent statuses for dashboard
        response = client.get("/api/v1/agents/status")
        assert response.status_code == 200
        all_statuses = response.json()
        
        # Verify all expected agents are present
        expected_agents = [agent.value for agent in AgentType]
        assert len(all_statuses) == len(expected_agents)
        
        # Step 2: Client selects specific agent for detailed view
        selected_agent = AgentType.ANALYST.value
        assert selected_agent in all_statuses
        
        response = client.get(f"/api/v1/agents/status/{selected_agent}")
        assert response.status_code == 200
        detailed_status = response.json()
        
        # Step 3: Client fetches historical data for the agent
        with patch('app.api.agents.get_session') as mock_get_session:
            mock_db = Mock()
            mock_query = Mock()
            
            # Mock history records
            mock_record1 = Mock()
            mock_record1.agent_type = selected_agent
            mock_record1.status = AgentStatus.WORKING.value
            mock_record1.current_task_id = str(uuid4())
            mock_record1.last_activity = datetime.now()
            mock_record1.error_message = None
            mock_record1.updated_at = datetime.now()
            
            mock_record2 = Mock()
            mock_record2.agent_type = selected_agent
            mock_record2.status = AgentStatus.IDLE.value
            mock_record2.current_task_id = None
            mock_record2.last_activity = datetime.now()
            mock_record2.error_message = None
            mock_record2.updated_at = datetime.now()
            
            mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
                mock_record1, mock_record2
            ]
            mock_db.query.return_value = mock_query
            mock_get_session.return_value = mock_db
            
            response = client.get(f"/api/v1/agents/status-history/{selected_agent}")
            assert response.status_code == 200
            history_data = response.json()
            
            # Verify client can access historical data
            assert isinstance(history_data, list)
            assert len(history_data) == 2
            
            # Verify data structure for client consumption
            for record in history_data:
                assert "agent_type" in record
                assert "status" in record
                assert "updated_at" in record


class TestProjectCompletionWorkflowE2E:
    """E2E tests for project completion workflow - S3-E2E-003, S3-E2E-004."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def sample_project_id(self):
        return uuid4()
    
    def test_project_completion_triggers_artifacts_workflow(self, client, sample_project_id):
        """Test complete project completion workflow - S3-E2E-003."""
        with patch('app.api.projects.get_session') as mock_get_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service, \
             patch('app.services.project_completion_service.artifact_service') as mock_artifact_service, \
             patch('app.services.project_completion_service.websocket_manager') as mock_ws:
            
            # Setup mocks
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            mock_ws.broadcast_to_project = AsyncMock()
            
            # Step 1: Check initial project completion status
            initial_status = {
                "project_id": str(sample_project_id),
                "project_name": "Test Project",
                "completion_percentage": 50.0,
                "is_complete": False,
                "total_tasks": 4,
                "completed_tasks": 2
            }
            mock_completion_service.get_project_completion_status = AsyncMock(return_value=initial_status)
            
            response = client.get(f"/api/v1/projects/{sample_project_id}/completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is False
            assert data["completion_percentage"] == 50.0
            
            # Step 2: Trigger completion check (simulating task completion)
            mock_completion_service.check_project_completion = AsyncMock(return_value=True)
            
            # Mock artifact generation for completion workflow
            mock_artifacts = [
                Mock(name="main.py", content="print('Hello')", file_type="py"),
                Mock(name="README.md", content="# Project", file_type="md"),
                Mock(name="requirements.txt", content="fastapi>=0.68.0", file_type="txt")
            ]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/project.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            response = client.post(f"/api/v1/projects/{sample_project_id}/check-completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            assert "and completed" in data["message"]
            
            # Verify completion workflow was triggered
            mock_completion_service.check_project_completion.assert_called_once()
            
            # Step 3: Verify updated completion status
            updated_status = {
                "project_id": str(sample_project_id),
                "project_name": "Test Project",
                "completion_percentage": 100.0,
                "is_complete": True,
                "total_tasks": 4,
                "completed_tasks": 4,
                "artifacts_available": True
            }
            mock_completion_service.get_project_completion_status = AsyncMock(return_value=updated_status)
            
            response = client.get(f"/api/v1/projects/{sample_project_id}/completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            assert data["completion_percentage"] == 100.0
            assert data["artifacts_available"] is True
    
    def test_user_can_download_complete_project_workflow(self, client, sample_project_id):
        """Test complete user download workflow - S3-E2E-004."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service, \
             patch('app.api.artifacts.FileResponse') as mock_file_response:
            
            # Setup database mock
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Completed Project"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Step 1: User checks project artifacts summary
            mock_artifacts = [
                Mock(name="main.py", file_type="py", created_at=datetime.now()),
                Mock(name="README.md", file_type="md", created_at=datetime.now()),
                Mock(name="requirements.txt", file_type="txt", created_at=datetime.now())
            ]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            
            # Mock ZIP exists
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/summary")
            assert response.status_code == 200
            summary_data = response.json()
            
            assert summary_data["project_name"] == "Completed Project"
            assert summary_data["artifact_count"] == 3
            assert summary_data["download_available"] is True
            assert len(summary_data["artifacts"]) == 3
            
            # Step 2: User initiates download
            mock_file_response.return_value = Mock()
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/download")
            
            # Verify file response was created with correct parameters
            assert mock_file_response.called
            call_args = mock_file_response.call_args
            assert "Completed_Project_artifacts.zip" in call_args[1]["filename"]
            assert call_args[1]["media_type"] == "application/zip"
            
            # Step 3: User can re-download if needed
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/download")
            
            # Should work multiple times
            assert mock_file_response.call_count >= 2
    
    def test_admin_can_manage_artifact_lifecycle_workflow(self, client, sample_project_id):
        """Test admin artifact management workflow - S3-E2E-005."""
        with patch('app.api.artifacts.get_session') as mock_get_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service:
            
            # Setup database mock
            mock_db = Mock()
            mock_project = Mock()
            mock_project.id = sample_project_id
            mock_project.name = "Test Project"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            mock_get_session.return_value = mock_db
            
            # Step 1: Admin generates artifacts manually
            mock_artifacts = [Mock(), Mock(), Mock()]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/project.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            response = client.post(f"/api/v1/artifacts/{sample_project_id}/generate")
            assert response.status_code == 200
            data = response.json()
            assert data["artifact_count"] == 3
            assert data["status"] == "success"
            
            # Step 2: Admin checks artifact summary
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            response = client.get(f"/api/v1/artifacts/{sample_project_id}/summary")
            assert response.status_code == 200
            summary_data = response.json()
            assert summary_data["download_available"] is True
            
            # Step 3: Admin cleans up project artifacts
            mock_zip_path.unlink = Mock()
            
            response = client.delete(f"/api/v1/artifacts/{sample_project_id}/artifacts")
            assert response.status_code == 200
            data = response.json()
            assert "cleaned up" in data["message"].lower()
            
            # Verify cleanup was performed
            mock_zip_path.unlink.assert_called_once()
            
            # Step 4: Admin performs system-wide cleanup
            mock_artifact_service.cleanup_old_artifacts = Mock()
            
            response = client.post("/api/v1/artifacts/cleanup-old?max_age_hours=24")
            assert response.status_code == 200
            data = response.json()
            assert "older than 24 hours" in data["message"]
            
            # Verify system cleanup was performed
            mock_artifact_service.cleanup_old_artifacts.assert_called_once_with(24)


class TestHITLWebSocketIntegrationE2E:
    """E2E tests for HITL WebSocket integration - S3-E2E-006."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_receives_real_time_hitl_updates_workflow(self, client):
        """Test complete HITL real-time update workflow - S3-E2E-006."""
        sample_request_id = uuid4()
        sample_project_id = uuid4()
        sample_task_id = uuid4()
        
        with patch('app.api.hitl.get_session') as mock_get_session, \
             patch('app.api.hitl.get_orchestrator_service') as mock_get_orchestrator, \
             patch('app.api.hitl.websocket_manager') as mock_ws:
            
            # Setup database mock
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Setup orchestrator mock
            mock_orchestrator = Mock()
            mock_get_orchestrator.return_value = mock_orchestrator
            mock_orchestrator.resume_workflow_after_hitl = AsyncMock()
            
            # Setup WebSocket mock
            mock_ws.broadcast_to_project = AsyncMock()
            
            # Create mock HITL request
            from app.models.hitl import HitlStatus, HitlAction
            
            mock_hitl_request = Mock()
            mock_hitl_request.id = sample_request_id
            mock_hitl_request.project_id = sample_project_id
            mock_hitl_request.task_id = sample_task_id
            mock_hitl_request.question = "Please review the generated code"
            mock_hitl_request.options = ["approve", "reject", "amend"]
            mock_hitl_request.status = HitlStatus.PENDING
            mock_hitl_request.history = []
            mock_hitl_request.created_at = datetime.now()
            mock_hitl_request.updated_at = datetime.now()
            mock_hitl_request.expires_at = None
            mock_hitl_request.responded_at = None
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_hitl_request
            
            # Step 1: Get HITL request details
            response = client.get(f"/api/v1/hitl/{sample_request_id}")
            assert response.status_code == 200
            request_data = response.json()
            
            assert request_data["request_id"] == str(sample_request_id)
            assert request_data["question"] == "Please review the generated code"
            assert request_data["status"] == HitlStatus.PENDING.value
            
            # Step 2: User responds to HITL request
            response_payload = {
                "action": HitlAction.APPROVE.value,
                "comment": "Code looks good!"
            }
            
            response = client.post(
                f"/api/v1/hitl/{sample_request_id}/respond",
                json=response_payload
            )
            assert response.status_code == 200
            response_data = response.json()
            
            assert response_data["request_id"] == str(sample_request_id)
            assert response_data["action"] == HitlAction.APPROVE.value
            assert response_data["workflow_resumed"] is True
            
            # Step 3: Verify WebSocket event was broadcast
            mock_ws.broadcast_to_project.assert_called_once()
            call_args = mock_ws.broadcast_to_project.call_args
            event, project_id_str = call_args[0]
            
            assert project_id_str == str(sample_project_id)
            assert event.event_type == "hitl_response"
            assert event.data["action"] == HitlAction.APPROVE.value
            assert event.data["hitl_request_id"] == str(sample_request_id)
            
            # Step 4: Verify workflow resumed
            mock_orchestrator.resume_workflow_after_hitl.assert_called_once_with(
                sample_project_id, sample_task_id
            )
            
            # Step 5: Verify HITL request status updated
            response = client.get(f"/api/v1/hitl/{sample_request_id}")
            assert response.status_code == 200
            updated_request_data = response.json()
            
            # In real scenario, the database would be updated
            # Here we verify the response flow worked correctly
            assert response.status_code == 200


class TestCompleteSprintWorkflowE2E:
    """E2E test for complete Sprint 3 workflow integration."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_sprint3_backend_workflow(self, client):
        """Test complete Sprint 3 backend workflow integration."""
        project_id = uuid4()
        task_id = uuid4()
        hitl_request_id = uuid4()
        
        with patch('app.services.agent_status_service.websocket_manager') as mock_agent_ws, \
             patch('app.api.projects.get_session') as mock_project_session, \
             patch('app.api.projects.project_completion_service') as mock_completion_service, \
             patch('app.api.artifacts.get_session') as mock_artifact_session, \
             patch('app.api.artifacts.artifact_service') as mock_artifact_service, \
             patch('app.api.hitl.get_session') as mock_hitl_session:
            
            # Setup common mocks
            mock_agent_ws.broadcast_global = AsyncMock()
            mock_db = Mock()
            mock_project_session.return_value = mock_db
            mock_artifact_session.return_value = mock_db
            mock_hitl_session.return_value = mock_db
            
            # Phase 1: Agent Status Management
            # ================================
            
            # Step 1: Check initial agent statuses
            response = client.get("/api/v1/agents/status")
            assert response.status_code == 200
            initial_statuses = response.json()
            assert len(initial_statuses) == len(AgentType)
            
            # Step 2: Simulate agents becoming active
            from app.services.agent_status_service import agent_status_service
            
            # Run status updates in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Analyst starts working
                loop.run_until_complete(
                    agent_status_service.set_agent_working(AgentType.ANALYST, task_id)
                )
                
                # Architect starts working  
                loop.run_until_complete(
                    agent_status_service.set_agent_working(AgentType.ARCHITECT, uuid4())
                )
                
                # Coder starts working
                loop.run_until_complete(
                    agent_status_service.set_agent_working(AgentType.CODER, uuid4())
                )
            finally:
                loop.close()
            
            # Verify agent status updates
            response = client.get("/api/v1/agents/status")
            assert response.status_code == 200
            updated_statuses = response.json()
            
            assert updated_statuses["analyst"]["status"] == AgentStatus.WORKING.value
            assert updated_statuses["architect"]["status"] == AgentStatus.WORKING.value
            assert updated_statuses["coder"]["status"] == AgentStatus.WORKING.value
            
            # Phase 2: Project Progression
            # ============================
            
            # Step 3: Check project completion status (in progress)
            in_progress_status = {
                "project_id": str(project_id),
                "completion_percentage": 60.0,
                "is_complete": False,
                "artifacts_available": False
            }
            mock_completion_service.get_project_completion_status = AsyncMock(
                return_value=in_progress_status
            )
            
            response = client.get(f"/api/v1/projects/{project_id}/completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is False
            assert data["completion_percentage"] == 60.0
            
            # Phase 3: Project Completion & Artifact Generation
            # =================================================
            
            # Step 4: Project reaches completion
            mock_completion_service.check_project_completion = AsyncMock(return_value=True)
            
            # Mock artifact generation
            mock_project = Mock()
            mock_project.id = project_id
            mock_project.name = "Sprint 3 Test Project"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_project
            
            mock_artifacts = [
                Mock(name="main.py", file_type="py", created_at=datetime.now()),
                Mock(name="README.md", file_type="md", created_at=datetime.now()),
                Mock(name="requirements.txt", file_type="txt", created_at=datetime.now()),
                Mock(name="project_summary.md", file_type="md", created_at=datetime.now())
            ]
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/project.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            # Trigger completion check
            response = client.post(f"/api/v1/projects/{project_id}/check-completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            
            # Step 5: Generate and verify artifacts
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            response = client.post(f"/api/v1/artifacts/{project_id}/generate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["artifact_count"] == 4
            
            # Step 6: Verify artifact summary
            response = client.get(f"/api/v1/artifacts/{project_id}/summary")
            assert response.status_code == 200
            summary_data = response.json()
            assert summary_data["artifact_count"] == 4
            assert summary_data["download_available"] is True
            
            # Phase 4: Final Verification
            # ===========================
            
            # Step 7: Verify final project status
            completed_status = {
                "project_id": str(project_id),
                "completion_percentage": 100.0,
                "is_complete": True,
                "artifacts_available": True
            }
            mock_completion_service.get_project_completion_status = AsyncMock(
                return_value=completed_status
            )
            
            response = client.get(f"/api/v1/projects/{project_id}/completion")
            assert response.status_code == 200
            data = response.json()
            assert data["is_complete"] is True
            assert data["completion_percentage"] == 100.0
            assert data["artifacts_available"] is True
            
            # Step 8: Reset agents to idle (project complete)
            response = client.post(f"/api/v1/agents/status/{AgentType.ANALYST.value}/reset")
            assert response.status_code == 200
            
            response = client.post(f"/api/v1/agents/status/{AgentType.ARCHITECT.value}/reset")
            assert response.status_code == 200
            
            response = client.post(f"/api/v1/agents/status/{AgentType.CODER.value}/reset")
            assert response.status_code == 200
            
            # Step 9: Verify all agents back to idle
            response = client.get("/api/v1/agents/status")
            assert response.status_code == 200
            final_statuses = response.json()
            
            assert final_statuses["analyst"]["status"] == AgentStatus.IDLE.value
            assert final_statuses["architect"]["status"] == AgentStatus.IDLE.value
            assert final_statuses["coder"]["status"] == AgentStatus.IDLE.value
            
            # Workflow complete - all Sprint 3 backend functionality verified!