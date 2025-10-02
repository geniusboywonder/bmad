"""
Workflow Data Models for BMAD Core Template System

This module defines Pydantic models for workflow definitions and execution.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WorkflowType(str, Enum):
    """Enumeration of supported workflow types."""
    GREENFIELD = "greenfield"
    BROWNFIELD = "brownfield"
    GENERIC = "generic"
    FULLSTACK = "fullstack"
    SERVICE = "service"
    UI = "ui"
    SDLC = "sdlc"  # Software Development Life Cycle workflow


class SDLCPhase(str, Enum):
    """Enumeration of SDLC phases."""
    DISCOVERY = "discovery"
    PLAN = "plan"
    DESIGN = "design"
    BUILD = "build"
    VALIDATE = "validate"
    LAUNCH = "launch"


class WorkflowStep(BaseModel):
    """
    Represents a single step in a workflow sequence.

    This model defines the structure of individual workflow steps including
    agent assignments, dependencies, conditions, and metadata.
    """
    agent: Optional[str] = Field(None, description="The agent responsible for this step (None for non-agent workflow steps)")
    creates: Optional[str] = Field(None, description="Output artifact created by this step")
    requires: Union[str, List[str]] = Field(default_factory=list, description="Required inputs or prerequisites")
    condition: Optional[str] = Field(None, description="Conditional execution criteria")
    notes: Optional[str] = Field(None, description="Additional notes and guidance")
    optional_steps: List[str] = Field(default_factory=list, description="Optional sub-steps that can be taken")
    action: Optional[str] = Field(None, description="Specific action to perform")
    repeatable: bool = Field(False, description="Whether this step can be repeated")

    model_config = ConfigDict(
        json_encoders={
            str: lambda v: v,
            list: lambda v: v
        }
    )


class WorkflowExecutionState(str, Enum):
    """Enumeration of workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowExecutionStep(BaseModel):
    """
    Represents the execution state of a workflow step.

    This model tracks the runtime state and results of individual workflow steps.
    """
    step_index: int = Field(..., description="Index of the step in the workflow sequence")
    agent: str = Field(..., description="Agent assigned to this step")
    status: WorkflowExecutionState = Field(default=WorkflowExecutionState.PENDING)
    started_at: Optional[str] = Field(None, description="Timestamp when step execution started")
    completed_at: Optional[str] = Field(None, description="Timestamp when step execution completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    artifacts_created: List[str] = Field(default_factory=list, description="List of artifacts created")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowExecution(BaseModel):
    """
    Represents the complete execution state of a workflow.

    This model tracks the overall progress and state of a workflow execution
    including all steps, current status, and execution metadata.
    """
    workflow_id: str = Field(..., description="ID of the workflow being executed")
    project_id: str = Field(..., description="ID of the project this execution belongs to")
    execution_id: str = Field(..., description="Unique identifier for this execution")
    status: WorkflowExecutionState = Field(default=WorkflowExecutionState.PENDING)
    current_step: Optional[int] = Field(None, description="Index of currently executing step")
    steps: List[WorkflowExecutionStep] = Field(default_factory=list, description="Execution state of all steps")
    started_at: Optional[str] = Field(None, description="Timestamp when execution started")
    completed_at: Optional[str] = Field(None, description="Timestamp when execution completed")
    created_artifacts: List[str] = Field(default_factory=list, description="All artifacts created during execution")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Execution context and variables")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class WorkflowDefinition(BaseModel):
    """
    Complete workflow definition loaded from YAML.

    This model represents a complete workflow definition with all its metadata,
    sequence of steps, decision guidance, and execution parameters.
    """
    id: str = Field(..., description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name of the workflow")
    description: str = Field("", description="Detailed description of the workflow")
    type: WorkflowType = Field(default=WorkflowType.GENERIC, description="Type of workflow")
    project_types: List[str] = Field(default_factory=list, description="Supported project types")
    sequence: List[WorkflowStep] = Field(default_factory=list, description="Ordered sequence of workflow steps")
    flow_diagram: str = Field("", description="Mermaid diagram representing workflow flow")
    decision_guidance: Dict[str, Any] = Field(default_factory=dict, description="Guidance for decision points")
    handoff_prompts: Dict[str, str] = Field(default_factory=dict, description="Prompts for agent handoffs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            WorkflowType: lambda v: v.value,
            WorkflowStep: lambda v: v.model_dump(),
            dict: lambda v: v,
            list: lambda v: v
        }
    )

    def get_step_by_index(self, index: int) -> Optional[WorkflowStep]:
        """Get a workflow step by its index in the sequence."""
        if 0 <= index < len(self.sequence):
            return self.sequence[index]
        return None

    def get_next_agent(self, current_step: Optional[int] = None) -> Optional[str]:
        """Get the next agent in the workflow sequence."""
        if current_step is None:
            return self.sequence[0].agent if self.sequence else None

        next_index = current_step + 1
        if next_index < len(self.sequence):
            return self.sequence[next_index].agent
        return None

    def validate_sequence(self) -> List[str]:
        """
        Validate the workflow sequence for consistency.

        Returns:
            List of validation error messages
        """
        errors = []

        if not self.sequence:
            errors.append("Workflow must have at least one step")
            return errors

        # Check for duplicate agents in sequence (if not allowed)
        agents = [step.agent for step in self.sequence]
        if len(agents) != len(set(agents)):
            errors.append("Duplicate agents found in workflow sequence")

        # Validate step dependencies
        for i, step in enumerate(self.sequence):
            if step.requires:
                required_items = step.requires if isinstance(step.requires, list) else [step.requires]
                # Check if required items are created by previous steps
                previous_creates = {s.creates for s in self.sequence[:i] if s.creates}
                for required in required_items:
                    if isinstance(required, str) and required not in previous_creates:
                        # This is just a warning, not necessarily an error
                        pass

        return errors

    def get_handoff_prompt(self, from_agent: str, to_agent: str) -> Optional[str]:
        """Get the handoff prompt for transitioning between agents."""
        prompt_key = f"{from_agent}_to_{to_agent}"
        return self.handoff_prompts.get(prompt_key)

    def is_conditional_step(self, step_index: int) -> bool:
        """Check if a step has conditional execution criteria."""
        if 0 <= step_index < len(self.sequence):
            return self.sequence[step_index].condition is not None
        return False

    def get_step_condition(self, step_index: int) -> Optional[str]:
        """Get the condition for a specific step."""
        if 0 <= step_index < len(self.sequence):
            return self.sequence[step_index].condition
        return None


class SDLCWorkflowDefinition(WorkflowDefinition):
    """
    Specialized workflow definition for Software Development Life Cycle.

    This class provides a structured 6-phase SDLC workflow with predefined
    phases, agent assignments, and validation rules.
    """

    def __init__(self, **data):
        super().__init__(**data)
        self.type = WorkflowType.SDLC
        self._initialize_sdlc_phases()

    def _initialize_sdlc_phases(self):
        """Initialize the 6-phase SDLC workflow structure."""

        sdlc_phases = [
            # Phase 1: Discovery
            WorkflowStep(
                agent="analyst",
                creates="project_requirements",
                requires=[],
                condition=None,
                notes="Gather and analyze project requirements, user needs, and business objectives",
                action="Analyze project requirements and create comprehensive PRD",
                repeatable=False
            ),

            # Phase 2: Plan
            WorkflowStep(
                agent="analyst",
                creates="project_plan",
                requires=["project_requirements"],
                condition=None,
                notes="Create detailed project plan with timeline, milestones, and resource allocation",
                action="Develop detailed project plan and success criteria",
                repeatable=False
            ),

            # Phase 3: Design
            WorkflowStep(
                agent="architect",
                creates="technical_architecture",
                requires=["project_plan"],
                condition=None,
                notes="Design system architecture, API specifications, and technical implementation plan",
                action="Create comprehensive technical architecture and design specifications",
                repeatable=False
            ),

            # Phase 4: Build
            WorkflowStep(
                agent="coder",
                creates="source_code",
                requires=["technical_architecture"],
                condition=None,
                notes="Implement the designed solution with comprehensive testing",
                action="Develop production-ready code following established patterns",
                repeatable=False
            ),

            # Phase 5: Validate
            WorkflowStep(
                agent="tester",
                creates="validation_results",
                requires=["source_code"],
                condition=None,
                notes="Comprehensive testing and validation of the implemented solution",
                action="Execute thorough testing and quality validation",
                repeatable=False
            ),

            # Phase 6: Launch
            WorkflowStep(
                agent="deployer",
                creates="deployment_artifacts",
                requires=["validation_results"],
                condition=None,
                notes="Deploy solution to production with monitoring and maintenance setup",
                action="Execute production deployment and establish monitoring",
                repeatable=False
            )
        ]

        self.sequence = sdlc_phases

        # Set SDLC-specific metadata
        self.metadata.update({
            "sdlc_phases": [phase.value for phase in SDLCPhase],
            "phase_gates": True,
            "quality_gates": True,
            "approval_required": True,
            "max_iterations_per_phase": 3
        })

        # Set handoff prompts for SDLC transitions
        self.handoff_prompts = {
            "analyst_to_analyst": "Transitioning from requirements analysis to detailed planning phase",
            "analyst_to_architect": "Handing off requirements to technical architecture design",
            "architect_to_coder": "Providing technical specifications for implementation",
            "coder_to_tester": "Delivering completed implementation for validation",
            "tester_to_deployer": "Providing validated solution for production deployment"
        }

    def get_sdlc_phase(self, step_index: int) -> Optional[SDLCPhase]:
        """Get the SDLC phase for a given step index."""
        phase_mapping = {
            0: SDLCPhase.DISCOVERY,
            1: SDLCPhase.PLAN,
            2: SDLCPhase.DESIGN,
            3: SDLCPhase.BUILD,
            4: SDLCPhase.VALIDATE,
            5: SDLCPhase.LAUNCH
        }
        return phase_mapping.get(step_index)

    def get_phase_requirements(self, phase: SDLCPhase) -> Dict[str, Any]:
        """Get requirements and validation criteria for a specific SDLC phase."""

        phase_requirements = {
            SDLCPhase.DISCOVERY: {
                "required_outputs": ["user_stories", "acceptance_criteria", "business_requirements"],
                "validation_criteria": ["completeness", "clarity", "feasibility"],
                "quality_gate": "requirements_review",
                "estimated_effort": "1-2 weeks"
            },
            SDLCPhase.PLAN: {
                "required_outputs": ["project_timeline", "resource_plan", "risk_assessment"],
                "validation_criteria": ["realism", "comprehensiveness", "alignment"],
                "quality_gate": "planning_review",
                "estimated_effort": "1 week"
            },
            SDLCPhase.DESIGN: {
                "required_outputs": ["architecture_diagram", "api_specification", "data_model"],
                "validation_criteria": ["scalability", "maintainability", "security"],
                "quality_gate": "design_review",
                "estimated_effort": "2-3 weeks"
            },
            SDLCPhase.BUILD: {
                "required_outputs": ["source_code", "unit_tests", "documentation"],
                "validation_criteria": ["functionality", "performance", "code_quality"],
                "quality_gate": "code_review",
                "estimated_effort": "4-6 weeks"
            },
            SDLCPhase.VALIDATE: {
                "required_outputs": ["test_results", "quality_report", "performance_metrics"],
                "validation_criteria": ["coverage", "reliability", "user_acceptance"],
                "quality_gate": "validation_review",
                "estimated_effort": "2-3 weeks"
            },
            SDLCPhase.LAUNCH: {
                "required_outputs": ["deployment_package", "monitoring_setup", "maintenance_plan"],
                "validation_criteria": ["stability", "performance", "security"],
                "quality_gate": "go_live_review",
                "estimated_effort": "1-2 weeks"
            }
        }

        return phase_requirements.get(phase, {})

    def validate_sdlc_compliance(self) -> List[str]:
        """Validate that the workflow complies with SDLC best practices."""

        errors = []
        warnings = []

        # Check phase sequence
        expected_phases = [SDLCPhase.DISCOVERY, SDLCPhase.PLAN, SDLCPhase.DESIGN,
                          SDLCPhase.BUILD, SDLCPhase.VALIDATE, SDLCPhase.LAUNCH]

        for i, expected_phase in enumerate(expected_phases):
            if i >= len(self.sequence):
                errors.append(f"Missing {expected_phase.value} phase")
                continue

            actual_agent = self.sequence[i].agent
            expected_agent = self._get_expected_agent_for_phase(expected_phase)

            if actual_agent != expected_agent:
                warnings.append(f"Phase {expected_phase.value}: expected agent '{expected_agent}', got '{actual_agent}'")

        # Check for required phase gates
        if not self.metadata.get("phase_gates", False):
            warnings.append("Phase gates not enabled - recommended for SDLC compliance")

        # Check for quality gates
        if not self.metadata.get("quality_gates", False):
            warnings.append("Quality gates not enabled - recommended for SDLC compliance")

        return errors + warnings

    def _get_expected_agent_for_phase(self, phase: SDLCPhase) -> str:
        """Get the expected agent for a given SDLC phase."""

        agent_mapping = {
            SDLCPhase.DISCOVERY: "analyst",
            SDLCPhase.PLAN: "analyst",
            SDLCPhase.DESIGN: "architect",
            SDLCPhase.BUILD: "coder",
            SDLCPhase.VALIDATE: "tester",
            SDLCPhase.LAUNCH: "deployer"
        }

        return agent_mapping.get(phase, "unknown")

    def get_sdlc_progress_percentage(self, current_step: int) -> float:
        """Calculate SDLC progress percentage based on current step."""

        if current_step < 0:
            return 0.0
        elif current_step >= len(self.sequence):
            return 100.0
        else:
            return (current_step / len(self.sequence)) * 100.0

    def can_proceed_to_next_phase(self, current_step: int, phase_results: Dict[str, Any]) -> bool:
        """Determine if workflow can proceed to the next SDLC phase."""

        if current_step >= len(self.sequence) - 1:
            return True  # Last phase completed

        current_phase = self.get_sdlc_phase(current_step)
        if not current_phase:
            return False

        # Get phase requirements
        requirements = self.get_phase_requirements(current_phase)

        # Check required outputs
        required_outputs = requirements.get("required_outputs", [])
        for output in required_outputs:
            if output not in phase_results:
                return False

        # Check validation criteria
        validation_criteria = requirements.get("validation_criteria", [])
        for criterion in validation_criteria:
            if not self._validate_criterion(criterion, phase_results):
                return False

        return True

    def _validate_criterion(self, criterion: str, phase_results: Dict[str, Any]) -> bool:
        """Validate a specific criterion against phase results."""

        # Simple validation logic - can be enhanced
        if criterion == "completeness":
            return phase_results.get("completeness_score", 0) >= 0.8
        elif criterion == "clarity":
            return phase_results.get("clarity_score", 0) >= 0.7
        elif criterion == "feasibility":
            return phase_results.get("feasibility_score", 0) >= 0.6
        elif criterion == "scalability":
            return phase_results.get("scalability_score", 0) >= 0.8
        elif criterion == "maintainability":
            return phase_results.get("maintainability_score", 0) >= 0.7
        elif criterion == "security":
            return phase_results.get("security_score", 0) >= 0.8
        elif criterion == "functionality":
            return phase_results.get("functionality_score", 0) >= 0.9
        elif criterion == "performance":
            return phase_results.get("performance_score", 0) >= 0.8
        elif criterion == "code_quality":
            return phase_results.get("code_quality_score", 0) >= 0.8
        elif criterion == "coverage":
            return phase_results.get("test_coverage", 0) >= 0.85
        elif criterion == "reliability":
            return phase_results.get("reliability_score", 0) >= 0.9
        elif criterion == "user_acceptance":
            return phase_results.get("user_acceptance_score", 0) >= 0.8
        elif criterion == "stability":
            return phase_results.get("stability_score", 0) >= 0.9

        # Default to True for unknown criteria
        return True
