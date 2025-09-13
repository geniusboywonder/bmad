"""Task model for agent work units."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
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
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        """Validate that agent_type is a valid AgentType enum value."""
        from app.models.agent import AgentType
        valid_agent_types = [agent_type.value for agent_type in AgentType]
        if v not in valid_agent_types:
            raise ValueError(f'Invalid agent_type: {v}. Must be one of {valid_agent_types}')
        return v
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
