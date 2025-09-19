"""Event log data models for audit trail."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class EventType(str, Enum):
    """Event types for audit trail."""
    
    # Task events
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    # HITL events
    HITL_REQUEST_CREATED = "hitl_request_created"
    HITL_RESPONSE = "hitl_response"
    HITL_TIMEOUT = "hitl_timeout"
    HITL_CANCELLED = "hitl_cancelled"
    
    # Agent events
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_ERROR = "agent_error"
    
    # Project events
    PROJECT_CREATED = "project_created"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_CANCELLED = "project_cancelled"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    WEBHOOK_RECEIVED = "webhook_received"


class EventSource(str, Enum):
    """Event sources for audit trail."""
    
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"
    WEBHOOK = "webhook"
    SCHEDULER = "scheduler"


class EventLogCreate(BaseModel):
    """Event log creation model."""
    
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    hitl_request_id: Optional[UUID] = None
    event_type: EventType
    event_source: EventSource
    event_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EventLogResponse(BaseModel):
    """Event log response model."""
    
    id: UUID
    project_id: Optional[UUID]
    task_id: Optional[UUID]
    hitl_request_id: Optional[UUID]
    event_type: str
    event_source: str
    event_data: Dict[str, Any]
    event_metadata: Dict[str, Any]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EventLogFilter(BaseModel):
    """Event log filtering model."""
    
    project_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    hitl_request_id: Optional[UUID] = None
    event_type: Optional[EventType] = None
    event_source: Optional[EventSource] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, gt=0, le=1000)
    offset: int = Field(default=0, ge=0)