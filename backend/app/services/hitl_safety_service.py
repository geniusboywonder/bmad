"""HITL Safety Service for mandatory agent approval controls."""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database.models import (
    HitlAgentApprovalDB,
    AgentBudgetControlDB,
    EmergencyStopDB,
    ProjectDB,
    TaskDB,
    ResponseApprovalDB
)
from app.database.connection import get_session
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
from app.services.llm_monitoring import LLMUsageTracker
from app.services.response_safety_analyzer import ResponseSafetyAnalyzer
from app.settings import settings
from app.models.agent import AgentStatus

logger = structlog.get_logger(__name__)


class ApprovalTimeoutError(Exception):
    """Exception raised when approval request times out."""
    pass


class AgentExecutionDenied(Exception):
    """Exception raised when agent execution is denied."""
    pass


class BudgetLimitExceeded(Exception):
    """Exception raised when budget limit is exceeded."""
    pass


class EmergencyStopActivated(Exception):
    """Exception raised when emergency stop is active."""
    pass


class ApprovalResult:
    """Result of an approval request."""

    def __init__(self, approved: bool, response: Optional[str] = None, comment: Optional[str] = None):
        self.approved = approved
        self.response = response
        self.comment = comment


class BudgetCheckResult:
    """Result of a budget check."""

    def __init__(self, approved: bool, reason: Optional[str] = None):
        self.approved = approved
        self.reason = reason


