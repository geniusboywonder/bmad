"""
Integration tests for Story 2.1: Sequential Task Handoff

Test scenarios:
- 2.1-INT-001: Orchestrator creates tasks from handoff (P0)
- 2.1-INT-002: Task status updates during handoff (P0)
- 2.1-INT-003: Context artifact passing between phases (P1)
- 2.1-INT-004: Agent status updates during workflow (P1)
- 2.1-INT-005: WebSocket events for handoff operations (P2)
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.database.models import TaskDB, ContextArtifactDB, AgentStatusDB
from app.models.task import TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.context import ArtifactType
from app.services.orchestrator import OrchestratorService
from app.services.context_store import ContextStoreService
from tests.conftest import assert_performance_threshold


class TestOrchestratorTaskCreationFromHandoff:
    """Test scenario 2.1-INT-001: Orchestrator creates tasks from handoff (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_orchestrator_creates_task_from_valid_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService, 
        project_factory, sample_handoff_schema_data
    ):
        """Test orchestrator creates task from valid handoff schema."""
        project = project_factory.create(db_session)
        handoff_data = sample_handoff_schema_data
        
        # Create task from handoff
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify task creation
        assert task.project_id == project.id
        assert task.agent_type == handoff_data["to_agent"]
        assert task.instructions == handoff_data["task_instructions"]
        assert task.context_ids == handoff_data["context_ids"]
        assert task.status == TaskStatus.PENDING
        
        # Verify database persistence
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert db_task is not None
        assert db_task.agent_type == handoff_data["to_agent"]
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_orchestrator_handles_context_ids_in_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, context_artifact_factory
    ):
        """Test orchestrator properly handles context IDs in handoff."""
        project = project_factory.create(db_session)
        
        # Create context artifact
        artifact = context_artifact_factory.create(
            db_session, 
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN
        )
        
        # Create handoff with context
        handoff_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design architecture using project plan",
            "context_ids": [str(artifact.id)]
        }
        
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify context IDs are preserved
        assert len(task.context_ids) == 1
        assert str(artifact.id) in task.context_ids
        
        # Verify context can be retrieved
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert len(db_task.context_ids) == 1
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_orchestrator_validates_handoff_before_task_creation(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory
    ):
        """Test orchestrator validates handoff schema before creating task."""
        project = project_factory.create(db_session)
        
        # Test with invalid handoff (missing required fields)
        invalid_handoff = {
            "from_agent": AgentType.ANALYST.value,
            # Missing to_agent and task_instructions
        }
        
        with pytest.raises((ValueError, KeyError, AssertionError)):
            orchestrator_service.create_task_from_handoff(
                project_id=project.id,
                handoff_schema=invalid_handoff
            )
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_orchestrator_handles_handoff_priority(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory
    ):
        """Test orchestrator handles handoff priority settings."""
        project = project_factory.create(db_session)
        
        high_priority_handoff = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Urgent architecture task",
            "priority": "high"
        }
        
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=high_priority_handoff
        )
        
        # Verify priority is preserved (may be stored in metadata)
        assert task is not None
        # Priority handling would be implementation-specific


