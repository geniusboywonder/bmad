"""Agent status and type models."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class AgentType(str, Enum):
    """Agent type enumeration."""
    ORCHESTRATOR = "orchestrator"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    CODER = "coder"
    TESTER = "tester"
    DEPLOYER = "deployer"


class AgentStatus(str, Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    WORKING = "working"
    WAITING_FOR_HITL = "waiting_for_hitl"
    ERROR = "error"


class AgentStatusModel(BaseModel):
    """Tracks the real-time status of each agent."""
    
    agent_type: AgentType = Field(description="Type of agent")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current agent status")
    current_task_id: Optional[UUID] = Field(default=None, description="Currently assigned task ID")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if status is error")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
