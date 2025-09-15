"""
Workflow State Models for BMAD Core Template System

This module defines Pydantic models for workflow execution state management
and persistence.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class WorkflowExecutionState(str, Enum):
    """Enumeration of workflow execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowStepExecutionState(BaseModel):
    """
    Represents the execution state of a single workflow step.

    This model tracks the runtime state and results of individual workflow steps
    for persistence and recovery.
    """
    step_index: int = Field(..., description="Index of the step in the workflow sequence")
    agent: str = Field(..., description="Agent assigned to this step")
    status: WorkflowExecutionState = Field(default=WorkflowExecutionState.PENDING)
    task_id: Optional[str] = Field(None, description="Associated task ID if created")
    started_at: Optional[str] = Field(None, description="Timestamp when step execution started")
    completed_at: Optional[str] = Field(None, description="Timestamp when step execution completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    artifacts_created: List[str] = Field(default_factory=list, description="List of artifacts created")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    last_retry_at: Optional[str] = Field(None, description="Timestamp of last retry attempt")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            UUID: lambda v: str(v),
        }
    )


class WorkflowExecutionStateModel(BaseModel):
    """
    Complete workflow execution state for persistence and recovery.

    This model represents the complete state of a workflow execution that can be
    persisted to the database and restored for recovery purposes.
    """
    execution_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for this execution")
    project_id: str = Field(..., description="ID of the project this execution belongs to")
    workflow_id: str = Field(..., description="ID of the workflow being executed")
    status: WorkflowExecutionState = Field(default=WorkflowExecutionState.PENDING)
    current_step: int = Field(default=0, description="Index of currently executing step")
    total_steps: int = Field(default=0, description="Total number of steps in the workflow")
    steps: List[WorkflowStepExecutionState] = Field(default_factory=list, description="Execution state of all steps")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow execution context and variables")
    created_artifacts: List[str] = Field(default_factory=list, description="All artifacts created during execution")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")
    started_at: Optional[str] = Field(None, description="Timestamp when execution started")
    completed_at: Optional[str] = Field(None, description="Timestamp when execution completed")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp when execution was created")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp when execution was last updated")

    # Recovery and resumption metadata
    recovery_attempts: int = Field(default=0, description="Number of recovery attempts")
    last_recovery_at: Optional[str] = Field(None, description="Timestamp of last recovery attempt")
    paused_reason: Optional[str] = Field(None, description="Reason for pausing if paused")
    cancelled_reason: Optional[str] = Field(None, description="Reason for cancellation if cancelled")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            UUID: lambda v: str(v),
        }
    )

    def get_pending_steps(self) -> List[WorkflowStepExecutionState]:
        """Get all steps that are pending execution."""
        return [step for step in self.steps if step.status == WorkflowExecutionState.PENDING]

    def get_running_steps(self) -> List[WorkflowStepExecutionState]:
        """Get all steps that are currently running."""
        return [step for step in self.steps if step.status == WorkflowExecutionState.RUNNING]

    def get_completed_steps(self) -> List[WorkflowStepExecutionState]:
        """Get all steps that have completed successfully."""
        return [step for step in self.steps if step.status == WorkflowExecutionState.COMPLETED]

    def get_failed_steps(self) -> List[WorkflowStepExecutionState]:
        """Get all steps that have failed."""
        return [step for step in self.steps if step.status == WorkflowExecutionState.FAILED]

    def get_current_step(self) -> Optional[WorkflowStepExecutionState]:
        """Get the currently executing step."""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None

    def get_next_pending_step(self) -> Optional[WorkflowStepExecutionState]:
        """Get the next pending step in sequence."""
        for step in self.steps:
            if step.status == WorkflowExecutionState.PENDING:
                return step
        return None

    def is_complete(self) -> bool:
        """Check if the workflow execution is complete."""
        return self.status in [WorkflowExecutionState.COMPLETED, WorkflowExecutionState.FAILED, WorkflowExecutionState.CANCELLED]

    def can_resume(self) -> bool:
        """Check if the workflow execution can be resumed."""
        return self.status in [WorkflowExecutionState.PENDING, WorkflowExecutionState.PAUSED, WorkflowExecutionState.RUNNING]

    def update_step_status(self, step_index: int, status: WorkflowExecutionState,
                          result: Optional[Dict[str, Any]] = None,
                          error_message: Optional[str] = None) -> None:
        """Update the status of a specific step."""
        if 0 <= step_index < len(self.steps):
            step = self.steps[step_index]
            step.status = status
            step.completed_at = datetime.now(timezone.utc).isoformat()

            if result is not None:
                step.result = result

            if error_message is not None:
                step.error_message = error_message

            # Update overall execution status
            self._update_execution_status()
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def _update_execution_status(self) -> None:
        """Update the overall execution status based on step statuses."""
        if not self.steps:
            return

        all_completed = all(step.status == WorkflowExecutionState.COMPLETED for step in self.steps)
        any_failed = any(step.status == WorkflowExecutionState.FAILED for step in self.steps)
        any_running = any(step.status == WorkflowExecutionState.RUNNING for step in self.steps)

        if all_completed:
            self.status = WorkflowExecutionState.COMPLETED
            self.completed_at = datetime.now(timezone.utc).isoformat()
        elif any_failed:
            self.status = WorkflowExecutionState.FAILED
        elif any_running:
            self.status = WorkflowExecutionState.RUNNING
        else:
            self.status = WorkflowExecutionState.PENDING

    def add_artifact(self, artifact_id: str) -> None:
        """Add an artifact to the list of created artifacts."""
        if artifact_id not in self.created_artifacts:
            self.created_artifacts.append(artifact_id)
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_started(self) -> None:
        """Mark the workflow execution as started."""
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()
        self.status = WorkflowExecutionState.RUNNING
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_completed(self) -> None:
        """Mark the workflow execution as completed."""
        self.status = WorkflowExecutionState.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def mark_failed(self, error_message: str) -> None:
        """Mark the workflow execution as failed."""
        self.status = WorkflowExecutionState.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def pause(self, reason: str) -> None:
        """Pause the workflow execution."""
        self.status = WorkflowExecutionState.PAUSED
        self.paused_reason = reason
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def resume(self) -> None:
        """Resume the workflow execution."""
        if self.status == WorkflowExecutionState.PAUSED:
            self.status = WorkflowExecutionState.RUNNING
            self.paused_reason = None
            self.updated_at = datetime.now(timezone.utc).isoformat()

    def cancel(self, reason: str) -> None:
        """Cancel the workflow execution."""
        self.status = WorkflowExecutionState.CANCELLED
        self.cancelled_reason = reason
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()


class WorkflowRecoveryPoint(BaseModel):
    """
    Represents a recovery point for workflow resumption.

    This model captures the state at a specific point that can be used
    to resume workflow execution after interruptions.
    """
    execution_id: str = Field(..., description="ID of the execution this recovery point belongs to")
    recovery_point_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for this recovery point")
    step_index: int = Field(..., description="Step index where recovery should resume")
    context_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Snapshot of context data at recovery point")
    artifacts_snapshot: List[str] = Field(default_factory=list, description="Snapshot of created artifacts")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Timestamp when recovery point was created")
    reason: str = Field(..., description="Reason for creating this recovery point")

    model_config = ConfigDict(arbitrary_types_allowed=True)
