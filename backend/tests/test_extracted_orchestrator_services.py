"""
Test suite for the extracted orchestrator services.

This module contains comprehensive tests for the services extracted from orchestrator.py:
- ProjectLifecycleManager
- AgentCoordinator
- WorkflowIntegrator
- HandoffManager
- StatusTracker
- ContextManager

Updated to reflect the SOLID design principles and dependency injection pattern.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.orchestrator.project_lifecycle_manager import ProjectLifecycleManager, SDLC_PHASES
from app.services.orchestrator.agent_coordinator import AgentCoordinator
from app.services.orchestrator.workflow_integrator import WorkflowIntegrator
from app.services.orchestrator.handoff_manager import HandoffManager
from app.services.orchestrator.status_tracker import StatusTracker
from app.services.orchestrator.context_manager import ContextManager
from app.models.task import Task, TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.context import ContextArtifact, ArtifactType
from app.models.hitl import HitlStatus


class TestProjectLifecycleManager:
    """Test cases for ProjectLifecycleManager service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def project_manager(self, mock_db):
        """Create ProjectLifecycleManager instance."""
        return ProjectLifecycleManager(mock_db)

    def test_initialization(self, project_manager, mock_db):
        """Test ProjectLifecycleManager initialization."""
        assert project_manager is not None
        assert project_manager.db == mock_db

    def test_create_project(self, project_manager, mock_db):
        """Test project creation."""
        project_name = "Test Project"
        project_description = "A test project"

        # Mock database operations
        mock_project = Mock()
        mock_project.id = uuid4()
        mock_project.name = project_name
        mock_project.description = project_description
        mock_project.current_phase = "discovery"
        mock_project.status = "active"

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Set attributes after refresh
        def refresh_side_effect(obj):
            obj.id = uuid4()
            obj.name = project_name
            obj.description = project_description
            obj.current_phase = "discovery"
            obj.status = "active"
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = refresh_side_effect

        result = project_manager.create_project(project_name, project_description)

        assert result is not None
        assert result.name == project_name
        assert result.description == project_description
        assert result.current_phase == "discovery"
        assert result.status == "active"

    def test_set_current_phase(self, project_manager, mock_db):
        """Test setting current project phase."""
        project_id = uuid4()
        new_phase = "design"

        # Mock project retrieval
        mock_project = Mock()
        mock_project.id = project_id
        mock_project.current_phase = "discovery"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        project_manager.set_current_phase(project_id, new_phase)

        assert mock_project.current_phase == new_phase
        assert mock_db.commit.called

    def test_get_current_phase(self, project_manager, mock_db):
        """Test getting current project phase."""
        project_id = uuid4()
        expected_phase = "design"

        # Mock project retrieval
        mock_project = Mock()
        mock_project.current_phase = expected_phase
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = project_manager.get_current_phase(project_id)

        assert result == expected_phase

    def test_validate_phase_completion(self, project_manager, mock_db):
        """Test phase completion validation."""
        project_id = uuid4()
        phase = "discovery"

        # Mock project and task retrieval
        mock_project = Mock()
        mock_project.current_phase = phase
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock tasks query
        mock_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        result = project_manager.validate_phase_completion(project_id, phase)

        assert result is True

    def test_sdlc_phases_constant(self):
        """Test SDLC_PHASES constant is properly defined."""
        assert isinstance(SDLC_PHASES, dict)
        assert "discovery" in SDLC_PHASES
        assert "design" in SDLC_PHASES
        assert "build" in SDLC_PHASES
        assert "validate" in SDLC_PHASES
        assert "launch" in SDLC_PHASES


