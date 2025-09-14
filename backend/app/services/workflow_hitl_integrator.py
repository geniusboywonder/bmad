"""
Workflow HITL Integrator

Integrates HITL functionality with workflow execution.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowStepExecutionState
from app.models.hitl import HitlRequest
import structlog

logger = structlog.get_logger(__name__)


class WorkflowHitlIntegrator:
    """
    Integrates HITL functionality with workflow execution.

    This class handles the integration between workflow execution and HITL triggers,
    including pausing workflows for human approval and resuming after responses.
    """

    def __init__(self, db: Session):
        self.db = db
        # Lazy import to avoid circular dependency
        self._hitl_service = None

    @property
    def hitl_service(self):
        """Lazy-loaded HITL service to avoid circular imports."""
        if self._hitl_service is None:
            from app.services.hitl_service import HitlService
            self._hitl_service = HitlService(self.db)
        return self._hitl_service

    async def check_hitl_triggers_after_step(
        self,
        execution: WorkflowExecutionStateModel,
        step: WorkflowStepExecutionState,
        result: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """
        Check for HITL triggers after step completion.

        Args:
            execution: Workflow execution state
            step: Completed workflow step
            result: Step execution result

        Returns:
            HitlRequest if trigger condition met, None otherwise
        """
        try:
            # Get project oversight level
            oversight_level = self.hitl_service.get_oversight_level(execution.project_id)

            # Prepare trigger context
            trigger_context = {
                "oversight_level": oversight_level,
                "current_phase": self._get_current_workflow_phase(execution),
                "step_index": step.step_index,
                "agent_type": step.agent,
                "confidence_score": result.get("confidence_score", 0.8),
                "error_type": result.get("error_type"),
                "conflict_detected": result.get("conflict_detected", False),
                "auto_resolution_attempts": result.get("auto_resolution_attempts", 0),
                "budget_usage_percent": result.get("budget_usage_percent", 0),
                "violation_type": result.get("safety_violation_type"),
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id
            }

            # Check for HITL triggers
            hitl_request = await self.hitl_service.check_hitl_triggers(
                project_id=UUID(execution.project_id),
                task_id=UUID(step.task_id) if step.task_id else UUID(execution.execution_id),
                agent_type=step.agent,
                trigger_context=trigger_context
            )

            if hitl_request:
                logger.info("HITL trigger activated after step completion",
                           execution_id=execution.execution_id,
                           step_index=step.step_index,
                           agent=step.agent,
                           hitl_request_id=str(hitl_request.request_id))

            return hitl_request

        except Exception as e:
            logger.error("Failed to check HITL triggers after step",
                        execution_id=execution.execution_id,
                        step_index=step.step_index,
                        error=str(e))
            return None

    async def pause_workflow_for_hitl(
        self,
        execution: WorkflowExecutionStateModel,
        hitl_request: HitlRequest,
        reason: str
    ) -> bool:
        """
        Pause workflow execution for HITL approval.

        Args:
            execution: Workflow execution to pause
            hitl_request: HITL request that triggered the pause
            reason: Reason for pausing

        Returns:
            True if paused successfully
        """
        try:
            # Update execution status
            execution.pause(reason)

            # Persist the updated state
            from app.services.workflow_persistence_manager import WorkflowPersistenceManager
            persistence_manager = WorkflowPersistenceManager(self.db)
            persistence_manager.persist_execution_state(execution)

            logger.info("Workflow paused for HITL approval",
                       execution_id=execution.execution_id,
                       hitl_request_id=str(hitl_request.request_id),
                       reason=reason)

            return True

        except Exception as e:
            logger.error("Failed to pause workflow for HITL",
                        execution_id=execution.execution_id,
                        hitl_request_id=str(hitl_request.request_id),
                        error=str(e))
            return False

    async def resume_workflow_after_hitl(
        self,
        execution: WorkflowExecutionStateModel,
        hitl_request: HitlRequest
    ) -> bool:
        """
        Resume workflow execution after HITL response.

        Args:
            execution: Workflow execution to resume
            hitl_request: HITL request that was completed

        Returns:
            True if resumed successfully
        """
        try:
            # Update execution status
            execution.resume()

            # Persist the updated state
            from app.services.workflow_persistence_manager import WorkflowPersistenceManager
            persistence_manager = WorkflowPersistenceManager(self.db)
            persistence_manager.persist_execution_state(execution)

            logger.info("Workflow resumed after HITL response",
                       execution_id=execution.execution_id,
                       hitl_request_id=str(hitl_request.request_id))

            return True

        except Exception as e:
            logger.error("Failed to resume workflow after HITL",
                        execution_id=execution.execution_id,
                        hitl_request_id=str(hitl_request.request_id),
                        error=str(e))
            return False

    def _get_current_workflow_phase(self, execution: WorkflowExecutionStateModel) -> str:
        """
        Determine the current workflow phase based on execution state.

        Args:
            execution: Workflow execution state

        Returns:
            Current phase name
        """
        # Map step indices to phases (this could be made configurable)
        phase_mapping = {
            0: "discovery",
            1: "plan",
            2: "design",
            3: "build",
            4: "validate",
            5: "launch"
        }

        current_step = execution.current_step
        if current_step < len(phase_mapping):
            return phase_mapping.get(current_step, "unknown")

        return "unknown"

    async def handle_hitl_response_for_workflow(
        self,
        execution_id: str,
        hitl_request: HitlRequest,
        action: str,
        response_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle HITL response and update workflow accordingly.

        Args:
            execution_id: Workflow execution ID
            hitl_request: HITL request that was responded to
            action: HITL action taken (approve/reject/amend)
            response_content: Optional response content

        Returns:
            Dictionary with handling results
        """
        try:
            # Get execution state
            from app.services.workflow_persistence_manager import WorkflowPersistenceManager
            persistence_manager = WorkflowPersistenceManager(self.db)
            execution = persistence_manager.recover_workflow_execution(execution_id)

            if not execution:
                return {"status": "error", "message": f"Execution {execution_id} not found"}

            # Handle based on action
            if action == "approve":
                # Resume workflow
                success = await self.resume_workflow_after_hitl(execution, hitl_request)
                return {
                    "status": "success" if success else "error",
                    "message": "Workflow resumed after approval" if success else "Failed to resume workflow",
                    "action": "approved"
                }

            elif action == "reject":
                # Mark execution as failed
                execution.mark_failed(f"Rejected via HITL: {hitl_request.response_comment}")
                persistence_manager.persist_execution_state(execution)
                return {
                    "status": "success",
                    "message": "Workflow marked as failed due to rejection",
                    "action": "rejected"
                }

            elif action == "amend":
                # Update execution context with amended content
                if response_content:
                    execution.context_data["hitl_amendment"] = {
                        "content": response_content,
                        "comment": hitl_request.response_comment,
                        "timestamp": hitl_request.responded_at.isoformat() if hitl_request.responded_at else None
                    }

                # Resume workflow with amended content
                success = await self.resume_workflow_after_hitl(execution, hitl_request)
                return {
                    "status": "success" if success else "error",
                    "message": "Workflow resumed with amendments" if success else "Failed to resume workflow",
                    "action": "amended"
                }

            else:
                return {"status": "error", "message": f"Unknown HITL action: {action}"}

        except Exception as e:
            logger.error("Failed to handle HITL response for workflow",
                        execution_id=execution_id,
                        hitl_request_id=str(hitl_request.request_id),
                        error=str(e))
            return {"status": "error", "message": f"Failed to handle response: {str(e)}"}

    async def get_workflow_hitl_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get HITL status for a workflow execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Dictionary with HITL status information
        """
        try:
            # Get pending HITL requests for this execution
            pending_requests = await self.hitl_service.get_pending_hitl_requests()

            # Filter for this execution
            execution_hitl_requests = [
                req for req in pending_requests
                if req.task_id and str(req.task_id) == execution_id
            ]

            return {
                "execution_id": execution_id,
                "pending_hitl_count": len(execution_hitl_requests),
                "has_pending_hitl": len(execution_hitl_requests) > 0,
                "pending_requests": [
                    {
                        "request_id": str(req.request_id),
                        "question": req.question,
                        "status": req.status.value,
                        "created_at": req.created_at.isoformat()
                    }
                    for req in execution_hitl_requests
                ]
            }

        except Exception as e:
            logger.error("Failed to get workflow HITL status",
                        execution_id=execution_id,
                        error=str(e))
            return {
                "execution_id": execution_id,
                "pending_hitl_count": 0,
                "has_pending_hitl": False,
                "pending_requests": [],
                "error": str(e)
            }
