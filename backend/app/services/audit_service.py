"""Audit trail service for comprehensive event logging.

This service implements the Single Responsibility Principle by focusing
solely on event logging and audit trail management.
"""

import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, select

from app.database.models import EventLogDB
from app.models.event_log import (
    EventLogCreate, 
    EventLogResponse, 
    EventLogFilter,
    EventType,
    EventSource
)


logger = structlog.get_logger(__name__)


class AuditService:
    """Service for managing audit trail and event logging.
    
    Follows SOLID principles:
    - Single Responsibility: Only handles event logging
    - Open/Closed: Extensible via event types and sources
    - Liskov Substitution: Can be substituted with other audit implementations
    - Interface Segregation: Focused interface for audit operations
    - Dependency Inversion: Depends on abstractions (AsyncSession)
    """
    
    def __init__(self, db_session: Session):
        """Initialize audit service with database session."""
        self.db_session = db_session
    
    async def log_event(
        self,
        event_type: EventType,
        event_source: EventSource,
        event_data: Dict[str, Any],
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        hitl_request_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventLogResponse:
        """Log a single event to the audit trail.
        
        Args:
            event_type: Type of event being logged
            event_source: Source of the event (agent, user, system)
            event_data: Full payload/context data
            project_id: Associated project ID (optional)
            task_id: Associated task ID (optional)
            hitl_request_id: Associated HITL request ID (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            EventLogResponse: The created event log entry
        """
        try:
            # Create event log entry
            event_log_data = EventLogCreate(
                project_id=project_id,
                task_id=task_id,
                hitl_request_id=hitl_request_id,
                event_type=event_type,
                event_source=event_source,
                event_data=event_data,
                metadata=metadata or {}
            )
            
            # Add additional system metadata
            enriched_metadata = {
                **(metadata or {}),
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "service_version": "1.0.0"
            }
            
            # Create database record
            db_event = EventLogDB(
                project_id=event_log_data.project_id,
                task_id=event_log_data.task_id,
                hitl_request_id=event_log_data.hitl_request_id,
                event_type=event_log_data.event_type.value,
                event_source=event_log_data.event_source.value,
                event_data=event_log_data.event_data,
                event_metadata=enriched_metadata
            )
            
            self.db_session.add(db_event)
            self.db_session.commit()
            self.db_session.refresh(db_event)
            
            # Log structured event for monitoring
            self._log_structured_event(db_event)
            
            return EventLogResponse.model_validate(db_event)
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(
                "Failed to log audit event",
                event_type=event_type.value,
                error=str(e),
                project_id=str(project_id) if project_id else None
            )
            raise
    
    async def get_events(
        self,
        filter_params: EventLogFilter
    ) -> List[EventLogResponse]:
        """Retrieve filtered event log entries.
        
        Args:
            filter_params: Filtering parameters
            
        Returns:
            List[EventLogResponse]: Filtered event log entries
        """
        try:
            # Build query with filters
            query = select(EventLogDB)
            conditions = []
            
            if filter_params.project_id:
                conditions.append(EventLogDB.project_id == filter_params.project_id)
            
            if filter_params.task_id:
                conditions.append(EventLogDB.task_id == filter_params.task_id)
            
            if filter_params.hitl_request_id:
                conditions.append(EventLogDB.hitl_request_id == filter_params.hitl_request_id)
            
            if filter_params.event_type:
                conditions.append(EventLogDB.event_type == filter_params.event_type.value)
            
            if filter_params.event_source:
                conditions.append(EventLogDB.event_source == filter_params.event_source.value)
            
            if filter_params.start_date:
                conditions.append(EventLogDB.created_at >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(EventLogDB.created_at <= filter_params.end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply ordering and pagination
            query = query.order_by(desc(EventLogDB.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = self.db_session.execute(query)
            events = result.scalars().all()
            
            return [EventLogResponse.model_validate(event) for event in events]
            
        except Exception as e:
            logger.error(
                "Failed to retrieve audit events",
                filter_params=filter_params.model_dump(),
                error=str(e)
            )
            raise
    
    async def get_event_by_id(self, event_id: UUID) -> Optional[EventLogResponse]:
        """Retrieve a specific event log entry by ID.
        
        Args:
            event_id: Event log entry ID
            
        Returns:
            EventLogResponse: Event log entry or None if not found
        """
        try:
            query = select(EventLogDB).where(EventLogDB.id == event_id)
            result = self.db_session.execute(query)
            event = result.scalar_one_or_none()
            
            if event:
                return EventLogResponse.model_validate(event)
            return None
            
        except Exception as e:
            logger.error(
                "Failed to retrieve audit event",
                event_id=str(event_id),
                error=str(e)
            )
            raise
    
    async def log_task_event(
        self,
        task_id: UUID,
        event_type: EventType,
        event_data: Dict[str, Any],
        project_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventLogResponse:
        """Convenience method for logging task-related events.
        
        Args:
            task_id: Task ID
            event_type: Type of task event
            event_data: Event payload
            project_id: Associated project ID
            metadata: Additional metadata
            
        Returns:
            EventLogResponse: The created event log entry
        """
        return await self.log_event(
            event_type=event_type,
            event_source=EventSource.SYSTEM,
            event_data=event_data,
            project_id=project_id,
            task_id=task_id,
            metadata=metadata
        )
    
    async def log_hitl_event(
        self,
        hitl_request_id: UUID,
        event_type: EventType,
        event_data: Dict[str, Any],
        event_source: EventSource = EventSource.USER,
        project_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EventLogResponse:
        """Convenience method for logging HITL-related events.
        
        Args:
            hitl_request_id: HITL request ID
            event_type: Type of HITL event
            event_data: Event payload
            event_source: Source of the event
            project_id: Associated project ID
            metadata: Additional metadata
            
        Returns:
            EventLogResponse: The created event log entry
        """
        return await self.log_event(
            event_type=event_type,
            event_source=event_source,
            event_data=event_data,
            project_id=project_id,
            hitl_request_id=hitl_request_id,
            metadata=metadata
        )
    
    def _log_structured_event(self, event: EventLogDB) -> None:
        """Log structured event for monitoring and alerting.
        
        Args:
            event: Event log database record
        """
        logger.info(
            "Audit event logged",
            event_id=str(event.id),
            event_type=event.event_type,
            event_source=event.event_source,
            project_id=str(event.project_id) if event.project_id else None,
            task_id=str(event.task_id) if event.task_id else None,
            hitl_request_id=str(event.hitl_request_id) if event.hitl_request_id else None,
            created_at=event.created_at.isoformat() if event.created_at else None
        )