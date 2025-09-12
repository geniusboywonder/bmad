"""WebSocket event models and types."""

from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID


class EventType(str, Enum):
    """WebSocket event type enumeration."""
    AGENT_STATUS_CHANGE = "agent_status_change"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    HITL_REQUEST = "hitl_request"
    HITL_REQUEST_CREATED = "hitl_request_created"
    HITL_RESPONSE = "hitl_response"
    WORKFLOW_RESUMED = "workflow_resumed"
    ARTIFACT_CREATED = "artifact_created"
    WORKFLOW_EVENT = "workflow_event"
    ERROR = "error"


class WebSocketEvent(BaseModel):
    """WebSocket event model."""
    
    event_type: EventType = Field(description="Type of event")
    project_id: Optional[UUID] = Field(default=None, description="Project ID if applicable")
    task_id: Optional[UUID] = Field(default=None, description="Task ID if applicable")
    agent_type: Optional[str] = Field(default=None, description="Agent type if applicable")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    
    model_config = ConfigDict(use_enum_values=True)
    
    @field_serializer('project_id', 'task_id')
    def serialize_uuid(self, value: Optional[UUID]) -> Optional[str]:
        return str(value) if value is not None else None
    
    @field_serializer('timestamp')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()
