"""
Test suite for Workflow Execution Engine

This module contains comprehensive tests for the workflow execution engine,
including dynamic workflow loading, agent handoffs, state persistence,
and complete SDLC workflow execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.services.workflow_engine import WorkflowExecutionEngine
from app.services.orchestrator import OrchestratorService
from app.models.workflow_state import (
    WorkflowExecutionStateModel,
    WorkflowExecutionState as ExecutionStateEnum,
    WorkflowStepExecutionState
)
from app.models.workflow import WorkflowDefinition, WorkflowStep, WorkflowType
from app.models.task import Task, TaskStatus
from app.models.agent import AgentType
from app.database.models import WorkflowStateDB
from app.services.context_store import ContextStoreService


class TestWorkflowExecutionEngine:
    """Test cases for the Workflow Execution Engine."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_workflow_service(self):
        """Mock workflow service."""
        service = Mock()

        # Mock workflow definition
        mock_workflow = WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            type=WorkflowType.GENERIC,
            sequence=[
                WorkflowStep(
                    agent="analyst",
                    creates="requirements",
                    action="Analyze requirements"
                ),
                WorkflowStep(
                    agent="architect",
                    requires="requirements",
                    creates="architecture",
                    action="Design architecture"
                ),
                WorkflowStep(
                    agent="coder",
                    requires="architecture",
                    creates="code",
                    action="Implement code"
                )
            ]
        )
        service.load_workflow.return_value = mock_workflow
        return service

    @pytest.fixture
    def mock_context_store(self):
        """Mock context store service."""
        service = Mock()
        mock_artifact = Mock()
        mock_artifact.context_id = str(uuid4())
        service.create_artifact.return_value = mock_artifact
        service.get_artifacts_by_ids.return_value = []
        return service

    @pytest.fixture
    def mock_autogen_service(self):
        """Mock AutoGen service."""
        service = Mock()
        service.execute_task = AsyncMock(return_value={
            "success": True,
            "result": "Task completed successfully",
            "artifacts": []
        })
        return service

    @pytest.fixture
    def workflow_engine(self, mock_db, mock_workflow_service, mock_context_store, mock_autogen_service):
        """Create workflow engine with mocked dependencies."""
        engine = WorkflowExecutionEngine(mock_db)
        engine.workflow_service = mock_workflow_service
        engine.context_store = mock_context_store
        engine.autogen_service = mock_autogen_service
        return engine

    @pytest.mark.asyncio
    async def test_start_workflow_execution(self, workflow_engine, mock_db):
        """Test starting a workflow execution."""
        project_id = str(uuid4())
        workflow_id = "test-workflow"

        # Mock database operations
        mock_db_state = Mock()
        mock_db_state.execution_id = "test-execution-id"
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        execution = await workflow_engine.start_workflow_execution(
            workflow_id=workflow_id,
            project_id=project_id,
            context_data={"test": "data"}
        )

        assert execution.workflow_id == workflow_id
        assert execution.project_id == project_id
        assert execution.status == ExecutionStateEnum.RUNNING  # Status changes to RUNNING after mark_started()
        assert execution.total_steps == 3  # Based on our mock workflow
        assert len(execution.steps) == 3

        # Verify database persistence was called
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_execute_workflow_step(self, workflow_engine):
        """Test executing a workflow step."""
        execution_id = "test-execution-id"

        # Create a mock execution state
        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            project_id=str(uuid4()),
            workflow_id="test-workflow",
            total_steps=3,
            steps=[
                WorkflowStepExecutionState(
                    step_index=0,
                    agent="analyst",
                    status=ExecutionStateEnum.PENDING
                ),
                WorkflowStepExecutionState(
                    step_index=1,
                    agent="architect",
                    status=ExecutionStateEnum.PENDING
                )
            ]
        )

        # Mock the execution state retrieval
        workflow_engine._active_executions[execution_id] = execution

        # Mock task creation
        mock_task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type="analyst",
            instructions="Test task",
            context_ids=[]
        )
        workflow_engine._create_agent_task = AsyncMock(return_value=mock_task)

        result = await workflow_engine.execute_workflow_step(execution_id)

        assert result["status"] == "completed"
        assert result["agent"] == "analyst"
        assert execution.steps[0].status == ExecutionStateEnum.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_step_execution(self, workflow_engine):
        """Test executing multiple steps in parallel."""
        execution_id = "test-execution-id"

        # Create execution with multiple pending steps
        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            project_id=str(uuid4()),
            workflow_id="test-workflow",
            total_steps=3,
            steps=[
                WorkflowStepExecutionState(
                    step_index=0,
                    agent="analyst",
                    status=ExecutionStateEnum.PENDING
                ),
                WorkflowStepExecutionState(
                    step_index=1,
                    agent="architect",
                    status=ExecutionStateEnum.PENDING
                ),
                WorkflowStepExecutionState(
                    step_index=2,
                    agent="coder",
                    status=ExecutionStateEnum.PENDING
                )
            ]
        )

        workflow_engine._active_executions[execution_id] = execution

        # Mock task creation with proper Task objects
        mock_task1 = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type="analyst",
            instructions="Test task 1",
            context_ids=[]
        )
        mock_task2 = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type="architect",
            instructions="Test task 2",
            context_ids=[]
        )

        workflow_engine._create_agent_task = AsyncMock(side_effect=[mock_task1, mock_task2])

        result = await workflow_engine.execute_parallel_steps(
            execution_id,
            [0, 1]  # Execute first two steps in parallel
        )

        assert result["success_count"] == 2
        assert result["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_workflow_pause_resume(self, workflow_engine):
        """Test pausing and resuming workflow execution."""
        execution_id = "test-execution-id"

        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            project_id=str(uuid4()),
            workflow_id="test-workflow",
            status=ExecutionStateEnum.RUNNING
        )

        workflow_engine._active_executions[execution_id] = execution

        # Test pause
        pause_result = await workflow_engine.pause_workflow_execution(
            execution_id,
            "User requested pause"
        )
        assert pause_result is True
        assert execution.status == ExecutionStateEnum.PAUSED
        assert execution.paused_reason == "User requested pause"

        # Test resume
        resume_result = await workflow_engine.resume_workflow_execution(execution_id)
        assert resume_result is True
        assert execution.status == ExecutionStateEnum.RUNNING
        assert execution.paused_reason is None

    @pytest.mark.asyncio
    async def test_workflow_recovery(self, workflow_engine, mock_db):
        """Test workflow execution recovery from database."""
        execution_id = "test-execution-id"

        # Mock database state
        mock_db_state = Mock()
        mock_db_state.execution_id = execution_id
        mock_db_state.project_id = uuid4()
        mock_db_state.workflow_id = "test-workflow"
        mock_db_state.status = "running"
        mock_db_state.current_step = 1
        mock_db_state.total_steps = 3
        mock_db_state.steps_data = [
            {
                "step_index": 0,
                "agent": "analyst",
                "status": "completed",
                "started_at": "2024-01-01T10:00:00",
                "completed_at": "2024-01-01T10:05:00"
            }
        ]
        mock_db_state.context_data = {"test": "data"}
        mock_db_state.created_artifacts = []
        mock_db_state.error_message = None
        mock_db_state.started_at = None
        mock_db_state.completed_at = None
        mock_db_state.created_at = "2024-01-01T10:00:00"
        mock_db_state.updated_at = "2024-01-01T10:05:00"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_db_state

        recovered_execution = workflow_engine.recover_workflow_execution(execution_id)

        assert recovered_execution is not None
        assert recovered_execution.execution_id == execution_id
        assert recovered_execution.status == ExecutionStateEnum.RUNNING
        assert len(recovered_execution.steps) == 1
        assert recovered_execution.steps[0].agent == "analyst"

    def test_workflow_status_tracking(self, workflow_engine):
        """Test workflow execution status tracking."""
        execution_id = "test-execution-id"

        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            project_id=str(uuid4()),
            workflow_id="test-workflow",
            total_steps=3,
            steps=[
                WorkflowStepExecutionState(
                    step_index=0,
                    agent="analyst",
                    status=ExecutionStateEnum.COMPLETED
                ),
                WorkflowStepExecutionState(
                    step_index=1,
                    agent="architect",
                    status=ExecutionStateEnum.RUNNING
                ),
                WorkflowStepExecutionState(
                    step_index=2,
                    agent="coder",
                    status=ExecutionStateEnum.PENDING
                )
            ]
        )

        workflow_engine._active_executions[execution_id] = execution

        status = workflow_engine.get_workflow_execution_status(execution_id)

        assert status is not None
        assert status["execution_id"] == execution_id
        assert status["status"] == "running"
        assert status["completed_steps"] == 1
        assert status["pending_steps"] == 1
        assert status["failed_steps"] == 0
        assert status["can_resume"] is True


