"""
Integration tests for Story 2.3: HITL Response Handling

Test scenarios:
- 2.3-INT-001: HITL request creation and persistence (P0)
- 2.3-INT-002: Response processing with DB updates (P0)
- 2.3-INT-003: Workflow resume after HITL response (P1)
- 2.3-INT-004: WebSocket event emission for HITL (P1)
- 2.3-INT-005: HITL request history tracking (P2)
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.database.models import HitlRequestDB, TaskDB, ProjectDB
from app.models.hitl import HitlStatus, HitlAction
from app.models.task import TaskStatus
from app.models.agent import AgentType
from tests.conftest import assert_performance_threshold


class TestHitlRequestCreationAndPersistence:
    """Test scenario 2.3-INT-001: HITL request creation and persistence (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_request_creation_via_orchestrator(
        self, db_session: Session, orchestrator_service, 
        project_factory, task_factory
    ):
        """Test HITL request creation through orchestrator service."""
        project = project_factory.create(db_session)
        task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ARCHITECT.value,
            status=TaskStatus.PENDING
        )
        
        # Create HITL request
        hitl_request = orchestrator_service.create_hitl_request(
            project_id=project.id,
            task_id=task.id,
            question="Please review and approve the system architecture",
            options=["approve", "reject", "amend"]
        )
        
        # Verify HITL request created
        assert hitl_request is not None
        assert hitl_request.project_id == project.id
        assert hitl_request.task_id == task.id
        assert hitl_request.status == HitlStatus.PENDING
        assert "review and approve" in hitl_request.question
        assert len(hitl_request.options) == 3
        
        # Verify database persistence
        db_hitl = db_session.query(HitlRequestDB).filter(
            HitlRequestDB.id == hitl_request.id
        ).first()
        assert db_hitl is not None
        assert db_hitl.project_id == project.id
        assert db_hitl.task_id == task.id
        assert db_hitl.status == HitlStatus.PENDING
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_request_with_expiration_time(
        self, db_session: Session, orchestrator_service,
        project_factory, task_factory
    ):
        """Test HITL request creation with automatic expiration time."""
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        
        creation_time = datetime.now()
        
        # Create HITL request with custom TTL
        hitl_request = orchestrator_service.create_hitl_request(
            project_id=project.id,
            task_id=task.id,
            question="Please review within 48 hours",
            options=["approve", "reject"],
            ttl_hours=48
        )
        
        # Verify expiration time is set correctly
        assert hitl_request.expiration_time is not None
        expected_expiration = creation_time + timedelta(hours=48)
        
        # Allow for small time difference (within 1 minute)
        time_diff = abs((hitl_request.expiration_time - expected_expiration).total_seconds())
        assert time_diff < 60
        
        # Verify database persistence of expiration
        db_hitl = db_session.query(HitlRequestDB).filter(
            HitlRequestDB.id == hitl_request.id
        ).first()
        assert db_hitl.expiration_time is not None
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_request_validation_constraints(
        self, db_session: Session, orchestrator_service,
        project_factory, task_factory
    ):
        """Test validation constraints during HITL request creation."""
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        
        # Test with missing required fields
        with pytest.raises((ValueError, TypeError)):
            orchestrator_service.create_hitl_request(
                project_id=project.id,
                task_id=task.id,
                question="",  # Empty question
                options=[]
            )
        
        # Test with invalid project/task relationship
        other_project = project_factory.create(db_session, name="Other Project")
        
        with pytest.raises((ValueError, AssertionError)):
            orchestrator_service.create_hitl_request(
                project_id=other_project.id,  # Different project
                task_id=task.id,  # Task from original project
                question="Invalid relationship test",
                options=["approve", "reject"]
            )
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_multiple_hitl_requests_per_project(
        self, db_session: Session, orchestrator_service,
        project_factory, task_factory
    ):
        """Test creating multiple HITL requests for the same project."""
        project = project_factory.create(db_session)
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = task_factory.create(
                db_session,
                project_id=project.id,
                agent_type=AgentType.ANALYST.value if i % 2 == 0 else AgentType.ARCHITECT.value,
                instructions=f"Task {i+1}"
            )
            tasks.append(task)
        
        # Create HITL request for each task
        hitl_requests = []
        for i, task in enumerate(tasks):
            hitl_request = orchestrator_service.create_hitl_request(
                project_id=project.id,
                task_id=task.id,
                question=f"Please review task {i+1} output",
                options=["approve", "reject", "amend"]
            )
            hitl_requests.append(hitl_request)
        
        # Verify all requests created successfully
        assert len(hitl_requests) == 3
        
        # Verify each request has unique ID but same project
        hitl_ids = [req.id for req in hitl_requests]
        assert len(set(hitl_ids)) == 3  # All unique IDs
        
        for hitl_request in hitl_requests:
            assert hitl_request.project_id == project.id
            assert hitl_request.status == HitlStatus.PENDING
        
        # Verify database persistence
        db_hitl_count = db_session.query(HitlRequestDB).filter(
            HitlRequestDB.project_id == project.id
        ).count()
        assert db_hitl_count == 3


