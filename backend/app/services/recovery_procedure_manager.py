"""Recovery Procedure Manager for systematic recovery from HITL failures."""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import structlog
from datetime import datetime
from enum import Enum

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


class RecoveryProcedureManager:
    """Manages systematic recovery procedures for HITL failures."""

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
        elif failure_context.get("retry_count", 0) > 2:
            return RecoveryStrategy.ABORT
        else:
            return RecoveryStrategy.RETRY

    def _create_recovery_steps(
        self,
        strategy: RecoveryStrategy,
        failure_context: Dict[str, Any]
    ) -> List[RecoveryStep]:
        """Create recovery steps based on the determined strategy."""

        steps = []

        if strategy == RecoveryStrategy.ROLLBACK:
            steps.extend([
                RecoveryStep(
                    step_id="rollback_state",
                    description="Rollback agent state to last known good state",
                    action_type="ROLLBACK_AGENT_STATE",
                    parameters={"rollback_point": failure_context.get("last_good_state")},
                    requires_approval=True
                ),
                RecoveryStep(
                    step_id="verify_rollback",
                    description="Verify rollback was successful",
                    action_type="VERIFY_STATE",
                    parameters={"expected_state": failure_context.get("expected_state")}
                ),
                RecoveryStep(
                    step_id="resume_operation",
                    description="Resume operation from rolled back state",
                    action_type="RESUME_OPERATION",
                    requires_approval=True
                )
            ])

        elif strategy == RecoveryStrategy.RETRY:
            retry_count = failure_context.get("retry_count", 0) + 1
            steps.extend([
                RecoveryStep(
                    step_id="prepare_retry",
                    description=f"Prepare for retry attempt #{retry_count}",
                    action_type="PREPARE_RETRY",
                    parameters={"retry_count": retry_count}
                ),
                RecoveryStep(
                    step_id="execute_retry",
                    description="Execute operation with retry logic",
                    action_type="EXECUTE_WITH_RETRY",
                    parameters={
                        "max_retries": 3,
                        "backoff_factor": 2.0,
                        "original_context": failure_context
                    }
                ),
                RecoveryStep(
                    step_id="validate_retry",
                    description="Validate retry was successful",
                    action_type="VALIDATE_SUCCESS"
                )
            ])

        elif strategy == RecoveryStrategy.CONTINUE:
            steps.extend([
                RecoveryStep(
                    step_id="assess_damage",
                    description="Assess the extent of the failure",
                    action_type="ASSESS_FAILURE_IMPACT",
                    parameters={"failure_context": failure_context}
                ),
                RecoveryStep(
                    step_id="apply_workaround",
                    description="Apply workaround for the identified issue",
                    action_type="APPLY_WORKAROUND",
                    parameters={"workaround_type": failure_context.get("suggested_workaround")},
                    requires_approval=True
                ),
                RecoveryStep(
                    step_id="continue_operation",
                    description="Continue operation with applied workaround",
                    action_type="CONTINUE_WITH_WORKAROUND"
                )
            ])

        elif strategy == RecoveryStrategy.ABORT:
            steps.extend([
                RecoveryStep(
                    step_id="cleanup_resources",
                    description="Clean up any allocated resources",
                    action_type="CLEANUP_RESOURCES",
                    parameters={"resources": failure_context.get("allocated_resources", [])}
                ),
                RecoveryStep(
                    step_id="notify_stakeholders",
                    description="Notify relevant stakeholders of abort",
                    action_type="NOTIFY_ABORT",
                    parameters={"reason": failure_context.get("abort_reason", "Operation aborted due to critical failure")}
                ),
                RecoveryStep(
                    step_id="log_abort",
                    description="Log abort details for analysis",
                    action_type="LOG_ABORT_DETAILS"
                )
            ])

        return steps

    async def execute_recovery_step(
        self,
        session_id: UUID,
        step_index: int,
        approved: bool = True,
        approval_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a specific recovery step."""

        logger.info("Executing recovery step",
                   session_id=str(session_id),
                   step_index=step_index,
                   approved=approved)

        if str(session_id) not in self.active_sessions:
            # Load from database
            await self._load_recovery_session(session_id)

        session_data = self.active_sessions.get(str(session_id))
        if not session_data:
            raise ValueError(f"Recovery session {session_id} not found")

        session = session_data["session"]
        steps = session_data["steps"]

        if step_index >= len(steps):
            raise ValueError(f"Step index {step_index} out of range")

        step = steps[step_index]

        # Check if step requires approval
        if step.requires_approval and not approved:
            step.status = "REJECTED"
            step.error = f"Step rejected: {approval_reason}"
            await self._update_session_progress(session, steps)
            return {
                "status": "REJECTED",
                "step": step.to_dict(),
                "reason": approval_reason
            }

        # Execute the step
        step.status = "IN_PROGRESS"
        step.started_at = datetime.utcnow()

        try:
            result = await self._execute_step_action(step, session)

            step.status = "COMPLETED"
            step.completed_at = datetime.utcnow()
            step.result = result

            logger.info("Recovery step completed",
                       session_id=str(session_id),
                       step_id=step.step_id,
                       result=result)

        except Exception as e:
            step.status = "FAILED"
            step.completed_at = datetime.utcnow()
            step.error = str(e)

            logger.error("Recovery step failed",
                        session_id=str(session_id),
                        step_id=step.step_id,
                        error=str(e))

        # Update session progress
        await self._update_session_progress(session, steps)

        # Check if recovery is complete
        if self._is_recovery_complete(steps):
            await self._complete_recovery_session(session, steps)

        return {
            "status": step.status,
            "step": step.to_dict(),
            "session_complete": self._is_recovery_complete(steps)
        }

    async def _execute_step_action(self, step: RecoveryStep, session: RecoverySessionDB) -> Dict[str, Any]:
        """Execute the specific action for a recovery step."""

        action_type = step.action_type
        parameters = step.parameters

        if action_type == "ROLLBACK_AGENT_STATE":
            return await self._rollback_agent_state(session, parameters)

        elif action_type == "VERIFY_STATE":
            return await self._verify_agent_state(session, parameters)

        elif action_type == "RESUME_OPERATION":
            return await self._resume_operation(session, parameters)

        elif action_type == "PREPARE_RETRY":
            return await self._prepare_retry(session, parameters)

        elif action_type == "EXECUTE_WITH_RETRY":
            return await self._execute_with_retry(session, parameters)

        elif action_type == "VALIDATE_SUCCESS":
            return await self._validate_success(session, parameters)

        elif action_type == "ASSESS_FAILURE_IMPACT":
            return await self._assess_failure_impact(session, parameters)

        elif action_type == "APPLY_WORKAROUND":
            return await self._apply_workaround(session, parameters)

        elif action_type == "CONTINUE_WITH_WORKAROUND":
            return await self._continue_with_workaround(session, parameters)

        elif action_type == "CLEANUP_RESOURCES":
            return await self._cleanup_resources(session, parameters)

        elif action_type == "NOTIFY_ABORT":
            return await self._notify_abort(session, parameters)

        elif action_type == "LOG_ABORT_DETAILS":
            return await self._log_abort_details(session, parameters)

        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _rollback_agent_state(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback agent state to a previous good state."""
        # Implementation would depend on specific agent state management
        rollback_point = parameters.get("rollback_point")
        logger.info("Rolling back agent state",
                   session_id=str(session.id),
                   rollback_point=rollback_point)

        # Placeholder implementation
        return {
            "action": "rollback",
            "rollback_point": rollback_point,
            "status": "completed"
        }

    async def _verify_agent_state(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that agent state rollback was successful."""
        expected_state = parameters.get("expected_state")
        logger.info("Verifying agent state",
                   session_id=str(session.id),
                   expected_state=expected_state)

        # Placeholder implementation
        return {
            "action": "verify",
            "expected_state": expected_state,
            "verified": True
        }

    async def _resume_operation(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resume operation from rolled back state."""
        logger.info("Resuming operation",
                   session_id=str(session.id))

        # Placeholder implementation
        return {
            "action": "resume",
            "status": "resumed"
        }

    async def _prepare_retry(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare for retry operation."""
        retry_count = parameters.get("retry_count", 1)
        logger.info("Preparing retry",
                   session_id=str(session.id),
                   retry_count=retry_count)

        return {
            "action": "prepare_retry",
            "retry_count": retry_count,
            "prepared": True
        }

    async def _execute_with_retry(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation with retry logic."""
        max_retries = parameters.get("max_retries", 3)
        backoff_factor = parameters.get("backoff_factor", 2.0)

        logger.info("Executing with retry",
                   session_id=str(session.id),
                   max_retries=max_retries)

        # Placeholder implementation
        return {
            "action": "retry_execute",
            "max_retries": max_retries,
            "backoff_factor": backoff_factor,
            "executed": True
        }

    async def _validate_success(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that retry was successful."""
        logger.info("Validating success",
                   session_id=str(session.id))

        # Placeholder implementation
        return {
            "action": "validate",
            "validated": True
        }

    async def _assess_failure_impact(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of the failure."""
        failure_context = parameters.get("failure_context", {})
        logger.info("Assessing failure impact",
                   session_id=str(session.id))

        # Placeholder implementation
        return {
            "action": "assess",
            "impact_level": "medium",
            "assessed": True
        }

    async def _apply_workaround(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a workaround for the failure."""
        workaround_type = parameters.get("workaround_type")
        logger.info("Applying workaround",
                   session_id=str(session.id),
                   workaround_type=workaround_type)

        # Placeholder implementation
        return {
            "action": "workaround",
            "workaround_type": workaround_type,
            "applied": True
        }

    async def _continue_with_workaround(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Continue operation with applied workaround."""
        logger.info("Continuing with workaround",
                   session_id=str(session.id))

        # Placeholder implementation
        return {
            "action": "continue",
            "continued": True
        }

    async def _cleanup_resources(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up allocated resources."""
        resources = parameters.get("resources", [])
        logger.info("Cleaning up resources",
                   session_id=str(session.id),
                   resources=resources)

        # Placeholder implementation
        return {
            "action": "cleanup",
            "resources_cleaned": resources,
            "cleaned": True
        }

    async def _notify_abort(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Notify stakeholders of abort."""
        reason = parameters.get("reason", "Operation aborted")
        logger.info("Notifying abort",
                   session_id=str(session.id),
                   reason=reason)

        # Broadcast abort notification
        await self._broadcast_recovery_event(session, "ABORTED", {"reason": reason})

        return {
            "action": "notify",
            "reason": reason,
            "notified": True
        }

    async def _log_abort_details(self, session: RecoverySessionDB, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Log abort details for analysis."""
        logger.info("Logging abort details",
                   session_id=str(session.id))

        # Placeholder implementation
        return {
            "action": "log",
            "logged": True
        }

    async def _update_session_progress(self, session: RecoverySessionDB, steps: List[RecoveryStep]):
        """Update session progress in database."""

        db = next(get_session())
        try:
            # Update session record
            db_session = db.query(RecoverySessionDB).filter(
                RecoverySessionDB.id == session.id
            ).first()

            if db_session:
                db_session.recovery_steps = [step.to_dict() for step in steps]
                db_session.current_step = next(
                    (i for i, step in enumerate(steps) if step.status == "IN_PROGRESS"),
                    len(steps)
                )
                db_session.updated_at = datetime.utcnow()
                db.commit()

        finally:
            db.close()

    def _is_recovery_complete(self, steps: List[RecoveryStep]) -> bool:
        """Check if all recovery steps are complete."""
        return all(step.status in ["COMPLETED", "FAILED", "REJECTED"] for step in steps)

    async def _complete_recovery_session(self, session: RecoverySessionDB, steps: List[RecoveryStep]):
        """Complete the recovery session."""

        # Determine final status
        failed_steps = [step for step in steps if step.status == "FAILED"]
        rejected_steps = [step for step in steps if step.status == "REJECTED"]

        if failed_steps or rejected_steps:
            final_status = "FAILED"
            recovery_result = {
                "status": "failed",
                "failed_steps": len(failed_steps),
                "rejected_steps": len(rejected_steps),
                "errors": [step.error for step in failed_steps + rejected_steps if step.error]
            }
        else:
            final_status = "COMPLETED"
            recovery_result = {
                "status": "success",
                "completed_steps": len(steps),
                "results": [step.result for step in steps if step.result]
            }

        db = next(get_session())
        try:
            db_session = db.query(RecoverySessionDB).filter(
                RecoverySessionDB.id == session.id
            ).first()

            if db_session:
                db_session.status = final_status
                db_session.recovery_result = recovery_result
                db_session.completed_at = datetime.utcnow()
                db.commit()

                # Broadcast completion
                await self._broadcast_recovery_event(db_session, final_status, recovery_result)

                logger.info("Recovery session completed",
                           session_id=str(session.id),
                           final_status=final_status)

        finally:
            db.close()

        # Remove from active sessions
        self.active_sessions.pop(str(session.id), None)

    async def _load_recovery_session(self, session_id: UUID):
        """Load recovery session from database."""

        db = next(get_session())
        try:
            session = db.query(RecoverySessionDB).filter(
                RecoverySessionDB.id == session_id
            ).first()

            if session:
                # Reconstruct steps from stored data
                steps = [
                    RecoveryStep(**step_data)
                    for step_data in session.recovery_steps
                ]

                strategy = RecoveryStrategy(session.recovery_strategy)

                self.active_sessions[str(session_id)] = {
                    "session": session,
                    "steps": steps,
                    "strategy": strategy
                }

        finally:
            db.close()

    async def _broadcast_recovery_event(
        self,
        session: RecoverySessionDB,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ):
        """Broadcast recovery event via WebSocket."""

        event = WebSocketEvent(
            event_type=EventType.ERROR,  # Using ERROR for recovery events
            project_id=session.project_id,
            data={
                "recovery_event": True,
                "session_id": str(session.id),
                "event_type": event_type,
                "agent_type": session.agent_type,
                "failure_reason": session.failure_reason,
                "recovery_strategy": session.recovery_strategy,
                "current_step": session.current_step,
                "total_steps": session.total_steps,
                "event_data": event_data or {}
            }
        )

        try:
            await websocket_manager.broadcast_to_project(event, str(session.project_id))
        except Exception as e:
            logger.error("Failed to broadcast recovery event",
                        session_id=str(session.id),
                        error=str(e))

    async def get_recovery_session(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get recovery session details."""

        if str(session_id) not in self.active_sessions:
            await self._load_recovery_session(session_id)

        session_data = self.active_sessions.get(str(session_id))
        if not session_data:
            return None

        session = session_data["session"]
        steps = session_data["steps"]

        return {
            "session_id": str(session.id),
            "project_id": str(session.project_id),
            "task_id": str(session.task_id),
            "agent_type": session.agent_type,
            "failure_reason": session.failure_reason,
            "recovery_strategy": session.recovery_strategy,
            "status": session.status,
            "current_step": session.current_step,
            "total_steps": session.total_steps,
            "steps": [step.to_dict() for step in steps],
            "created_at": session.created_at.isoformat(),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }

    async def get_active_recovery_sessions(self, project_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all active recovery sessions."""

        db = next(get_session())
        try:
            query = db.query(RecoverySessionDB).filter(
                RecoverySessionDB.status.in_(["INITIATED", "IN_PROGRESS"])
            )

            if project_id:
                query = query.filter(RecoverySessionDB.project_id == project_id)

            sessions = query.order_by(RecoverySessionDB.created_at.desc()).all()

            result = []
            for session in sessions:
                result.append({
                    "session_id": str(session.id),
                    "project_id": str(session.project_id),
                    "task_id": str(session.task_id),
                    "agent_type": session.agent_type,
                    "failure_reason": session.failure_reason,
                    "recovery_strategy": session.recovery_strategy,
                    "status": session.status,
                    "current_step": session.current_step,
                    "total_steps": session.total_steps,
                    "created_at": session.created_at.isoformat()
                })

            return result

        finally:
            db.close()
