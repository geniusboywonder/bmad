"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .connection import Base
from app.models.task import TaskStatus
from app.models.agent import AgentType, AgentStatus
from app.models.context import ArtifactType
from app.models.hitl import HitlStatus


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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="event_logs")


class ProjectDB(Base):
    """Project database model."""
    
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    current_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"))
    last_activity = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContextArtifactDB(Base):
    """Context artifact database model."""
    
    __tablename__ = "context_artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    source_agent = Column(String(50), nullable=False)
    artifact_type = Column(SQLEnum(ArtifactType), nullable=False)
    content = Column(JSON, nullable=False)
    artifact_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    expiration_time = Column(DateTime)  # Alias for expires_at for compatibility
    responded_at = Column(DateTime)
    
    # Relationships
    project = relationship("ProjectDB", back_populates="hitl_requests")