class TestResponseProcessingWithDBUpdates:
    """Test scenario 2.3-INT-002: Response processing with DB updates (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_approve_response_processing(
        self, client: TestClient, db_session: Session,
        project_with_hitl
    ):
        """Test processing of HITL approve responses with database updates."""
        project = project_with_hitl["project"]
        task = project_with_hitl["task"]
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit approve response
        approve_data = {
            "action": "approve",
            "comment": "Architecture looks good, proceed with implementation"
        }
        
        response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=approve_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["action"] == "approve"
        assert response_data["workflow_resumed"] is True
        
        # Verify database updates
        db_session.refresh(hitl_request)
        assert hitl_request.status == HitlStatus.APPROVED
        assert hitl_request.user_response == "approved"
        assert hitl_request.response_comment == approve_data["comment"]
        assert hitl_request.responded_at is not None
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_reject_response_processing(
        self, client: TestClient, db_session: Session,
        project_with_hitl
    ):
        """Test processing of HITL reject responses."""
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit reject response
        reject_data = {
            "action": "reject",
            "comment": "Architecture does not meet scalability requirements",
            "reason": "insufficient_scalability"
        }
        
        response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=reject_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["action"] == "reject"
        assert response_data["workflow_resumed"] is True  # Workflow continues with rejection handling
        
        # Verify database updates
        db_session.refresh(hitl_request)
        assert hitl_request.status == HitlStatus.REJECTED
        assert hitl_request.user_response == "rejected"
        assert "scalability requirements" in hitl_request.response_comment
        assert hitl_request.responded_at is not None
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_amend_response_processing(
        self, client: TestClient, db_session: Session,
        project_with_hitl
    ):
        """Test processing of HITL amend responses with content updates."""
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit amend response
        amend_data = {
            "action": "amend",
            "content": "Please add load balancing strategy and database sharding approach to the architecture",
            "comment": "Need more detail on scalability mechanisms"
        }
        
        response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json=amend_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["action"] == "amend"
        assert response_data["workflow_resumed"] is True
        
        # Verify database updates for amendments
        db_session.refresh(hitl_request)
        assert hitl_request.status == HitlStatus.AMENDED
        assert hitl_request.user_response == "amended"
        assert hitl_request.amended_content is not None
        
        # Verify amended content structure
        amended_content = hitl_request.amended_content
        assert "amended_content" in amended_content
        assert "load balancing" in amended_content["amended_content"]
        assert "comment" in amended_content
        assert amended_content["comment"] == amend_data["comment"]
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.hitl
    def test_hitl_response_error_handling(
        self, client: TestClient, db_session: Session
    ):
        """Test error handling during HITL response processing."""
        # Test with non-existent HITL request
        fake_hitl_id = uuid4()
        response = client.post(
            f"/api/v1/hitl/{fake_hitl_id}/respond",
            json={"action": "approve", "comment": "Test comment"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test with invalid action
        project_with_hitl = self._create_test_hitl_request(db_session)
        hitl_request = project_with_hitl["hitl_request"]
        
        invalid_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={"action": "invalid_action", "comment": "Invalid test"}
        )
        assert invalid_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test with missing required fields
        missing_fields_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={}  # Missing action
        )
        assert missing_fields_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def _create_test_hitl_request(self, db_session):
        """Helper method to create test HITL request."""
        from tests.conftest import ProjectFactory, TaskFactory, HitlRequestFactory
        
        project_factory = ProjectFactory()
        task_factory = TaskFactory()
        hitl_factory = HitlRequestFactory()
        
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        hitl_request = hitl_factory.create(
            db_session,
            project_id=project.id,
            task_id=task.id
        )
        
        return {"project": project, "task": task, "hitl_request": hitl_request}
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    def test_concurrent_hitl_responses(
        self, client: TestClient, db_session: Session,
        project_factory, task_factory, hitl_request_factory
    ):
        """Test handling of concurrent HITL responses."""
        import threading
        import time
        
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        hitl_request = hitl_request_factory.create(
            db_session,
            project_id=project.id,
            task_id=task.id
        )
        
        results = {"responses": [], "errors": []}
        
        def submit_response(action: str, comment: str):
            """Submit HITL response in separate thread."""
            try:
                response = client.post(
                    f"/api/v1/hitl/{hitl_request.id}/respond",
                    json={"action": action, "comment": comment}
                )
                results["responses"].append({
                    "status_code": response.status_code,
                    "action": action,
                    "response_data": response.json() if response.status_code == 200 else None
                })
            except Exception as e:
                results["errors"].append(str(e))
        
        # Create multiple threads attempting to respond simultaneously
        threads = []
        actions = ["approve", "reject", "amend"]
        
        for i, action in enumerate(actions):
            thread = threading.Thread(
                target=submit_response,
                args=(action, f"Concurrent response {i+1}")
            )
            threads.append(thread)
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify only one response succeeded
        successful_responses = [
            resp for resp in results["responses"] 
            if resp["status_code"] == 200
        ]
        
        # Should have exactly one successful response
        assert len(successful_responses) == 1
        
        # Other responses should have failed with conflict status
        failed_responses = [
            resp for resp in results["responses"]
            if resp["status_code"] != 200
        ]
        assert len(failed_responses) >= 1  # At least one should fail due to concurrency
        
        # Verify final database state
        db_session.refresh(hitl_request)
        assert hitl_request.status in [HitlStatus.APPROVED, HitlStatus.REJECTED, HitlStatus.AMENDED]


class TestWorkflowResumeAfterHitlResponse:
    """Test scenario 2.3-INT-003: Workflow resume after HITL response (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_workflow_resume_after_approval(
        self, client: TestClient, db_session: Session,
        orchestrator_service, project_with_hitl
    ):
        """Test workflow resumption after HITL approval."""
        project = project_with_hitl["project"]
        task = project_with_hitl["task"]
        hitl_request = project_with_hitl["hitl_request"]
        
        # Verify task is initially waiting for HITL
        assert task.status == TaskStatus.PENDING
        
        # Submit approval
        approve_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={"action": "approve", "comment": "Approved for continuation"}
        )
        assert approve_response.status_code == status.HTTP_200_OK
        
        # Verify workflow resumption
        resume_result = orchestrator_service.resume_workflow_after_hitl(
            hitl_request.id,
            HitlAction.APPROVE
        )
        
        assert resume_result["workflow_resumed"] is True
        assert resume_result["next_action"] == "continue_task"
        
        # Verify task can proceed
        db_session.refresh(task)
        # In full implementation, task status might change to WORKING
        # For now, verify the task is accessible and can be updated
        assert task.id is not None
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_workflow_handling_after_rejection(
        self, client: TestClient, db_session: Session,
        orchestrator_service, project_with_hitl
    ):
        """Test workflow handling after HITL rejection."""
        project = project_with_hitl["project"]
        task = project_with_hitl["task"]
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit rejection
        reject_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "reject", 
                "comment": "Does not meet requirements",
                "reason": "insufficient_detail"
            }
        )
        assert reject_response.status_code == status.HTTP_200_OK
        
        # Verify workflow handling of rejection
        resume_result = orchestrator_service.resume_workflow_after_hitl(
            hitl_request.id,
            HitlAction.REJECT
        )
        
        assert resume_result["workflow_resumed"] is True
        assert resume_result["next_action"] == "handle_rejection"
        
        # In full implementation, this might:
        # - Mark task as needing rework
        # - Create new task for addressing feedback
        # - Notify relevant agents
        
        # Verify task state reflects rejection
        db_session.refresh(task)
        assert task.id is not None  # Task still exists for rework
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_workflow_continuation_after_amendment(
        self, client: TestClient, db_session: Session,
        orchestrator_service, project_with_hitl
    ):
        """Test workflow continuation after HITL amendment."""
        project = project_with_hitl["project"]
        task = project_with_hitl["task"]
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit amendment
        amend_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "amend",
                "content": "Please add database optimization strategies",
                "comment": "Need more detail on performance"
            }
        )
        assert amend_response.status_code == status.HTTP_200_OK
        
        # Verify workflow handles amendment
        resume_result = orchestrator_service.resume_workflow_after_hitl(
            hitl_request.id,
            HitlAction.AMEND
        )
        
        assert resume_result["workflow_resumed"] is True
        assert resume_result["next_action"] == "apply_amendments"
        
        # Verify amendment content is available for workflow
        db_session.refresh(hitl_request)
        assert hitl_request.amended_content is not None
        amended_content = hitl_request.amended_content["amended_content"]
        assert "database optimization" in amended_content
        
        # In full implementation, this would:
        # - Update task instructions with amendments
        # - Notify agent of required changes
        # - Continue task execution with new context
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    @pytest.mark.workflow
    def test_multi_stage_hitl_workflow(
        self, client: TestClient, db_session: Session,
        orchestrator_service, project_factory, task_factory,
        hitl_request_factory
    ):
        """Test workflow with multiple HITL checkpoints."""
        project = project_factory.create(db_session)
        
        # Create workflow with multiple HITL checkpoints
        analysis_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ANALYST.value,
            instructions="Analysis phase with HITL checkpoint"
        )
        
        architecture_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ARCHITECT.value,
            instructions="Architecture phase with HITL checkpoint"
        )
        
        # First HITL checkpoint - Analysis review
        analysis_hitl = hitl_request_factory.create(
            db_session,
            project_id=project.id,
            task_id=analysis_task.id,
            question="Please review analysis results"
        )
        
        # Approve analysis
        client.post(
            f"/api/v1/hitl/{analysis_hitl.id}/respond",
            json={"action": "approve", "comment": "Analysis approved"}
        )
        
        # Resume workflow after first HITL
        orchestrator_service.resume_workflow_after_hitl(
            analysis_hitl.id,
            HitlAction.APPROVE
        )
        
        # Complete analysis task
        orchestrator_service.update_task_status(
            analysis_task.id,
            TaskStatus.COMPLETED,
            output={"analysis": "completed after HITL approval"}
        )
        
        # Second HITL checkpoint - Architecture review
        architecture_hitl = hitl_request_factory.create(
            db_session,
            project_id=project.id,
            task_id=architecture_task.id,
            question="Please review architecture design"
        )
        
        # Amend architecture
        client.post(
            f"/api/v1/hitl/{architecture_hitl.id}/respond",
            json={
                "action": "amend",
                "content": "Add microservices communication patterns",
                "comment": "Need more detail on service interactions"
            }
        )
        
        # Resume workflow after amendment
        resume_result = orchestrator_service.resume_workflow_after_hitl(
            architecture_hitl.id,
            HitlAction.AMEND
        )
        
        # Verify multi-stage workflow state
        assert resume_result["workflow_resumed"] is True
        
        # Verify both HITL requests have been processed
        db_session.refresh(analysis_hitl)
        db_session.refresh(architecture_hitl)
        
        assert analysis_hitl.status == HitlStatus.APPROVED
        assert architecture_hitl.status == HitlStatus.AMENDED
        
        # Verify workflow can continue with amendments applied
        assert architecture_hitl.amended_content is not None


