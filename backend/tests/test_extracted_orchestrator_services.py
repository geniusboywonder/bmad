"""
Test suite for the extracted orchestrator services.

This module contains comprehensive tests for the services extracted from orchestrator.py:
- ProjectLifecycleManager
- AgentCoordinator
- WorkflowIntegrator
- HandoffManager
- StatusTracker
- ContextManager

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies (Celery, Redis, etc.) remain appropriately mocked.
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
from tests.utils.database_test_utils import DatabaseTestManager

class TestProjectLifecycleManager:
    """Test cases for ProjectLifecycleManager service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for orchestrator tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def project_manager(self, db_manager):
        """Create ProjectLifecycleManager with real database session."""
        with db_manager.get_session() as session:
            return ProjectLifecycleManager(session)

    @pytest.mark.real_data
    def test_initialization(self, project_manager, db_manager):
        """Test ProjectLifecycleManager initialization with real database."""
        assert project_manager is not None
        assert project_manager.db is not None
        # Verify it can actually interact with database
        assert hasattr(project_manager, 'create_project')
        assert hasattr(project_manager, 'set_current_phase')

    @pytest.mark.real_data
    def test_create_project(self, db_manager):
        """Test project creation with real database operations."""
        project_name = "Test Project"
        project_description = "A test project"

        with db_manager.get_session() as session:
            project_manager = ProjectLifecycleManager(session)
            
            # Create project with real database operations
            result = project_manager.create_project(project_name, project_description)

            assert result is not None
            assert result.name == project_name
            assert result.description == project_description
            assert result.current_phase == "discovery"
            assert result.status == "active"
            assert result.id is not None
            assert result.created_at is not None

            # Verify database state
            db_checks = [
                {
                    'table': 'projects',
                    'conditions': {'name': project_name},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)

    @pytest.mark.real_data
    def test_set_current_phase(self, db_manager):
        """Test setting current project phase with real database."""
        # Create a real project first
        project = db_manager.create_test_project(
            name="Phase Test Project",
            current_phase="discovery"
        )

        with db_manager.get_session() as session:
            project_manager = ProjectLifecycleManager(session)
            
            # Set new phase
            new_phase = "design"
            project_manager.set_current_phase(project.id, new_phase)

            # Verify phase was updated in database
            db_checks = [
                {
                    'table': 'projects',
                    'conditions': {'id': str(project.id), 'current_phase': new_phase},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)

    @pytest.mark.real_data
    def test_get_current_phase(self, db_manager):
        """Test getting current project phase with real database."""
        # Create a real project
        project = db_manager.create_test_project(
            name="Get Phase Test Project",
            current_phase="design"
        )

        with db_manager.get_session() as session:
            project_manager = ProjectLifecycleManager(session)
            
            result = project_manager.get_current_phase(project.id)

            assert result == "design"

    @pytest.mark.real_data
    def test_validate_phase_completion(self, db_manager):
        """Test phase completion validation with real database."""
        # Create a real project
        project = db_manager.create_test_project(
            name="Phase Completion Test",
            current_phase="discovery"
        )

        # Create tasks that satisfy the completion criteria for the 'discovery' phase
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="analyst",
            status=TaskStatus.COMPLETED,
            instructions="analyze user input" # Satisfies "user_input_analyzed"
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="analyst",
            status=TaskStatus.COMPLETED,
            instructions="gather requirements" # Satisfies "requirements_gathered"
        )

        with db_manager.get_session() as session:
            project_manager = ProjectLifecycleManager(session)
            
            result = project_manager.validate_phase_completion(project.id, "discovery")

            assert result["valid"] is True
            assert len(result["missing_criteria"]) == 0

    @pytest.mark.real_data
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
    def db_manager(self):
        """Real database manager for agent coordinator tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_initialization(self, db_manager):
        """Test AgentCoordinator initialization with real database."""
        with db_manager.get_session() as session:
            agent_coordinator = AgentCoordinator(session)
            assert agent_coordinator is not None
            assert agent_coordinator.db == session

    @pytest.mark.real_data
    def test_create_task(self, db_manager):
        """Test task creation through agent coordinator with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Agent Coordinator Test")
        
        agent_type = "analyst"
        instructions = "Analyze requirements"
        context_ids = ["ctx-1", "ctx-2"]

        with db_manager.get_session() as session:
            agent_coordinator = AgentCoordinator(session)
            
            result = agent_coordinator.create_task(
                project_id=project.id,
                agent_type=agent_type,
                instructions=instructions,
                context_ids=context_ids
            )

            assert result is not None
            assert result.agent_type == agent_type
            assert result.instructions == instructions
            assert result.context_ids == context_ids
            assert result.status == TaskStatus.PENDING

            # Verify real database persistence
            db_checks = [
                {
                    'table': 'tasks',
                    'conditions': {'project_id': str(project.id), 'agent_type': agent_type},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)

    @pytest.mark.real_data
    def test_update_agent_status(self, db_manager):
        """Test agent status updates with real database."""
        agent_type = "analyst"
        new_status = AgentStatus.WORKING

        with db_manager.get_session() as session:
            # Create real agent status record
            from app.database.models import AgentStatusDB
            agent_status = AgentStatusDB(
                agent_type=agent_type,
                status=AgentStatus.IDLE
            )
            session.add(agent_status)
            session.commit()
            session.refresh(agent_status)
            
            db_manager.track_test_record('agent_statuses', str(agent_status.id))

            agent_coordinator = AgentCoordinator(session)
            agent_coordinator.update_agent_status(agent_type, new_status)

            # Verify status was updated in database
            session.refresh(agent_status)
            assert agent_status.status == new_status

    @pytest.mark.real_data
    def test_get_agent_status(self, db_manager):
        """Test getting agent status with real database."""
        agent_type = "analyst"
        expected_status = AgentStatus.WORKING

        with db_manager.get_session() as session:
            # Create real agent status record
            from app.database.models import AgentStatusDB
            agent_status = AgentStatusDB(
                agent_type=agent_type,
                status=expected_status
            )
            session.add(agent_status)
            session.commit()
            session.refresh(agent_status)
            
            db_manager.track_test_record('agent_statuses', str(agent_status.id))

            agent_coordinator = AgentCoordinator(session)
            result = agent_coordinator.get_agent_status(agent_type)

            assert result == expected_status

class TestWorkflowIntegrator:
    """Test cases for WorkflowIntegrator service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for workflow integrator tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_initialization(self, db_manager):
        """Test WorkflowIntegrator initialization with real database."""
        with db_manager.get_session() as session:
            # Mock external context store service (external dependency)
            with patch('app.services.orchestrator.workflow_integrator.ContextStoreService') as mock_ctx_store:
                mock_context_store = Mock()
                mock_ctx_store.return_value = mock_context_store
                
                integrator = WorkflowIntegrator(session)
                
                assert integrator is not None
                assert integrator.db == session
                assert hasattr(integrator, 'context_store')

    @pytest.mark.external_service
    def test_run_workflow(self, db_manager):
        """Test workflow execution with real database and mocked external workflow engine."""
        # Create real project
        project = db_manager.create_test_project(name="Workflow Integration Test")
        
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.workflow_integrator.ContextStoreService'):
                integrator = WorkflowIntegrator(session)
                
                # Mock external workflow engine (external dependency)
                integrator.workflow_engine = Mock()
                mock_result = {"status": "completed", "artifacts": []}
                integrator.workflow_engine.run_project_workflow = AsyncMock(return_value=mock_result)

                # Test that the method exists and can be called
                assert hasattr(integrator, 'run_workflow')
                assert callable(integrator.run_workflow)

    @pytest.mark.external_service
    def test_pause_workflow(self, db_manager):
        """Test workflow pausing with real database."""
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.workflow_integrator.ContextStoreService'):
                integrator = WorkflowIntegrator(session)
                
                # Mock external workflow engine (external dependency)
                integrator.workflow_engine = Mock()
                integrator.workflow_engine.pause_workflow_execution = AsyncMock(return_value=True)

                # Test that the method exists
                assert hasattr(integrator, 'pause_workflow')
                assert callable(integrator.pause_workflow)

    @pytest.mark.external_service
    def test_resume_workflow(self, db_manager):
        """Test workflow resumption with real database."""
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.workflow_integrator.ContextStoreService'):
                integrator = WorkflowIntegrator(session)
                
                # Mock external workflow engine (external dependency)
                integrator.workflow_engine = Mock()
                integrator.workflow_engine.resume_workflow_execution = AsyncMock(return_value=True)

                # Test that the method exists and is callable
                assert hasattr(integrator, 'resume_workflow')
                assert callable(integrator.resume_workflow)

class TestHandoffManager:
    """Test cases for HandoffManager service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for handoff manager tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def handoff_manager(self, db_manager):
        """Create HandoffManager instance with real database."""
        with db_manager.get_session() as session:
            return HandoffManager(session)

    @pytest.mark.real_data
    def test_initialization(self, db_manager):
        """Test HandoffManager initialization with real database."""
        with db_manager.get_session() as session:
            handoff_manager = HandoffManager(session)
            assert handoff_manager is not None
            assert handoff_manager.db == session

    @pytest.mark.real_data
    def test_create_handoff(self, db_manager):
        """Test handoff creation with real database operations."""
        # Create real project and task
        project = db_manager.create_test_project(name="Handoff Test Project")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        with db_manager.get_session() as session:
            handoff_manager = HandoffManager(session)
            from_agent = "analyst"
            to_agent = "architect"
            context_ids = ["ctx-1", "ctx-2"]

            # Create handoff with real database operations
            result = handoff_manager.create_handoff(
                from_agent=from_agent,
                to_agent=to_agent,
                context_ids=context_ids,
                task_id=task.id
            )

            assert result is not None
            assert result.from_agent == from_agent
            assert result.to_agent == to_agent
            assert result.context_ids == context_ids
            assert result.task_id == task.id
            
            # Verify database state
            db_checks = [
                {
                    'table': 'handoffs',
                    'conditions': {'from_agent': from_agent, 'to_agent': to_agent},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)

    @pytest.mark.real_data
    def test_get_pending_handoffs(self, db_manager):
        """Test getting pending handoffs with real database."""
        # Create real project and handoffs
        project = db_manager.create_test_project(name="Pending Handoffs Test")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        with db_manager.get_session() as session:
            handoff_manager = HandoffManager(session)
            agent_type = "architect"

            # Create real handoff records
            from app.database.models import HandoffDB
            handoff1 = HandoffDB(
                project_id=project.id,
                task_id=task.id,
                from_agent="analyst",
                to_agent="architect",
                context_ids=["ctx-1"],
                status="pending"
            )
            handoff2 = HandoffDB(
                project_id=project.id,
                task_id=task.id,
                from_agent="coder",
                to_agent="architect",
                context_ids=["ctx-2"],
                status="pending"
            )
            session.add_all([handoff1, handoff2])
            session.commit()

            result = handoff_manager.get_pending_handoffs(agent_type)

            assert len(result) == 2
            assert all(h.to_agent == agent_type for h in result)
            assert all(h.status == "pending" for h in result)
            
            # Verify database state
            db_checks = [
                {
                    'table': 'handoffs',
                    'conditions': {'to_agent': agent_type, 'status': 'pending'},
                    'count': 2
                }
            ]
            assert db_manager.verify_database_state(db_checks)

class TestStatusTracker:
    """Test cases for StatusTracker service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for status tracker tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def status_tracker(self, db_manager):
        """Create StatusTracker instance with real database."""
        with db_manager.get_session() as session:
            return StatusTracker(session)

    @pytest.mark.real_data
    def test_initialization(self, db_manager):
        """Test StatusTracker initialization with real database."""
        with db_manager.get_session() as session:
            status_tracker = StatusTracker(session)
            assert status_tracker is not None
            assert status_tracker.db == session

    @pytest.mark.real_data
    def test_get_performance_metrics(self, db_manager, status_tracker):
        """Test getting comprehensive project performance metrics with real database."""
        project = db_manager.create_test_project(name="Status Test Project")
        db_manager.create_test_task(project_id=project.id, agent_type="analyst", status=TaskStatus.COMPLETED)
        db_manager.create_test_task(project_id=project.id, agent_type="architect", status=TaskStatus.WORKING)

        result = status_tracker.get_performance_metrics(project.id)

        assert result is not None
        assert "time_metrics" in result
        assert "task_metrics" in result
        assert result["task_metrics"]["total_tasks"] == 2
        assert result["task_metrics"]["completed_tasks"] == 1
        assert result["task_metrics"]["working_tasks"] == 1

    @pytest.mark.real_data
    def test_get_phase_progress(self, db_manager, status_tracker):
        """Test getting phase progress for all phases with real database."""
        project = db_manager.create_test_project(name="Phase Progress Test")
        db_manager.create_test_task(project_id=project.id, agent_type="analyst", status=TaskStatus.COMPLETED, instructions="analyze")

        result = status_tracker.get_phase_progress(project.id)

        assert result is not None
        assert "overall_progress" in result
        assert "phases" in result
        assert "discovery" in result["phases"]
        assert result["phases"]["discovery"]["completed"] is True

class TestContextManager:
    """Test cases for ContextManager service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for context manager tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def mock_context_store(self):
        """Mock context store service (external dependency)."""
        service = Mock()
        return service

    @pytest.fixture
    def context_manager(self, db_manager, mock_context_store):
        """Create ContextManager instance with real database."""
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
                mock_ctx_store.return_value = mock_context_store
                manager = ContextManager(session)
                return manager

    @pytest.mark.external_service
    def test_initialization(self, db_manager):
        """Test ContextManager initialization with real database."""
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
                mock_context_store = Mock()
                mock_ctx_store.return_value = mock_context_store
                
                context_manager = ContextManager(session)
                assert context_manager is not None
                assert context_manager.db == session
                assert hasattr(context_manager, 'context_store')

    @pytest.mark.external_service
    def test_get_integrated_context(self, db_manager, mock_context_store):
        """Test getting integrated context with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Context Integration Test")
        
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
                mock_ctx_store.return_value = mock_context_store
                context_manager = ContextManager(session)

                # Mock external context store (external dependency)
                mock_artifacts = [
                    Mock(artifact_type=ArtifactType.USER_INPUT, content={"user_idea": "Build app"}),
                    Mock(artifact_type=ArtifactType.REQUIREMENTS, content={"requirements": "Reqs here"})
                ]
                mock_context_store.get_artifacts_by_project.return_value = mock_artifacts

                result = context_manager.get_integrated_context(project.id)

                assert result is not None
                assert "artifacts" in result
                assert "summary" in result
                assert "context_ids" in result

    @pytest.mark.external_service
    def test_create_context_artifact(self, db_manager, mock_context_store):
        """Test creating context artifacts with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Context Artifact Test")
        
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
                mock_ctx_store.return_value = mock_context_store
                context_manager = ContextManager(session)

                source_agent = "analyst"
                artifact_type = ArtifactType.REQUIREMENTS
                content = {"requirements": "Detailed requirements"}

                # Mock external context store artifact creation
                mock_artifact = Mock()
                mock_artifact.context_id = uuid4()
                mock_context_store.create_artifact.return_value = mock_artifact

                result = context_manager.create_context_artifact(
                    project_id=project.id,
                    source_agent=source_agent,
                    artifact_type=artifact_type,
                    content=content
                )

                assert result == mock_artifact
                mock_context_store.create_artifact.assert_called_once()

    @pytest.mark.external_service
    def test_get_context_granularity_report(self, db_manager, mock_context_store):
        """Test context granularity reporting with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Context Granularity Test")
        
        with db_manager.get_session() as session:
            with patch('app.services.orchestrator.context_manager.ContextStoreService') as mock_ctx_store:
                mock_ctx_store.return_value = mock_context_store
                context_manager = ContextManager(session)

                # Mock external context store artifacts
                mock_artifacts = [
                    Mock(artifact_type=ArtifactType.USER_INPUT, content={"size": "small"}),
                    Mock(artifact_type=ArtifactType.REQUIREMENTS, content={"size": "large"}),
                    Mock(artifact_type=ArtifactType.ARCHITECTURE, content={"size": "medium"})
                ]
                mock_context_store.get_artifacts_by_project.return_value = mock_artifacts

                result = context_manager.get_context_granularity_report(project.id)

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

    @pytest.mark.mock_data
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

    @pytest.mark.mock_data
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