class HITLSafetyService:
    """Service for managing HITL safety controls and mandatory approvals."""

    def __init__(self, db_session: Optional[Session] = None):
        self.active_monitors = {}
        self.emergency_stops = set()
        self.usage_tracker = LLMUsageTracker(enable_tracking=settings.llm_enable_usage_tracking)
        self.response_analyzer = ResponseSafetyAnalyzer()
        self._db_session = db_session

    def _get_session(self):
        """Get database session, either injected or default."""
        if self._db_session is not None:
            return self._db_session
        return next(get_session())

    async def create_approval_request(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        request_type: str,
        request_data: Dict[str, Any],
        estimated_tokens: Optional[int] = None,
        timeout_minutes: int = 30
    ) -> UUID:
        """Create a new HITL approval request."""

        # Calculate estimated cost if tokens provided
        estimated_cost = Decimal('0.00')
        if estimated_tokens:
            estimated_cost = await self.calculate_cost(estimated_tokens)

        # Create approval request
        approval = HitlAgentApprovalDB(
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            request_type=request_type,
            request_data=request_data,
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)
        )

        db = self._get_session()
        try:
            db.add(approval)
            db.commit()
            db.refresh(approval)

            # Send real-time notification
            await self._send_hitl_notification(approval)

            logger.info("HITL approval request created",
                       approval_id=str(approval.id),
                       agent_type=agent_type,
                       request_type=request_type,
                       project_id=str(project_id))

            return approval.id

        finally:
            db.close()

    async def wait_for_approval(
        self,
        approval_id: UUID,
        timeout_minutes: int = 30
    ) -> ApprovalResult:
        """Wait for human approval with timeout."""

        start_time = datetime.now(timezone.utc)
        timeout_time = start_time + timedelta(minutes=timeout_minutes)

        db = self._get_session()
        try:
            while datetime.now(timezone.utc) < timeout_time:
                # Check for emergency stops
                if await self._is_emergency_stopped():
                    raise EmergencyStopActivated("Emergency stop is active")

                # Check approval status
                approval = db.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.id == approval_id
                ).first()

                if not approval:
                    raise ValueError(f"Approval request {approval_id} not found")

                if approval.status in ['APPROVED', 'REJECTED']:
                    return ApprovalResult(
                        approved=(approval.status == 'APPROVED'),
                        response=approval.user_response,
                        comment=approval.user_comment
                    )

                # Wait before checking again
                await asyncio.sleep(5)

            # Timeout - automatically reject
            approval.status = 'EXPIRED'
            db.commit()

            raise ApprovalTimeoutError(f"Approval request {approval_id} timed out")

        finally:
            db.close()

    async def check_budget_limits(
        self,
        project_id: UUID,
        agent_type: str,
        estimated_tokens: int
    ) -> BudgetCheckResult:
        """Check if operation is within budget limits."""

        db = self._get_session()
        try:
            # Get or create budget control
            budget = db.query(AgentBudgetControlDB).filter(
                and_(
                    AgentBudgetControlDB.project_id == project_id,
                    AgentBudgetControlDB.agent_type == agent_type
                )
            ).first()

            if not budget:
                budget = AgentBudgetControlDB(
                    project_id=project_id,
                    agent_type=agent_type
                )
                db.add(budget)
                db.commit()
                db.refresh(budget)

            # Reset counters if needed
            await self._reset_budget_counters_if_needed(budget, db)

            # Check daily limit
            if budget.tokens_used_today + estimated_tokens > budget.daily_token_limit:
                return BudgetCheckResult(
                    approved=False,
                    reason=f"Would exceed daily limit ({budget.daily_token_limit})"
                )

            # Check session limit
            if budget.tokens_used_session + estimated_tokens > budget.session_token_limit:
                return BudgetCheckResult(
                    approved=False,
                    reason=f"Would exceed session limit ({budget.session_token_limit})"
                )

            return BudgetCheckResult(approved=True)

        finally:
            db.close()

    async def update_budget_usage(
        self,
        project_id: UUID,
        agent_type: str,
        tokens_used: int
    ):
        """Update budget usage counters."""

        db = self._get_session()
        try:
            budget = db.query(AgentBudgetControlDB).filter(
                and_(
                    AgentBudgetControlDB.project_id == project_id,
                    AgentBudgetControlDB.agent_type == agent_type
                )
            ).first()

            if budget:
                budget.tokens_used_today += tokens_used
                budget.tokens_used_session += tokens_used
                budget.updated_at = datetime.now(timezone.utc)
                db.commit()

                logger.info("Budget usage updated",
                           project_id=str(project_id),
                           agent_type=agent_type,
                           tokens_used=tokens_used,
                           total_today=budget.tokens_used_today)

        finally:
            db.close()

    async def trigger_emergency_stop(
        self,
        project_id: Optional[UUID],
        agent_type: Optional[str],
        reason: str,
        triggered_by: str = "USER",
        budget_based: bool = False,
        task_cancellation: bool = False,
        cancel_task_ids: Optional[List[UUID]] = None
    ):
        """Trigger an emergency stop for agents with enhanced features."""

        db = self._get_session()
        try:
            stop = EmergencyStopDB(
                project_id=project_id,
                agent_type=agent_type,
                stop_reason=reason,
                triggered_by=triggered_by,
                active=True
            )

            db.add(stop)
            db.commit()
            db.refresh(stop)

            # Add to active stops
            self.emergency_stops.add(str(stop.id))

            # Handle budget-based emergency stop
            if budget_based:
                await self._handle_budget_based_stop(stop, db)

            # Handle task cancellation if requested
            if task_cancellation and cancel_task_ids:
                await self._cancel_tasks(stop, cancel_task_ids, db)

            # Broadcast emergency stop with enhanced data
            await self._broadcast_emergency_stop(stop, budget_based, task_cancellation)

            logger.warning("Emergency stop triggered",
                          stop_id=str(stop.id),
                          project_id=str(project_id) if project_id else None,
                          agent_type=agent_type,
                          reason=reason,
                          triggered_by=triggered_by,
                          budget_based=budget_based,
                          task_cancellation=task_cancellation)

        finally:
            db.close()

    async def deactivate_emergency_stop(self, stop_id: UUID):
        """Deactivate an emergency stop."""

        db = self._get_session()
        try:
            stop = db.query(EmergencyStopDB).filter(
                EmergencyStopDB.id == stop_id
            ).first()

            if stop and stop.active:
                stop.active = False
                stop.deactivated_at = datetime.now(timezone.utc)
                db.commit()

                # Remove from active stops
                self.emergency_stops.discard(str(stop_id))

                logger.info("Emergency stop deactivated", stop_id=str(stop_id))

        finally:
            db.close()

    async def get_active_emergency_stops(self) -> List[Dict[str, Any]]:
        """Get all active emergency stops."""

        db = self._get_session()
        try:
            stops = db.query(EmergencyStopDB).filter(
                EmergencyStopDB.active == True
            ).all()

            return [
                {
                    "id": str(stop.id),
                    "project_id": str(stop.project_id) if stop.project_id else None,
                    "agent_type": stop.agent_type,
                    "stop_reason": stop.stop_reason,
                    "triggered_by": stop.triggered_by,
                    "created_at": stop.created_at.isoformat()
                }
                for stop in stops
            ]

        finally:
            db.close()

    async def calculate_cost(self, tokens: int) -> Decimal:
        """Calculate estimated cost for tokens."""

        # Use LLM monitoring service for cost calculation
        cost_result = await self.usage_tracker.calculate_costs(
            input_tokens=tokens,
            output_tokens=0,
            provider="openai",
            model="gpt-4o-mini"
        )

        # Handle both single value and tuple return
        if isinstance(cost_result, tuple):
            cost = cost_result[0]
        else:
            cost = cost_result

        return Decimal(str(cost))

    async def _is_emergency_stopped(self) -> bool:
        """Check if emergency stop is active."""

        if self.emergency_stops:
            return True

        # Check database for any active stops
        db = self._get_session()
        try:
            active_stops = db.query(EmergencyStopDB).filter(
                EmergencyStopDB.active == True
            ).count()

            return active_stops > 0

        finally:
            db.close()

    async def _reset_budget_counters_if_needed(self, budget: AgentBudgetControlDB, db: Session):
        """Reset budget counters if needed (daily reset)."""

        now = datetime.now(timezone.utc)
        budget_reset_date = budget.budget_reset_at.date()
        today = now.date()

        if budget_reset_date < today:
            # Reset daily counter
            budget.tokens_used_today = 0
            budget.budget_reset_at = now
            db.commit()

    async def _send_hitl_notification(self, approval: HitlAgentApprovalDB):
        """Send real-time notification for HITL approval request."""

        event = WebSocketEvent(
            event_type=EventType.HITL_REQUEST_CREATED,
            project_id=approval.project_id,
            data={
                "approval_id": str(approval.id),
                "agent_type": approval.agent_type,
                "request_type": approval.request_type,
                "estimated_tokens": approval.estimated_tokens,
                "estimated_cost": float(approval.estimated_cost) if approval.estimated_cost else 0.0,
                "expires_at": approval.expires_at.isoformat(),
                "request_data": approval.request_data
            }
        )

        try:
            await websocket_manager.broadcast_to_project(event, str(approval.project_id))
        except Exception as e:
            logger.error("Failed to send HITL notification",
                        approval_id=str(approval.id),
                        error=str(e))

    async def _broadcast_emergency_stop(self, stop: EmergencyStopDB):
        """Broadcast emergency stop event."""

        event = WebSocketEvent(
            event_type=EventType.ERROR,
            data={
                "emergency_stop": True,
                "stop_id": str(stop.id),
                "reason": stop.stop_reason,
                "agent_type": stop.agent_type,
                "project_id": str(stop.project_id) if stop.project_id else None,
                "triggered_by": stop.triggered_by
            }
        )

        try:
            if stop.project_id:
                await websocket_manager.broadcast_to_project(event, str(stop.project_id))
            else:
                await websocket_manager.broadcast_global(event)
        except Exception as e:
            logger.error("Failed to broadcast emergency stop",
                        stop_id=str(stop.id),
                        error=str(e))

    async def _handle_budget_based_stop(self, stop: EmergencyStopDB, db: Session):
        """Handle budget-based emergency stop by adjusting budget limits."""

        if not stop.project_id or not stop.agent_type:
            return

        # Find the budget control for this project/agent
        budget = db.query(AgentBudgetControlDB).filter(
            and_(
                AgentBudgetControlDB.project_id == stop.project_id,
                AgentBudgetControlDB.agent_type == stop.agent_type
            )
        ).first()

        if budget:
            # Temporarily reduce budget limits to prevent further spending
            original_daily_limit = budget.daily_token_limit
            original_session_limit = budget.session_token_limit

            # Reduce limits by 50% or set minimum limits
            budget.daily_token_limit = max(100, budget.daily_token_limit // 2)
            budget.session_token_limit = max(50, budget.session_token_limit // 2)
            budget.emergency_stop_enabled = True
            budget.updated_at = datetime.now(timezone.utc)
            db.commit()

            logger.warning("Budget limits reduced due to emergency stop",
                          stop_id=str(stop.id),
                          project_id=str(stop.project_id),
                          agent_type=stop.agent_type,
                          original_daily_limit=original_daily_limit,
                          new_daily_limit=budget.daily_token_limit,
                          original_session_limit=original_session_limit,
                          new_session_limit=budget.session_token_limit)

    async def _cancel_tasks(self, stop: EmergencyStopDB, task_ids: List[UUID], db: Session):
        """Cancel specified tasks due to emergency stop."""

        cancelled_count = 0
        for task_id in task_ids:
            task = db.query(TaskDB).filter(
                and_(
                    TaskDB.id == task_id,
                    TaskDB.status.in_(["PENDING", "IN_PROGRESS"])  # Only cancel active tasks
                )
            ).first()

            if task:
                # Update task status to cancelled
                from app.models.task import TaskStatus
                task.status = TaskStatus.CANCELLED
                task.error_message = f"Task cancelled due to emergency stop: {stop.stop_reason}"
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                cancelled_count += 1

                logger.info("Task cancelled due to emergency stop",
                           stop_id=str(stop.id),
                           task_id=str(task_id),
                           project_id=str(task.project_id),
                           agent_type=task.agent_type)

        if cancelled_count > 0:
            db.commit()
            logger.warning("Tasks cancelled due to emergency stop",
                          stop_id=str(stop.id),
                          cancelled_count=cancelled_count,
                          total_requested=len(task_ids))

    async def _broadcast_emergency_stop(self, stop: EmergencyStopDB, budget_based: bool = False, task_cancellation: bool = False):
        """Broadcast emergency stop event with enhanced data."""

        event = WebSocketEvent(
            event_type=EventType.ERROR,
            data={
                "emergency_stop": True,
                "stop_id": str(stop.id),
                "reason": stop.stop_reason,
                "agent_type": stop.agent_type,
                "project_id": str(stop.project_id) if stop.project_id else None,
                "triggered_by": stop.triggered_by,
                "budget_based": budget_based,
                "task_cancellation": task_cancellation,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        try:
            if stop.project_id:
                await websocket_manager.broadcast_to_project(event, str(stop.project_id))
            else:
                await websocket_manager.broadcast_global(event)
        except Exception as e:
            logger.error("Failed to broadcast emergency stop",
                        stop_id=str(stop.id),
                        error=str(e))

    async def check_budget_emergency_stop(self, project_id: UUID, agent_type: str) -> bool:
        """Check if budget-based emergency stop should be triggered."""

        db = self._get_session()
        try:
            # Get budget control
            budget = db.query(AgentBudgetControlDB).filter(
                and_(
                    AgentBudgetControlDB.project_id == project_id,
                    AgentBudgetControlDB.agent_type == agent_type
                )
            ).first()

            if not budget:
                return False

            # Check if emergency stop is already active
            active_stop = db.query(EmergencyStopDB).filter(
                and_(
                    EmergencyStopDB.project_id == project_id,
                    EmergencyStopDB.agent_type == agent_type,
                    EmergencyStopDB.active == True,
                    EmergencyStopDB.triggered_by == "BUDGET"
                )
            ).first()

            if active_stop:
                return True  # Emergency stop already active

            # Check budget thresholds for emergency stop
            daily_usage_percent = (budget.tokens_used_today / budget.daily_token_limit) if budget.daily_token_limit > 0 else 0
            session_usage_percent = (budget.tokens_used_session / budget.session_token_limit) if budget.session_token_limit > 0 else 0

            # Trigger emergency stop if usage exceeds 90%
            emergency_threshold = 0.9
            should_trigger = (
                daily_usage_percent >= emergency_threshold or
                session_usage_percent >= emergency_threshold
            )

            if should_trigger:
                await self.trigger_emergency_stop(
                    project_id=project_id,
                    agent_type=agent_type,
                    reason=f"Budget emergency stop triggered - Daily: {daily_usage_percent:.1%}, Session: {session_usage_percent:.1%}",
                    triggered_by="BUDGET",
                    budget_based=True
                )
                return True

            return False

        finally:
            db.close()

    async def get_emergency_stop_stats(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get statistics about emergency stops."""

        db = self._get_session()
        try:
            query = db.query(EmergencyStopDB)

            if project_id:
                query = query.filter(EmergencyStopDB.project_id == project_id)

            total_stops = query.count()
            active_stops = query.filter(EmergencyStopDB.active == True).count()
            user_triggered = query.filter(EmergencyStopDB.triggered_by == "USER").count()
            budget_triggered = query.filter(EmergencyStopDB.triggered_by == "BUDGET").count()
            error_triggered = query.filter(EmergencyStopDB.triggered_by == "ERROR").count()

            # Get recent stops (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_stops = query.filter(EmergencyStopDB.created_at >= yesterday).count()

            return {
                "total_stops": total_stops,
                "active_stops": active_stops,
                "user_triggered": user_triggered,
                "budget_triggered": budget_triggered,
                "error_triggered": error_triggered,
                "recent_stops": recent_stops,
                "stop_rate_per_day": recent_stops  # Approximation
            }

        finally:
            db.close()

    async def cancel_task_due_to_emergency(self, task_id: UUID, stop_id: UUID, reason: str) -> bool:
        """Cancel a specific task due to emergency stop."""

        db = self._get_session()
        try:
            task = db.query(TaskDB).filter(
                and_(
                    TaskDB.id == task_id,
                    TaskDB.status.in_(["PENDING", "IN_PROGRESS"])
                )
            ).first()

            if not task:
                logger.warning("Task not found or not cancellable",
                              task_id=str(task_id),
                              stop_id=str(stop_id))
                return False

            # Update task status
            from app.models.task import TaskStatus
            task.status = TaskStatus.CANCELLED
            task.error_message = f"Task cancelled due to emergency stop: {reason}"
            task.completed_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

            # Cancel any pending approvals for this task
            pending_approvals = db.query(HitlAgentApprovalDB).filter(
                and_(
                    HitlAgentApprovalDB.task_id == task_id,
                    HitlAgentApprovalDB.status == "PENDING"
                )
            ).all()

            for approval in pending_approvals:
                approval.status = "REJECTED"
                approval.user_response = f"Approval cancelled due to emergency stop: {reason}"
                approval.user_comment = "Automatically rejected due to emergency stop"
                approval.responded_at = datetime.now(timezone.utc)

            if pending_approvals:
                db.commit()

            logger.info("Task cancelled due to emergency stop",
                       task_id=str(task_id),
                       stop_id=str(stop_id),
                       project_id=str(task.project_id),
                       agent_type=task.agent_type,
                       cancelled_approvals=len(pending_approvals))

            return True

        except Exception as e:
            logger.error("Failed to cancel task due to emergency",
                        task_id=str(task_id),
                        stop_id=str(stop_id),
                        error=str(e))
            db.rollback()
            return False
        finally:
            db.close()

    async def analyze_agent_response(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        approval_request_id: UUID,
        response_content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze agent response for safety and quality using ResponseSafetyAnalyzer."""

        logger.info("Analyzing agent response for safety",
                   project_id=str(project_id),
                   task_id=str(task_id),
                   agent_type=agent_type,
                   approval_request_id=str(approval_request_id))

        try:
            # Analyze the response
            analysis_result = await self.response_analyzer.analyze_response(
                response_content=response_content,
                agent_type=agent_type,
                context=context
            )

            # Create response approval record
            response_approval_id = await self.response_analyzer.create_response_approval_record(
                project_id=project_id,
                task_id=task_id,
                agent_type=agent_type,
                approval_request_id=approval_request_id,
                response_content=response_content,
                analysis_result=analysis_result
            )

            result = {
                "response_approval_id": str(response_approval_id),
                "analysis_result": analysis_result.to_dict(),
                "auto_approved": analysis_result.auto_approvable,
                "requires_manual_review": not analysis_result.auto_approvable
            }

            logger.info("Response analysis completed",
                       response_approval_id=str(response_approval_id),
                       auto_approved=analysis_result.auto_approvable,
                       safety_score=analysis_result.content_safety_score,
                       code_score=analysis_result.code_validation_score)

            return result

        except Exception as e:
            logger.error("Failed to analyze agent response",
                        project_id=str(project_id),
                        task_id=str(task_id),
                        agent_type=agent_type,
                        error=str(e))
            raise

    async def get_response_analysis(self, response_approval_id: UUID) -> Optional[Dict[str, Any]]:
        """Get analysis results for a response approval."""

        return await self.response_analyzer.get_response_approval_analysis(response_approval_id)

    async def approve_response_manually(
        self,
        response_approval_id: UUID,
        approved: bool,
        approved_by: str,
        approval_reason: Optional[str] = None
    ) -> bool:
        """Manually approve or reject a response after analysis."""

        db = self._get_session()
        try:
            # Get the response approval record
            response_approval = db.query(ResponseApprovalDB).filter(
                ResponseApprovalDB.id == response_approval_id
            ).first()

            if not response_approval:
                logger.error("Response approval record not found",
                           response_approval_id=str(response_approval_id))
                return False

            # Update the record
            response_approval.status = "APPROVED" if approved else "REJECTED"
            response_approval.approved_by = approved_by
            response_approval.approval_reason = approval_reason
            response_approval.approved_at = datetime.now(timezone.utc)
            response_approval.updated_at = datetime.now(timezone.utc)

            # Update the main approval request if this is the final decision
            main_approval = db.query(HitlAgentApprovalDB).filter(
                HitlAgentApprovalDB.id == response_approval.approval_request_id
            ).first()

            if main_approval:
                main_approval.status = response_approval.status
                main_approval.user_response = approval_reason
                main_approval.user_comment = f"Response {'approved' if approved else 'rejected'} by {approved_by}"
                main_approval.responded_at = datetime.now(timezone.utc)

            db.commit()

            logger.info("Response manually approved/rejected",
                       response_approval_id=str(response_approval_id),
                       approved=approved,
                       approved_by=approved_by,
                       reason=approval_reason)

            return True

        except Exception as e:
            logger.error("Failed to manually approve response",
                        response_approval_id=str(response_approval_id),
                        error=str(e))
            db.rollback()
            return False
        finally:
            db.close()

    async def get_pending_response_reviews(self, project_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get all pending response reviews that require manual approval."""

        db = self._get_session()
        try:
            query = db.query(ResponseApprovalDB).filter(
                ResponseApprovalDB.status == "PENDING"
            )

            if project_id:
                query = query.filter(ResponseApprovalDB.project_id == project_id)

            pending_reviews = query.order_by(ResponseApprovalDB.created_at.desc()).all()

            return [
                {
                    "response_approval_id": str(review.id),
                    "project_id": str(review.project_id),
                    "task_id": str(review.task_id),
                    "agent_type": review.agent_type,
                    "content_safety_score": float(review.content_safety_score) if review.content_safety_score else None,
                    "code_validation_score": float(review.code_validation_score) if review.code_validation_score else None,
                    "quality_metrics": review.quality_metrics,
                    "safety_flags": review.quality_metrics.get('safety_flags', []),
                    "recommendations": review.quality_metrics.get('recommendations', []),
                    "created_at": review.created_at.isoformat()
                }
                for review in pending_reviews
            ]

        finally:
            db.close()

    async def get_response_approval_stats(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get statistics about response approvals."""

        db = self._get_session()
        try:
            query = db.query(ResponseApprovalDB)

            if project_id:
                query = query.filter(ResponseApprovalDB.project_id == project_id)

            total_reviews = query.count()
            auto_approved = query.filter(ResponseApprovalDB.auto_approved == True).count()
            manual_approved = query.filter(
                and_(
                    ResponseApprovalDB.status == "APPROVED",
                    ResponseApprovalDB.auto_approved == False
                )
            ).count()
            rejected = query.filter(ResponseApprovalDB.status == "REJECTED").count()
            pending = query.filter(ResponseApprovalDB.status == "PENDING").count()

            return {
                "total_reviews": total_reviews,
                "auto_approved": auto_approved,
                "manual_approved": manual_approved,
                "rejected": rejected,
                "pending": pending,
                "auto_approval_rate": (auto_approved / total_reviews) if total_reviews > 0 else 0.0,
                "manual_review_rate": (manual_approved / total_reviews) if total_reviews > 0 else 0.0,
                "rejection_rate": (rejected / total_reviews) if total_reviews > 0 else 0.0
            }

        finally:
            db.close()