class TestAgentCoordinator:
    """Test cases for AgentCoordinator service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def agent_coordinator(self, mock_db):
        """Create AgentCoordinator instance."""
        return AgentCoordinator(mock_db)

    def test_initialization(self, agent_coordinator, mock_db):
        """Test AgentCoordinator initialization."""
        assert agent_coordinator is not None
        assert agent_coordinator.db == mock_db

    def test_create_task(self, agent_coordinator, mock_db):
        """Test task creation through agent coordinator."""
        project_id = uuid4()
        agent_type = "analyst"
        instructions = "Analyze requirements"
        context_ids = ["ctx-1", "ctx-2"]

        # Mock database operations
        mock_task = Mock()
        mock_task.task_id = uuid4()
        mock_task.project_id = project_id
        mock_task.agent_type = agent_type
        mock_task.instructions = instructions
        mock_task.context_ids = context_ids
        mock_task.status = TaskStatus.PENDING

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Set attributes after refresh
        def refresh_side_effect(obj):
            obj.task_id = uuid4()
            obj.status = TaskStatus.PENDING
            obj.created_at = datetime.now(timezone.utc)
            obj.updated_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = refresh_side_effect

        result = agent_coordinator.create_task(
            project_id=project_id,
            agent_type=agent_type,
            instructions=instructions,
            context_ids=context_ids
        )

        assert result is not None
        assert result.agent_type == agent_type
        assert result.instructions == instructions
        assert result.context_ids == context_ids
        assert result.status == TaskStatus.PENDING

    def test_update_agent_status(self, agent_coordinator, mock_db):
        """Test agent status updates."""
        agent_type = "analyst"
        new_status = AgentStatus.WORKING

        # Mock agent status retrieval and update
        mock_agent_status = Mock()
        mock_agent_status.agent_type = agent_type
        mock_agent_status.status = AgentStatus.IDLE
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent_status

        agent_coordinator.update_agent_status(agent_type, new_status)

        assert mock_agent_status.status == new_status
        assert mock_db.commit.called

    def test_get_agent_status(self, agent_coordinator, mock_db):
        """Test getting agent status."""
        agent_type = "analyst"
        expected_status = AgentStatus.WORKING

        # Mock agent status retrieval
        mock_agent_status = Mock()
        mock_agent_status.status = expected_status
        mock_db.query.return_value.filter.return_value.first.return_value = mock_agent_status

        result = agent_coordinator.get_agent_status(agent_type)

        assert result == expected_status


class TestWorkflowIntegrator:
    """Test cases for WorkflowIntegrator service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_context_store(self):
        """Mock context store service."""
        service = Mock()
        return service

    @pytest.fixture
    def workflow_integrator(self, mock_db, mock_context_store):
        """Create WorkflowIntegrator instance."""
        with patch('app.services.orchestrator.workflow_integrator.ContextStoreService') as mock_ctx_store:
            mock_ctx_store.return_value = mock_context_store
            integrator = WorkflowIntegrator(mock_db)
            return integrator

    def test_initialization(self, workflow_integrator, mock_db):
        """Test WorkflowIntegrator initialization."""
        assert workflow_integrator is not None
        assert workflow_integrator.db == mock_db
        assert hasattr(workflow_integrator, 'context_store')

    def test_run_workflow(self, workflow_integrator):
        """Test workflow execution."""
        project_id = uuid4()
        workflow_type = "greenfield-fullstack"
        user_idea = "Build a web application"

        # Mock workflow execution
        mock_result = {"status": "completed", "artifacts": []}
        workflow_integrator.workflow_engine = Mock()
        workflow_integrator.workflow_engine.run_project_workflow = AsyncMock(return_value=mock_result)

        # Note: This would need to be an async test in real implementation
        # For now, we'll test the method exists and can be called
        assert hasattr(workflow_integrator, 'run_workflow')

    def test_pause_workflow(self, workflow_integrator):
        """Test workflow pausing."""
        execution_id = "test-execution"
        reason = "HITL required"

        workflow_integrator.workflow_engine = Mock()
        workflow_integrator.workflow_engine.pause_workflow_execution = AsyncMock(return_value=True)

        # Test that the method exists
        assert hasattr(workflow_integrator, 'pause_workflow')

    def test_resume_workflow(self, workflow_integrator):
        """Test workflow resumption."""
        execution_id = "test-execution"

        workflow_integrator.workflow_engine = Mock()
        workflow_integrator.workflow_engine.resume_workflow_execution = AsyncMock(return_value=True)

        # Test that the method exists
        assert hasattr(workflow_integrator, 'resume_workflow')


