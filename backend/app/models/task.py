"""Task model for agent work units."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from uuid import UUID, uuid4


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Represents a single unit of work for an agent."""

    task_id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    project_id: UUID = Field(description="Project this task belongs to")
    agent_type: str = Field(description="Type of agent assigned to this task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    context_ids: List[UUID] = Field(default_factory=list, description="Context artifacts to use")
    instructions: str = Field(description="Detailed instructions for the agent")
    output: Optional[Dict[str, Any]] = Field(default=None, description="Task output data")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")

    @field_validator('agent_type')
    @classmethod
    def validate_agent_type(cls, v):
        """Validate that agent_type is a valid AgentType enum value."""
        from app.models.agent import AgentType
        valid_agent_types = [agent_type.value for agent_type in AgentType]
        if v not in valid_agent_types:
            raise ValueError(f'Invalid agent_type: {v}. Must be one of {valid_agent_types}')
        return v

    model_config = ConfigDict(use_enum_values=True)

    @field_serializer('created_at', 'updated_at', 'started_at', 'completed_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None

    @field_serializer('task_id', 'project_id')
    def serialize_uuid(self, uuid_val: UUID) -> str:
        return str(uuid_val)

    @field_serializer('context_ids')
    def serialize_context_ids(self, uuid_list: List[UUID]) -> List[str]:
        return [str(uuid_val) for uuid_val in uuid_list]

    @field_validator('task_id', 'project_id', mode='before')
    @classmethod
    def validate_uuid_fields(cls, v):
        """Ensure UUID fields are properly converted from strings."""
        if isinstance(v, str):
            return UUID(v)
        return v

    @field_validator('context_ids', mode='before')
    @classmethod
    def validate_context_ids(cls, v):
        """Ensure context_ids are UUID objects."""
        if isinstance(v, list):
            return [UUID(str(cid)) if not isinstance(cid, UUID) else cid for cid in v]
        return v
