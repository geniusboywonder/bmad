"""Handoff schema for agent communication."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class HandoffSchema(BaseModel):
    """Generic JSON schema for structured handoffs between agents."""
    
    handoff_id: UUID = Field(description="Unique handoff identifier")
    from_agent: str = Field(description="Agent sending the handoff")
    to_agent: str = Field(description="Agent receiving the handoff")
    project_id: UUID = Field(description="Project this handoff belongs to")
    phase: str = Field(description="SDLC phase of the handoff")
    context_ids: List[UUID] = Field(description="Context artifacts to pass along")
    instructions: str = Field(description="Specific instructions for the receiving agent")
    expected_outputs: List[str] = Field(description="Expected output types")
    priority: int = Field(default=1, description="Handoff priority (1=highest)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional handoff metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Handoff creation timestamp")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
    )
