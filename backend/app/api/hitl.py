"""Human-in-the-Loop (HITL) API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.hitl import HitlAction, HitlStatus, HitlHistoryEntry
from app.api.dependencies import get_orchestrator_service, get_db_session
from app.services.orchestrator import OrchestratorService
from app.database.models import HitlRequestDB
from app.websocket.events import WebSocketEvent, EventType
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
    amended_content: Optional[dict] = None
    created_at: str
    updated_at: str


class HitlProcessResponse(BaseModel):
    """Response model for HITL processing."""
    request_id: UUID
    action: str
    status: str
    message: str
    workflow_resumed: bool


@router.post("/{request_id}/respond", response_model=HitlProcessResponse)
async def respond_to_hitl_request(
    request_id: UUID,
    request: HitlResponseRequest,
    db: Session = Depends(get_db_session),
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
        timestamp=datetime.utcnow(),
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
    
    # Add history entry
    if not hitl_request.history:
        hitl_request.history = []
    hitl_request.history.append(history_entry.dict())
    hitl_request.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(hitl_request)
    
    # 4. Emit WebSocket events for real-time updates
    await emit_hitl_response_event(hitl_request, request.action)
    
    # 5. Resume workflow if needed
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
    db: Session = Depends(get_db_session)
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
        amended_content=hitl_request.amended_content,
        created_at=hitl_request.created_at.isoformat(),
        updated_at=hitl_request.updated_at.isoformat()
    )


@router.get("/project/{project_id}/requests", response_model=List[HitlRequestResponse])
async def get_project_hitl_requests(
    project_id: UUID,
    db: Session = Depends(get_db_session),
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
            amended_content=req.amended_content,
            created_at=req.created_at.isoformat(),
            updated_at=req.updated_at.isoformat()
        )
        for req in hitl_requests
    ]


async def emit_hitl_response_event(hitl_request: HitlRequestDB, action: HitlAction):
    """Emit WebSocket event for HITL response."""
    
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
    
    # In a full implementation, this would emit the event to WebSocket clients
    logger.info("HITL response event emitted", 
                request_id=hitl_request.id, 
                action=action.value)
