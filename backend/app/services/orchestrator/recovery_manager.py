"""Recovery management service - systematic recovery procedures for orchestrator failures.

Extracted from orchestrator.py during Phase 3 targeted cleanup to separate recovery concerns.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum
import structlog

from app.database.models import RecoverySessionDB, EmergencyStopDB
from app.database.connection import get_session
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class RecoveryStrategy(Enum):
    """Recovery strategies for different failure scenarios."""
    ROLLBACK = "ROLLBACK"
    RETRY = "RETRY"
    CONTINUE = "CONTINUE"
    ABORT = "ABORT"


class RecoveryStep:
    """Represents a single step in a recovery procedure."""

    def __init__(
        self,
        step_id: str,
        description: str,
        action_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
        timeout_seconds: int = 300
    ):
        self.step_id = step_id
        self.description = description
        self.action_type = action_type
        self.parameters = parameters or {}
        self.requires_approval = requires_approval
        self.timeout_seconds = timeout_seconds
        self.status = "PENDING"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "requires_approval": self.requires_approval,
            "timeout_seconds": self.timeout_seconds,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


class RecoveryManager:
    """Manages systematic recovery procedures for orchestrator failures."""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    async def initiate_recovery(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        failure_reason: str,
        failure_context: Dict[str, Any],
        emergency_stop_id: Optional[UUID] = None
    ) -> UUID:
        """Initiate a recovery session for a failed operation."""

        logger.info("Initiating recovery session",
                   project_id=str(project_id),
                   task_id=str(task_id),
                   agent_type=agent_type,
                   failure_reason=failure_reason)

        # Determine recovery strategy based on failure type
        strategy = self._determine_recovery_strategy(failure_reason, failure_context)

        # Create recovery steps based on strategy
        recovery_steps = self._create_recovery_steps(strategy, failure_context)

        # Create recovery session record
        session = RecoverySessionDB(
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            failure_reason=failure_reason,
            failure_context=failure_context,
            recovery_strategy=strategy.value,
            recovery_steps=[step.to_dict() for step in recovery_steps],
            current_step=0,
            total_steps=len(recovery_steps),
            status="INITIATED"
        )

        if emergency_stop_id:
            session.emergency_stop_id = emergency_stop_id

        db = next(get_session())
        try:
            db.add(session)
            db.commit()
            db.refresh(session)

            # Store in active sessions
            self.active_sessions[str(session.id)] = {
                "session": session,
                "steps": recovery_steps,
                "strategy": strategy
            }

            # Broadcast recovery initiation
            await self._broadcast_recovery_event(session, "INITIATED")

            logger.info("Recovery session created",
                       session_id=str(session.id),
                       strategy=strategy.value,
                       steps_count=len(recovery_steps))

            return session.id

        finally:
            db.close()

    def _determine_recovery_strategy(
        self,
        failure_reason: str,
        failure_context: Dict[str, Any]
    ) -> RecoveryStrategy:
        """Determine the appropriate recovery strategy based on failure analysis."""

        # Analyze failure type
        if "budget" in failure_reason.lower():
            return RecoveryStrategy.ABORT
        elif "timeout" in failure_reason.lower():
            return RecoveryStrategy.RETRY
        elif "emergency" in failure_reason.lower():
            return RecoveryStrategy.ROLLBACK
        elif "validation" in failure_reason.lower():
            return RecoveryStrategy.CONTINUE
        else:
            return RecoveryStrategy.RETRY

    def _create_recovery_steps(
        self,
        strategy: RecoveryStrategy,
        failure_context: Dict[str, Any]
    ) -> List[RecoveryStep]:
        """Create recovery steps based on strategy."""

        steps = []

        if strategy == RecoveryStrategy.ROLLBACK:
            steps.extend([
                RecoveryStep("rollback_state", "Rollback to previous state", "rollback"),
                RecoveryStep("verify_rollback", "Verify rollback success", "verify"),
                RecoveryStep("notify_completion", "Notify recovery completion", "notify")
            ])
        elif strategy == RecoveryStrategy.RETRY:
            steps.extend([
                RecoveryStep("analyze_failure", "Analyze failure cause", "analyze"),
                RecoveryStep("retry_operation", "Retry failed operation", "retry"),
                RecoveryStep("verify_success", "Verify operation success", "verify")
            ])
        elif strategy == RecoveryStrategy.CONTINUE:
            steps.extend([
                RecoveryStep("skip_failed_step", "Skip failed step", "skip"),
                RecoveryStep("continue_workflow", "Continue with next step", "continue")
            ])
        elif strategy == RecoveryStrategy.ABORT:
            steps.extend([
                RecoveryStep("cleanup_resources", "Clean up resources", "cleanup"),
                RecoveryStep("abort_workflow", "Abort workflow", "abort"),
                RecoveryStep("notify_abort", "Notify workflow abort", "notify")
            ])

        return steps

    async def _broadcast_recovery_event(self, session: RecoverySessionDB, event_type: str):
        """Broadcast recovery event via WebSocket."""
        event = WebSocketEvent(
            type=EventType.RECOVERY_UPDATE,
            data={
                "session_id": str(session.id),
                "project_id": str(session.project_id),
                "event_type": event_type,
                "strategy": session.recovery_strategy,
                "status": session.status
            }
        )

        await websocket_manager.broadcast_to_project(str(session.project_id), event)
