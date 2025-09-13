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


class WorkflowStep(BaseModel):
    """
    Represents a single step in a workflow sequence.

    This model defines the structure of individual workflow steps including
    agent assignments, dependencies, conditions, and metadata.
    """
    agent: str = Field(..., description="The agent responsible for this step")
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