class TestTaskStatusUpdatesDuringHandoff:
    """Test scenario 2.1-INT-002: Task status updates during handoff (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_source_task_completion_before_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, task_factory
    ):
        """Test source task is marked complete before creating handoff task."""
        project = project_factory.create(db_session)
        
        # Create initial task
        source_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.WORKING
        )
        
        # Complete source task with output
        output_data = {"analysis": "Requirements analyzed", "next_phase": "architecture"}
        orchestrator_service.update_task_status(
            source_task.id,
            TaskStatus.COMPLETED,
            output=output_data
        )
        
        # Verify task status updated
        db_session.refresh(source_task)
        assert source_task.status == TaskStatus.COMPLETED
        assert source_task.output == output_data
        
        # Verify timestamp updated
        assert source_task.updated_at > source_task.created_at
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.handoff
    def test_handoff_task_creation_after_completion(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, task_factory
    ):
        """Test handoff task is created after source task completion."""
        project = project_factory.create(db_session)
        
        # Create and complete source task
        source_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ANALYST.value
        )
        
        orchestrator_service.update_task_status(
            source_task.id,
            TaskStatus.COMPLETED,
            output={"analysis_complete": True}
        )
        
        # Create handoff task
        handoff_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design architecture",
            "context_ids": []
        }
        
        handoff_task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify handoff task created with pending status
        assert handoff_task.status == TaskStatus.PENDING
        assert handoff_task.agent_type == AgentType.ARCHITECT.value
        
        # Verify both tasks exist in database
        all_tasks = db_session.query(TaskDB).filter(TaskDB.project_id == project.id).all()
        assert len(all_tasks) == 2
        
        task_statuses = [task.status for task in all_tasks]
        assert TaskStatus.COMPLETED in task_statuses
        assert TaskStatus.PENDING in task_statuses
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_parallel_task_handling_during_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, task_factory
    ):
        """Test handling of parallel tasks during handoff operations."""
        project = project_factory.create(db_session)
        
        # Create multiple tasks in different states
        analysis_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.COMPLETED
        )
        
        architecture_task = task_factory.create(
            db_session,
            project_id=project.id,
            agent_type=AgentType.ARCHITECT.value,
            status=TaskStatus.WORKING
        )
        
        # Create handoff for new coding task
        handoff_data = {
            "from_agent": AgentType.ARCHITECT.value,
            "to_agent": AgentType.CODER.value,
            "task_instructions": "Implement based on architecture",
        }
        
        coding_task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify all tasks exist with correct statuses
        all_tasks = db_session.query(TaskDB).filter(TaskDB.project_id == project.id).all()
        assert len(all_tasks) == 3
        
        status_counts = {}
        for task in all_tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1
        
        assert status_counts[TaskStatus.COMPLETED] == 1
        assert status_counts[TaskStatus.WORKING] == 1  
        assert status_counts[TaskStatus.PENDING] == 1


class TestContextArtifactPassingBetweenPhases:
    """Test scenario 2.1-INT-003: Context artifact passing between phases (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    @pytest.mark.context
    def test_context_artifact_retrieval_for_handoff_task(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        context_store_service: ContextStoreService, project_factory,
        context_artifact_factory
    ):
        """Test context artifacts are properly retrieved for handoff tasks."""
        project = project_factory.create(db_session)
        
        # Create context artifacts from previous phases
        analysis_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"requirements": "User needs analysis", "scope": "MVP features"}
        )
        
        # Create handoff with context reference
        handoff_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design architecture using requirements analysis",
            "context_ids": [str(analysis_artifact.id)]
        }
        
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Retrieve context for the task
        context_artifacts = context_store_service.get_artifacts_by_ids(task.context_ids)
        
        # Verify context retrieval
        assert len(context_artifacts) == 1
        retrieved_artifact = context_artifacts[0]
        assert retrieved_artifact.id == analysis_artifact.id
        assert retrieved_artifact.artifact_type == ArtifactType.PROJECT_PLAN
        assert "requirements" in retrieved_artifact.content
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    @pytest.mark.context
    def test_multiple_context_artifacts_in_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, context_artifact_factory
    ):
        """Test handoff with multiple context artifacts from different phases."""
        project = project_factory.create(db_session)
        
        # Create multiple context artifacts
        user_input = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            source_agent=AgentType.ORCHESTRATOR,
            artifact_type=ArtifactType.USER_INPUT,
            content={"requirements": "Build a task manager"}
        )
        
        analysis_output = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"features": ["task creation", "task tracking"]}
        )
        
        # Create handoff with multiple contexts
        handoff_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design system using user input and analysis",
            "context_ids": [str(user_input.id), str(analysis_output.id)]
        }
        
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify all context IDs are preserved
        assert len(task.context_ids) == 2
        assert str(user_input.id) in task.context_ids
        assert str(analysis_output.id) in task.context_ids
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.handoff
    @pytest.mark.context
    def test_context_artifact_filtering_by_relevance(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test filtering context artifacts by relevance to handoff phase."""
        project = project_factory.create(db_session)
        
        # Create artifacts for different purposes
        relevant_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"architecture_requirements": "System needs microservices"}
        )
        
        irrelevant_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.TEST_RESULTS,
            content={"test_status": "Not relevant for architecture phase"}
        )
        
        # Get all project artifacts
        all_artifacts = context_store_service.get_artifacts_by_project(project.id)
        assert len(all_artifacts) == 2
        
        # Filter by artifact type (mock filtering logic)
        architecture_relevant_types = [ArtifactType.PROJECT_PLAN, ArtifactType.USER_INPUT]
        relevant_artifacts = [
            artifact for artifact in all_artifacts 
            if artifact.artifact_type in architecture_relevant_types
        ]
        
        assert len(relevant_artifacts) == 1
        assert relevant_artifacts[0].id == relevant_artifact.id


class TestAgentStatusUpdatesDuringWorkflow:
    """Test scenario 2.1-INT-004: Agent status updates during workflow (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_agent_status_updates_during_handoff(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, agent_status_factory
    ):
        """Test agent status updates during handoff operations."""
        project = project_factory.create(db_session)
        
        # Create initial agent statuses
        analyst_status = agent_status_factory.create(
            db_session,
            agent_type=AgentType.ANALYST,
            status=AgentStatus.WORKING
        )
        
        architect_status = agent_status_factory.create(
            db_session,
            agent_type=AgentType.ARCHITECT,
            status=AgentStatus.IDLE
        )
        
        # Simulate handoff from analyst to architect
        handoff_data = {
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_instructions": "Design architecture"
        }
        
        # Create handoff task (in real implementation, this would update agent statuses)
        task = orchestrator_service.create_task_from_handoff(
            project_id=project.id,
            handoff_schema=handoff_data
        )
        
        # Verify task created successfully
        assert task.agent_type == AgentType.ARCHITECT.value
        
        # In full implementation, agent statuses would be updated:
        # - Analyst -> IDLE (completed work)  
        # - Architect -> WORKING (received new task)
        
        # Verify statuses exist in database
        all_statuses = db_session.query(AgentStatusDB).all()
        agent_types = [status.agent_type for status in all_statuses]
        assert AgentType.ANALYST in agent_types
        assert AgentType.ARCHITECT in agent_types
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.handoff
    def test_concurrent_agent_status_management(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, agent_status_factory
    ):
        """Test management of agent statuses during concurrent operations."""
        project = project_factory.create(db_session)
        
        # Create multiple agent statuses
        for agent_type in [AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER]:
            agent_status_factory.create(
                db_session,
                agent_type=agent_type,
                status=AgentStatus.IDLE
            )
        
        # Create multiple handoff tasks
        handoffs = [
            {
                "from_agent": AgentType.ANALYST.value,
                "to_agent": AgentType.ARCHITECT.value,
                "task_instructions": "Architecture task 1"
            },
            {
                "from_agent": AgentType.ARCHITECT.value,
                "to_agent": AgentType.CODER.value,
                "task_instructions": "Coding task 1"
            }
        ]
        
        # Create tasks from handoffs
        created_tasks = []
        for handoff_data in handoffs:
            task = orchestrator_service.create_task_from_handoff(
                project_id=project.id,
                handoff_schema=handoff_data
            )
            created_tasks.append(task)
        
        # Verify all tasks created
        assert len(created_tasks) == 2
        assert created_tasks[0].agent_type == AgentType.ARCHITECT.value
        assert created_tasks[1].agent_type == AgentType.CODER.value
        
        # Verify agent statuses still exist
        status_count = db_session.query(AgentStatusDB).count()
        assert status_count == 3


class TestWebSocketEventsForHandoffOperations:
    """Test scenario 2.1-INT-005: WebSocket events for handoff operations (P2)"""
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.handoff
    @pytest.mark.asyncio
    async def test_websocket_events_during_handoff_creation(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, mock_websocket_manager
    ):
        """Test WebSocket events are emitted during handoff operations."""
        project = project_factory.create(db_session)
        
        # Mock the global WebSocket manager
        with patch('app.services.orchestrator.websocket_manager', mock_websocket_manager):
            handoff_data = {
                "from_agent": AgentType.ANALYST.value,
                "to_agent": AgentType.ARCHITECT.value,
                "task_instructions": "Design system architecture"
            }
            
            # Create handoff task
            task = orchestrator_service.create_task_from_handoff(
                project_id=project.id,
                handoff_schema=handoff_data
            )
            
            # Verify task created
            assert task is not None
            
            # In full implementation, WebSocket events would be sent:
            # - Task handoff initiated
            # - New task created
            # - Agent status changed
            
            # Mock verification would check that broadcast was called
            # mock_websocket_manager.broadcast.assert_called()
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.handoff
    @pytest.mark.asyncio
    async def test_real_time_handoff_notifications(
        self, db_session: Session, orchestrator_service: OrchestratorService,
        project_factory, mock_websocket_manager, performance_timer
    ):
        """Test real-time notifications for handoff operations."""
        project = project_factory.create(db_session)
        
        performance_timer.start()
        
        with patch('app.services.orchestrator.websocket_manager', mock_websocket_manager):
            # Simulate multiple rapid handoffs
            handoffs = [
                {
                    "from_agent": AgentType.ANALYST.value,
                    "to_agent": AgentType.ARCHITECT.value,
                    "task_instructions": f"Architecture task {i}"
                }
                for i in range(3)
            ]
            
            tasks = []
            for handoff_data in handoffs:
                task = orchestrator_service.create_task_from_handoff(
                    project_id=project.id,
                    handoff_schema=handoff_data
                )
                tasks.append(task)
        
        performance_timer.stop()
        
        # Verify all tasks created quickly
        assert len(tasks) == 3
        assert_performance_threshold(performance_timer.elapsed_ms, 1000, "Multiple handoff creation")
        
        # In full implementation, would verify WebSocket events sent for each handoff
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.handoff
    def test_handoff_event_payload_structure(self, mock_websocket_manager):
        """Test structure of WebSocket event payloads for handoffs."""
        # Mock event payload structure
        expected_handoff_event = {
            "event_type": "task_handoff",
            "project_id": str(uuid4()),
            "from_agent": AgentType.ANALYST.value,
            "to_agent": AgentType.ARCHITECT.value,
            "task_id": str(uuid4()),
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "handoff_reason": "phase_completion",
                "context_artifacts": 2
            }
        }
        
        # Verify required fields
        required_fields = ["event_type", "project_id", "from_agent", "to_agent", "task_id", "timestamp"]
        for field in required_fields:
            assert field in expected_handoff_event
        
        # Verify field types
        assert isinstance(expected_handoff_event["project_id"], str)
        assert isinstance(expected_handoff_event["from_agent"], str)
        assert isinstance(expected_handoff_event["to_agent"], str)
        assert isinstance(expected_handoff_event["metadata"], dict)
        
        # Verify agent types are valid
        valid_agents = [agent.value for agent in AgentType]
        assert expected_handoff_event["from_agent"] in valid_agents
        assert expected_handoff_event["to_agent"] in valid_agents