"""Human-in-the-Loop (HITL) API endpoints."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.hitl import HitlAction, HitlStatus, HitlHistoryEntry
from app.api.dependencies import get_orchestrator_service
from app.database.connection import get_session
from app.services.orchestrator import OrchestratorService
from app.database.models import HitlRequestDB
from app.websocket.events import WebSocketEvent, EventType
from app.websocket.manager import websocket_manager
from app.services.audit_service import AuditService
from app.models.event_log import EventType as AuditEventType, EventSource
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


class HitlResponseRequest(BaseModel):
    """Request model for HITL responses."""
    action: HitlAction
    content: Optional[str] = None
    comment: Optional[str] = None


class HitlRequestResponse(BaseModel):
    """Response model for HITL requests."""
    request_id: UUID
    project_id: UUID
    task_id: UUID
    question: str
    options: List[str]
    status: str
    user_response: Optional[str] = None
    response_comment: Optional[str] = None
    amended_content: Optional[dict] = None
    history: Optional[List[dict]] = None
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None
    responded_at: Optional[str] = None


class HitlProcessResponse(BaseModel):
    """Response model for HITL processing."""
    request_id: UUID
    action: str
    status: str
    message: str
    workflow_resumed: bool


class HitlBulkApproveRequest(BaseModel):
    """Request model for bulk HITL approval."""
    request_ids: List[UUID]
    comment: str


class HitlBulkResponse(BaseModel):
    """Response model for bulk HITL operations."""
    approved_count: int
    failed_count: int
    errors: List[str]
    message: str


class HitlContextResponse(BaseModel):
    """Response model for HITL request context."""
    hitl_request: HitlRequestResponse
    task: Optional[dict] = None
    context_artifacts: List[dict] = []
    workflow_context: Optional[dict] = None
    project_info: dict


class HitlStatisticsResponse(BaseModel):
    """Response model for HITL statistics."""
    total_requests: int
    pending_requests: int
    approved_requests: int
    rejected_requests: int
    amended_requests: int
    expired_requests: int
    approval_rate: float
    average_response_time_hours: Optional[float] = None


class HitlConfigUpdateRequest(BaseModel):
    """Request model for HITL configuration updates."""
    trigger_condition: str
    enabled: bool
    config: Optional[Dict[str, Any]] = None


class OversightLevelUpdateRequest(BaseModel):
    """Request model for oversight level updates."""
    level: str  # "high", "medium", "low"


@router.get("/approvals", response_model=dict)
async def get_hitl_approvals(
    status: Optional[str] = None,
    project_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_session)
):
    """Get HITL approval requests with status filtering for frontend polling."""
    from app.database.models import HitlAgentApprovalDB

    try:
        query = db.query(HitlAgentApprovalDB)

        if status:
            query = query.filter(HitlAgentApprovalDB.status == status.upper())

        if project_id:
            query = query.filter(HitlAgentApprovalDB.project_id == project_id)

        approvals = query.order_by(HitlAgentApprovalDB.created_at.desc()).limit(limit).all()

        return {
            "approvals": [
                {
                    "id": str(approval.id),
                    "project_id": str(approval.project_id),
                    "task_id": str(approval.task_id),
                    "agent_type": approval.agent_type,
                    "request_type": approval.request_type,
                    "status": approval.status,
                    "estimated_tokens": approval.estimated_tokens,
                    "estimated_cost": float(approval.estimated_cost) if approval.estimated_cost else None,
                    "expires_at": approval.expires_at.isoformat(),
                    "created_at": approval.created_at.isoformat(),
                    "user_response": approval.user_response,
                    "user_comment": approval.user_comment,
                    "responded_at": approval.responded_at.isoformat() if approval.responded_at else None,
                    "request_data": approval.request_data
                }
                for approval in approvals
            ]
        }

    except Exception as e:
        logger.error("Failed to get HITL approvals", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approvals: {str(e)}"
        )


@router.post("/{request_id}/respond", response_model=HitlProcessResponse)
async def respond_to_hitl_request(
    request_id: UUID,
    request: HitlResponseRequest,
    db: Session = Depends(get_session),
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Respond to a HITL request with approve, reject, or amend actions."""
    
    logger.info("Processing HITL response", 
                request_id=request_id, 
                action=request.action)
    
    # 1. Validate the HITL request exists and is pending
    hitl_request = db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()
    
    if not hitl_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HITL request {request_id} not found"
        )
    
    if hitl_request.status != HitlStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"HITL request {request_id} is not pending (current status: {hitl_request.status})"
        )
    
    # 2. Create history entry
    history_entry = HitlHistoryEntry(
        timestamp=datetime.now(timezone.utc),
        action=request.action.value,
        content={"user_content": request.content} if request.content else None,
        comment=request.comment
    )
    
    # 3. Update the request based on the action
    workflow_resumed = False
    
    if request.action == HitlAction.APPROVE:
        hitl_request.status = HitlStatus.APPROVED
        hitl_request.user_response = "approved"
        workflow_resumed = True
        message = "Request approved. Workflow will resume."
        
    elif request.action == HitlAction.REJECT:
        hitl_request.status = HitlStatus.REJECTED
        hitl_request.user_response = "rejected"
        workflow_resumed = True  # Workflow continues with rejection handling
        message = "Request rejected. Workflow will be halted."
        
    elif request.action == HitlAction.AMEND:
        if not request.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content is required for amend action"
            )
        
        hitl_request.status = HitlStatus.AMENDED
        hitl_request.user_response = "amended"
        hitl_request.amended_content = {"amended_content": request.content, "comment": request.comment}
        workflow_resumed = True
        message = "Request amended. Workflow will resume with updated content."
    
    # Set the response comment and responded timestamp
    hitl_request.response_comment = request.comment
    hitl_request.responded_at = datetime.now(timezone.utc)
    
    # Add history entry
    if not hitl_request.history:
        hitl_request.history = []
    hitl_request.history.append(history_entry.model_dump(mode="json"))
    hitl_request.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(hitl_request)
    
    # 4. Log audit event for HITL response
    audit_service = AuditService(db)
    await audit_service.log_hitl_event(
        hitl_request_id=hitl_request.id,
        event_type=AuditEventType.HITL_RESPONSE,
        event_source=EventSource.USER,
        event_data={
            "action": request.action.value,
            "status": hitl_request.status.value,
            "user_response": hitl_request.user_response,
            "response_comment": request.comment,
            "amended_content": hitl_request.amended_content,
            "original_question": hitl_request.question,
            "workflow_resumed": workflow_resumed
        },
        project_id=hitl_request.project_id,
        metadata={
            "endpoint": "/hitl/{request_id}/respond",
            "user_action": request.action.value,
            "request_timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    
    # 5. Emit WebSocket events for real-time updates
    await emit_hitl_response_event(hitl_request, request.action)
    
    # 6. Resume workflow if needed
    if workflow_resumed:
        await orchestrator.resume_workflow_after_hitl(hitl_request.project_id, hitl_request.task_id)
    
    logger.info("HITL response processed", 
                request_id=request_id, 
                action=request.action, 
                status=hitl_request.status)
    
    return HitlProcessResponse(
        request_id=request_id,
        action=request.action.value,
        status=hitl_request.status,
        message=message,
        workflow_resumed=workflow_resumed
    )


@router.get("/{request_id}", response_model=HitlRequestResponse)
async def get_hitl_request(
    request_id: UUID,
    db: Session = Depends(get_session)
):
    """Get a specific HITL request."""
    
    hitl_request = db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()
    
    if not hitl_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HITL request {request_id} not found"
        )
    
    return HitlRequestResponse(
        request_id=hitl_request.id,
        project_id=hitl_request.project_id,
        task_id=hitl_request.task_id,
        question=hitl_request.question,
        options=hitl_request.options or [],
        status=hitl_request.status,
        user_response=hitl_request.user_response,
        response_comment=hitl_request.response_comment,
        amended_content=hitl_request.amended_content,
        history=hitl_request.history or [],
        created_at=hitl_request.created_at.isoformat(),
        updated_at=hitl_request.updated_at.isoformat(),
        expires_at=hitl_request.expires_at.isoformat() if hitl_request.expires_at else None,
        responded_at=hitl_request.responded_at.isoformat() if hitl_request.responded_at else None
    )


@router.get("/{request_id}/history", response_model=dict)
async def get_hitl_request_history(
    request_id: UUID,
    db: Session = Depends(get_session)
):
    """Get the history of a HITL request."""

    hitl_request = db.query(HitlRequestDB).filter(HitlRequestDB.id == request_id).first()

    if not hitl_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HITL request {request_id} not found"
        )

    # Return history in the expected format
    return {
        "history": hitl_request.history or []
    }


