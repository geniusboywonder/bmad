"""Orchestrator service interface for dependency injection."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.models.task import Task
from app.models.handoff import HandoffSchema


class IOrchestratorService(ABC):
    """Interface for orchestrator service operations."""

    # ===== PROJECT LIFECYCLE =====

    @abstractmethod
    def create_project(self, name: str, description: str = None) -> UUID:
        """Create new project with initial state."""
        pass

    @abstractmethod
    def get_current_phase(self, project_id: UUID) -> str:
        """Get the current SDLC phase for a project."""
        pass

    @abstractmethod
    def set_current_phase(self, project_id: UUID, phase: str):
        """Set the current SDLC phase for a project."""
        pass

    @abstractmethod
    def validate_phase_completion(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate if a phase has met its completion criteria."""
        pass

    @abstractmethod
    def transition_to_next_phase(self, project_id: UUID) -> Dict[str, Any]:
        """Transition project to the next SDLC phase if current phase is completed."""
        pass

    @abstractmethod
    def get_phase_progress(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive progress information for all phases."""
        pass

    @abstractmethod
    def get_project_tasks(self, project_id: UUID) -> List[Task]:
        """Get all tasks for a project."""
        pass

    # ===== WORKFLOW EXECUTION =====

    @abstractmethod
    async def run_project_workflow(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """Runs a dynamic workflow for a project using the WorkflowExecutionEngine."""
        pass

    @abstractmethod
    def run_project_workflow_sync(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """Synchronous wrapper for run_project_workflow."""
        pass

    # ===== AGENT COORDINATION =====

    @abstractmethod
    def create_task(self, project_id: UUID, agent_type: str, instructions: str, context_ids: List[UUID] = None) -> Task:
        """Create a new task for an agent."""
        pass

    @abstractmethod
    def submit_task(self, task: Task) -> str:
        """Submit a task to the Celery queue."""
        pass

    @abstractmethod
    def update_task_status(self, task_id: UUID, status, output: Dict[str, Any] = None, error_message: str = None):
        """Update a task's status."""
        pass

    @abstractmethod
    def update_agent_status(self, agent_type: str, status, current_task_id: UUID = None, error_message: str = None):
        """Update an agent's status."""
        pass

    @abstractmethod
    def get_agent_status(self, agent_type: str):
        """Get an agent's current status."""
        pass

    # ===== HANDOFF MANAGEMENT =====

    @abstractmethod
    def create_task_from_handoff(self, handoff: HandoffSchema = None, project_id: UUID = None,
                               handoff_schema: Dict[str, Any] = None) -> Task:
        """Create a task from a HandoffSchema or raw handoff data."""
        pass

    @abstractmethod
    async def process_task_with_autogen(self, task: Task, handoff: HandoffSchema) -> dict:
        """Process a task using AutoGen with handoff context."""
        pass

    # ===== STATUS AND METRICS =====

    @abstractmethod
    def get_phase_time_analysis(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive time analysis for all project phases."""
        pass

    @abstractmethod
    def get_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the project."""
        pass

    # ===== CONTEXT MANAGEMENT =====

    @abstractmethod
    def get_selective_context(self, project_id: UUID, phase: str, agent_type: str) -> List[UUID]:
        """Get selective context artifacts relevant to the current phase and agent."""
        pass

    @abstractmethod
    def get_integrated_context_summary(self, project_id: UUID, agent_type: str, phase: str,
                                     include_time_analysis: bool = True,
                                     time_budget_hours: float = None) -> Dict[str, Any]:
        """Get comprehensive integrated context summary with all granularity features."""
        pass

    # ===== HITL INTEGRATION =====

    @abstractmethod
    def create_hitl_request(self, project_id: UUID, request_type: str, content: Dict[str, Any],
                          priority: str = "medium") -> UUID:
        """Create a new HITL request."""
        pass

    @abstractmethod
    def process_hitl_response(self, request_id: UUID, action: str, response_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process HITL response and update workflow accordingly."""
        pass

    # ===== HEALTH CHECK =====

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all orchestrator services."""
        pass