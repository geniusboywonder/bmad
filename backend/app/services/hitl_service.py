"""
Human-in-the-Loop (HITL) Service

Comprehensive HITL system with configurable trigger conditions, workflow integration,
and safety measures for agent approval and oversight.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.hitl import HitlStatus, HitlAction, HitlHistoryEntry, HitlRequest, HitlResponse
from app.models.task import Task, TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.database.models import (
    HitlRequestDB,
    TaskDB,
    ProjectDB,
    HitlAgentApprovalDB,
    AgentBudgetControlDB,
    EmergencyStopDB,
    ResponseApprovalDB
)
from app.services.context_store import ContextStoreService
from app.services.audit_service import AuditService
from app.services.hitl_trigger_manager import HitlTriggerManager, OversightLevel, HitlTriggerCondition
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
import structlog

logger = structlog.get_logger(__name__)


class HitlService:
    """
    Comprehensive HITL service with configurable trigger conditions and workflow integration.

    Features:
    - Configurable trigger conditions (phase completion, quality thresholds, conflicts)
    - User-configurable oversight levels (High/Medium/Low)
    - Quality threshold monitoring with agent confidence scoring
    - Conflict detection and escalation mechanisms
    - Complete history tracking with audit trail
    - Bulk approval operations for similar items
    - Context-aware approval interfaces with artifact previews
    - HITL request expiration with configurable timeouts
    - Seamless workflow integration for pausing/resuming
    """

    def __init__(self, db: Session):
        self.db = db
        # Lazy import to avoid circular dependency
        self._workflow_engine = None
        self.context_store = ContextStoreService(db)
        self.audit_service = AuditService(db)
        self.trigger_manager = HitlTriggerManager(db)

        # Default configuration
        self.default_oversight_level = OversightLevel.MEDIUM
        self.bulk_approval_batch_size = 10

    @property
    def workflow_engine(self):
        """Lazy-loaded workflow engine to avoid circular imports."""
        if self._workflow_engine is None:
            from app.services.workflow_engine import WorkflowExecutionEngine
            self._workflow_engine = WorkflowExecutionEngine(self.db)
        return self._workflow_engine

    async def check_hitl_triggers(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """
        Check if any HITL trigger conditions are met and create request if needed.

        Args:
            project_id: Project identifier
            task_id: Task identifier
            agent_type: Agent type that triggered the check
            trigger_context: Context data for trigger evaluation

        Returns:
            HitlRequest if trigger condition met, None otherwise
        """
        # Delegate to trigger manager
        return await self.trigger_manager.check_hitl_triggers(
            project_id, task_id, agent_type, trigger_context
        )



    async def _pause_workflow_for_hitl(
        self,
        hitl_request: HitlRequestDB,
        condition: str,
        trigger_context: Dict[str, Any]
    ) -> None:
        """Pause workflow execution for HITL approval."""

        try:
            # Find active workflow executions for this project
            from app.database.models import WorkflowStateDB
            from app.models.workflow_state import WorkflowExecutionState as ExecutionStateEnum

            active_workflows = self.db.query(WorkflowStateDB).filter(
                and_(
                    WorkflowStateDB.project_id == hitl_request.project_id,
                    WorkflowStateDB.status == ExecutionStateEnum.RUNNING.value
                )
            ).all()

            for workflow_state in active_workflows:
                # Check if this workflow contains the task that triggered HITL
                if workflow_state.steps_data:
                    for step_data in workflow_state.steps_data:
                        if step_data.get("task_id") == str(hitl_request.task_id):
                            # Found the workflow, pause it
                            await self.workflow_engine.pause_workflow_execution(
                                workflow_state.execution_id,
                                f"HITL approval required: {condition}"
                            )
                            break

        except Exception as e:
            logger.error("Failed to pause workflow for HITL",
                        hitl_request_id=str(hitl_request.id),
                        error=str(e))

    async def _emit_hitl_request_event(self, hitl_request: HitlRequestDB) -> None:
        """Emit WebSocket event for HITL request creation."""

        event = WebSocketEvent(
            event_type=EventType.HITL_REQUEST_CREATED,
            project_id=hitl_request.project_id,
            data={
                "hitl_request_id": str(hitl_request.id),
                "task_id": str(hitl_request.task_id),
                "question": hitl_request.question,
                "options": hitl_request.options,
                "expires_at": hitl_request.expires_at.isoformat() if hitl_request.expires_at else None
            }
        )

        try:
            await websocket_manager.broadcast_to_project(event, str(hitl_request.project_id))
        except Exception as e:
            logger.error("Failed to emit HITL request event",
                        hitl_request_id=str(hitl_request.id),
                        error=str(e))

    async def process_hitl_response(
        self,
        request_id: UUID,
        action: HitlAction,
        response_content: Optional[str] = None,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process HITL response with comprehensive validation and workflow resumption."""

        # Get HITL request
        hitl_request = self.db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()
        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        if hitl_request.status != HitlStatus.PENDING:
            raise ValueError(f"HITL request {request_id} is not pending")

        # Validate response based on action
        self._validate_hitl_response(action, response_content, comment)

        # Update request status
        if action == HitlAction.APPROVE:
            hitl_request.status = HitlStatus.APPROVED
            hitl_request.user_response = "approved"
        elif action == HitlAction.REJECT:
            hitl_request.status = HitlStatus.REJECTED
            hitl_request.user_response = "rejected"
        elif action == HitlAction.AMEND:
            hitl_request.status = HitlStatus.AMENDED
            hitl_request.user_response = "amended"
            hitl_request.amended_content = {"amended_content": response_content, "comment": comment}

        # Update response data
        hitl_request.response_comment = comment
        hitl_request.responded_at = datetime.now(timezone.utc)

        # Add history entry
        history_entry = HitlHistoryEntry(
            timestamp=datetime.now(timezone.utc),
            action=action.value,
            user_id=user_id,
            content={"response_content": response_content} if response_content else None,
            comment=comment
        )

        if not hitl_request.history:
            hitl_request.history = []
        hitl_request.history.append(history_entry.model_dump(mode="json"))

        self.db.commit()
        self.db.refresh(hitl_request)

        # Update task status based on response
        await self._update_task_status_from_hitl_response(hitl_request, action)

        # Resume workflow if needed
        workflow_resumed = await self._resume_workflow_after_hitl_response(hitl_request, action)

        # Emit WebSocket event
        await self._emit_hitl_response_event(hitl_request, action)

        # Log audit event
        await self.audit_service.log_hitl_event(
            hitl_request_id=hitl_request.id,
            event_type=self.audit_service.EventType.HITL_RESPONSE,
            event_source=self.audit_service.EventSource.USER,
            event_data={
                "action": action.value,
                "status": hitl_request.status.value,
                "user_response": hitl_request.user_response,
                "response_comment": comment,
                "amended_content": hitl_request.amended_content,
                "workflow_resumed": workflow_resumed
            },
            project_id=hitl_request.project_id,
            metadata={
                "user_id": user_id,
                "response_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        logger.info("HITL response processed",
                   request_id=str(request_id),
                   action=action.value,
                   workflow_resumed=workflow_resumed)

        return {
            "request_id": str(request_id),
            "action": action.value,
            "status": hitl_request.status.value,
            "workflow_resumed": workflow_resumed,
            "message": self._get_hitl_response_message(action, workflow_resumed)
        }

    def _validate_hitl_response(
        self,
        action: HitlAction,
        response_content: Optional[str],
        comment: Optional[str]
    ) -> None:
        """Validate HITL response data."""

        if action == HitlAction.AMEND and not response_content:
            raise ValueError("Response content is required for amend action")

        if not comment or comment.strip() == "":
            raise ValueError("Comment is required for all HITL responses")

    async def _update_task_status_from_hitl_response(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction
    ) -> None:
        """Update task status based on HITL response."""

        task = self.db.query(TaskDB).filter(TaskDB.id == hitl_request.task_id).first()
        if not task:
            return

        if action == HitlAction.APPROVE:
            task.status = TaskStatus.COMPLETED
        elif action == HitlAction.REJECT:
            task.status = TaskStatus.FAILED
            task.error_message = f"Task rejected via HITL: {hitl_request.response_comment}"
        elif action == HitlAction.AMEND:
            task.status = TaskStatus.COMPLETED
            # Store amended content in task output
            if hitl_request.amended_content:
                task.output = hitl_request.amended_content

        task.updated_at = datetime.now(timezone.utc)
        self.db.commit()

    async def _resume_workflow_after_hitl_response(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction
    ) -> bool:
        """Resume workflow after HITL response."""

        try:
            # Find paused workflows for this project
            from app.database.models import WorkflowStateDB
            from app.models.workflow_state import WorkflowExecutionState as ExecutionStateEnum

            paused_workflows = self.db.query(WorkflowStateDB).filter(
                and_(
                    WorkflowStateDB.project_id == hitl_request.project_id,
                    WorkflowStateDB.status == ExecutionStateEnum.PAUSED.value
                )
            ).all()

            workflow_resumed = False

            for workflow_state in paused_workflows:
                # Check if this workflow contains the task that was waiting for HITL
                if workflow_state.steps_data:
                    for step_data in workflow_state.steps_data:
                        if step_data.get("task_id") == str(hitl_request.task_id):
                            # Found the workflow, resume it
                            resume_success = await self.workflow_engine.resume_workflow_execution_sync(
                                workflow_state.execution_id
                            )
                            if resume_success:
                                workflow_resumed = True
                                logger.info("Workflow resumed after HITL response",
                                           execution_id=workflow_state.execution_id,
                                           hitl_request_id=str(hitl_request.id),
                                           action=action.value)
                            break

                if workflow_resumed:
                    break

            return workflow_resumed

        except Exception as e:
            logger.error("Failed to resume workflow after HITL response",
                        hitl_request_id=str(hitl_request.id),
                        error=str(e))
            return False

    async def _emit_hitl_response_event(
        self,
        hitl_request: HitlRequestDB,
        action: HitlAction
    ) -> None:
        """Emit WebSocket event for HITL response."""

        event = WebSocketEvent(
            event_type=EventType.HITL_RESPONSE,
            project_id=hitl_request.project_id,
            data={
                "hitl_request_id": str(hitl_request.id),
                "action": action.value,
                "status": hitl_request.status.value,
                "user_response": hitl_request.user_response,
                "amended_content": hitl_request.amended_content
            }
        )

        try:
            await websocket_manager.broadcast_to_project(event, str(hitl_request.project_id))
        except Exception as e:
            logger.error("Failed to emit HITL response event",
                        hitl_request_id=str(hitl_request.id),
                        error=str(e))

    def _get_hitl_response_message(self, action: HitlAction, workflow_resumed: bool) -> str:
        """Get appropriate response message for HITL action."""

        base_message = {
            HitlAction.APPROVE: "Request approved",
            HitlAction.REJECT: "Request rejected",
            HitlAction.AMEND: "Request amended"
        }.get(action, "Response recorded")

        if workflow_resumed:
            return f"{base_message}. Workflow has been resumed."
        else:
            return f"{base_message}. Workflow resumption status unknown."

    async def get_pending_hitl_requests(
        self,
        project_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[HitlRequest]:
        """Get pending HITL requests with optional project filtering."""

        query = self.db.query(HitlRequestDB).filter(HitlRequestDB.status == HitlStatus.PENDING)

        if project_id:
            query = query.filter(HitlRequestDB.project_id == project_id)

        # Filter out expired requests
        query = query.filter(
            or_(
                HitlRequestDB.expires_at.is_(None),
                HitlRequestDB.expires_at > datetime.now(timezone.utc)
            )
        )

        hitl_requests = query.order_by(HitlRequestDB.created_at.desc()).limit(limit).all()

        return [HitlRequest.from_db(req) for req in hitl_requests]

    async def bulk_approve_requests(
        self,
        request_ids: List[UUID],
        comment: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk approve multiple HITL requests."""

        if len(request_ids) > self.bulk_approval_batch_size:
            raise ValueError(f"Cannot approve more than {self.bulk_approval_batch_size} requests at once")

        approved_count = 0
        failed_count = 0
        errors = []

        for request_id in request_ids:
            try:
                await self.process_hitl_response(
                    request_id,
                    HitlAction.APPROVE,
                    comment=comment,
                    user_id=user_id
                )
                approved_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Request {request_id}: {str(e)}")

        return {
            "approved_count": approved_count,
            "failed_count": failed_count,
            "errors": errors,
            "message": f"Bulk approval completed: {approved_count} approved, {failed_count} failed"
        }

    async def get_hitl_request_context(
        self,
        request_id: UUID
    ) -> Dict[str, Any]:
        """Get full context for HITL request including artifacts and task details."""

        hitl_request = self.db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()
        if not hitl_request:
            raise ValueError(f"HITL request {request_id} not found")

        # Get task details
        task = self.db.query(TaskDB).filter(TaskDB.id == hitl_request.task_id).first()

        # Get relevant context artifacts
        context_artifacts = []
        if task and task.context_ids:
            context_artifacts = self.context_store.get_artifacts_by_ids(
                [UUID(cid) for cid in task.context_ids]
            )

        # Get workflow execution context if available
        workflow_context = await self._get_workflow_context_for_hitl(hitl_request)

        return {
            "hitl_request": HitlRequest.from_db(hitl_request),
            "task": task,
            "context_artifacts": context_artifacts,
            "workflow_context": workflow_context,
            "project_info": await self._get_project_info(hitl_request.project_id)
        }

    async def _get_workflow_context_for_hitl(self, hitl_request: HitlRequestDB) -> Optional[Dict[str, Any]]:
        """Get workflow execution context for HITL request."""

        try:
            # Find workflow executions that contain this task
            from app.database.models import WorkflowStateDB

            workflows = self.db.query(WorkflowStateDB).filter(
                WorkflowStateDB.project_id == hitl_request.project_id
            ).all()

            for workflow in workflows:
                if workflow.steps_data:
                    for step_data in workflow.steps_data:
                        if step_data.get("task_id") == str(hitl_request.task_id):
                            return {
                                "execution_id": workflow.execution_id,
                                "workflow_id": workflow.workflow_id,
                                "current_step": workflow.current_step,
                                "total_steps": workflow.total_steps,
                                "status": workflow.status
                            }

        except Exception as e:
            logger.error("Failed to get workflow context for HITL",
                        hitl_request_id=str(hitl_request.id),
                        error=str(e))

        return None

    async def _get_project_info(self, project_id: UUID) -> Dict[str, Any]:
        """Get project information for HITL context."""

        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()

        if project:
            return {
                "project_id": str(project.id),
                "name": project.name,
                "description": project.description,
                "status": project.status
            }

        return {"project_id": str(project_id)}

    async def get_hitl_statistics(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get HITL statistics for monitoring and analytics."""

        query = self.db.query(HitlRequestDB)

        if project_id:
            query = query.filter(HitlRequestDB.project_id == project_id)

        total_requests = query.count()
        pending_requests = query.filter(HitlRequestDB.status == HitlStatus.PENDING).count()
        approved_requests = query.filter(HitlRequestDB.status == HitlStatus.APPROVED).count()
        rejected_requests = query.filter(HitlRequestDB.status == HitlStatus.REJECTED).count()
        amended_requests = query.filter(HitlRequestDB.status == HitlStatus.AMENDED).count()
        expired_requests = query.filter(HitlRequestDB.status == HitlStatus.EXPIRED).count()

        # Calculate average response time
        avg_response_time = self.db.query(
            func.avg(
                func.extract('epoch', HitlRequestDB.responded_at - HitlRequestDB.created_at)
            )
        ).filter(
            and_(
                HitlRequestDB.responded_at.isnot(None),
                HitlRequestDB.status.in_([HitlStatus.APPROVED, HitlStatus.REJECTED, HitlStatus.AMENDED])
            )
        ).scalar()

        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "amended_requests": amended_requests,
            "expired_requests": expired_requests,
            "approval_rate": (approved_requests / total_requests) if total_requests > 0 else 0,
            "average_response_time_hours": (avg_response_time / 3600) if avg_response_time else None
        }

    def configure_trigger_condition(
        self,
        condition: str,
        enabled: bool,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Configure a HITL trigger condition."""
        # Delegate to trigger manager
        self.trigger_manager.configure_trigger_condition(condition, enabled, config)

    def set_oversight_level(self, project_id: UUID, level: str) -> None:
        """Set oversight level for a project."""

        if level not in [OversightLevel.HIGH, OversightLevel.MEDIUM, OversightLevel.LOW]:
            raise ValueError(f"Invalid oversight level: {level}")

        # Store oversight level in project metadata or separate table
        # For now, we'll use a simple approach
        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if project:
            if not project.description:
                project.description = ""
            # Store oversight level in description for now
            project.description = f"[OVERSIGHT:{level}] {project.description}"
            self.db.commit()

        logger.info("Oversight level set for project",
                   project_id=str(project_id),
                   level=level)

    def get_oversight_level(self, project_id: UUID) -> str:
        """Get oversight level for a project."""

        project = self.db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if project and project.description and "[OVERSIGHT:" in project.description:
            # Extract oversight level from description
            start = project.description.find("[OVERSIGHT:") + 11
            end = project.description.find("]", start)
            if end > start:
                level = project.description[start:end]
                if level in [OversightLevel.HIGH, OversightLevel.MEDIUM, OversightLevel.LOW]:
                    return level

        return self.default_oversight_level

    async def cleanup_expired_requests(self) -> int:
        """Clean up expired HITL requests and return count of cleaned requests."""

        expired_count = self.db.query(HitlRequestDB).filter(
            and_(
                HitlRequestDB.status == HitlStatus.PENDING,
                HitlRequestDB.expires_at <= datetime.now(timezone.utc)
            )
        ).update({
            "status": HitlStatus.EXPIRED,
            "response_comment": "Request expired due to timeout",
            "responded_at": datetime.now(timezone.utc)
        })

        if expired_count > 0:
            self.db.commit()

        logger.info("Cleaned up expired HITL requests", count=expired_count)

        return expired_count