@router.get("/project/{project_id}/requests", response_model=List[HitlRequestResponse])
async def get_project_hitl_requests(
    project_id: UUID,
    db: Session = Depends(get_session),
    status_filter: Optional[str] = None
):
    """Get all HITL requests for a project."""

    query = db.query(HitlRequestDB).filter(HitlRequestDB.project_id == project_id)

    if status_filter:
        try:
            status_enum = HitlStatus(status_filter)
            query = query.filter(HitlRequestDB.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter: {status_filter}"
            )

    hitl_requests = query.order_by(HitlRequestDB.created_at.desc()).all()

    return [
        HitlRequestResponse(
            request_id=req.id,
            project_id=req.project_id,
            task_id=req.task_id,
            question=req.question,
            options=req.options or [],
            status=req.status,
            user_response=req.user_response,
            response_comment=req.response_comment,
            amended_content=req.amended_content,
            history=req.history or [],
            created_at=req.created_at.isoformat(),
            updated_at=req.updated_at.isoformat(),
            expires_at=req.expires_at.isoformat() if req.expires_at else None,
            responded_at=req.responded_at.isoformat() if req.responded_at else None
        )
        for req in hitl_requests
    ]


async def emit_hitl_response_event(hitl_request: HitlRequestDB, action: HitlAction):
    """Emit WebSocket event for HITL response."""
    
    from app.websocket.manager import websocket_manager
    
    event = WebSocketEvent(
        event_type=EventType.HITL_RESPONSE,
        project_id=hitl_request.project_id,
        task_id=hitl_request.task_id,
        data={
            "hitl_request_id": str(hitl_request.id),
            "action": action.value,
            "status": hitl_request.status,
            "user_response": hitl_request.user_response,
            "amended_content": hitl_request.amended_content
        }
    )
    
    # Broadcast the event to WebSocket clients
    try:
        await websocket_manager.broadcast_to_project(event, str(hitl_request.project_id))
        logger.info("HITL response event broadcasted", 
                    request_id=hitl_request.id, 
                    action=action.value,
                    project_id=hitl_request.project_id)
    except Exception as e:
        logger.error("Failed to broadcast HITL response event",
                    request_id=hitl_request.id,
                    error=str(e),
                    exc_info=True)


