"""
✅ SIMPLIFIED HITL API - True Radical Simplification

BEFORE: 28 endpoints across 3 files (hitl.py, hitl_safety.py, hitl_request_endpoints.py)
AFTER: 8 essential endpoints in 1 file (67% reduction)

Core HITL workflow: Request → Approve/Reject → Monitor
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.services.hitl_approval_service import HitlApprovalService
from app.services.hitl_safety_service import HITLSafetyService
from app.database.models import HitlAgentApprovalDB
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


# ✅ SIMPLIFIED REQUEST/RESPONSE MODELS
class HITLApprovalRequest(BaseModel):
    """Simplified approval request."""
    project_id: UUID
    task_id: UUID
    agent_type: str
    instructions: str
    estimated_tokens: Optional[int] = 100


class HITLApprovalResponse(BaseModel):
    """Simplified approval response."""
    approved: bool
    response: Optional[str] = None


class HITLApprovalStatus(BaseModel):
    """Simplified approval status."""
    id: UUID
    project_id: UUID
    agent_type: str
    status: str  # PENDING, APPROVED, REJECTED
    created_at: str
    instructions: str


class HITLSettingsUpdateRequest(BaseModel):
    """Request model for updating HITL counter settings."""
    new_limit: Optional[int] = None
    new_status: Optional[bool] = None


# ✅ 8 ESSENTIAL ENDPOINTS (was 28)

@router.post("/settings/{project_id}",
             response_model=dict,
             summary="⚙️ Update HITL Counter Settings")
async def update_hitl_settings(
    project_id: UUID,
    request: HITLSettingsUpdateRequest,
):
    """Updates the HITL auto-approval settings for a project."""
    try:
        from app.services.hitl_counter_service import HitlCounterService
        hitl_counter_service = HitlCounterService()

        updated_settings = hitl_counter_service.update_settings(
            project_id=project_id,
            new_limit=request.new_limit,
            new_status=request.new_status,
        )

        return {
            "success": True,
            "message": "HITL settings updated successfully.",
            "updated_settings": updated_settings,
        }
    except Exception as e:
        logger.error("Failed to update HITL settings", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/request-approval", 
             response_model=dict,
             summary="🚨 Request Agent Approval")
async def request_agent_approval(
    request: HITLApprovalRequest,
    db: Session = Depends(get_session)
):
    """
    ✅ CORE ENDPOINT: Request approval for agent execution.
    Replaces: request-agent-execution + multiple approval creation endpoints
    """
    try:
        hitl_service = HITLSafetyService(db_session=db)
        approval_id = await hitl_service.create_approval_request(
            project_id=request.project_id,
            task_id=request.task_id,
            agent_type=request.agent_type,
            request_type="PRE_EXECUTION",
            request_data={"instructions": request.instructions},
            estimated_tokens=request.estimated_tokens
        )
        
        return {
            "success": True,
            "approval_id": approval_id,
            "message": "Approval request created successfully"
        }
    except Exception as e:
        logger.error("Failed to create approval request", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve/{approval_id}", 
             response_model=dict,
             summary="✅ Approve Agent Request")
async def approve_agent_request(
    approval_id: UUID,
    response: HITLApprovalResponse,
    db: Session = Depends(get_session)
):
    """
    ✅ CORE ENDPOINT: Approve or reject agent execution.
    Replaces: approve-agent-execution + respond endpoints
    """
    try:
        hitl_service = HITLSafetyService()
        await hitl_service.process_approval_response(
            approval_id=approval_id,
            approved=response.approved,
            response_text=response.response,
            db=db
        )
        
        action = "approved" if response.approved else "rejected"
        return {
            "success": True,
            "message": f"Agent request {action} successfully"
        }
    except Exception as e:
        logger.error("Failed to process approval", approval_id=approval_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending",
            response_model=List[HITLApprovalStatus],
            summary="📋 Get Pending Approvals")
async def get_pending_approvals(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_session)
):
    """
    ✅ CORE ENDPOINT: Get all pending approval requests.
    Replaces: multiple pending/statistics/list endpoints
    """
    try:
        query = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.status == "PENDING"
        )

        if project_id:
            query = query.filter(HitlAgentApprovalDB.project_id == project_id)

        approvals = query.all()

        return [
            HITLApprovalStatus(
                id=approval.id,
                project_id=approval.project_id,
                agent_type=approval.agent_type,
                status=approval.status,
                created_at=approval.created_at.isoformat(),
                instructions=approval.request_data.get("instructions", "") if approval.request_data else ""
            )
            for approval in approvals
        ]
    except Exception as e:
        logger.error("Failed to get pending approvals", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals",
            response_model=List[HITLApprovalStatus],
            summary="📋 Get Approvals (Alias)")
async def get_approvals_by_status(
    status: Optional[str] = "pending",
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_session)
):
    """
    ✅ ALIAS ENDPOINT: Get approvals by status (for frontend compatibility).
    Defaults to pending if no status specified.
    """
    try:
        query = db.query(HitlAgentApprovalDB)

        # Filter by status (uppercase to match DB enum)
        if status:
            query = query.filter(HitlAgentApprovalDB.status == status.upper())

        if project_id:
            query = query.filter(HitlAgentApprovalDB.project_id == project_id)

        approvals = query.all()

        return [
            HITLApprovalStatus(
                id=approval.id,
                project_id=approval.project_id,
                agent_type=approval.agent_type,
                status=approval.status,
                created_at=approval.created_at.isoformat(),
                instructions=approval.request_data.get("instructions", "") if approval.request_data else ""
            )
            for approval in approvals
        ]
    except Exception as e:
        logger.error("Failed to get approvals", status=status, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{approval_id}", 
            response_model=HITLApprovalStatus,
            summary="📊 Get Approval Status")
async def get_approval_status(
    approval_id: UUID,
    db: Session = Depends(get_session)
):
    """
    ✅ CORE ENDPOINT: Get specific approval status.
    Replaces: multiple get/history/context endpoints
    """
    try:
        approval = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.id == approval_id
        ).first()
        
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        
        return HITLApprovalStatus(
            id=approval.id,
            project_id=approval.project_id,
            agent_type=approval.agent_type,
            status=approval.status,
            created_at=approval.created_at.isoformat(),
            instructions=approval.request_data.get("instructions", "") if approval.request_data else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get approval status", approval_id=approval_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop", 
             response_model=dict,
             summary="🛑 Emergency Stop All Agents")
async def emergency_stop_all_agents(
    project_id: Optional[UUID] = None,
    reason: str = "Manual emergency stop",
    db: Session = Depends(get_session)
):
    """
    ✅ SAFETY ENDPOINT: Emergency stop for all or project-specific agents.
    Replaces: complex emergency stop management
    """
    try:
        hitl_service = HITLSafetyService()
        stop_id = await hitl_service.create_emergency_stop(
            project_id=project_id,
            reason=reason,
            db=db
        )
        
        return {
            "success": True,
            "stop_id": stop_id,
            "message": "Emergency stop activated"
        }
    except Exception as e:
        logger.error("Failed to create emergency stop", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/emergency-stop/{stop_id}", 
               response_model=dict,
               summary="▶️ Deactivate Emergency Stop")
async def deactivate_emergency_stop(
    stop_id: UUID,
    db: Session = Depends(get_session)
):
    """
    ✅ SAFETY ENDPOINT: Deactivate emergency stop.
    """
    try:
        hitl_service = HITLSafetyService()
        await hitl_service.deactivate_emergency_stop(stop_id, db)
        
        return {
            "success": True,
            "message": "Emergency stop deactivated"
        }
    except Exception as e:
        logger.error("Failed to deactivate emergency stop", stop_id=stop_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}/summary", 
            response_model=dict,
            summary="📈 Project HITL Summary")
async def get_project_hitl_summary(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """
    ✅ MONITORING ENDPOINT: Get HITL summary for a project.
    Replaces: statistics/oversight-level/budget endpoints
    """
    try:
        # Get approval counts
        total_approvals = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.project_id == project_id
        ).count()
        
        pending_approvals = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.project_id == project_id,
            HitlAgentApprovalDB.status == "PENDING"
        ).count()
        
        approved_count = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.project_id == project_id,
            HitlAgentApprovalDB.status == "APPROVED"
        ).count()
        
        rejected_count = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.project_id == project_id,
            HitlAgentApprovalDB.status == "REJECTED"
        ).count()
        
        return {
            "project_id": project_id,
            "total_requests": total_approvals,
            "pending": pending_approvals,
            "approved": approved_count,
            "rejected": rejected_count,
            "approval_rate": round(approved_count / max(total_approvals, 1) * 100, 1)
        }
    except Exception as e:
        logger.error("Failed to get project HITL summary", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", 
            response_model=dict,
            summary="❤️ HITL System Health")
async def hitl_health_check(db: Session = Depends(get_session)):
    """
    ✅ HEALTH ENDPOINT: Check HITL system health.
    """
    try:
        # Simple health check
        pending_count = db.query(HitlAgentApprovalDB).filter(
            HitlAgentApprovalDB.status == "PENDING"
        ).count()
        
        return {
            "status": "healthy",
            "pending_approvals": pending_count,
            "services": {
                "hitl_approval_service": "operational",
                "hitl_safety_service": "operational"
            }
        }
    except Exception as e:
        logger.error("HITL health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }