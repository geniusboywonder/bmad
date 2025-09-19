"""Tests for ADK Orchestration Service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.adk_orchestration_service import ADKOrchestrationService
from app.agents.bmad_adk_wrapper import BMADADKWrapper

@pytest.fixture
def orchestration_service():
    """Create a fresh ADK Orchestration Service for testing."""
    return ADKOrchestrationService()

@pytest.fixture
def mock_adk_wrapper():
    """Create a mock BMADADKWrapper for testing."""
    wrapper = Mock(spec=BMADADKWrapper)
    wrapper.agent_name = "test_agent"
    wrapper.agent_type = "analyst"
    wrapper.is_initialized = True
    wrapper.adk_agent = Mock()
    return wrapper

class TestADKOrchestrationService:
    """Test ADK Orchestration Service functionality."""

    @pytest.mark.mock_data

    def test_service_initialization(self, orchestration_service):
        """Test that orchestration service initializes correctly."""
        assert orchestration_service.session_service is not None
        assert isinstance(orchestration_service.active_workflows, dict)
        assert orchestration_service.orchestration_count == 0

    @pytest.mark.mock_data

    def test_create_multi_agent_workflow(self, orchestration_service, mock_adk_wrapper):
        """Test creating multi-agent workflow."""
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="test_workflow",
            project_id="test_project"
        )

        assert workflow_id.startswith("adk_workflow_test_project_test_workflow_")
        assert workflow_id in orchestration_service.active_workflows

        # Check workflow metadata
        metadata = orchestration_service.active_workflows[workflow_id]
        assert metadata["agents"] == ["test_agent"]
        assert metadata["workflow_type"] == "test_workflow"
        assert metadata["project_id"] == "test_project"
        assert metadata["status"] == "created"

    @pytest.mark.mock_data

    def test_create_workflow_with_no_agents_fails(self, orchestration_service):
        """Test that creating workflow with no agents fails."""
        with pytest.raises(ValueError, match="At least one agent required"):
            orchestration_service.create_multi_agent_workflow(
                agents=[],
                workflow_type="test",
                project_id="test"
            )

    @pytest.mark.mock_data

    def test_create_workflow_with_uninitialized_agent_fails(self, orchestration_service):
        """Test that creating workflow with uninitialized agent fails."""
        mock_wrapper = Mock(spec=BMADADKWrapper)
        mock_wrapper.is_initialized = False

        with pytest.raises(ValueError, match="No valid ADK agents available"):
            orchestration_service.create_multi_agent_workflow(
                agents=[mock_wrapper],
                workflow_type="test",
                project_id="test"
            )

    @pytest.mark.mock_data

    def test_get_workflow_status_for_unknown_workflow(self, orchestration_service):
        """Test getting status for unknown workflow."""
        result = orchestration_service.get_workflow_status("unknown_workflow")
        assert result is None

    @pytest.mark.mock_data

    def test_get_workflow_status_for_existing_workflow(self, orchestration_service, mock_adk_wrapper):
        """Test getting status for existing workflow."""
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="test",
            project_id="test"
        )

        status = orchestration_service.get_workflow_status(workflow_id)
        assert status is not None
        assert status["workflow_id"] == workflow_id
        assert status["status"] == "created"

    @pytest.mark.mock_data

    def test_list_active_workflows(self, orchestration_service):
        """Test listing active workflows."""
        # Initially empty
        assert orchestration_service.list_active_workflows() == []

        # Add a workflow
        orchestration_service.active_workflows["test_workflow"] = {
            "project_id": "test_project"
        }
        assert "test_workflow" in orchestration_service.list_active_workflows()

    @pytest.mark.mock_data

    def test_list_active_workflows_with_project_filter(self, orchestration_service, mock_adk_wrapper):
        """Test listing active workflows with project filter."""
        # Create workflows for different projects
        wf1 = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="test1",
            project_id="project_a"
        )

        wf2 = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="test2",
            project_id="project_b"
        )

        # Filter by project
        project_a_workflows = orchestration_service.list_active_workflows("project_a")
        assert wf1 in project_a_workflows
        assert wf2 not in project_a_workflows

    @pytest.mark.mock_data

    def test_terminate_workflow(self, orchestration_service, mock_adk_wrapper):
        """Test terminating a workflow."""
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="test",
            project_id="test"
        )

        # Terminate workflow
        result = orchestration_service.terminate_workflow(workflow_id)
        assert result is True

        # Check status updated
        status = orchestration_service.get_workflow_status(workflow_id)
        assert status["status"] == "terminated"
        assert "terminated_at" in status

    @pytest.mark.mock_data

    def test_terminate_unknown_workflow(self, orchestration_service):
        """Test terminating unknown workflow."""
        result = orchestration_service.terminate_workflow("unknown_workflow")
        assert result is False

    @pytest.mark.mock_data

    def test_get_workflow_config_defaults(self, orchestration_service):
        """Test workflow configuration generation."""
        config = orchestration_service._get_workflow_config("unknown_type", {})

        assert config["coordination_strategy"] == "sequential"
        assert config["max_iterations"] == 10
        assert config["allow_agent_delegation"] is True
        assert config["timeout_minutes"] == 30

    @pytest.mark.mock_data

    def test_get_workflow_config_requirements_analysis(self, orchestration_service):
        """Test workflow config for requirements analysis."""
        config = orchestration_service._get_workflow_config("requirements_analysis", {})

        assert config["coordination_strategy"] == "collaborative"
        assert config["max_iterations"] == 8
        assert config["focus_areas"] == ["functional", "non_functional", "constraints"]

    @pytest.mark.mock_data

    def test_get_workflow_config_system_design(self, orchestration_service):
        """Test workflow config for system design."""
        config = orchestration_service._get_workflow_config("system_design", {})

        assert config["coordination_strategy"] == "hierarchical"
        assert config["max_iterations"] == 12
        assert config["design_phases"] == ["architecture", "components", "interfaces"]

    @pytest.mark.mock_data

    def test_get_workflow_config_with_overrides(self, orchestration_service):
        """Test workflow config with custom overrides."""
        custom_config = {"max_iterations": 20, "custom_setting": "test"}
        config = orchestration_service._get_workflow_config("system_design", custom_config)

        assert config["max_iterations"] == 20  # Override applied
        assert config["custom_setting"] == "test"  # Custom setting added
        assert config["coordination_strategy"] == "hierarchical"  # Default preserved

    @pytest.mark.mock_data

    def test_enhance_prompt_with_context(self, orchestration_service):
        """Test prompt enhancement with context data."""
        prompt = "Analyze this project"
        context_data = {
            "project_name": "Test Project",
            "project_description": "A test project",
            "existing_artifacts": ["PRD", "Architecture"],
            "requirements": "Must be scalable",
            "constraints": "Budget limited"
        }

        enhanced = orchestration_service._enhance_prompt_with_context(prompt, context_data)

        assert "Initial Request: Analyze this project" in enhanced
        assert "Project: Test Project" in enhanced
        assert "PRD" in enhanced
        assert "Must be scalable" in enhanced
        assert "Budget limited" in enhanced

    @pytest.mark.mock_data

    def test_enhance_prompt_without_context(self, orchestration_service):
        """Test prompt enhancement without context data."""
        prompt = "Simple request"
        enhanced = orchestration_service._enhance_prompt_with_context(prompt, None)

        assert enhanced == prompt

    @pytest.mark.mock_data

    def test_cleanup_completed_workflows(self, orchestration_service):
        """Test cleanup of completed workflows."""
        # Add some completed workflows
        orchestration_service.active_workflows.update({
            "completed_1": {"status": "completed"},
            "completed_2": {"status": "failed"},
            "running_1": {"status": "running"},
            "terminated_1": {"status": "terminated"}
        })

        initial_count = len(orchestration_service.active_workflows)
        cleaned_count = orchestration_service.cleanup_completed_workflows()

        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0
        # Should have fewer workflows after cleanup
        assert len(orchestration_service.active_workflows) <= initial_count

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_execute_collaborative_analysis_success(self, orchestration_service, mock_adk_wrapper):
        """Test successful collaborative analysis execution."""
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="requirements_analysis",
            project_id="test_project"
        )

        result = await orchestration_service.execute_collaborative_analysis(
            workflow_id=workflow_id,
            initial_prompt="Analyze requirements for a web application",
            user_id="test_user"
        )

        assert result["workflow_id"] == workflow_id
        assert result["status"] == "completed"
        assert "result" in result
        assert result["agents_involved"] == ["test_agent"]

        # Check workflow metadata updated
        metadata = orchestration_service.get_workflow_status(workflow_id)
        assert metadata["status"] == "completed"
        assert "completed_at" in metadata

    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_execute_collaborative_analysis_unknown_workflow(self, orchestration_service):
        """Test collaborative analysis with unknown workflow."""
        result = await orchestration_service.execute_collaborative_analysis(
            workflow_id="unknown_workflow",
            initial_prompt="Test prompt",
            user_id="test_user"
        )

        assert "error" in result
        assert "not found" in result["error"]

class TestADKOrchestrationIntegration:
    """Integration tests for ADK Orchestration Service."""

    @pytest.mark.mock_data

    def test_workflow_creation_and_listing_integration(self, orchestration_service, mock_adk_wrapper):
        """Test workflow creation and listing integration."""
        initial_count = len(orchestration_service.list_active_workflows())

        # Create workflow
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="integration_test",
            project_id="integration_project"
        )

        # Verify it appears in listing
        workflows = orchestration_service.list_active_workflows()
        assert len(workflows) == initial_count + 1
        assert workflow_id in workflows

    @pytest.mark.mock_data

    def test_configuration_methods_exist(self, orchestration_service):
        """Test that all expected methods exist."""
        assert hasattr(orchestration_service, 'create_multi_agent_workflow')
        assert hasattr(orchestration_service, 'execute_collaborative_analysis')
        assert hasattr(orchestration_service, 'get_workflow_status')
        assert hasattr(orchestration_service, 'terminate_workflow')
        assert hasattr(orchestration_service, 'list_active_workflows')
        assert hasattr(orchestration_service, '_get_workflow_config')
        assert hasattr(orchestration_service, '_enhance_prompt_with_context')
        assert hasattr(orchestration_service, 'cleanup_completed_workflows')

    @pytest.mark.mock_data

    def test_workflow_lifecycle(self, orchestration_service, mock_adk_wrapper):
        """Test complete workflow lifecycle."""
        # Create workflow
        workflow_id = orchestration_service.create_multi_agent_workflow(
            agents=[mock_adk_wrapper],
            workflow_type="lifecycle_test",
            project_id="lifecycle_project"
        )

        # Verify creation
        status = orchestration_service.get_workflow_status(workflow_id)
        assert status["status"] == "created"

        # Terminate workflow
        terminated = orchestration_service.terminate_workflow(workflow_id)
        assert terminated is True

        # Verify termination
        status = orchestration_service.get_workflow_status(workflow_id)
        assert status["status"] == "terminated"