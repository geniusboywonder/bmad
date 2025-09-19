"""HITL Request Models for Human-in-the-Loop interactions.

This module defines the data models for HITL requests, responses, and related
functionality for the BMAD Enterprise AI Platform.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4


class HITLRequestType(Enum):
    """Types of HITL requests."""
    APPROVAL = "approval"
    REVIEW = "review"
    DECISION = "decision"
    VALIDATION = "validation"
    ESCALATION = "escalation"


class HITLRequestStatus(Enum):
    """Status of HITL requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class HITLRequestPriority(Enum):
    """Priority levels for HITL requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HITLRequest(BaseModel):
    """HITL request model for human intervention requests."""
    
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    task_id: Optional[UUID] = None
    agent_type: str
    request_type: HITLRequestType
    status: HITLRequestStatus = HITLRequestStatus.PENDING
    priority: HITLRequestPriority = HITLRequestPriority.MEDIUM
    
    title: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Request data
    request_data: Dict[str, Any] = Field(default_factory=dict)
    options: List[str] = Field(default_factory=list)
    
    # Response data
    response: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    response_comment: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    responded_by: Optional[str] = None
    
    # Escalation
    escalation_count: int = 0
    escalated_at: Optional[datetime] = None
    escalated_to: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class HITLResponse(BaseModel):
    """HITL response model for human responses to requests."""
    
    request_id: UUID
    response: str
    response_data: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None
    responded_by: str
    responded_at: datetime = Field(default_factory=datetime.utcnow)


class HITLEscalation(BaseModel):
    """HITL escalation model for escalated requests."""
    
    request_id: UUID
    escalated_from: str
    escalated_to: str
    escalation_reason: str
    escalated_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None


class HITLMetrics(BaseModel):
    """HITL metrics model for tracking HITL performance."""
    
    project_id: UUID
    total_requests: int = 0
    pending_requests: int = 0
    approved_requests: int = 0
    rejected_requests: int = 0
    escalated_requests: int = 0
    expired_requests: int = 0
    
    average_response_time_minutes: Optional[float] = None
    approval_rate: float = 0.0
    escalation_rate: float = 0.0
    
    calculated_at: datetime = Field(default_factory=datetime.utcnow)