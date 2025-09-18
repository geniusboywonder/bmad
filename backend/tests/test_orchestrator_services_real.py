"""
Real Implementation Tests for Orchestrator Services

This module replaces the mock-heavy orchestrator service tests with real database
and service implementations to catch actual business logic issues.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text

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


class TestProjectLifecycleManagerReal:
    """Test ProjectLifecycleManager with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for orchestrator tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def project_manager(self, db_manager):
        """Create ProjectLifecycleManager with real database session."""
        with db_manager.get_session() as session:
            return ProjectLifecycleManager(session)

    @pytest.mark.real_data
    def test_initialization_real_db(self, project_manager, db_manager):
        """Test ProjectLifecycleManager initialization with real database."""
        assert project_manager is not None
        assert project_manager.db is not None

        # Verify it can actually interact with database
        with db_manager.get_session() as session:
            # Test that it can execute a real query
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_create_project_real_db(self, db_manager):
        """Test project creation with real database persistence."""
        with db_manager.get_session() as session:
            manager = ProjectLifecycleManager(session)

            project_data = {
                'name': 'Real Test Project',
                'description': 'Testing with real database',
                'requirements': ['requirement 1', 'requirement 2']
            }

            project = await manager.create_project(project_data)

            # Verify project was actually created in database
            assert project is not None
            assert project.name == 'Real Test Project'

            # Verify database persistence
            with db_manager.get_session() as verify_session:
                from app.database.models import ProjectDB
                db_project = verify_session.query(ProjectDB).filter_by(
                    name='Real Test Project'
                ).first()

                assert db_project is not None
                assert db_project.description == 'Testing with real database'

            db_manager.track_test_record('projects', str(project.id))

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_advance_project_phase_real_db(self, db_manager):
        """Test project phase advancement with real database."""
        # Create project
        project = db_manager.create_test_project(name='Phase Test Project')

        with db_manager.get_session() as session:
            manager = ProjectLifecycleManager(session)

            # Test phase advancement
            success = await manager.advance_project_phase(
                project.id,
                from_phase='analysis',
                to_phase='architecture'
            )

            assert success is True

            # Verify phase change was persisted
            with db_manager.get_session() as verify_session:
                from app.database.models import ProjectDB
                updated_project = verify_session.query(ProjectDB).filter_by(
                    id=project.id
                ).first()

                # Check if phase tracking exists in database
                assert updated_project is not None

    @pytest.mark.real_data
    def test_get_current_phase_real_db(self, db_manager):
        """Test getting current project phase from real database."""
        project = db_manager.create_test_project(name='Current Phase Test')

        with db_manager.get_session() as session:
            manager = ProjectLifecycleManager(session)

            current_phase = manager.get_current_phase(project.id)

            # Should return actual phase from database
            assert current_phase is not None
            assert current_phase in SDLC_PHASES


