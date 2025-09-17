"""Context manager interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID


class IContextManager(ABC):
    """Interface for context management operations."""

    @abstractmethod
    def get_selective_context(self, project_id: UUID, phase: str, agent_type: str) -> List[UUID]:
        """Get selective context artifacts relevant to the current phase and agent."""
        pass

    @abstractmethod
    def get_latest_amended_artifact(self, project_id: UUID, task_id: UUID) -> Optional['ContextArtifact']:
        """Get the latest amended artifact for a specific task."""
        pass

    @abstractmethod
    def get_integrated_context_summary(self, project_id: UUID, agent_type: str, phase: str,
                                     include_time_analysis: bool = True,
                                     time_budget_hours: float = None) -> Dict[str, Any]:
        """Get comprehensive integrated context summary with all granularity features."""
        pass

    @abstractmethod
    def get_context_granularity_report(self, project_id: UUID) -> Dict[str, Any]:
        """Generate comprehensive context granularity report for the project."""
        pass