"""Tests for ADK Workflow Templates."""

import pytest
from unittest.mock import Mock

from app.workflows.adk_workflow_templates import (
    ADKWorkflowTemplates,
    WorkflowTemplate,
    WorkflowStep,
    WorkflowType
)

class TestADKWorkflowTemplates:
    """Test ADK Workflow Templates functionality."""

    @pytest.mark.mock_data

    def test_get_template_requirements_analysis(self):
        """Test getting requirements analysis template."""
        template = ADKWorkflowTemplates.get_template(WorkflowType.REQUIREMENTS_ANALYSIS)

        assert isinstance(template, WorkflowTemplate)
        assert template.workflow_type == WorkflowType.REQUIREMENTS_ANALYSIS
        assert template.name == "Comprehensive Requirements Analysis"
        assert len(template.steps) == 3
        assert template.required_agents == ["analyst", "architect"]
        assert template.max_duration_minutes == 45

    @pytest.mark.mock_data

    def test_get_template_system_design(self):
        """Test getting system design template."""
        template = ADKWorkflowTemplates.get_template(WorkflowType.SYSTEM_DESIGN)

        assert isinstance(template, WorkflowTemplate)
        assert template.workflow_type == WorkflowType.SYSTEM_DESIGN
        assert template.name == "System Design Collaboration"
        assert len(template.steps) == 3
        assert template.required_agents == ["architect", "analyst"]

    @pytest.mark.mock_data

    def test_get_template_code_review(self):
        """Test getting code review template."""
        template = ADKWorkflowTemplates.get_template(WorkflowType.CODE_REVIEW)

        assert isinstance(template, WorkflowTemplate)
        assert template.workflow_type == WorkflowType.CODE_REVIEW
        assert template.name == "Code Review Collaboration"
        assert len(template.steps) == 3
        assert template.required_agents == ["coder", "architect", "analyst"]

    @pytest.mark.mock_data

    def test_get_template_testing_strategy(self):
        """Test getting testing strategy template."""
        template = ADKWorkflowTemplates.get_template(WorkflowType.TESTING_STRATEGY)

        assert isinstance(template, WorkflowTemplate)
        assert template.workflow_type == WorkflowType.TESTING_STRATEGY
        assert template.name == "Testing Strategy Collaboration"
        assert len(template.steps) == 3
        assert template.required_agents == ["analyst", "architect", "coder"]

    @pytest.mark.mock_data

    def test_get_template_deployment_planning(self):
        """Test getting deployment planning template."""
        template = ADKWorkflowTemplates.get_template(WorkflowType.DEPLOYMENT_PLANNING)

        assert isinstance(template, WorkflowTemplate)
        assert template.workflow_type == WorkflowType.DEPLOYMENT_PLANNING
        assert template.name == "Deployment Planning Collaboration"
        assert len(template.steps) == 3
        assert template.required_agents == ["architect", "analyst", "coder"]

    @pytest.mark.mock_data

    def test_get_template_unknown_type_fails(self):
        """Test getting unknown template type fails."""
        with pytest.raises(ValueError, match="Unsupported workflow type"):
            ADKWorkflowTemplates.get_template("unknown_type")

    @pytest.mark.mock_data

    def test_list_available_templates(self):
        """Test listing all available templates."""
        templates = ADKWorkflowTemplates.list_available_templates()

        assert isinstance(templates, dict)
        assert len(templates) == 5  # All 5 templates

        # Check that all expected templates are present
        expected_names = [
            "Comprehensive Requirements Analysis",
            "System Design Collaboration",
            "Code Review Collaboration",
            "Testing Strategy Collaboration",
            "Deployment Planning Collaboration"
        ]

        for name in expected_names:
            assert name in templates
            template_info = templates[name]
            assert "description" in template_info
            assert "workflow_type" in template_info
            assert "max_duration_minutes" in template_info
            assert "required_agents" in template_info
            assert "step_count" in template_info
            assert "success_criteria" in template_info

    @pytest.mark.mock_data

    def test_get_template_for_agents_all_available(self):
        """Test getting templates for agents when all required agents are available."""
        available_agents = ["analyst", "architect", "coder", "tester", "deployer"]
        templates = ADKWorkflowTemplates.get_template_for_agents(available_agents)

        assert len(templates) == 5  # All templates should be available
        template_names = [t.name for t in templates]
        assert "Comprehensive Requirements Analysis" in template_names

    @pytest.mark.mock_data

    def test_get_template_for_agents_partial_availability(self):
        """Test getting templates for agents with partial availability."""
        available_agents = ["analyst", "architect"]  # Only 2 agents available
        templates = ADKWorkflowTemplates.get_template_for_agents(available_agents)

        # Should only return templates that can work with these agents
        assert len(templates) == 2  # Requirements Analysis and System Design
        template_names = [t.name for t in templates]
        assert "Comprehensive Requirements Analysis" in template_names
        assert "System Design Collaboration" in template_names

    @pytest.mark.mock_data

    def test_get_template_for_agents_no_matches(self):
        """Test getting templates for agents with no matches."""
        available_agents = ["unknown_agent"]
        templates = ADKWorkflowTemplates.get_template_for_agents(available_agents)

        assert len(templates) == 0

    @pytest.mark.mock_data

    def test_create_custom_template(self):
        """Test creating a custom workflow template."""
        custom_steps = [
            WorkflowStep(
                agent_type="analyst",
                instruction="Custom analysis step",
                expected_output="analysis_result",
                handoff_conditions=["analysis_complete"]
            )
        ]

        custom_template = ADKWorkflowTemplates.create_custom_template(
            name="Custom Test Template",
            description="A custom template for testing",
            workflow_type=WorkflowType.ARCHITECTURE_REVIEW,
            steps=custom_steps,
            required_agents=["analyst"],
            max_duration_minutes=30
        )

        assert isinstance(custom_template, WorkflowTemplate)
        assert custom_template.name == "Custom Test Template"
        assert custom_template.workflow_type == WorkflowType.ARCHITECTURE_REVIEW
        assert len(custom_template.steps) == 1
        assert custom_template.required_agents == ["analyst"]
        assert custom_template.max_duration_minutes == 30
        assert custom_template.success_criteria == ["Custom workflow completed successfully"]

