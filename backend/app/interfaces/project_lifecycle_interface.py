"""Project lifecycle manager interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from uuid import UUID

from app.models.task import Task


class IProjectLifecycleManager(ABC):
    """Interface for project lifecycle management operations."""

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