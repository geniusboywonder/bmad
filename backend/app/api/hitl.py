"""Human-in-the-Loop (HITL) API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.hitl import HitlAction
from app.api.dependencies import get_orchestrator_service
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/hitl", tags=["hitl"])


class HitlResponseRequest(BaseModel):
    """Request model for HITL responses."""
    action: HitlAction
    content: str = None
    comment: str = None


class HitlRequestResponse(BaseModel):
    """Response model for HITL requests."""
    request_id: UUID
    project_id: UUID
    task_id: UUID
    question: str
    options: List[str]
    status: str
    created_at: str


@router.post("/{request_id}/respond", status_code=status.HTTP_200_OK)
async def respond_to_hitl_request(
    request_id: UUID,
    request: HitlResponseRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Respond to a HITL request."""
    
    # In a real implementation, this would:
    # 1. Validate the HITL request exists and is pending
    # 2. Update the request status based on the action
    # 3. Handle the response (approve/reject/amend)
    # 4. Resume or modify the agent workflow accordingly
    # 5. Emit WebSocket events for real-time updates
    
    # For now, we'll just return a success response
    return {
        "request_id": request_id,
        "action": request.action,
        "status": "processed",
        "message": f"HITL request {request_id} processed with action {request.action}"
    }


@router.get("/{request_id}", response_model=HitlRequestResponse)
async def get_hitl_request(
    request_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Get a specific HITL request."""
    
    # In a real implementation, this would fetch the HITL request from the database
    # For now, we'll return a mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="HITL request retrieval not yet implemented"
    )


@router.get("/project/{project_id}/requests", response_model=List[HitlRequestResponse])
async def get_project_hitl_requests(
    project_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Get all HITL requests for a project."""
    
    # In a real implementation, this would fetch all HITL requests for the project
    # For now, we'll return a mock response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Project HITL requests retrieval not yet implemented"
    )