@router.post("/bulk/approve", response_model=HitlBulkResponse)
async def bulk_approve_hitl_requests(
    request: HitlBulkApproveRequest,
    db: Session = Depends(get_session)
):
    """Bulk approve multiple HITL requests."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        result = await hitl_service.bulk_approve_requests(
            request_ids=request.request_ids,
            comment=request.comment
        )

        return HitlBulkResponse(**result)

    except Exception as e:
        logger.error("Bulk HITL approval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk approval failed: {str(e)}"
        )


@router.get("/{request_id}/context", response_model=HitlContextResponse)
async def get_hitl_request_context(
    request_id: UUID,
    db: Session = Depends(get_session)
):
    """Get full context for a HITL request including artifacts and task details."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        context = await hitl_service.get_hitl_request_context(request_id)

        # Convert to API response format
        return HitlContextResponse(
            hitl_request=HitlRequestResponse(
                request_id=context["hitl_request"].request_id,
                project_id=context["hitl_request"].project_id,
                task_id=context["hitl_request"].task_id,
                question=context["hitl_request"].question,
                options=context["hitl_request"].options,
                status=context["hitl_request"].status.value,
                user_response=context["hitl_request"].user_response,
                response_comment=context["hitl_request"].response_comment,
                amended_content=context["hitl_request"].amended_content,
                history=[entry.model_dump() for entry in context["hitl_request"].history],
                created_at=context["hitl_request"].created_at.isoformat(),
                updated_at=context["hitl_request"].updated_at.isoformat(),
                expires_at=context["hitl_request"].expires_at.isoformat() if context["hitl_request"].expires_at else None,
                responded_at=context["hitl_request"].responded_at.isoformat() if context["hitl_request"].responded_at else None
            ),
            task=context.get("task"),
            context_artifacts=context.get("context_artifacts", []),
            workflow_context=context.get("workflow_context"),
            project_info=context.get("project_info", {})
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get HITL request context", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}"
        )


