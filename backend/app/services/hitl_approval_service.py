"""
HITL Approval Service - Consolidated HITL request lifecycle management.

Handles HITL request creation, processing, and approval workflows.
Consolidates functionality from hitl_core.py, trigger_processor.py, and response_processor.py.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import structlog

from app.models.hitl import HitlStatus, HitlAction, HitlRequest, HitlResponse
from app.models.task import Task, TaskStatus
from app.database.models import HitlRequestDB, TaskDB
from app.services.context_store import ContextStoreService
from app.services.audit_service import AuditService
from app.services.hitl_trigger_manager import HitlTriggerManager, OversightLevel
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class HitlApprovalService:
    """
    Consolidated HITL approval service handling complete request lifecycle.
    
    Combines core HITL coordination, trigger processing, and response handling
    into a single, focused service following SOLID principles.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        if db:
            self.context_store = ContextStoreService(db)
            self.audit_service = AuditService(db)
            self.trigger_manager = HitlTriggerManager(db)
        else:
            # Mock services for DB-less initialization, typically for testing
            from unittest.mock import MagicMock
            self.context_store = MagicMock(spec=ContextStoreService)
            self.audit_service = MagicMock(spec=AuditService)
            self.trigger_manager = MagicMock(spec=HitlTriggerManager)

        # Configuration
        self.default_oversight_level = OversightLevel.MEDIUM
        self.bulk_approval_batch_size = 10
        self.default_timeout_hours = 24
        self.trigger_configs = {}
        self.oversight_levels = {}  # Project-specific oversight levels

    # ========== CORE HITL MANAGEMENT ==========

    async def check_hitl_triggers(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """Check if any HITL trigger conditions are met."""
        logger.info(
            "Checking HITL triggers",
            project_id=str(project_id),
            task_id=str(task_id),
            agent_type=agent_type
        )

        # Delegate to trigger manager for actual trigger evaluation
        return await self.trigger_manager.check_hitl_triggers(
            project_id, task_id, agent_type, trigger_context
        )

    async def get_pending_hitl_requests(
        self,
        project_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        limit: int = 50
    ) -> List[HitlRequestDB]:
        """Get pending HITL requests with optional filtering."""
        query = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.status == HitlStatus.PENDING
        )

        if project_id:
            query = query.filter(HitlRequestDB.project_id == project_id)
        if agent_type:
            query = query.filter(HitlRequestDB.agent_type == agent_type)

        return query.limit(limit).all()

    async def get_hitl_request_context(
        self,
        request_id: UUID,
        include_artifacts: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive context for HITL request."""
        hitl_request = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.id == request_id
        ).first()

        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        context = {
            "request": hitl_request,
            "project_info": await self._get_project_info(hitl_request.project_id),
            "task_info": await self._get_task_info(hitl_request.task_id) if hitl_request.task_id else None
        }

        if include_artifacts and hitl_request.task_id:
            context["artifacts"] = await self.context_store.get_artifacts_by_task(
                hitl_request.task_id
            )

        return context

    async def get_hitl_statistics(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get HITL request statistics."""
        query = self.db.query(HitlRequestDB)
        if project_id:
            query = query.filter(HitlRequestDB.project_id == project_id)

        total_requests = query.count()
        pending_requests = query.filter(HitlRequestDB.status == HitlStatus.PENDING).count()
        approved_requests = query.filter(HitlRequestDB.status == HitlStatus.APPROVED).count()
        rejected_requests = query.filter(HitlRequestDB.status == HitlStatus.REJECTED).count()

        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "approval_rate": approved_requests / total_requests if total_requests > 0 else 0,
            "avg_response_time_hours": await self._calculate_avg_response_time(query)
        }

    async def cleanup_expired_requests(self) -> int:
        """Clean up expired HITL requests."""
        current_time = datetime.now(timezone.utc)
        expired_requests = self.db.query(HitlRequestDB).filter(
            HitlRequestDB.status == HitlStatus.PENDING,
            HitlRequestDB.expires_at < current_time
        ).all()

        count = 0
        for request in expired_requests:
            request.status = HitlStatus.EXPIRED
            request.responded_at = current_time
            count += 1

        self.db.commit()
        logger.info(f"Cleaned up {count} expired HITL requests")
        return count

    # ========== TRIGGER PROCESSING ==========

    def configure_trigger_condition(
        self,
        condition_type: str,
        project_id: Optional[UUID] = None,
        config: Dict[str, Any] = None
    ) -> None:
        """Configure HITL trigger condition."""
        key = f"{project_id}:{condition_type}" if project_id else condition_type
        self.trigger_configs[key] = config or {}

        logger.info(
            "Configured trigger condition",
            condition_type=condition_type,
            project_id=str(project_id) if project_id else "global",
            config=config
        )

    def set_oversight_level(self, project_id: UUID, level: str) -> None:
        """Set oversight level for project."""
        try:
            oversight_level = OversightLevel(level.upper())
            self.oversight_levels[project_id] = oversight_level
            logger.info(f"Set oversight level for project {project_id} to {level}")
        except ValueError:
            raise ValueError(f"Invalid oversight level: {level}")

    def get_oversight_level(self, project_id: UUID) -> str:
        """Get current oversight level for project."""
        level = self.oversight_levels.get(project_id, self.default_oversight_level)
        return level.value

    def evaluate_quality_threshold(
        self,
        trigger_context: Dict[str, Any],
        project_id: UUID
    ) -> bool:
        """Evaluate if quality threshold trigger should fire."""
        oversight_level = self.oversight_levels.get(project_id, self.default_oversight_level)

        # Get quality metrics from context
        confidence_score = trigger_context.get("confidence_score", 1.0)
        quality_score = trigger_context.get("quality_score", 1.0)

        # Define thresholds based on oversight level
        thresholds = {
            OversightLevel.HIGH: {"confidence": 0.8, "quality": 0.9},
            OversightLevel.MEDIUM: {"confidence": 0.6, "quality": 0.7},
            OversightLevel.LOW: {"confidence": 0.4, "quality": 0.5}
        }

        threshold = thresholds.get(oversight_level, thresholds[OversightLevel.MEDIUM])

        should_trigger = (
            confidence_score < threshold["confidence"] or
            quality_score < threshold["quality"]
        )

        if should_trigger:
            logger.info(
                "Quality threshold trigger fired",
                project_id=str(project_id),
                confidence_score=confidence_score,
                quality_score=quality_score,
                oversight_level=oversight_level.value
            )

        return should_trigger

    # ========== RESPONSE PROCESSING ==========

    async def process_hitl_response(
        self,
        request_id: UUID,
        action: HitlAction,
        user_id: str,
        response_comment: Optional[str] = None,
        amendments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process HITL user response and handle workflow resumption."""
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
        """Bulk approve multiple HITL requests."""
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

    # ========== PRIVATE HELPER METHODS ==========

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
                # Lazy import to avoid circular dependency
                from app.services.workflow_engine import WorkflowExecutionEngine
                workflow_engine = WorkflowExecutionEngine(self.db)
                
                await workflow_engine.resume_workflow_after_hitl(
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

    async def _get_project_info(self, project_id: UUID) -> Dict[str, Any]:
        """Get project information."""
        from app.database.models import ProjectDB
        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            return {}

        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at
        }

    async def _get_task_info(self, task_id: UUID) -> Dict[str, Any]:
        """Get task information."""
        task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            return {}

        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status,
            "agent_type": task.agent_type,
            "created_at": task.created_at
        }

    async def _calculate_avg_response_time(self, query) -> float:
        """Calculate average response time for HITL requests."""
        completed_requests = query.filter(
            HitlRequestDB.status.in_([HitlStatus.APPROVED, HitlStatus.REJECTED]),
            HitlRequestDB.responded_at.isnot(None)
        ).all()

        if not completed_requests:
            return 0.0

        total_hours = 0
        for request in completed_requests:
            if request.responded_at and request.created_at:
                diff = request.responded_at - request.created_at
                total_hours += diff.total_seconds() / 3600

        return total_hours / len(completed_requests)