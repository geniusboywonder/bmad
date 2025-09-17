"""Handoff manager interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.models.task import Task
from app.models.handoff import HandoffSchema


class IHandoffManager(ABC):
    """Interface for handoff management operations."""

    @abstractmethod
    def create_task_from_handoff(self, handoff: HandoffSchema = None, project_id: UUID = None,
                               handoff_schema: Dict[str, Any] = None) -> Task:
        """Create a task from a HandoffSchema or raw handoff data."""
        pass

    @abstractmethod
    async def process_task_with_autogen(self, task: Task, handoff: HandoffSchema) -> dict:
        """Process a task using AutoGen with handoff context."""
        pass

    @abstractmethod
    def create_handoff_chain(self, project_id: UUID, handoff_chain: List[Dict[str, Any]]) -> List[Task]:
        """Create a chain of handoff tasks."""
        pass

    @abstractmethod
    def get_handoff_history(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get handoff history for a project."""
        pass

    @abstractmethod
    def validate_handoff_chain(self, handoff_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a handoff chain for consistency."""
        pass

    @abstractmethod
    def get_active_handoffs(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get currently active handoffs for a project."""
        pass

    @abstractmethod
    def cancel_handoff(self, task_id: UUID, reason: str) -> bool:
        """Cancel an active handoff."""
        pass