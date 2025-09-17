"""Workflow integrator interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID


class IWorkflowIntegrator(ABC):
    """Interface for workflow integration operations."""

    @abstractmethod
    async def run_project_workflow(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """Runs a dynamic workflow for a project using the WorkflowExecutionEngine."""
        pass

    @abstractmethod
    async def detect_and_resolve_conflicts(self, project_id: UUID, workflow_id: str) -> Dict[str, Any]:
        """Detect and attempt to resolve conflicts in a project workflow."""
        pass

    @abstractmethod
    async def execute_workflow_phase(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Execute workflow phase with HITL integration."""
        pass

    @abstractmethod
    async def handle_phase_transition(self, project_id: UUID, from_phase: str, to_phase: str) -> bool:
        """Handle workflow phase transitions with validation."""
        pass

    @abstractmethod
    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current workflow execution status."""
        pass

    @abstractmethod
    async def cancel_workflow(self, execution_id: str, reason: str) -> bool:
        """Cancel a running workflow execution."""
        pass