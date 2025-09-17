"""
HITL Response Processor - Handles response processing and workflow resumption.

Responsible for processing HITL user responses and managing workflow state transitions.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.hitl import HitlStatus, HitlAction, HitlResponse
from app.models.task import TaskStatus
from app.database.models import HitlRequestDB, TaskDB
from app.services.audit_service import AuditService
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class ResponseProcessor:
    """
    Processes HITL user responses and manages workflow resumption.

    Follows Single Responsibility Principle by focusing solely on response handling.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
        # Lazy import to avoid circular dependency
        self._workflow_engine = None

    @property
    def workflow_engine(self):
        """Lazy-loaded workflow engine to avoid circular imports."""
        if self._workflow_engine is None:
            from app.services.workflow_engine import WorkflowExecutionEngine
            self._workflow_engine = WorkflowExecutionEngine(self.db)
        return self._workflow_engine

    async def process_hitl_response(
        self,
        request_id: UUID,
        action: HitlAction,
        user_id: str,
        response_comment: Optional[str] = None,
        amendments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process HITL user response and handle workflow resumption.

        Args:
            request_id: HITL request identifier
            action: User action (APPROVE, REJECT, AMEND)
            user_id: User who provided the response
            response_comment: Optional comment from user
            amendments: Optional amendments for AMEND action

        Returns:
            Dictionary containing response processing results
        """
        logger.info(
            "Processing HITL response",
            request_id=str(request_id),
            action=action.value,
            user_id=user_id
        )

        # Get the HITL request
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == request_id
        ).first()

        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        if hitl_request.status != HitlStatus.PENDING:
            raise ValueError(f"HITL request {request_id} is not pending")

        # Validate response
        self._validate_hitl_response(action, amendments)

        # Update request status
        response_time = datetime.now(timezone.utc)
        hitl_request.status = self._get_status_from_action(action)
        hitl_request.user_response = action.value
        hitl_request.response_comment = response_comment
        hitl_request.responded_at = response_time
        hitl_request.user_id = user_id

        # Store amendments if provided
        if amendments:
            hitl_request.amendments = amendments

        self.db.commit()

        # Update task status based on response
        task_updated = await self._update_task_status_from_hitl_response(
            hitl_request, action
        )

        # Resume workflow if approved or amended
        workflow_resumed = False
        if action in [HitlAction.APPROVE, HitlAction.AMEND]:
            try:
                workflow_resumed = await self._resume_workflow_after_hitl_response(
                    hitl_request, action, amendments
                )
            except Exception as e:
                logger.error(
                    "Failed to resume workflow after HITL response",
                    request_id=str(request_id),
                    error=str(e)
                )

        # Log audit event
        await self.audit_service.log_event(
            event_type="hitl_response_processed",
            project_id=hitl_request.project_id,
            task_id=hitl_request.task_id,
            metadata={
                "hitl_request_id": str(request_id),
                "action": action.value,
                "user_id": user_id,
                "response_comment": response_comment,
                "workflow_resumed": workflow_resumed,
                "task_updated": task_updated,
                "has_amendments": amendments is not None
            }
        )

        # Broadcast response event
        await self._emit_hitl_response_event(
            hitl_request, action, workflow_resumed
        )

        return {
            "status": "success",
            "action": action.value,
            "message": self._get_hitl_response_message(action, workflow_resumed),
            "workflow_resumed": workflow_resumed,
            "task_updated": task_updated,
            "request_id": str(request_id)
        }

    async def bulk_approve_requests(
        self,
        request_ids: List[UUID],
        user_id: str,
        response_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple HITL requests.

        Args:
            request_ids: List of HITL request identifiers
            user_id: User performing bulk approval
            response_comment: Optional comment for all requests

        Returns:
            Dictionary containing bulk approval results
        """
        logger.info(
            "Processing bulk HITL approval",
            request_count=len(request_ids),
            user_id=user_id
        )

        results = {
            "total_requests": len(request_ids),
            "successful_approvals": 0,
            "failed_approvals": 0,
            "errors": []
        }

        for request_id in request_ids:
            try:
                await self.process_hitl_response(
                    request_id,
                    HitlAction.APPROVE,
                    user_id,
                    response_comment
                )
                results["successful_approvals"] += 1
            except Exception as e:
                results["failed_approvals"] += 1
                results["errors"].append({
                    "request_id": str(request_id),
                    "error": str(e)
                })
                logger.error(
                    "Failed to process bulk approval",
                    request_id=str(request_id),
                    error=str(e)
                )

        # Log bulk approval audit event
        await self.audit_service.log_event(
            event_type="hitl_bulk_approval",
            metadata={
                "user_id": user_id,
                "total_requests": results["total_requests"],
                "successful_approvals": results["successful_approvals"],
                "failed_approvals": results["failed_approvals"],
                "response_comment": response_comment
            }
        )

        return results

    def _validate_hitl_response(self, action: HitlAction, amendments: Optional[Dict[str, Any]]) -> None:
        """Validate HITL response parameters."""
        if action == HitlAction.AMEND and not amendments:
            raise ValueError("Amendments are required for AMEND action")

    def _get_status_from_action(self, action: HitlAction) -> HitlStatus:
        """Get HITL status from user action."""
        action_to_status = {
            HitlAction.APPROVE: HitlStatus.APPROVED,
            HitlAction.REJECT: HitlStatus.REJECTED,
            HitlAction.AMEND: HitlStatus.APPROVED  # Amendments are approved with changes
        }
        return action_to_status[action]

    async def _update_task_status_from_hitl_response(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction
    ) -> bool:
        """Update related task status based on HITL response."""
        if not hitl_request.task_id:
            return False

        task = self.db.query(TaskDB).filter(TaskDB.id == hitl_request.task_id).first()
        if not task:
            return False

        if action == HitlAction.REJECT:
            task.status = TaskStatus.FAILED
            task.error_message = f"Rejected by user: {hitl_request.response_comment or 'No reason provided'}"
        elif action in [HitlAction.APPROVE, HitlAction.AMEND]:
            # Resume task or mark as completed depending on current status
            if task.status == TaskStatus.WAITING_FOR_HITL:
                task.status = TaskStatus.PENDING  # Resume processing

        self.db.commit()
        return True

    async def _resume_workflow_after_hitl_response(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction,
        amendments: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Resume workflow execution after HITL response."""
        try:
            # Check if this was a workflow pause
            if hitl_request.workflow_context:
                context = hitl_request.workflow_context.copy()

                # Add response information to context
                context.update({
                    "hitl_response": {
                        "action": action.value,
                        "amendments": amendments,
                        "response_comment": hitl_request.response_comment,
                        "user_id": hitl_request.user_id
                    }
                })

                # Resume workflow with updated context
                await self.workflow_engine.resume_workflow_after_hitl(
                    hitl_request.project_id,
                    hitl_request.task_id,
                    context
                )
                return True

        except Exception as e:
            logger.error(
                "Failed to resume workflow",
                hitl_request_id=str(hitl_request.id),
                error=str(e)
            )
            return False

        return False

    async def _emit_hitl_response_event(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction,
        workflow_resumed: bool
    ) -> None:
        """Emit WebSocket event for HITL response."""
        try:
            event = WebSocketEvent(
                type=EventType.HITL_RESPONSE,
                project_id=hitl_request.project_id,
                data={
                    "hitl_request_id": str(hitl_request.id),
                    "action": action.value,
                    "status": hitl_request.status.value,
                    "workflow_resumed": workflow_resumed,
                    "user_id": hitl_request.user_id,
                    "response_comment": hitl_request.response_comment,
                    "responded_at": hitl_request.responded_at.isoformat() if hitl_request.responded_at else None
                }
            )

            await websocket_manager.broadcast_to_project(
                hitl_request.project_id,
                event.model_dump()
            )

        except Exception as e:
            logger.error(
                "Failed to emit HITL response event",
                hitl_request_id=str(hitl_request.id),
                error=str(e)
            )

    def _get_hitl_response_message(self, action: HitlAction, workflow_resumed: bool) -> str:
        """Get human-readable message for HITL response."""
        base_messages = {
            HitlAction.APPROVE: "Request approved successfully",
            HitlAction.REJECT: "Request rejected",
            HitlAction.AMEND: "Request approved with amendments"
        }

        message = base_messages[action]

        if workflow_resumed:
            message += " and workflow resumed"
        elif action != HitlAction.REJECT:
            message += " but workflow could not be resumed"

        return message

    async def get_response_history(
        self,
        request_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get response history for a HITL request.

        Args:
            request_id: HITL request identifier

        Returns:
            List of response history entries
        """
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == request_id
        ).first()

        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        history = []

        # Add the main response if it exists
        if hitl_request.user_response:
            history.append({
                "timestamp": hitl_request.responded_at,
                "user_id": hitl_request.user_id,
                "action": hitl_request.user_response,
                "comment": hitl_request.response_comment,
                "amendments": hitl_request.amendments
            })

        return history

    async def reprocess_failed_response(
        self,
        request_id: UUID,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Reprocess a failed HITL response (retry workflow resumption).

        Args:
            request_id: HITL request identifier
            user_id: User requesting reprocessing

        Returns:
            Dictionary containing reprocessing results
        """
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == request_id
        ).first()

        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        if hitl_request.status not in [HitlStatus.APPROVED]:
            raise ValueError(f"Only approved requests can be reprocessed")

        # Attempt to resume workflow again
        action = HitlAction(hitl_request.user_response)
        workflow_resumed = await self._resume_workflow_after_hitl_response(
            hitl_request, action, hitl_request.amendments
        )

        # Log reprocessing attempt
        await self.audit_service.log_event(
            event_type="hitl_response_reprocessed",
            project_id=hitl_request.project_id,
            task_id=hitl_request.task_id,
            metadata={
                "hitl_request_id": str(request_id),
                "reprocessed_by": user_id,
                "workflow_resumed": workflow_resumed,
                "original_action": action.value
            }
        )

        return {
            "status": "success" if workflow_resumed else "failed",
            "workflow_resumed": workflow_resumed,
            "message": "Workflow resumed successfully" if workflow_resumed else "Failed to resume workflow",
            "request_id": str(request_id)
        }