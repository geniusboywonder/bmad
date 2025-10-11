"""SQLAlchemy database models."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .connection import Base
from app.models.task import TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.context import ArtifactType
from app.models.hitl import HitlStatus
from sqlalchemy import Numeric, Boolean


def utcnow():
    """Return timezone-aware UTC datetime for SQLAlchemy defaults."""
    return datetime.now(timezone.utc)


class EventLogDB(Base):
    """Event log database model for audit trail."""
    
    __tablename__ = "event_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    hitl_request_id = Column(UUID(as_uuid=True), ForeignKey("hitl_requests.id"), nullable=True)
    event_type = Column(String(100), nullable=False)  # e.g., 'task_created', 'hitl_response', 'task_failed'
    event_source = Column(String(100), nullable=False)  # e.g., 'agent', 'user', 'system'
    event_data = Column(JSON, nullable=False)  # Full payload/context data
    event_metadata = Column(JSON, default=dict)  # Additional metadata
    created_at = Column(DateTime, default=utcnow)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="event_logs")


class ProjectDB(Base):
    """Project database model."""
    
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    current_phase = Column(String(50), default="discovery", nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    tasks = relationship("TaskDB", back_populates="project")
    context_artifacts = relationship("ContextArtifactDB", back_populates="project")
    hitl_requests = relationship("HitlRequestDB", back_populates="project")
    event_logs = relationship("EventLogDB", back_populates="project")


class TaskDB(Base):
    """Task database model."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    context_ids = Column(JSON, default=list)
    instructions = Column(Text, nullable=False)
    output = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="tasks")


class AgentStatusDB(Base):
    """Agent status database model."""
    
    __tablename__ = "agent_status"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type = Column(SQLEnum(AgentType), nullable=False, unique=True)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.IDLE)
    current_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    last_activity = Column(DateTime, default=utcnow)
    error_message = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class ContextArtifactDB(Base):
    """Context artifact database model."""
    
    __tablename__ = "context_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    source_agent = Column(String(50), nullable=False)
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    content = Column(JSON, nullable=False)
    artifact_metadata = Column(JSON)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="context_artifacts")


class HitlRequestDB(Base):
    """HITL request database model."""
    
    __tablename__ = "hitl_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, default=list)
    status = Column(SQLEnum(HitlStatus), default=HitlStatus.PENDING)
    user_response = Column(Text)
    response_comment = Column(Text)
    amended_content = Column(JSON)
    history = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    expires_at = Column(DateTime)
    expiration_time = Column(DateTime)  # Alias for expires_at for compatibility
    responded_at = Column(DateTime)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="hitl_requests")


class HitlAgentApprovalDB(Base):
    """HITL agent approval database model for mandatory safety controls."""

    __tablename__ = "hitl_agent_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    request_type = Column(String(50), nullable=False)  # 'PRE_EXECUTION', 'RESPONSE_APPROVAL', 'NEXT_STEP'
    request_data = Column(JSON, nullable=False)
    status = Column(String(50), default="PENDING")  # 'PENDING', 'APPROVED', 'REJECTED', 'EXPIRED'
    estimated_tokens = Column(Integer)
    estimated_cost = Column(Numeric(10, 4), nullable=True)
    user_response = Column(Text)
    user_comment = Column(Text)
    expires_at = Column(DateTime)
    responded_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB")
    task = relationship("TaskDB")


class AgentBudgetControlDB(Base):
    """Agent budget control database model for token limits."""

    __tablename__ = "agent_budget_controls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    daily_token_limit = Column(Integer, default=10000)
    session_token_limit = Column(Integer, default=2000)
    tokens_used_today = Column(Integer, default=0)
    tokens_used_session = Column(Integer, default=0)
    budget_reset_at = Column(DateTime, default=utcnow)
    emergency_stop_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB")


class EmergencyStopDB(Base):
    """Emergency stop database model for immediate agent halting."""

    __tablename__ = "emergency_stops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))  # NULL for global stops
    agent_type = Column(String(50))  # NULL for global stops
    stop_reason = Column(String(200), nullable=False)
    triggered_by = Column(String(100), nullable=False)  # 'USER', 'BUDGET', 'REPETITION', 'ERROR'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    deactivated_at = Column(DateTime)


class ResponseApprovalDB(Base):
    """Response approval database model for advanced HITL safety controls."""

    __tablename__ = "response_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("hitl_agent_approvals.id"), nullable=False)

    # Response content and metadata
    response_content = Column(JSON, nullable=False)
    response_metadata = Column(JSON, default=dict)

    # Safety analysis results
    content_safety_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    code_validation_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    quality_metrics = Column(JSON, default=dict)

    # Approval status
    status = Column(String(50), default="PENDING")  # 'PENDING', 'APPROVED', 'REJECTED', 'AUTO_APPROVED'
    approved_by = Column(String(100))
    approval_reason = Column(Text)
    auto_approved = Column(Boolean, default=False)  # True if auto-approved

    # Timestamps
    created_at = Column(DateTime, default=utcnow)
    approved_at = Column(DateTime)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB")
    task = relationship("TaskDB")
    approval_request = relationship("HitlAgentApprovalDB")


class RecoverySessionDB(Base):
    """Recovery session database model for systematic recovery procedures."""

    __tablename__ = "recovery_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    agent_type = Column(String(50), nullable=False)

    # Recovery context
    failure_reason = Column(String(200), nullable=False)
    failure_context = Column(JSON, nullable=False)
    recovery_strategy = Column(String(100), nullable=False)  # 'ROLLBACK', 'RETRY', 'CONTINUE', 'ABORT'

    # Recovery steps
    recovery_steps = Column(JSON, default=list)  # List of recovery steps with status
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)

    # Recovery status
    status = Column(String(50), default="INITIATED")  # 'INITIATED', 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    recovery_result = Column(JSON)

    # Emergency stop reference (if recovery from emergency stop)
    emergency_stop_id = Column(UUID(as_uuid=True), ForeignKey("emergency_stops.id"))

    # Timestamps
    created_at = Column(DateTime, default=utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB")
    task = relationship("TaskDB")
    emergency_stop = relationship("EmergencyStopDB")


class WebSocketNotificationDB(Base):
    """WebSocket notification database model for advanced event tracking."""

    __tablename__ = "websocket_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    event_type = Column(String(100), nullable=False)
    priority = Column(String(20), default="NORMAL")  # 'LOW', 'NORMAL', 'HIGH', 'CRITICAL'
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    event_data = Column(JSON, default=dict)

    # Delivery tracking
    delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime)
    delivery_attempts = Column(Integer, default=0)

    # Expiration
    expires_at = Column(DateTime)
    expired = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB")


class WorkflowStateDB(Base):
    """Workflow state database model for persistence and recovery."""

    __tablename__ = "workflow_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    workflow_id = Column(String(100), nullable=False)
    execution_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, paused, cancelled
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=0)
    steps_data = Column(JSON, default=list)  # List of step execution states
    context_data = Column(JSON, default=dict)  # Workflow execution context
    created_artifacts = Column(JSON, default=list)  # List of created artifact IDs
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    project = relationship("ProjectDB", back_populates="workflow_states")


# Add workflow_states relationship to ProjectDB
ProjectDB.workflow_states = relationship("WorkflowStateDB", back_populates="project")