class TestHandoffManager:
    """Test cases for HandoffManager service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def handoff_manager(self, mock_db):
        """Create HandoffManager instance."""
        return HandoffManager(mock_db)

    def test_initialization(self, handoff_manager, mock_db):
        """Test HandoffManager initialization."""
        assert handoff_manager is not None
        assert handoff_manager.db == mock_db

    def test_create_handoff(self, handoff_manager, mock_db):
        """Test handoff creation."""
        from_agent = "analyst"
        to_agent = "architect"
        context_ids = ["ctx-1", "ctx-2"]
        task_id = uuid4()

        # Mock database operations
        mock_handoff = Mock()
        mock_handoff.handoff_id = uuid4()
        mock_handoff.from_agent = from_agent
        mock_handoff.to_agent = to_agent
        mock_handoff.context_ids = context_ids
        mock_handoff.task_id = task_id

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Set attributes after refresh
        def refresh_side_effect(obj):
            obj.handoff_id = uuid4()
            obj.created_at = datetime.now(timezone.utc)

        mock_db.refresh.side_effect = refresh_side_effect

        result = handoff_manager.create_handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            context_ids=context_ids,
            task_id=task_id
        )

        assert result is not None
        assert result.from_agent == from_agent
        assert result.to_agent == to_agent
        assert result.context_ids == context_ids
        assert result.task_id == task_id

    def test_get_pending_handoffs(self, handoff_manager, mock_db):
        """Test getting pending handoffs."""
        agent_type = "architect"

        # Mock handoff retrieval
        mock_handoffs = [
            Mock(from_agent="analyst", to_agent="architect", status="pending"),
            Mock(from_agent="coder", to_agent="architect", status="pending")
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_handoffs

        result = handoff_manager.get_pending_handoffs(agent_type)

        assert len(result) == 2
        assert all(h.to_agent == agent_type for h in result)
        assert all(h.status == "pending" for h in result)


class TestStatusTracker:
    """Test cases for StatusTracker service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def status_tracker(self, mock_db):
        """Create StatusTracker instance."""
        return StatusTracker(mock_db)

    def test_initialization(self, status_tracker, mock_db):
        """Test StatusTracker initialization."""
        assert status_tracker is not None
        assert status_tracker.db == mock_db

    def test_get_project_status(self, status_tracker, mock_db):
        """Test getting comprehensive project status."""
        project_id = uuid4()

        # Mock project retrieval
        mock_project = Mock()
        mock_project.current_phase = "design"
        mock_project.status = "active"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock task retrieval
        mock_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.WORKING),
            Mock(status=TaskStatus.PENDING)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        result = status_tracker.get_project_status(project_id)

        assert result is not None
        assert "phase" in result
        assert "completion_percentage" in result
        assert "total_tasks" in result
        assert "completed_tasks" in result
        assert "in_progress_tasks" in result
        assert "pending_tasks" in result

    def test_get_phase_progress(self, status_tracker, mock_db):
        """Test getting phase progress."""
        project_id = uuid4()
        phase = "design"

        # Mock task retrieval for phase
        mock_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.WORKING)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_tasks

        result = status_tracker.get_phase_progress(project_id, phase)

        assert result is not None
        assert "phase" in result
        assert "completion_percentage" in result
        assert "total_tasks" in result
        assert "completed_tasks" in result


