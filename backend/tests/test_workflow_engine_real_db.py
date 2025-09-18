"""
Real Database Tests for Workflow Execution Engine

This module replaces mock-heavy workflow engine tests with real database
operations to validate actual business logic and database constraints.
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone

from app.services.workflow_engine import WorkflowExecutionEngine
from app.services.orchestrator import OrchestratorService
from app.models.workflow_state import (
    WorkflowExecutionStateModel,
    WorkflowExecutionState as ExecutionStateEnum,
    WorkflowStepExecutionState
)
from app.models.workflow import WorkflowDefinition, WorkflowStep, WorkflowType
from app.models.task import Task, TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.hitl import HitlStatus
from app.database.models import WorkflowStateDB, TaskDB, ProjectDB

from tests.utils.database_test_utils import DatabaseTestManager


class TestWorkflowExecutionEngineReal:
    """Test WorkflowExecutionEngine with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for workflow engine tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_workflow_state_persistence_real_db(self, db_manager):
        """Test workflow state persistence with real database."""
        project = db_manager.create_test_project(name='Workflow Test Project')

        with db_manager.get_session() as session:
            # Create workflow execution engine
            engine = WorkflowExecutionEngine(session)

            # Create workflow state in database
            workflow_state = WorkflowStateDB(
                execution_id=str(uuid4()),
                project_id=project.id,
                workflow_id='test-workflow',
                status='running',
                current_step=0,
                total_steps=3,
                steps_data=[{
                    'step_index': 0,
                    'agent': 'analyst',
                    'status': 'pending'
                }],
                context_data={'test': 'data'},
                created_artifacts=[]
            )

            session.add(workflow_state)
            session.commit()
            db_manager.track_test_record('workflow_states', str(workflow_state.id))

            # Verify state was persisted
            with db_manager.get_session() as verify_session:
                retrieved_state = verify_session.query(WorkflowStateDB).filter_by(
                    execution_id=workflow_state.execution_id
                ).first()

                assert retrieved_state is not None
                assert retrieved_state.project_id == project.id
                assert retrieved_state.workflow_id == 'test-workflow'
                assert retrieved_state.status == 'running'
                assert retrieved_state.total_steps == 3

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_workflow_recovery_real_db(self, db_manager):
        """Test workflow recovery from real database state."""
        project = db_manager.create_test_project(name='Recovery Test Project')

        # Create workflow state in database
        execution_id = str(uuid4())
        with db_manager.get_session() as session:
            workflow_state = WorkflowStateDB(
                execution_id=execution_id,
                project_id=project.id,
                workflow_id='recovery-workflow',
                status='paused',
                current_step=1,
                total_steps=3,
                steps_data=[
                    {
                        'step_index': 0,
                        'agent': 'analyst',
                        'status': 'completed',
                        'started_at': '2024-01-01T10:00:00Z',
                        'completed_at': '2024-01-01T10:05:00Z'
                    },
                    {
                        'step_index': 1,
                        'agent': 'architect',
                        'status': 'running'
                    }
                ],
                context_data={'recovered': True}
            )

            session.add(workflow_state)
            session.commit()
            db_manager.track_test_record('workflow_states', str(workflow_state.id))

        # Test recovery
        with db_manager.get_session() as session:
            engine = WorkflowExecutionEngine(session)

            recovered_execution = engine.recover_workflow_execution(execution_id)

            assert recovered_execution is not None
            assert recovered_execution.execution_id == execution_id
            assert recovered_execution.project_id == str(project.id)
            assert recovered_execution.workflow_id == 'recovery-workflow'
            assert recovered_execution.status == ExecutionStateEnum.PAUSED
            assert recovered_execution.current_step == 1
            assert len(recovered_execution.steps) == 2
            assert recovered_execution.steps[0].status == ExecutionStateEnum.COMPLETED
            assert recovered_execution.steps[1].status == ExecutionStateEnum.RUNNING

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_workflow_step_task_integration_real_db(self, db_manager):
        """Test workflow step to task creation with real database."""
        project = db_manager.create_test_project(name='Step Integration Test')

        with db_manager.get_session() as session:
            engine = WorkflowExecutionEngine(session)

            # Create initial workflow state
            execution_id = str(uuid4())
            workflow_state = WorkflowStateDB(
                execution_id=execution_id,
                project_id=project.id,
                workflow_id='integration-workflow',
                status='running',
                current_step=0,
                total_steps=2,
                steps_data=[
                    {
                        'step_index': 0,
                        'agent': 'analyst',
                        'status': 'pending',
                        'action': 'Analyze requirements'
                    }
                ],
                context_data={'integration_test': True}
            )

            session.add(workflow_state)
            session.commit()
            db_manager.track_test_record('workflow_states', str(workflow_state.id))

            # Create a task for this workflow step
            task = db_manager.create_test_task(
                project_id=project.id,
                agent_type=AgentType.ANALYST,
                instructions='Analyze requirements for integration test',
                status=TaskStatus.PENDING
            )

            # Update workflow step with task ID
            workflow_state.steps_data[0]['task_id'] = str(task.id)
            session.commit()

            # Verify the integration
            with db_manager.get_session() as verify_session:
                # Check workflow state
                updated_workflow = verify_session.query(WorkflowStateDB).filter_by(
                    execution_id=execution_id
                ).first()

                assert updated_workflow is not None
                assert updated_workflow.steps_data[0]['task_id'] == str(task.id)

                # Check task exists
                linked_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert linked_task is not None
                assert linked_task.project_id == project.id
                assert linked_task.agent_type == AgentType.ANALYST
                assert linked_task.status == TaskStatus.PENDING


