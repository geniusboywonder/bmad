"""
HITL Service Interface - Interface definitions for HITL services.

Defines interfaces for all HITL-related services following Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from app.models.handoff import HandoffSchema
from app.models.workflow_state import WorkflowExecutionStateModel
from app.models.task import Task


class IHitlCore(ABC):
    """Interface for HITL core coordination service."""

    @abstractmethod
    async def request_human_input(
        self,
        project_id: UUID,
        request_type: str,
        details: Dict[str, Any],
        priority: str = "normal",
        timeout_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Request human input for project decisions."""
        pass

    @abstractmethod
    async def process_human_response(
        self,
        project_id: UUID,
        task_id: UUID,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process human response and continue workflow."""
        pass

    @abstractmethod
    async def check_hitl_triggers_after_step(
        self,
        execution: WorkflowExecutionStateModel,
        step_result: Dict[str, Any]
    ) -> Optional[Task]:
        """Check if HITL should be triggered after workflow step."""
        pass


class ITriggerProcessor(ABC):
    """Interface for HITL trigger processing."""

    @abstractmethod
    async def should_trigger_hitl(
        self,
        execution: WorkflowExecutionStateModel,
        step_result: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Determine if HITL should be triggered."""
        pass

    @abstractmethod
    async def evaluate_trigger_conditions(
        self,
        project_id: UUID,
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate trigger conditions."""
        pass


class IResponseProcessor(ABC):
    """Interface for HITL response processing."""

    @abstractmethod
    async def validate_response(
        self,
        task: Task,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate human response data."""
        pass

    @abstractmethod
    async def extract_decisions(
        self,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract decisions from response data."""
        pass


class IPhaseGateManager(ABC):
    """Interface for HITL phase gate management."""

    @abstractmethod
    async def evaluate_phase_completion(
        self,
        project_id: UUID,
        phase: str,
        deliverables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate if phase can be completed."""
        pass

    @abstractmethod
    async def request_phase_approval(
        self,
        project_id: UUID,
        phase: str,
        completion_data: Dict[str, Any]
    ) -> Task:
        """Request approval for phase completion."""
        pass


class IValidationEngine(ABC):
    """Interface for HITL validation engine."""

    @abstractmethod
    async def validate_deliverable_quality(
        self,
        deliverable: Dict[str, Any],
        quality_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate deliverable quality."""
        pass

    @abstractmethod
    async def assess_project_progress(
        self,
        project_id: UUID,
        current_phase: str
    ) -> Dict[str, Any]:
        """Assess overall project progress."""
        pass