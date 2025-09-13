"""
Unit tests for Workflow Service

Tests the BMAD Core workflow service functionality including loading,
execution, and agent orchestration.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.services.workflow_service import WorkflowService
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowExecutionState,
    WorkflowType
)
from app.models.handoff import HandoffSchema


class TestWorkflowService:
    """Test cases for WorkflowService."""

    @pytest.fixture
    def workflow_service(self):
        """Create a workflow service instance for testing."""
        return WorkflowService()

    @pytest.fixture
    def mock_workflow_definition(self):
        """Create a mock workflow definition for testing."""
        return WorkflowDefinition(
            id="test-workflow",
            name="Test Workflow",
            description="A test workflow",
            type=WorkflowType.GENERIC,
            sequence=[
                WorkflowStep(
                    agent="analyst",
                    creates="analysis.md",
                    requires=[],
                    notes="Analyze requirements"
                ),
                WorkflowStep(
                    agent="architect",
                    creates="architecture.md",
                    requires=["analysis.md"],
                    notes="Design architecture"
                )
            ]
        )

    def test_service_initialization(self, workflow_service):
        """Test workflow service initialization."""
        assert workflow_service.yaml_parser is not None
        assert workflow_service.workflow_base_path.name == "workflows"
        assert workflow_service._cache_enabled is True
        assert workflow_service._workflow_cache == {}
        assert workflow_service._execution_cache == {}

    def test_load_workflow_success(self, workflow_service, mock_workflow_definition):
        """Test successful workflow loading."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch.object(workflow_service.yaml_parser, 'load_workflow', return_value=mock_workflow_definition):

            result = workflow_service.load_workflow("test-workflow")

            assert result.id == "test-workflow"
            assert result.name == "Test Workflow"
            assert len(result.sequence) == 2
            assert result.sequence[0].agent == "analyst"
            assert result.sequence[1].agent == "architect"

    def test_load_workflow_file_not_found(self, workflow_service):
        """Test workflow loading when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Workflow 'nonexistent' not found"):
                workflow_service.load_workflow("nonexistent")

    def test_start_workflow_execution(self, workflow_service, mock_workflow_definition):
        """Test starting workflow execution."""
        with patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):
            execution = workflow_service.start_workflow_execution(
                "test-workflow",
                "project-123"
            )

            assert execution.workflow_id == "test-workflow"
            assert execution.project_id == "project-123"
            assert execution.status == WorkflowExecutionState.PENDING
            assert len(execution.steps) == 2
            assert execution.steps[0].agent == "analyst"
            assert execution.steps[1].agent == "architect"

    def test_get_next_agent(self, workflow_service):
        """Test getting next agent in workflow execution."""
        # Create a mock execution
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.PENDING
                ),
                WorkflowExecutionStep(
                    step_index=1,
                    agent="architect",
                    status=WorkflowExecutionState.PENDING
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution):
            next_agent = workflow_service.get_next_agent("exec-123")

            assert next_agent == "analyst"

    def test_get_next_agent_no_pending_steps(self, workflow_service):
        """Test getting next agent when no steps are pending."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.COMPLETED
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution):
            next_agent = workflow_service.get_next_agent("exec-123")

            assert next_agent is None

    def test_advance_workflow_execution(self, workflow_service):
        """Test advancing workflow execution."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.RUNNING
                ),
                WorkflowExecutionStep(
                    step_index=1,
                    agent="architect",
                    status=WorkflowExecutionState.PENDING
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution), \
             patch.object(workflow_service, '_set_execution'):

            result = workflow_service.advance_workflow_execution(
                "exec-123",
                "analyst",
                result={"analysis": "complete"}
            )

            assert result.steps[0].status == WorkflowExecutionState.COMPLETED
            assert result.steps[0].result == {"analysis": "complete"}

    def test_advance_workflow_execution_complete(self, workflow_service):
        """Test advancing workflow execution to completion."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.RUNNING
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution), \
             patch.object(workflow_service, '_set_execution'):

            result = workflow_service.advance_workflow_execution(
                "exec-123",
                "analyst",
                result={"analysis": "complete"}
            )

            assert result.status == WorkflowExecutionState.COMPLETED
            assert result.completed_at is not None

    def test_generate_handoff(self, workflow_service, mock_workflow_definition):
        """Test generating handoff between agents."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123"
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution), \
             patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):

            handoff = workflow_service.generate_handoff(
                "exec-123",
                "analyst",
                "architect"
            )

            assert handoff is not None
            assert handoff.from_agent == "analyst"
            assert handoff.to_agent == "architect"
            assert handoff.phase == "workflow_test-workflow"
            assert "architect" in handoff.expected_outputs

    def test_get_workflow_execution_status(self, workflow_service, mock_workflow_definition):
        """Test getting workflow execution status."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            status=WorkflowExecutionState.RUNNING,
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.COMPLETED
                ),
                WorkflowExecutionStep(
                    step_index=1,
                    agent="architect",
                    status=WorkflowExecutionState.RUNNING
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution), \
             patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):

            status = workflow_service.get_workflow_execution_status("exec-123")

            assert status["execution_id"] == "exec-123"
            assert status["status"] == "running"
            assert status["completed_steps"] == 1
            assert status["next_agent"] == "architect"
            assert status["workflow_name"] == "Test Workflow"

    def test_list_available_workflows(self, workflow_service, mock_workflow_definition):
        """Test listing available workflows."""
        with patch.object(workflow_service.workflow_base_path, 'exists', return_value=True), \
             patch.object(workflow_service.workflow_base_path, 'glob') as mock_glob, \
             patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):

            # Mock workflow files
            mock_file = Path("test-workflow.yaml")
            mock_file.stem = "test-workflow"
            mock_glob.return_value = [mock_file]

            result = workflow_service.list_available_workflows()

            assert len(result) == 1
            assert result[0]["id"] == "test-workflow"
            assert result[0]["name"] == "Test Workflow"
            assert result[0]["steps_count"] == 2
            assert "analyst" in result[0]["agents"]
            assert "architect" in result[0]["agents"]

    def test_get_workflow_metadata(self, workflow_service, mock_workflow_definition):
        """Test getting workflow metadata."""
        with patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):
            metadata = workflow_service.get_workflow_metadata("test-workflow")

            assert metadata["id"] == "test-workflow"
            assert metadata["name"] == "Test Workflow"
            assert metadata["type"] == "generic"
            assert metadata["steps_count"] == 2
            assert metadata["agents"] == ["analyst", "architect"]

    def test_validate_workflow_execution(self, workflow_service, mock_workflow_definition):
        """Test workflow execution validation."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123",
            steps=[
                WorkflowExecutionStep(
                    step_index=0,
                    agent="analyst",
                    status=WorkflowExecutionState.COMPLETED
                ),
                WorkflowExecutionStep(
                    step_index=1,
                    agent="architect",
                    status=WorkflowExecutionState.PENDING
                )
            ]
        )

        with patch.object(workflow_service, '_get_execution', return_value=execution), \
             patch.object(workflow_service, 'load_workflow', return_value=mock_workflow_definition):

            validation = workflow_service.validate_workflow_execution("exec-123")

            assert validation["valid"] is True
            assert validation["errors"] == []
            assert validation["warnings"] == []

    def test_cache_operations(self, workflow_service):
        """Test cache operations."""
        # Test cache clearing
        workflow_service._workflow_cache["test"] = "workflow_data"
        workflow_service._execution_cache["exec-123"] = "execution_data"
        workflow_service.clear_cache()

        assert workflow_service._workflow_cache == {}
        assert workflow_service._execution_cache == {}

        # Test cache enabling/disabling
        workflow_service.enable_cache(False)
        assert workflow_service._cache_enabled is False

        workflow_service.enable_cache(True)
        assert workflow_service._cache_enabled is True

    def test_find_workflow_file(self, workflow_service):
        """Test workflow file finding."""
        with patch.object(workflow_service.workflow_base_path, '__truediv__') as mock_div, \
             patch('pathlib.Path.exists') as mock_exists:

            mock_file = Path("test-workflow.yaml")
            mock_div.return_value = mock_file
            mock_exists.return_value = True

            result = workflow_service._find_workflow_file("test-workflow")

            assert result == mock_file
            mock_div.assert_called_with("test-workflow.yaml")

    def test_workflow_definition_validation(self, mock_workflow_definition):
        """Test workflow definition validation."""
        errors = mock_workflow_definition.validate_sequence()

        # Should have no errors for our well-formed workflow
        assert len(errors) == 0

    def test_workflow_definition_get_methods(self, mock_workflow_definition):
        """Test workflow definition helper methods."""
        # Test get_step_by_index
        step = mock_workflow_definition.get_step_by_index(0)
        assert step is not None
        assert step.agent == "analyst"

        # Test get_next_agent
        next_agent = mock_workflow_definition.get_next_agent()
        assert next_agent == "analyst"

        next_agent = mock_workflow_definition.get_next_agent(0)
        assert next_agent == "architect"

        # Test get_handoff_prompt
        prompt = mock_workflow_definition.get_handoff_prompt("analyst", "architect")
        # Should return None since we don't have handoff prompts in our mock
        assert prompt is None

    def test_workflow_execution_state_transitions(self):
        """Test workflow execution state transitions."""
        execution = WorkflowExecution(
            workflow_id="test-workflow",
            project_id="project-123",
            execution_id="exec-123"
        )

        # Initial state should be PENDING
        assert execution.status == WorkflowExecutionState.PENDING

        # Test state changes
        execution.status = WorkflowExecutionState.RUNNING
        assert execution.status == WorkflowExecutionState.RUNNING

        execution.status = WorkflowExecutionState.COMPLETED
        assert execution.status == WorkflowExecutionState.COMPLETED

    def test_workflow_step_validation(self):
        """Test workflow step validation."""
        step = WorkflowStep(
            agent="analyst",
            creates="analysis.md",
            requires=["requirements.txt"],
            condition="project_type == 'web'",
            notes="Analyze project requirements"
        )

        assert step.agent == "analyst"
        assert step.creates == "analysis.md"
        assert step.requires == ["requirements.txt"]
        assert step.condition == "project_type == 'web'"
        assert step.notes == "Analyze project requirements"
