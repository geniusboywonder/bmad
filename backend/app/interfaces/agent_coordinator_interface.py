"""Agent coordinator interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.models.task import Task
from app.models.agent import AgentStatus


class IAgentCoordinator(ABC):
    """Interface for agent coordination operations."""

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
    def update_agent_status(self, agent_type: str, status: AgentStatus, current_task_id: UUID = None, error_message: str = None):
        """Update an agent's status."""
        pass

    @abstractmethod
    def get_agent_status(self, agent_type: str) -> Optional[AgentStatus]:
        """Get an agent's current status."""
        pass

    @abstractmethod
    def assign_agent_to_task(self, task: Task) -> Dict[str, Any]:
        """Assign appropriate agent to task based on requirements."""
        pass

    @abstractmethod
    def coordinate_multi_agent_workflow(self, project_id: UUID, agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordinate multiple agents for complex workflows."""
        pass

    @abstractmethod
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of all available (non-working) agents."""
        pass

    @abstractmethod
    def get_agent_workload(self) -> Dict[str, Any]:
        """Get current workload distribution across agents."""
        pass

    @abstractmethod
    def reassign_failed_task(self, task_id: UUID) -> Dict[str, Any]:
        """Reassign a failed task to the same or different agent."""
        pass