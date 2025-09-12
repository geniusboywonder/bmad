"""Human-in-the-Loop (HITL) request models."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class HitlStatus(str, Enum):
    """HITL request status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AMENDED = "amended"


class HitlAction(str, Enum):
    """HITL response action enumeration."""
    APPROVE = "approve"
    REJECT = "reject"
    AMEND = "amend"


class HitlHistoryEntry(BaseModel):
    """History entry for HITL request changes."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Entry timestamp")
    action: str = Field(description="Action taken")
    user_id: Optional[str] = Field(default=None, description="User who took the action")
    content: Optional[Dict[str, Any]] = Field(default=None, description="Content of the action")
    comment: Optional[str] = Field(default=None, description="Additional comment")


class HitlRequest(BaseModel):
    """Model for Human-in-the-Loop requests."""
    
    request_id: UUID = Field(default_factory=uuid4, description="Unique request identifier")
    project_id: UUID = Field(description="Project this request belongs to")
    task_id: UUID = Field(description="Task that triggered this request")
    question: str = Field(description="Question or request for the user")
    options: List[str] = Field(default_factory=list, description="Available response options")
    status: HitlStatus = Field(default=HitlStatus.PENDING, description="Current request status")
    user_response: Optional[str] = Field(default=None, description="User's response")
    amended_content: Optional[Dict[str, Any]] = Field(default=None, description="Amended content if action is amend")
    history: List[HitlHistoryEntry] = Field(default_factory=list, description="Request history log")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Request creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Request expiration timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )


class HitlResponse(BaseModel):
    """Model for Human-in-the-Loop responses."""
    
    request_id: UUID = Field(description="Request identifier this response belongs to")
    action: HitlAction = Field(description="Action taken in response")
    response_content: Optional[str] = Field(default=None, description="Response content")
    amended_data: Optional[Dict[str, Any]] = Field(default=None, description="Amended data if action is amend")
    comment: Optional[str] = Field(default=None, description="Additional comment")
    user_id: Optional[str] = Field(default=None, description="User who provided the response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )
