"""
HITL Core Service - Main coordination logic with dependency injection.

Handles core HITL request lifecycle management and delegates to specialized services.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.hitl import HitlStatus, HitlAction, HitlRequest, HitlResponse
from app.models.task import Task
from app.database.models import HitlRequestDB
from app.services.context_store import ContextStoreService
from app.services.audit_service import AuditService
from app.services.hitl_trigger_manager import HitlTriggerManager, OversightLevel

from .trigger_processor import TriggerProcessor
from .phase_gate_manager import PhaseGateManager
from .response_processor import ResponseProcessor
from .validation_engine import ValidationEngine

logger = structlog.get_logger(__name__)


class HitlCore:
    """
    Core HITL service that coordinates specialized HITL services.

    Follows Single Responsibility Principle by delegating specialized tasks
    to focused service components.
    """

    def __init__(self, db: Session):
        self.db = db
        self.context_store = ContextStoreService(db)
        self.audit_service = AuditService(db)
        self.trigger_manager = HitlTriggerManager(db)

        # Initialize specialized services
        self.trigger_processor = TriggerProcessor(db)
        self.phase_gate_manager = PhaseGateManager(db)
        self.response_processor = ResponseProcessor(db)
        self.validation_engine = ValidationEngine(db)

        # Configuration
        self.default_oversight_level = OversightLevel.MEDIUM
        self.bulk_approval_batch_size = 10
        self.default_timeout_hours = 24

    async def check_hitl_triggers(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """Check if any HITL trigger conditions are met."""
        return await self.trigger_processor.check_hitl_triggers(
            project_id, task_id, agent_type, trigger_context
        )

    async def process_hitl_response(
        self,
        request_id: UUID,
        action: HitlAction,
        user_id: str,
        response_comment: Optional[str] = None,
        amendments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process HITL response and handle workflow resumption."""
        return await self.response_processor.process_hitl_response(
            request_id, action, user_id, response_comment, amendments
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

    async def bulk_approve_requests(
        self,
        request_ids: List[UUID],
        user_id: str,
        response_comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk approve multiple HITL requests."""
        return await self.response_processor.bulk_approve_requests(
            request_ids, user_id, response_comment
        )

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

    def configure_trigger_condition(
        self,
        condition_type: str,
        project_id: Optional[UUID] = None,
        config: Dict[str, Any] = None
    ) -> None:
        """Configure HITL trigger condition."""
        self.trigger_processor.configure_trigger_condition(
            condition_type, project_id, config
        )

    def set_oversight_level(self, project_id: UUID, level: str) -> None:
        """Set oversight level for project."""
        try:
            oversight_level = OversightLevel(level.upper())
            self.trigger_processor.set_oversight_level(project_id, oversight_level)
            logger.info(f"Set oversight level for project {project_id} to {level}")
        except ValueError:
            raise ValueError(f"Invalid oversight level: {level}")

    def get_oversight_level(self, project_id: UUID) -> str:
        """Get current oversight level for project."""
        return self.trigger_processor.get_oversight_level(project_id).value

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

    # Phase Gate Methods (delegated to PhaseGateManager)
    async def create_phase_gate_hitl(
        self,
        project_id: UUID,
        phase: str,
        gate_type: str = "approval",
        deliverables: Optional[List[Dict[str, Any]]] = None
    ) -> HitlRequestDB:
        """Create phase gate HITL request."""
        return await self.phase_gate_manager.create_phase_gate_hitl(
            project_id, phase, gate_type, deliverables
        )

    async def validate_phase_gate_requirements(
        self,
        project_id: UUID,
        phase: str
    ) -> Dict[str, Any]:
        """Validate phase gate requirements."""
        return await self.phase_gate_manager.validate_phase_gate_requirements(
            project_id, phase
        )

    async def process_phase_gate_response(
        self,
        request_id: UUID,
        action: HitlAction,
        user_id: str,
        amendments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process phase gate response."""
        return await self.phase_gate_manager.process_phase_gate_response(
            request_id, action, user_id, amendments
        )

    async def get_phase_gate_status(self, project_id: UUID) -> Dict[str, Any]:
        """Get phase gate status for project."""
        return await self.phase_gate_manager.get_phase_gate_status(project_id)

    async def auto_create_phase_gates(self, project_id: UUID) -> List[UUID]:
        """Auto-create phase gates for project."""
        return await self.phase_gate_manager.auto_create_phase_gates(project_id)

    # Private helper methods
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
        from app.database.models import TaskDB
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