@router.get("/statistics", response_model=HitlStatisticsResponse)
async def get_hitl_statistics(
    project_id: Optional[UUID] = None,
    db: Session = Depends(get_session)
):
    """Get HITL statistics for monitoring and analytics."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        stats = await hitl_service.get_hitl_statistics(project_id)
        return HitlStatisticsResponse(**stats)

    except Exception as e:
        logger.error("Failed to get HITL statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post("/config/trigger-condition", response_model=dict)
async def configure_hitl_trigger_condition(
    request: HitlConfigUpdateRequest,
    db: Session = Depends(get_session)
):
    """Configure a HITL trigger condition."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        hitl_service.configure_trigger_condition(
            condition=request.trigger_condition,
            enabled=request.enabled,
            config=request.config
        )

        return {
            "message": f"HITL trigger condition '{request.trigger_condition}' configured successfully",
            "condition": request.trigger_condition,
            "enabled": request.enabled
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to configure HITL trigger condition",
                    condition=request.trigger_condition,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration failed: {str(e)}"
        )


@router.post("/project/{project_id}/oversight-level", response_model=dict)
async def set_project_oversight_level(
    project_id: UUID,
    request: OversightLevelUpdateRequest,
    db: Session = Depends(get_session)
):
    """Set oversight level for a project."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        hitl_service.set_oversight_level(project_id, request.level)

        return {
            "message": f"Oversight level set to '{request.level}' for project",
            "project_id": str(project_id),
            "oversight_level": request.level
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to set oversight level",
                    project_id=str(project_id),
                    level=request.level,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set oversight level: {str(e)}"
        )


@router.get("/project/{project_id}/oversight-level", response_model=dict)
async def get_project_oversight_level(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Get oversight level for a project."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        level = hitl_service.get_oversight_level(project_id)

        return {
            "project_id": str(project_id),
            "oversight_level": level
        }

    except Exception as e:
        logger.error("Failed to get oversight level",
                    project_id=str(project_id),
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get oversight level: {str(e)}"
        )


@router.post("/cleanup-expired", response_model=dict)
async def cleanup_expired_hitl_requests(
    db: Session = Depends(get_session)
):
    """Clean up expired HITL requests."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        cleaned_count = await hitl_service.cleanup_expired_requests()

        return {
            "message": f"Cleaned up {cleaned_count} expired HITL requests",
            "expired_requests_cleaned": cleaned_count
        }

    except Exception as e:
        logger.error("Failed to cleanup expired HITL requests", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/pending", response_model=List[HitlRequestResponse])
async def get_pending_hitl_requests(
    project_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_session)
):
    """Get pending HITL requests with optional project filtering."""
    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        pending_requests = await hitl_service.get_pending_hitl_requests(
            project_id=project_id,
            limit=limit
        )

        return [
            HitlRequestResponse(
                request_id=req.request_id,
                project_id=req.project_id,
                task_id=req.task_id,
                question=req.question,
                options=req.options,
                status=req.status.value,
                user_response=req.user_response,
                response_comment=req.response_comment,
                amended_content=req.amended_content,
                history=[entry.model_dump() for entry in req.history],
                created_at=req.created_at.isoformat(),
                updated_at=req.updated_at.isoformat(),
                expires_at=req.expires_at.isoformat() if req.expires_at else None,
                responded_at=req.responded_at.isoformat() if req.responded_at else None
            )
            for req in pending_requests
        ]

    except Exception as e:
        logger.error("Failed to get pending HITL requests", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending requests: {str(e)}"
        )