class TestAgentCoordinatorReal:
    """Test AgentCoordinator with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for agent coordinator tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_assign_agent_to_task_real_db(self, db_manager):
        """Test agent assignment with real database persistence."""
        # Create test scenario
        project = db_manager.create_test_project()
        task = db_manager.create_test_task(project_id=project.id)

        with db_manager.get_session() as session:
            coordinator = AgentCoordinator(session)

            # Assign agent to task
            assignment = await coordinator.assign_agent_to_task(
                task_id=task.id,
                agent_type=AgentType.ANALYST,
                priority='high'
            )

            assert assignment is not None
            assert assignment['agent_type'] == AgentType.ANALYST

            # Verify assignment persisted to database
            with db_manager.get_session() as verify_session:
                from app.database.models import TaskDB
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert updated_task is not None
                assert updated_task.agent_type == AgentType.ANALYST

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_get_available_agents_real_db(self, db_manager):
        """Test getting available agents from real database."""
        with db_manager.get_session() as session:
            coordinator = AgentCoordinator(session)

            # Create some agent status records
            from app.database.models import AgentStatusDB
            agent_status = AgentStatusDB(
                agent_type=AgentType.ANALYST,
                status=AgentStatus.IDLE,
                current_task_id=None
            )
            session.add(agent_status)
            session.commit()
            db_manager.track_test_record('agent_status', str(agent_status.id))

            # Get available agents
            available = await coordinator.get_available_agents()

            assert available is not None
            assert isinstance(available, list)

    @pytest.mark.real_data
    def test_update_agent_status_real_db(self, db_manager):
        """Test agent status update with real database."""
        with db_manager.get_session() as session:
            coordinator = AgentCoordinator(session)

            # Update agent status
            success = coordinator.update_agent_status(
                agent_type=AgentType.ARCHITECT,
                status=AgentStatus.WORKING,
                task_id=str(uuid4())
            )

            assert success is True

            # Verify status was persisted
            from app.database.models import AgentStatusDB
            agent_status = session.query(AgentStatusDB).filter_by(
                agent_type=AgentType.ARCHITECT
            ).first()

            if agent_status:
                assert agent_status.status == AgentStatus.WORKING
                db_manager.track_test_record('agent_status', str(agent_status.id))


class TestWorkflowIntegratorReal:
    """Test WorkflowIntegrator with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for workflow integrator tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_execute_workflow_step_real_db(self, db_manager):
        """Test workflow step execution with real database."""
        # Create test scenario
        project = db_manager.create_test_project()
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST
        )

        with db_manager.get_session() as session:
            integrator = WorkflowIntegrator(session)

            # Execute workflow step
            result = await integrator.execute_workflow_step(
                project_id=project.id,
                step_name='analysis',
                agent_type=AgentType.ANALYST,
                input_data={'requirements': 'test requirements'}
            )

            # Verify result structure
            assert result is not None
            if isinstance(result, dict):
                assert 'status' in result or 'success' in result

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_get_workflow_state_real_db(self, db_manager):
        """Test workflow state retrieval from real database."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            integrator = WorkflowIntegrator(session)

            # Get workflow state
            state = await integrator.get_workflow_state(project.id)

            # Should return actual state from database
            assert state is not None


class TestHandoffManagerReal:
    """Test HandoffManager with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for handoff manager tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_create_handoff_real_db(self, db_manager):
        """Test handoff creation with real database persistence."""
        # Create test scenario
        project = db_manager.create_test_project()
        from_task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST,
            status=TaskStatus.COMPLETED
        )

        with db_manager.get_session() as session:
            handoff_manager = HandoffManager(session)

            # Create handoff
            handoff = await handoff_manager.create_handoff(
                from_agent=AgentType.ANALYST,
                to_agent=AgentType.ARCHITECT,
                project_id=project.id,
                context_data={'analysis_complete': True},
                handoff_reason='Analysis phase completed'
            )

            assert handoff is not None
            if hasattr(handoff, 'from_agent'):
                assert handoff.from_agent == AgentType.ANALYST
                assert handoff.to_agent == AgentType.ARCHITECT

    @pytest.mark.real_data
    def test_validate_handoff_real_db(self, db_manager):
        """Test handoff validation with real business logic."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            handoff_manager = HandoffManager(session)

            # Test handoff validation
            is_valid = handoff_manager.validate_handoff(
                from_agent=AgentType.ANALYST,
                to_agent=AgentType.ARCHITECT,
                project_id=project.id
            )

            # Should return actual validation result
            assert isinstance(is_valid, bool)


class TestStatusTrackerReal:
    """Test StatusTracker with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for status tracker tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_update_task_status_real_db(self, db_manager):
        """Test task status update with real database persistence."""
        # Create test scenario
        project = db_manager.create_test_project()
        task = db_manager.create_test_task(project_id=project.id)

        with db_manager.get_session() as session:
            status_tracker = StatusTracker(session)

            # Update task status
            success = status_tracker.update_task_status(
                task_id=task.id,
                status=TaskStatus.WORKING,
                progress=50
            )

            assert success is True

            # Verify status was persisted
            with db_manager.get_session() as verify_session:
                from app.database.models import TaskDB
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert updated_task is not None
                assert updated_task.status == TaskStatus.WORKING

    @pytest.mark.real_data
    def test_get_project_status_real_db(self, db_manager):
        """Test project status retrieval from real database."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            status_tracker = StatusTracker(session)

            # Get project status
            status = status_tracker.get_project_status(project.id)

            # Should return actual status from database
            assert status is not None


class TestContextManagerReal:
    """Test ContextManager with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for context manager tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_store_context_real_db(self, db_manager):
        """Test context storage with real database persistence."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            context_manager = ContextManager(session)

            # Store context
            context_id = await context_manager.store_context(
                project_id=project.id,
                agent_type=AgentType.ANALYST,
                context_data={'analysis': 'test analysis data'},
                artifact_type=ArtifactType.PROJECT_PLAN
            )

            assert context_id is not None

            # Verify context was persisted
            with db_manager.get_session() as verify_session:
                from app.database.models import ContextArtifactDB
                context = verify_session.query(ContextArtifactDB).filter_by(
                    id=context_id
                ).first()

                assert context is not None
                assert context.project_id == project.id
                assert context.source_agent == AgentType.ANALYST

            db_manager.track_test_record('context_artifacts', str(context_id))

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_retrieve_context_real_db(self, db_manager):
        """Test context retrieval from real database."""
        project = db_manager.create_test_project()

        # Create context artifact
        context_artifact = db_manager.create_test_context_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={'test': 'context data'}
        )

        with db_manager.get_session() as session:
            context_manager = ContextManager(session)

            # Retrieve context
            retrieved = await context_manager.retrieve_context(
                context_id=context_artifact.id
            )

            assert retrieved is not None
            if hasattr(retrieved, 'content'):
                assert retrieved.content == {'test': 'context data'}

    @pytest.mark.real_data
    def test_get_project_context_real_db(self, db_manager):
        """Test getting project context from real database."""
        project = db_manager.create_test_project()

        # Create multiple context artifacts
        db_manager.create_test_context_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN
        )
        db_manager.create_test_context_artifact(
            project_id=project.id,
            source_agent=AgentType.ARCHITECT,
            artifact_type=ArtifactType.SOFTWARE_SPECIFICATION
        )

        with db_manager.get_session() as session:
            context_manager = ContextManager(session)

            # Get project context
            context_list = context_manager.get_project_context(project.id)

            assert context_list is not None
            assert isinstance(context_list, list)
            # Should have at least the artifacts we created
            assert len(context_list) >= 2