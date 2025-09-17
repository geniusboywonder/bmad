"""Status tracker interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from uuid import UUID


class IStatusTracker(ABC):
    """Interface for status tracking operations."""

    @abstractmethod
    def get_phase_time_analysis(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive time analysis for all project phases."""
        pass

    @abstractmethod
    def get_time_conscious_context(self, project_id: UUID, phase: str, agent_type: str,
                                 time_budget_hours: float = None) -> Dict[str, Any]:
        """Get context information that is time-conscious and filtered based on current time pressure."""
        pass

    @abstractmethod
    def get_time_based_phase_transition(self, project_id: UUID) -> Dict[str, Any]:
        """Determine if phase transition should occur based on time analysis."""
        pass

    @abstractmethod
    def get_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the project."""
        pass