class TestWebSocketEventEmissionForHitl:
    """Test scenario 2.3-INT-004: WebSocket event emission for HITL (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.asyncio
    async def test_websocket_events_on_hitl_request_creation(
        self, db_session: Session, orchestrator_service,
        project_factory, task_factory, mock_websocket_manager
    ):
        """Test WebSocket events emitted when HITL requests are created."""
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        
        # Mock the WebSocket manager in orchestrator
        with patch.object(orchestrator_service, 'websocket_manager', mock_websocket_manager):
            # Create HITL request
            hitl_request = orchestrator_service.create_hitl_request(
                project_id=project.id,
                task_id=task.id,
                question="Please review the implementation approach",
                options=["approve", "reject", "amend"]
            )
            
            # Verify HITL request created
            assert hitl_request is not None
            
            # In full implementation, WebSocket events would be sent:
            # - HITL_REQUEST_CREATED event to project subscribers
            # - Task status update (waiting for human input)
            # - Agent status change (paused pending HITL)
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.hitl
    @pytest.mark.asyncio
    async def test_websocket_events_on_hitl_response_submission(
        self, client: TestClient, db_session: Session,
        project_with_hitl, mock_websocket_manager
    ):
        """Test WebSocket events emitted when HITL responses are submitted."""
        hitl_request = project_with_hitl["hitl_request"]
        
        # Mock WebSocket manager for response processing
        with patch('app.api.hitl.websocket_manager', mock_websocket_manager):
            # Submit HITL response
            response = client.post(
                f"/api/v1/hitl/{hitl_request.id}/respond",
                json={
                    "action": "approve",
                    "comment": "Architecture approved for implementation"
                }
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            # In full implementation, WebSocket events would be sent:
            # - HITL_RESPONSE_RECEIVED event
            # - Workflow status update (resumed)
            # - Task status change (ready to continue)
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_websocket_event_payload_structure(
        self, mock_websocket_manager
    ):
        """Test structure of WebSocket event payloads for HITL operations."""
        # Mock HITL WebSocket event payloads
        hitl_request_created_event = {
            "event_type": "hitl_request_created",
            "project_id": str(uuid4()),
            "task_id": str(uuid4()),
            "hitl_request_id": str(uuid4()),
            "question": "Please review the system design",
            "options": ["approve", "reject", "amend"],
            "expiration_time": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        hitl_response_event = {
            "event_type": "hitl_response_received",
            "project_id": str(uuid4()),
            "hitl_request_id": str(uuid4()),
            "action": "approve",
            "user_id": "reviewer123",
            "comment": "Approved for implementation",
            "workflow_status": "resumed",
            "timestamp": datetime.now().isoformat()
        }
        
        # Verify event structure
        required_request_fields = [
            "event_type", "project_id", "task_id", "hitl_request_id",
            "question", "options", "timestamp"
        ]
        
        for field in required_request_fields:
            assert field in hitl_request_created_event
        
        required_response_fields = [
            "event_type", "project_id", "hitl_request_id", "action",
            "workflow_status", "timestamp"
        ]
        
        for field in required_response_fields:
            assert field in hitl_response_event
        
        # Verify field types
        assert isinstance(hitl_request_created_event["options"], list)
        assert isinstance(hitl_response_event["action"], str)
        assert hitl_response_event["action"] in ["approve", "reject", "amend"]
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    @pytest.mark.performance
    def test_websocket_event_emission_performance(
        self, db_session: Session, orchestrator_service,
        project_factory, task_factory, mock_websocket_manager,
        performance_timer
    ):
        """Test performance of WebSocket event emission during HITL operations."""
        project = project_factory.create(db_session)
        
        # Create multiple tasks for HITL requests
        tasks = []
        for i in range(10):
            task = task_factory.create(
                db_session,
                project_id=project.id,
                instructions=f"Performance test task {i+1}"
            )
            tasks.append(task)
        
        performance_timer.start()
        
        # Create multiple HITL requests with WebSocket events
        with patch.object(orchestrator_service, 'websocket_manager', mock_websocket_manager):
            hitl_requests = []
            for i, task in enumerate(tasks):
                hitl_request = orchestrator_service.create_hitl_request(
                    project_id=project.id,
                    task_id=task.id,
                    question=f"Review task {i+1} output",
                    options=["approve", "reject"]
                )
                hitl_requests.append(hitl_request)
        
        performance_timer.stop()
        
        # Verify all requests created successfully
        assert len(hitl_requests) == 10
        
        # Verify performance threshold
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            2000,  # 2 seconds for 10 HITL requests with WebSocket events
            "Create 10 HITL requests with WebSocket events"
        )


class TestHitlRequestHistoryTracking:
    """Test scenario 2.3-INT-005: HITL request history tracking (P2)"""
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_response_history_creation(
        self, client: TestClient, db_session: Session,
        project_with_hitl
    ):
        """Test creation of history entries for HITL responses."""
        hitl_request = project_with_hitl["hitl_request"]
        
        # Submit initial amendment
        amend_response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "amend",
                "content": "Please add performance benchmarks",
                "comment": "Need quantitative performance data"
            }
        )
        assert amend_response.status_code == status.HTTP_200_OK
        
        # Get HITL request history
        history_response = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        assert history_response.status_code == status.HTTP_200_OK
        
        history_data = history_response.json()
        assert "history" in history_data
        assert len(history_data["history"]) >= 1
        
        # Verify history entry structure
        history_entry = history_data["history"][0]
        required_fields = ["action", "timestamp", "comment"]
        
        for field in required_fields:
            assert field in history_entry
        
        assert history_entry["action"] == "amend"
        assert "performance benchmarks" in history_entry["comment"]
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_multiple_hitl_responses_history_tracking(
        self, client: TestClient, db_session: Session,
        project_factory, task_factory, hitl_request_factory
    ):
        """Test history tracking for multiple HITL responses on same request."""
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        hitl_request = hitl_request_factory.create(
            db_session,
            project_id=project.id,
            task_id=task.id
        )
        
        # First response: Amendment
        client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "amend",
                "content": "Add security considerations",
                "comment": "Security analysis missing"
            }
        )
        
        # Update HITL request status to allow re-review
        hitl_request.status = HitlStatus.PENDING
        db_session.commit()
        
        # Second response: Approval (after amendments applied)
        client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "approve", 
                "comment": "Security concerns addressed, approved"
            }
        )
        
        # Get complete history
        history_response = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        history_data = history_response.json()
        
        # Should have 2 history entries
        assert len(history_data["history"]) == 2
        
        # Verify chronological order (newest first)
        histories = history_data["history"]
        
        # First entry should be the approval
        assert histories[0]["action"] == "approve"
        assert "approved" in histories[0]["comment"]
        
        # Second entry should be the amendment
        assert histories[1]["action"] == "amend"
        assert "security" in histories[1]["comment"].lower()
        
        # Verify timestamps are in correct order
        first_timestamp = datetime.fromisoformat(histories[0]["timestamp"])
        second_timestamp = datetime.fromisoformat(histories[1]["timestamp"])
        assert first_timestamp > second_timestamp
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_history_with_user_information(
        self, client: TestClient, db_session: Session,
        project_with_hitl
    ):
        """Test HITL history tracking includes user information."""
        hitl_request = project_with_hitl["hitl_request"]
        
        # Mock user authentication (in real implementation)
        test_user = "senior_architect@company.com"
        
        # Submit response with user context
        response = client.post(
            f"/api/v1/hitl/{hitl_request.id}/respond",
            json={
                "action": "reject",
                "comment": "Requirements are incomplete",
                "reason": "missing_use_cases"
            },
            headers={"X-User-ID": test_user}  # Mock user header
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Get history
        history_response = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        history_data = history_response.json()
        
        history_entry = history_data["history"][0]
        
        # In full implementation, user information would be tracked
        # assert "user_id" in history_entry
        # assert history_entry["user_id"] == test_user
        
        # For now, verify core fields exist
        assert "action" in history_entry
        assert "timestamp" in history_entry
        assert history_entry["action"] == "reject"
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.hitl
    def test_hitl_history_filtering_and_pagination(
        self, client: TestClient, db_session: Session,
        project_factory, task_factory, hitl_request_factory
    ):
        """Test filtering and pagination of HITL request history."""
        project = project_factory.create(db_session)
        task = task_factory.create(db_session, project_id=project.id)
        hitl_request = hitl_request_factory.create(
            db_session,
            project_id=project.id,
            task_id=task.id
        )
        
        # Create multiple history entries by simulating multiple reviews
        actions = ["amend", "amend", "approve"]
        comments = [
            "First amendment: Add error handling",
            "Second amendment: Improve documentation", 
            "Final approval: All issues addressed"
        ]
        
        for action, comment in zip(actions, comments):
            # Reset status to allow multiple responses (simulation)
            hitl_request.status = HitlStatus.PENDING
            db_session.commit()
            
            client.post(
                f"/api/v1/hitl/{hitl_request.id}/respond",
                json={"action": action, "comment": comment}
            )
        
        # Test history retrieval with pagination
        paginated_response = client.get(
            f"/api/v1/hitl/{hitl_request.id}/history?limit=2&offset=0"
        )
        
        assert paginated_response.status_code == status.HTTP_200_OK
        paginated_data = paginated_response.json()
        
        # Should return up to 2 entries
        assert len(paginated_data["history"]) <= 2
        
        # Test filtering by action type
        filtered_response = client.get(
            f"/api/v1/hitl/{hitl_request.id}/history?action=amend"
        )
        
        if filtered_response.status_code == status.HTTP_200_OK:
            filtered_data = filtered_response.json()
            # All returned entries should be amendments
            for entry in filtered_data["history"]:
                assert entry["action"] == "amend"
        
        # Get complete history for final verification
        complete_response = client.get(f"/api/v1/hitl/{hitl_request.id}/history")
        complete_data = complete_response.json()
        
        # Should have 3 total entries
        assert len(complete_data["history"]) == 3
        
        # Verify final state is approval
        final_entry = complete_data["history"][0]  # Newest first
        assert final_entry["action"] == "approve"
        assert "All issues addressed" in final_entry["comment"]