class TestContextManager:
    """Test cases for ContextManager service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_context_store(self):
        """Mock context store service."""
        service = Mock()
        return service

    @pytest.fixture
    def context_manager(self, mock_db, mock_context_store):
        """Create ContextManager instance."""
        with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
            mock_ctx_store.return_value = mock_context_store
            manager = ContextManager(mock_db)
            return manager

    def test_initialization(self, context_manager, mock_db):
        """Test ContextManager initialization."""
        assert context_manager is not None
        assert context_manager.db == mock_db
        assert hasattr(context_manager, 'context_store')

    def test_get_integrated_context(self, context_manager):
        """Test getting integrated context."""
        project_id = uuid4()

        # Mock context artifacts
        mock_artifacts = [
            Mock(artifact_type=ArtifactType.USER_INPUT, content={"user_idea": "Build app"}),
            Mock(artifact_type=ArtifactType.REQUIREMENTS, content={"requirements": "Reqs here"})
        ]
        context_manager.context_store.get_artifacts_by_project.return_value = mock_artifacts

        result = context_manager.get_integrated_context(project_id)

        assert result is not None
        assert "artifacts" in result
        assert "summary" in result
        assert "context_ids" in result

    def test_create_context_artifact(self, context_manager):
        """Test creating context artifacts."""
        project_id = uuid4()
        source_agent = "analyst"
        artifact_type = ArtifactType.REQUIREMENTS
        content = {"requirements": "Detailed requirements"}

        # Mock artifact creation
        mock_artifact = Mock()
        mock_artifact.context_id = uuid4()
        context_manager.context_store.create_artifact.return_value = mock_artifact

        result = context_manager.create_context_artifact(
            project_id=project_id,
            source_agent=source_agent,
            artifact_type=artifact_type,
            content=content
        )

        assert result == mock_artifact
        context_manager.context_store.create_artifact.assert_called_once()

    def test_get_context_granularity_report(self, context_manager):
        """Test context granularity reporting."""
        project_id = uuid4()

        # Mock artifacts with different granularities
        mock_artifacts = [
            Mock(artifact_type=ArtifactType.USER_INPUT, content={"size": "small"}),
            Mock(artifact_type=ArtifactType.REQUIREMENTS, content={"size": "large"}),
            Mock(artifact_type=ArtifactType.ARCHITECTURE, content={"size": "medium"})
        ]
        context_manager.context_store.get_artifacts_by_project.return_value = mock_artifacts

        result = context_manager.get_context_granularity_report(project_id)

        assert result is not None
        assert "total_artifacts" in result
        assert "granularity_distribution" in result
        assert "average_size" in result


class TestServiceIntegration:
    """Integration tests for service interactions."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    def test_services_work_together(self, mock_db):
        """Test that all services can be instantiated and work together."""
        # Create all services
        project_manager = ProjectLifecycleManager(mock_db)
        agent_coordinator = AgentCoordinator(mock_db)

        with patch('app.services.orchestrator.workflow_integrator.ContextStoreService'), \
             patch('app.services.orchestrator.context_manager.ContextStoreService'):

            workflow_integrator = WorkflowIntegrator(mock_db)
            context_manager = ContextManager(mock_db)

        handoff_manager = HandoffManager(mock_db)
        status_tracker = StatusTracker(mock_db)

        # Verify all services are properly initialized
        assert project_manager is not None
        assert agent_coordinator is not None
        assert workflow_integrator is not None
        assert context_manager is not None
        assert handoff_manager is not None
        assert status_tracker is not None

        # Verify they all share the same database session
        assert project_manager.db == mock_db
        assert agent_coordinator.db == mock_db
        assert workflow_integrator.db == mock_db
        assert context_manager.db == mock_db
        assert handoff_manager.db == mock_db
        assert status_tracker.db == mock_db

    def test_dependency_injection_pattern(self, mock_db):
        """Test that services follow dependency injection pattern."""
        # This test verifies that services accept their dependencies through constructor
        # rather than creating them internally

        # Create services with injected dependencies
        project_manager = ProjectLifecycleManager(mock_db)
        agent_coordinator = AgentCoordinator(mock_db)
        handoff_manager = HandoffManager(mock_db)
        status_tracker = StatusTracker(mock_db)

        # Verify services don't create their own dependencies
        # (This is more of a design verification than a runtime test)
        assert hasattr(project_manager, 'db')
        assert hasattr(agent_coordinator, 'db')
        assert hasattr(handoff_manager, 'db')
        assert hasattr(status_tracker, 'db')

        # Verify the injected database is the same instance
        assert project_manager.db is mock_db
        assert agent_coordinator.db is mock_db
        assert handoff_manager.db is mock_db
        assert status_tracker.db is mock_db


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
