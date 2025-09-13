"""Audit trail API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.services.audit_service import AuditService
from app.models.event_log import EventLogResponse, EventLogFilter, EventType, EventSource


router = APIRouter(prefix="/audit", tags=["audit"])


async def get_audit_service(db: Session = Depends(get_session)) -> AuditService:
    """Dependency to get audit service instance."""
    return AuditService(db)


@router.get("/events", response_model=List[EventLogResponse])
async def get_audit_events(
    project_id: UUID = Query(None, description="Filter by project ID"),
    task_id: UUID = Query(None, description="Filter by task ID"),
    hitl_request_id: UUID = Query(None, description="Filter by HITL request ID"),
    event_type: EventType = Query(None, description="Filter by event type"),
    event_source: EventSource = Query(None, description="Filter by event source"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    audit_service: AuditService = Depends(get_audit_service)
) -> List[EventLogResponse]:
    """Retrieve filtered audit events.
    
    Returns a list of audit events based on the provided filters.
    Events are ordered by creation time (newest first).
    """
    try:
        filter_params = EventLogFilter(
            project_id=project_id,
            task_id=task_id,
            hitl_request_id=hitl_request_id,
            event_type=event_type,
            event_source=event_source,
            limit=limit,
            offset=offset
        )
        
        events = await audit_service.get_events(filter_params)
        return events
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit events: {str(e)}"
        )


@router.get("/events/{event_id}", response_model=EventLogResponse)
async def get_audit_event(
    event_id: UUID,
    audit_service: AuditService = Depends(get_audit_service)
) -> EventLogResponse:
    """Retrieve a specific audit event by ID."""
    try:
        event = await audit_service.get_event_by_id(event_id)
        
        if not event:
            raise HTTPException(
                status_code=404,
                detail=f"Audit event with ID {event_id} not found"
            )
        
        return event
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit event: {str(e)}"
        )


@router.get("/projects/{project_id}/events", response_model=List[EventLogResponse])
async def get_project_audit_events(
    project_id: UUID,
    event_type: EventType = Query(None, description="Filter by event type"),
    event_source: EventSource = Query(None, description="Filter by event source"),
    limit: int = Query(100, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    audit_service: AuditService = Depends(get_audit_service)
) -> List[EventLogResponse]:
    """Retrieve audit events for a specific project.
    
    Returns all audit events associated with the given project ID.
    """
    try:
        filter_params = EventLogFilter(
            project_id=project_id,
            event_type=event_type,
            event_source=event_source,
            limit=limit,
            offset=offset
        )
        
        events = await audit_service.get_events(filter_params)
        return events
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve project audit events: {str(e)}"
        )


@router.get("/tasks/{task_id}/events", response_model=List[EventLogResponse])
async def get_task_audit_events(
    task_id: UUID,
    event_type: EventType = Query(None, description="Filter by event type"),
    limit: int = Query(50, le=1000, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    audit_service: AuditService = Depends(get_audit_service)
) -> List[EventLogResponse]:
    """Retrieve audit events for a specific task.
    
    Returns all audit events associated with the given task ID.
    """
    try:
        filter_params = EventLogFilter(
            task_id=task_id,
            event_type=event_type,
            limit=limit,
            offset=offset
        )
        
        events = await audit_service.get_events(filter_params)
        return events
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task audit events: {str(e)}"
        )