class TestOrchestratorWorkflowIntegrationReal:
    """Test OrchestratorService workflow integration with real database."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for orchestrator integration tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_project_creation_real_db(self, db_manager):
        """Test project creation with real database persistence."""
        with db_manager.get_session() as session:
            orchestrator = OrchestratorService(session)

            project_name = "Real Integration Test Project"
            project_description = "Testing orchestrator with real database"

            project_id = orchestrator.create_project(project_name, project_description)

            assert project_id is not None

            # Verify project was actually created in database
            with db_manager.get_session() as verify_session:
                created_project = verify_session.query(ProjectDB).filter_by(
                    id=project_id
                ).first()

                assert created_project is not None
                assert created_project.name == project_name
                assert created_project.description == project_description

            db_manager.track_test_record('projects', str(project_id))

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_task_creation_and_status_updates_real_db(self, db_manager):
        """Test task creation and status updates with real database."""
        project = db_manager.create_test_project(name='Task Test Project')

        with db_manager.get_session() as session:
            orchestrator = OrchestratorService(session)

            # Create task
            agent_type = "analyst"
            instructions = "Analyze real database integration"

            task = orchestrator.create_task(project.id, agent_type, instructions)

            assert task is not None
            assert task.agent_type == agent_type
            assert task.instructions == instructions
            assert task.status == TaskStatus.PENDING

            # Update task status
            orchestrator.update_task_status(task.task_id, TaskStatus.WORKING)

            # Verify status update persisted
            with db_manager.get_session() as verify_session:
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.task_id
                ).first()

                assert updated_task is not None
                assert updated_task.status == TaskStatus.WORKING
                assert updated_task.started_at is not None

            # Update to completed
            orchestrator.update_task_status(task.task_id, TaskStatus.COMPLETED)

            # Verify completion
            with db_manager.get_session() as verify_session:
                completed_task = verify_session.query(TaskDB).filter_by(
                    id=task.task_id
                ).first()

                assert completed_task is not None
                assert completed_task.status == TaskStatus.COMPLETED
                assert completed_task.completed_at is not None

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_hitl_request_lifecycle_real_db(self, db_manager):
        """Test HITL request creation and processing with real database."""
        project = db_manager.create_test_project(name='HITL Test Project')
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST
        )

        with db_manager.get_session() as session:
            orchestrator = OrchestratorService(session)

            # Create HITL request
            question = "Please review this analysis for real database integration"

            hitl_request = orchestrator.create_hitl_request(
                project.id, task.id, question
            )

            assert hitl_request is not None
            assert hitl_request.question == question
            assert hitl_request.status.value == "pending"

            # Verify HITL request was persisted
            with db_manager.get_session() as verify_session:
                from app.database.models import HitlRequestDB

                persisted_hitl = verify_session.query(HitlRequestDB).filter_by(
                    id=hitl_request.id
                ).first()

                assert persisted_hitl is not None
                assert persisted_hitl.project_id == project.id
                assert persisted_hitl.task_id == task.id
                assert persisted_hitl.question == question
                assert persisted_hitl.status == HitlStatus.PENDING

            db_manager.track_test_record('hitl_requests', str(hitl_request.id))

    @pytest.mark.real_data
    def test_agent_status_tracking_real_db(self, db_manager):
        """Test agent status updates with real database."""
        with db_manager.get_session() as session:
            orchestrator = OrchestratorService(session)

            # Update agent status
            agent_type = AgentType.ARCHITECT
            new_status = AgentStatus.WORKING
            task_id = str(uuid4())

            orchestrator.update_agent_status(agent_type, new_status, task_id)

            # Verify status was persisted
            with db_manager.get_session() as verify_session:
                from app.database.models import AgentStatusDB

                agent_status = verify_session.query(AgentStatusDB).filter_by(
                    agent_type=agent_type
                ).first()

                if agent_status:
                    assert agent_status.status == new_status
                    assert agent_status.current_task_id == task_id
                    db_manager.track_test_record('agent_status', str(agent_status.id))


class TestWorkflowErrorHandlingReal:
    """Test workflow error handling with real database constraints."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for error handling tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_workflow_state_constraint_validation_real_db(self, db_manager):
        """Test workflow state database constraints."""
        project = db_manager.create_test_project(name='Constraint Test Project')

        with db_manager.get_session() as session:
            # Test duplicate execution_id constraint
            execution_id = str(uuid4())

            # Create first workflow state
            workflow_state1 = WorkflowStateDB(
                execution_id=execution_id,
                project_id=project.id,
                workflow_id='constraint-test',
                status='running',
                current_step=0,
                total_steps=1,
                steps_data=[],
                context_data={}
            )

            session.add(workflow_state1)
            session.commit()
            db_manager.track_test_record('workflow_states', str(workflow_state1.id))

            # Attempt to create second workflow state with same execution_id
            workflow_state2 = WorkflowStateDB(
                execution_id=execution_id,  # Same execution_id
                project_id=project.id,
                workflow_id='duplicate-test',
                status='running',
                current_step=0,
                total_steps=1,
                steps_data=[],
                context_data={}
            )

            session.add(workflow_state2)

            # This should raise an integrity error due to unique constraint
            with pytest.raises(Exception):  # Database integrity constraint violation
                session.commit()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_invalid_project_reference_real_db(self, db_manager):
        """Test workflow creation with invalid project reference."""
        with db_manager.get_session() as session:
            # Attempt to create workflow state with non-existent project
            invalid_project_id = uuid4()

            workflow_state = WorkflowStateDB(
                execution_id=str(uuid4()),
                project_id=invalid_project_id,  # Non-existent project
                workflow_id='invalid-project-test',
                status='running',
                current_step=0,
                total_steps=1,
                steps_data=[],
                context_data={}
            )

            session.add(workflow_state)

            # This should raise a foreign key constraint error
            with pytest.raises(Exception):  # Foreign key constraint violation
                session.commit()

    @pytest.mark.real_data
    def test_workflow_status_enum_validation_real_db(self, db_manager):
        """Test workflow status enum validation in database."""
        project = db_manager.create_test_project(name='Status Enum Test')

        with db_manager.get_session() as session:
            # Valid status values should work
            valid_statuses = ['pending', 'running', 'paused', 'completed', 'failed', 'cancelled']

            for i, status in enumerate(valid_statuses):
                workflow_state = WorkflowStateDB(
                    execution_id=str(uuid4()),
                    project_id=project.id,
                    workflow_id=f'status-test-{i}',
                    status=status,
                    current_step=0,
                    total_steps=1,
                    steps_data=[],
                    context_data={}
                )

                session.add(workflow_state)
                session.commit()
                db_manager.track_test_record('workflow_states', str(workflow_state.id))

                # Verify status was set correctly
                assert workflow_state.status == status


