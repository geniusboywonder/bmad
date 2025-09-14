"""
HITL Request Endpoints

API endpoints for managing HITL requests and their lifecycle.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.hitl import HitlStatus, HitlRequestResponse
from app.database.models import HitlRequestDB
from app.database.connection import get_session
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl-requests"])


@router.get("/{request_id}", response_model=HitlRequestResponse)
async def get_hitl_request(
    request_id: UUID,
    db: Session = Depends(get_session)
):
    """Get a specific HITL request."""
    logger.info("Getting HITL request", request_id=request_id)

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
    logger.info("Getting HITL request history", request_id=request_id)

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
    logger.info("Getting project HITL requests", project_id=project_id, status_filter=status_filter)

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


@router.get("/pending", response_model=List[HitlRequestResponse])
async def get_pending_hitl_requests(
    project_id: Optional[UUID] = None,
    limit: int = 50,
    db: Session = Depends(get_session)
):
    """Get pending HITL requests with optional project filtering."""
    logger.info("Getting pending HITL requests", project_id=project_id, limit=limit)

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


@router.get("/{request_id}/context", response_model=dict)
async def get_hitl_request_context(
    request_id: UUID,
    db: Session = Depends(get_session)
):
    """Get full context for a HITL request including artifacts and task details."""
    logger.info("Getting HITL request context", request_id=request_id)

    from app.services.hitl_service import HitlService

    hitl_service = HitlService(db)

    try:
        context = await hitl_service.get_hitl_request_context(request_id)

        # Convert to API response format
        return {
            "hitl_request": {
                "request_id": str(context["hitl_request"].request_id),
                "project_id": str(context["hitl_request"].project_id),
                "task_id": str(context["hitl_request"].task_id),
                "question": context["hitl_request"].question,
                "options": context["hitl_request"].options,
                "status": context["hitl_request"].status.value,
                "user_response": context["hitl_request"].user_response,
                "response_comment": context["hitl_request"].response_comment,
                "amended_content": context["hitl_request"].amended_content,
                "history": [entry.model_dump() for entry in context["hitl_request"].history],
                "created_at": context["hitl_request"].created_at.isoformat(),
                "updated_at": context["hitl_request"].updated_at.isoformat(),
                "expires_at": context["hitl_request"].expires_at.isoformat() if context["hitl_request"].expires_at else None,
                "responded_at": context["hitl_request"].responded_at.isoformat() if context["hitl_request"].responded_at else None
            },
            "task": context.get("task"),
            "context_artifacts": context.get("context_artifacts", []),
            "workflow_context": context.get("workflow_context"),
            "project_info": context.get("project_info", {})
        }

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
