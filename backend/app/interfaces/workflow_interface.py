"""
Workflow Service Interface - Interface definitions for workflow services.

Defines interfaces for all workflow-related services following Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowExecutionState
from app.models.handoff import HandoffSchema


class IExecutionEngine(ABC):
    """Interface for workflow execution engine."""

    @abstractmethod
    async def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: UUID,
        context_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start workflow execution."""
        pass

    @abstractmethod
    async def execute_workflow_step(
        self,
        execution_id: str,
        step_index: int,
        context_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a specific workflow step."""
        pass

    @abstractmethod
    async def execute_parallel_steps(
        self,
        execution_id: str,
        step_indices: List[int],
        context_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple workflow steps in parallel."""
        pass

    @abstractmethod
    async def pause_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """Pause workflow execution."""
        pass

    @abstractmethod
    async def resume_workflow_execution(self, execution_id: str) -> bool:
        """Resume paused workflow execution."""
        pass

    @abstractmethod
    async def cancel_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """Cancel workflow execution."""
        pass


class IStateManager(ABC):
    """Interface for workflow state management."""

    @abstractmethod
    def get_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Get workflow execution state by ID."""
        pass

    @abstractmethod
    def persist_execution_state(self, execution: WorkflowExecutionStateModel) -> None:
        """Persist workflow execution state to database."""
        pass

    @abstractmethod
    def create_execution_state(
        self,
        execution_id: str,
        workflow_id: str,
        project_id: UUID,
        workflow_definition: Dict[str, Any],
        initial_context: Dict[str, Any]
    ) -> WorkflowExecutionStateModel:
        """Create new workflow execution state."""
        pass

    @abstractmethod
    def update_execution_state(
        self,
        execution_id: str,
        state: Optional[WorkflowExecutionState] = None,
        current_step_index: Optional[int] = None,
        context_data: Optional[Dict[str, Any]] = None,
        step_results: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecutionStateModel]:
        """Update workflow execution state."""
        pass

    @abstractmethod
    def recover_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Recover workflow execution state from persistence."""
        pass


class IEventDispatcher(ABC):
    """Interface for workflow event dispatching."""

    @abstractmethod
    async def emit_workflow_started(
        self,
        execution: WorkflowExecutionStateModel,
        workflow_definition: Dict[str, Any]
    ) -> None:
        """Emit workflow started event."""
        pass

    @abstractmethod
    async def emit_workflow_step_completed(
        self,
        execution: WorkflowExecutionStateModel,
        step_index: int,
        step_result: Dict[str, Any]
    ) -> None:
        """Emit workflow step completed event."""
        pass

    @abstractmethod
    async def emit_workflow_completed(
        self,
        execution: WorkflowExecutionStateModel,
        final_results: Dict[str, Any]
    ) -> None:
        """Emit workflow completed event."""
        pass

    @abstractmethod
    async def emit_workflow_failed(
        self,
        execution: WorkflowExecutionStateModel,
        error_message: str,
        error_details: Dict[str, Any] = None
    ) -> None:
        """Emit workflow failed event."""
        pass

    @abstractmethod
    async def emit_workflow_paused(
        self,
        execution: WorkflowExecutionStateModel,
        reason: str
    ) -> None:
        """Emit workflow paused event."""
        pass

    @abstractmethod
    async def emit_workflow_resumed(
        self,
        execution: WorkflowExecutionStateModel
    ) -> None:
        """Emit workflow resumed event."""
        pass


class ISdlcOrchestrator(ABC):
    """Interface for SDLC workflow orchestration."""

    @abstractmethod
    async def execute_sdlc_workflow(
        self,
        project_id: UUID,
        requirements: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute SDLC workflow."""
        pass

    @abstractmethod
    def get_sdlc_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get SDLC workflow status."""
        pass

    @abstractmethod
    async def execute_sdlc_phase(
        self,
        execution: WorkflowExecutionStateModel,
        phase: str,
        phase_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute specific SDLC phase."""
        pass