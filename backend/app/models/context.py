"""Context artifact model for persistent memory."""

from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ArtifactType(str, Enum):
    """Artifact type enumeration."""
    PROJECT_PLAN = "project_plan"
    SOFTWARE_SPECIFICATION = "software_specification"
    IMPLEMENTATION_PLAN = "implementation_plan"
    SOURCE_CODE = "source_code"
    TEST_RESULTS = "test_results"
    DEPLOYMENT_LOG = "deployment_log"
    USER_INPUT = "user_input"
    AGENT_OUTPUT = "agent_output"
    HITL_RESPONSE = "hitl_response"


class ContextArtifact(BaseModel):
    """Represents a piece of information stored in the persistent memory."""
    
    context_id: UUID = Field(default_factory=uuid4, description="Unique context identifier")
    project_id: UUID = Field(description="Project this artifact belongs to")
    source_agent: str = Field(description="Agent that created this artifact")
    artifact_type: ArtifactType = Field(description="Type of artifact")
    content: Dict[str, Any] = Field(description="Artifact content data")
    artifact_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
