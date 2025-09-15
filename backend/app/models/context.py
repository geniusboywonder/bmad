"""Context artifact model for persistent memory."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from uuid import UUID, uuid4
from app.models.agent import AgentType


class ArtifactType(str, Enum):
    """Artifact type enumeration."""
    PROJECT_PLAN = "project_plan"
    SOFTWARE_SPECIFICATION = "software_specification"
    IMPLEMENTATION_PLAN = "implementation_plan"
    SYSTEM_ARCHITECTURE = "system_architecture"
    SOURCE_CODE = "source_code"
    TEST_RESULTS = "test_results"
    DEPLOYMENT_LOG = "deployment_log"
    DEPLOYMENT_PACKAGE = "deployment_package"
    USER_INPUT = "user_input"
    AGENT_OUTPUT = "agent_output"
    HITL_RESPONSE = "hitl_response"


class ContextArtifact(BaseModel):
    """Represents a piece of information stored in the persistent memory."""
    
    context_id: UUID = Field(default_factory=uuid4, description="Unique context identifier")
    project_id: UUID = Field(description="Project this artifact belongs to")
    source_agent: AgentType = Field(description="Agent that created this artifact")
    artifact_type: ArtifactType = Field(description="Type of artifact")
    content: Dict[str, Any] = Field(description="Artifact content data")
    artifact_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )
    
    @field_serializer('context_id', 'project_id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
    
    @field_serializer('created_at', 'updated_at')  
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()