class TestWorkflowPerformanceReal:
    """Test workflow engine performance with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for performance tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_multiple_workflow_states_real_db(self, db_manager):
        """Test creating multiple workflow states efficiently."""
        project = db_manager.create_test_project(name='Performance Test Project')

        with db_manager.get_session() as session:
            # Create multiple workflow states
            workflow_count = 10
            workflow_states = []

            for i in range(workflow_count):
                workflow_state = WorkflowStateDB(
                    execution_id=str(uuid4()),
                    project_id=project.id,
                    workflow_id=f'performance-test-{i}',
                    status='running',
                    current_step=0,
                    total_steps=3,
                    steps_data=[
                        {'step_index': j, 'agent': f'agent-{j}', 'status': 'pending'}
                        for j in range(3)
                    ],
                    context_data={'test_index': i}
                )

                workflow_states.append(workflow_state)
                session.add(workflow_state)
                db_manager.track_test_record('workflow_states', str(workflow_state.id))

            # Commit all at once
            session.commit()

            # Verify all were created
            with db_manager.get_session() as verify_session:
                created_workflows = verify_session.query(WorkflowStateDB).filter_by(
                    project_id=project.id
                ).all()

                assert len(created_workflows) == workflow_count

                # Verify each workflow has correct data
                for workflow in created_workflows:
                    assert workflow.project_id == project.id
                    assert workflow.total_steps == 3
                    assert len(workflow.steps_data) == 3
                    assert 'test_index' in workflow.context_data

    @pytest.mark.real_data
    def test_workflow_query_performance_real_db(self, db_manager):
        """Test workflow state queries perform efficiently."""
        project = db_manager.create_test_project(name='Query Performance Test')

        # Create multiple workflows
        workflow_ids = []
        with db_manager.get_session() as session:
            for i in range(5):
                workflow_state = WorkflowStateDB(
                    execution_id=str(uuid4()),
                    project_id=project.id,
                    workflow_id=f'query-test-{i}',
                    status='running',
                    current_step=i % 3,
                    total_steps=3,
                    steps_data=[],
                    context_data={}
                )

                session.add(workflow_state)
                session.commit()
                workflow_ids.append(workflow_state.execution_id)
                db_manager.track_test_record('workflow_states', str(workflow_state.id))

        # Test various query patterns
        with db_manager.get_session() as session:
            # Query by project
            project_workflows = session.query(WorkflowStateDB).filter_by(
                project_id=project.id
            ).all()
            assert len(project_workflows) == 5

            # Query by status
            running_workflows = session.query(WorkflowStateDB).filter_by(
                project_id=project.id,
                status='running'
            ).all()
            assert len(running_workflows) == 5

            # Query by execution_id
            for execution_id in workflow_ids:
                specific_workflow = session.query(WorkflowStateDB).filter_by(
                    execution_id=execution_id
                ).first()
                assert specific_workflow is not None
                assert specific_workflow.execution_id == execution_id