class TestWorkflowStep:
    """Test WorkflowStep dataclass."""

    @pytest.mark.mock_data

    def test_workflow_step_creation(self):
        """Test creating a workflow step."""
        step = WorkflowStep(
            agent_type="analyst",
            instruction="Analyze requirements",
            expected_output="analysis_report",
            handoff_conditions=["analysis_complete", "requirements_clear"],
            priority="high",
            timeout_minutes=20,
            required_context=["project_description", "stakeholder_input"]
        )

        assert step.agent_type == "analyst"
        assert step.instruction == "Analyze requirements"
        assert step.expected_output == "analysis_report"
        assert step.handoff_conditions == ["analysis_complete", "requirements_clear"]
        assert step.priority == "high"
        assert step.timeout_minutes == 20
        assert step.required_context == ["project_description", "stakeholder_input"]

    @pytest.mark.mock_data

    def test_workflow_step_default_values(self):
        """Test workflow step with default values."""
        step = WorkflowStep(
            agent_type="architect",
            instruction="Design system",
            expected_output="system_design",
            handoff_conditions=["design_complete"]
        )

        assert step.priority == "medium"
        assert step.timeout_minutes == 10
        assert step.required_context == []

class TestWorkflowTemplate:
    """Test WorkflowTemplate dataclass."""

    @pytest.mark.mock_data

    def test_workflow_template_creation(self):
        """Test creating a workflow template."""
        steps = [
            WorkflowStep(
                agent_type="analyst",
                instruction="Step 1",
                expected_output="output1",
                handoff_conditions=["step1_complete"]
            ),
            WorkflowStep(
                agent_type="architect",
                instruction="Step 2",
                expected_output="output2",
                handoff_conditions=["step2_complete"]
            )
        ]

        template = WorkflowTemplate(
            name="Test Template",
            description="A test template",
            workflow_type=WorkflowType.REQUIREMENTS_ANALYSIS,
            steps=steps,
            max_duration_minutes=60,
            required_agents=["analyst", "architect"],
            success_criteria=["All steps completed", "Quality standards met"]
        )

        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert template.workflow_type == WorkflowType.REQUIREMENTS_ANALYSIS
        assert len(template.steps) == 2
        assert template.max_duration_minutes == 60
        assert template.required_agents == ["analyst", "architect"]
        assert template.success_criteria == ["All steps completed", "Quality standards met"]
        assert template.fallback_strategies == {}

    @pytest.mark.mock_data

    def test_workflow_template_default_fallback_strategies(self):
        """Test workflow template default fallback strategies."""
        template = WorkflowTemplate(
            name="Test",
            description="Test",
            workflow_type=WorkflowType.SYSTEM_DESIGN,
            steps=[],
            max_duration_minutes=30,
            required_agents=["architect"],
            success_criteria=["Success"]
        )

        assert template.fallback_strategies == {}

class TestWorkflowType:
    """Test WorkflowType enum."""

    @pytest.mark.mock_data

    def test_workflow_type_values(self):
        """Test workflow type enum values."""
        assert WorkflowType.REQUIREMENTS_ANALYSIS.value == "requirements_analysis"
        assert WorkflowType.SYSTEM_DESIGN.value == "system_design"
        assert WorkflowType.CODE_REVIEW.value == "code_review"
        assert WorkflowType.TESTING_STRATEGY.value == "testing_strategy"
        assert WorkflowType.DEPLOYMENT_PLANNING.value == "deployment_planning"
        assert WorkflowType.ARCHITECTURE_REVIEW.value == "architecture_review"
        assert WorkflowType.SECURITY_ASSESSMENT.value == "security_assessment"
        assert WorkflowType.PERFORMANCE_OPTIMIZATION.value == "performance_optimization"

    @pytest.mark.mock_data

    def test_workflow_type_string_representation(self):
        """Test workflow type string representation."""
        assert str(WorkflowType.REQUIREMENTS_ANALYSIS) == "WorkflowType.REQUIREMENTS_ANALYSIS"
        assert WorkflowType.REQUIREMENTS_ANALYSIS.value == "requirements_analysis"