class TestOrchestratorWorkflowIntegration:
    """Integration tests for orchestrator with workflow engine."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def orchestrator_service(self, mock_db):
        """Create orchestrator service with mocked database."""
        return OrchestratorService(mock_db)

    @pytest.mark.asyncio
    async def test_run_project_workflow_sync(self, orchestrator_service, mock_db):
        """Test synchronous workflow execution wrapper."""
        project_id = uuid4()
        user_idea = "Build a simple web application"

        # Mock the async method
        with patch.object(orchestrator_service, 'run_project_workflow', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"status": "completed"}

            # This should work without hanging
            result = orchestrator_service.run_project_workflow_sync(
                project_id,
                user_idea,
                "greenfield-fullstack"
            )

            # Verify the async method was called
            mock_run.assert_called_once_with(
                project_id,
                user_idea,
                "greenfield-fullstack"
            )

    def test_create_project(self, orchestrator_service, mock_db):
        """Test project creation."""
        project_name = "Test Project"
        project_description = "A test project"

        # Mock database operations
        mock_project = Mock()
        mock_project.id = uuid4()
        mock_project.name = project_name
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_project

        result = orchestrator_service.create_project(project_name, project_description)

        assert result == mock_project.id
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_task(self, orchestrator_service, mock_db):
        """Test task creation."""
        project_id = uuid4()
        agent_type = "analyst"
        instructions = "Analyze requirements"

        # Mock database operations
        mock_task = Mock()
        mock_task.id = uuid4()
        mock_task.project_id = project_id
        mock_task.agent_type = agent_type
        mock_task.instructions = instructions
        mock_task.context_ids = []
        mock_task.status = TaskStatus.PENDING
        mock_task.output = None
        mock_task.error_message = None
        mock_task.created_at = "2024-01-01T10:00:00"
        mock_task.updated_at = "2024-01-01T10:00:00"
        mock_task.started_at = None
        mock_task.completed_at = None

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_task

        task = orchestrator_service.create_task(project_id, agent_type, instructions)

        assert task.task_id == mock_task.id
        assert task.agent_type == agent_type
        assert task.instructions == instructions

    def test_hitl_request_creation(self, orchestrator_service, mock_db):
        """Test HITL request creation."""
        project_id = uuid4()
        task_id = uuid4()
        question = "Please review this analysis"

        # Mock task validation
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.project_id = project_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        # Mock HITL request creation
        mock_hitl = Mock()
        mock_hitl.id = uuid4()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_hitl

        hitl_request = orchestrator_service.create_hitl_request(
            project_id, task_id, question
        )

        assert hitl_request.id == mock_hitl.id
        assert hitl_request.question == question

    def test_hitl_response_processing(self, orchestrator_service, mock_db):
        """Test HITL response processing."""
        hitl_request_id = uuid4()
        action = "approve"
        comment = "Looks good"

        # Mock HITL request retrieval
        mock_hitl = Mock()
        mock_hitl.id = hitl_request_id
        mock_hitl.status = "PENDING"
        mock_hitl.user_response = None
        mock_hitl.response_comment = None
        mock_hitl.responded_at = None
        mock_hitl.history = []
        mock_db.query.return_value.filter.return_value.first.return_value = mock_hitl

        result = orchestrator_service.process_hitl_response(
            hitl_request_id, action, comment
        )

        assert result["action"] == action
        assert result["workflow_resumed"] is True
        assert mock_db.commit.called

    def test_task_status_update(self, orchestrator_service, mock_db):
        """Test task status updates."""
        task_id = uuid4()
        new_status = TaskStatus.COMPLETED

        # Mock task retrieval
        mock_task = Mock()
        mock_task.id = task_id
        mock_task.status = TaskStatus.WORKING
        mock_task.started_at = "2024-01-01T10:00:00"
        mock_task.completed_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task

        orchestrator_service.update_task_status(task_id, new_status)

        assert mock_task.status == new_status
        assert mock_task.completed_at is not None
        assert mock_db.commit.called


class TestCompleteSDLCWorkflow:
    """End-to-end tests for complete SDLC workflow execution."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session for end-to-end testing."""
        return Mock()

    @pytest.fixture
    def orchestrator_service(self, mock_db):
        """Create orchestrator service for end-to-end testing."""
        return OrchestratorService(mock_db)

    @pytest.mark.asyncio
    async def test_complete_sdlc_workflow_execution(self, orchestrator_service):
        """
        Test complete SDLC workflow execution from Analyst through Deployer.

        This test verifies the entire workflow orchestration engine works
        correctly with dynamic workflow loading and agent handoffs.
        """
        project_id = uuid4()
        user_idea = "Build a simple task management web application"

        # Mock all the services and dependencies
        with patch.object(orchestrator_service.workflow_engine, 'start_workflow_execution') as mock_start, \
             patch.object(orchestrator_service.workflow_engine, 'execute_workflow_step') as mock_execute, \
             patch.object(orchestrator_service.workflow_engine, 'get_workflow_execution_status') as mock_status, \
             patch.object(orchestrator_service.context_store, 'create_artifact') as mock_create_artifact:

            # Mock workflow execution
            mock_execution = Mock()
            mock_execution.execution_id = "test-execution-id"
            mock_execution.is_complete.return_value = False
            mock_execution.status = ExecutionStateEnum.RUNNING
            mock_start.return_value = mock_execution

            # Mock step execution results
            mock_execute.side_effect = [
                {"status": "completed", "agent": "analyst", "step_index": 0},
                {"status": "completed", "agent": "architect", "step_index": 1},
                {"status": "completed", "agent": "coder", "step_index": 2},
                {"status": "completed", "agent": "tester", "step_index": 3},
                {"status": "completed", "agent": "deployer", "step_index": 4},
                {"status": "no_pending_steps"}
            ]

            # Mock final status
            mock_status.return_value = {
                "status": "completed",
                "total_steps": 5,
                "completed_steps": 5,
                "failed_steps": 0
            }

            # Mock artifact creation
            mock_artifact = Mock()
            mock_artifact.context_id = str(uuid4())
            mock_create_artifact.return_value = mock_artifact

            # Execute the workflow
            await orchestrator_service.run_project_workflow(
                project_id,
                user_idea,
                "greenfield-fullstack"
            )

            # Verify workflow was started
            mock_start.assert_called_once()
            start_call = mock_start.call_args
            assert start_call[1]["workflow_id"] == "greenfield-fullstack"
            assert start_call[1]["project_id"] == str(project_id)
            assert "user_idea" in start_call[1]["context_data"]

            # Verify all steps were executed
            assert mock_execute.call_count == 6  # 5 steps + 1 no_pending_steps

            # Verify final status was checked
            mock_status.assert_called()

            # Verify initial context artifact was created
            mock_create_artifact.assert_called()
            artifact_call = mock_create_artifact.call_args
            assert artifact_call[1]["project_id"] == project_id
            assert artifact_call[1]["source_agent"] == "orchestrator"
            assert artifact_call[1]["artifact_type"] == "user_input"

    @pytest.mark.asyncio
    async def test_workflow_with_hitl_interaction(self, orchestrator_service):
        """
        Test workflow execution with HITL interaction.

        This test verifies that workflows can pause for human approval
        and resume after HITL responses.
        """
        project_id = uuid4()
        user_idea = "Build a complex e-commerce platform"

        with patch.object(orchestrator_service.workflow_engine, 'start_workflow_execution') as mock_start, \
             patch.object(orchestrator_service.workflow_engine, 'execute_workflow_step') as mock_execute, \
             patch.object(orchestrator_service, '_handle_workflow_hitl') as mock_hitl_handler:

            # Mock workflow execution
            mock_execution = Mock()
            mock_execution.execution_id = "test-hitl-execution"
            mock_execution.is_complete.return_value = False
            mock_start.return_value = mock_execution

            # Mock step execution with HITL requirement
            mock_execute.side_effect = [
                {"status": "completed", "agent": "analyst", "requires_hitl": True},
                {"status": "no_pending_steps"}
            ]

            # Mock HITL handler
            mock_hitl_handler.return_value = {"approved": True}

            # Execute workflow
            await orchestrator_service.run_project_workflow(
                project_id,
                user_idea
            )

            # Verify HITL handler was called
            mock_hitl_handler.assert_called_once()

            # Verify workflow continued after HITL approval
            assert mock_execute.call_count == 2

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, orchestrator_service):
        """
        Test workflow error handling and recovery.

        This test verifies that workflows handle errors gracefully
        and can be cancelled when necessary.
        """
        project_id = uuid4()
        user_idea = "Build a failing application"

        with patch.object(orchestrator_service.workflow_engine, 'start_workflow_execution') as mock_start, \
             patch.object(orchestrator_service.workflow_engine, 'execute_workflow_step') as mock_execute, \
             patch.object(orchestrator_service.workflow_engine, 'cancel_workflow_execution') as mock_cancel:

            # Mock workflow execution
            mock_execution = Mock()
            mock_execution.execution_id = "test-error-execution"
            mock_start.return_value = mock_execution

            # Mock step execution failure
            mock_execute.side_effect = Exception("Task execution failed")

            # Execute workflow (should handle error gracefully)
            with pytest.raises(Exception):
                await orchestrator_service.run_project_workflow(
                    project_id,
                    user_idea
                )

            # Verify error handling
            mock_cancel.assert_called_once_with(
                "test-error-execution",
                "Step execution failed: Task execution failed"
            )

    @pytest.mark.asyncio
    async def test_hitl_workflow_integration(self, orchestrator_service):
        """
        Test complete HITL-workflow integration.

        This test verifies that:
        1. Workflows pause when HITL is required
        2. HITL responses properly resume workflows
        3. Agent status is updated correctly during HITL
        4. Task status reflects HITL outcomes
        """
        project_id = uuid4()
        user_idea = "Build a complex e-commerce platform with HITL checkpoints"

        # Mock all services and dependencies
        with patch.object(orchestrator_service.workflow_engine, 'start_workflow_execution') as mock_start, \
             patch.object(orchestrator_service.workflow_engine, 'execute_workflow_step') as mock_execute, \
             patch.object(orchestrator_service.workflow_engine, 'pause_workflow_execution') as mock_pause, \
             patch.object(orchestrator_service.workflow_engine, 'resume_workflow_execution_sync') as mock_resume, \
             patch.object(orchestrator_service, 'update_agent_status') as mock_update_agent, \
             patch.object(orchestrator_service, 'update_task_status') as mock_update_task, \
             patch.object(orchestrator_service.context_store, 'create_artifact') as mock_create_artifact:

            # Setup workflow execution mock
            mock_execution = Mock()
            mock_execution.execution_id = "test-hitl-execution"
            mock_execution.project_id = str(project_id)
            mock_execution.is_complete.return_value = False
            mock_start.return_value = mock_execution

            # Mock step execution that requires HITL
            mock_execute.side_effect = [
                {
                    "status": "completed",
                    "agent": "analyst",
                    "step_index": 0,
                    "task_id": str(uuid4()),
                    "requires_hitl": True,
                    "hitl_question": "Please review the requirements analysis"
                },
                {"status": "no_pending_steps"}
            ]

            # Mock pause and resume
            mock_pause.return_value = True
            mock_resume.return_value = True

            # Execute workflow - should pause at HITL
            await orchestrator_service.run_project_workflow(
                project_id,
                user_idea,
                "greenfield-fullstack"
            )

            # Verify workflow was started
            mock_start.assert_called_once()

            # Verify step was executed
            assert mock_execute.call_count == 1

            # Verify workflow was paused for HITL
            mock_pause.assert_called_once()
            pause_call = mock_pause.call_args
            assert "HITL approval required" in pause_call[0][1]  # reason parameter

            # Now simulate HITL response processing
            hitl_request_id = uuid4()
            task_id = uuid4()

            # Mock HITL request and task
            with patch.object(orchestrator_service.db, 'query') as mock_query:
                # Mock HITL request
                mock_hitl = Mock()
                mock_hitl.id = hitl_request_id
                mock_hitl.task_id = task_id
                mock_hitl.project_id = project_id
                mock_hitl.status = "PENDING"
                mock_hitl.response_comment = "Looks good, please proceed"
                mock_hitl.amended_content = None
                mock_hitl.history = []

                # Mock task
                mock_task = Mock()
                mock_task.id = task_id
                mock_task.agent_type = "analyst"
                mock_task.status = TaskStatus.WORKING

                # Setup query chain
                mock_query.return_value.filter.return_value.first.side_effect = [mock_hitl, mock_task]

                # Mock database commit
                mock_commit = Mock()
                orchestrator_service.db.commit = mock_commit

                # Process HITL approval response
                result = orchestrator_service.process_hitl_response(
                    hitl_request_id,
                    "approve",
                    comment="Looks good, please proceed"
                )

                # Verify HITL response was processed
                assert result["action"] == "approve"
                assert result["workflow_resumed"] is True
                assert result["task_status"] == "completed"

                # Verify agent status was updated to IDLE
                mock_update_agent.assert_called_with("analyst", AgentStatus.IDLE)

                # Verify task status was updated to COMPLETED
                mock_update_task.assert_called_with(task_id, TaskStatus.COMPLETED)

                # Verify workflow resume was attempted
                mock_resume.assert_called_once()

                # Verify database was committed
                assert mock_commit.call_count >= 2  # HITL update + task update

    @pytest.mark.asyncio
    async def test_hitl_workflow_rejection_handling(self, orchestrator_service):
        """
        Test HITL rejection handling in workflows.

        This test verifies that workflow tasks are properly marked as failed
        when HITL requests are rejected.
        """
        project_id = uuid4()
        hitl_request_id = uuid4()
        task_id = uuid4()

        with patch.object(orchestrator_service.db, 'query') as mock_query, \
             patch.object(orchestrator_service.workflow_engine, 'resume_workflow_execution_sync') as mock_resume, \
             patch.object(orchestrator_service, 'update_agent_status') as mock_update_agent, \
             patch.object(orchestrator_service, 'update_task_status') as mock_update_task:

            # Mock HITL request
            mock_hitl = Mock()
            mock_hitl.id = hitl_request_id
            mock_hitl.task_id = task_id
            mock_hitl.project_id = project_id
            mock_hitl.status = "PENDING"
            mock_hitl.response_comment = "Requirements need revision"
            mock_hitl.amended_content = None
            mock_hitl.history = []

            # Mock task
            mock_task = Mock()
            mock_task.id = task_id
            mock_task.agent_type = "analyst"
            mock_task.status = TaskStatus.WORKING

            # Setup query chain
            mock_query.return_value.filter.return_value.first.side_effect = [mock_hitl, mock_task]

            # Mock database operations
            mock_commit = Mock()
            orchestrator_service.db.commit = mock_commit

            # Process HITL rejection response
            result = orchestrator_service.process_hitl_response(
                hitl_request_id,
                "reject",
                comment="Requirements need revision"
            )

            # Verify rejection was processed
            assert result["action"] == "reject"
            assert result["workflow_resumed"] is True
            assert result["task_status"] == "failed"

            # Verify agent status was updated to IDLE
            mock_update_agent.assert_called_with("analyst", AgentStatus.IDLE)

            # Verify task status was updated to FAILED with rejection reason
            mock_update_task.assert_called_with(
                task_id,
                TaskStatus.FAILED,
                error_message="Task rejected via HITL: Requirements need revision"
            )

            # Verify workflow resume was attempted
            mock_resume.assert_called_once()

    @pytest.mark.asyncio
    async def test_hitl_workflow_amendment_handling(self, orchestrator_service):
        """
        Test HITL amendment handling in workflows.

        This test verifies that workflow tasks incorporate amendments
        when HITL requests are amended.
        """
        project_id = uuid4()
        hitl_request_id = uuid4()
        task_id = uuid4()

        amended_content = {
            "requirements": "Updated requirements with amendments",
            "priority": "high"
        }

        with patch.object(orchestrator_service.db, 'query') as mock_query, \
             patch.object(orchestrator_service.workflow_engine, 'resume_workflow_execution_sync') as mock_resume, \
             patch.object(orchestrator_service, 'update_agent_status') as mock_update_agent, \
             patch.object(orchestrator_service, 'update_task_status') as mock_update_task:

            # Mock HITL request
            mock_hitl = Mock()
            mock_hitl.id = hitl_request_id
            mock_hitl.task_id = task_id
            mock_hitl.project_id = project_id
            mock_hitl.status = "PENDING"
            mock_hitl.response_comment = "Made some amendments"
            mock_hitl.amended_content = amended_content
            mock_hitl.history = []

            # Mock task
            mock_task = Mock()
            mock_task.id = task_id
            mock_task.agent_type = "architect"
            mock_task.status = TaskStatus.WORKING

            # Setup query chain
            mock_query.return_value.filter.return_value.first.side_effect = [mock_hitl, mock_task]

            # Mock database operations
            mock_commit = Mock()
            orchestrator_service.db.commit = mock_commit

            # Process HITL amendment response
            result = orchestrator_service.process_hitl_response(
                hitl_request_id,
                "amend",
                comment="Made some amendments",
                amended_data=amended_content
            )

            # Verify amendment was processed
            assert result["action"] == "amend"
            assert result["workflow_resumed"] is True
            assert result["task_status"] == "completed"

            # Verify agent status was updated to IDLE
            mock_update_agent.assert_called_with("architect", AgentStatus.IDLE)

            # Verify task status was updated to COMPLETED with amended content
            mock_update_task.assert_called_with(
                task_id,
                TaskStatus.COMPLETED,
                output=amended_content
            )

            # Verify workflow resume was attempted
            mock_resume.assert_called_once()
