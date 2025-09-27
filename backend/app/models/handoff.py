"""Handoff schema for agent communication."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_serializer
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
    is_group_chat: bool = Field(default=False, description="Whether this is a group chat handoff")
    group_chat_agents: Optional[List[str]] = Field(default=None, description="Agents in the group chat")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional handoff metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Handoff creation timestamp")
    
    model_config = ConfigDict()

    @field_serializer('created_at')
    def serialize_datetime(self, dt: datetime) -> str:
        return dt.isoformat()

    @field_serializer('handoff_id', 'project_id')
    def serialize_uuid(self, uuid_val: UUID) -> str:
        return str(uuid_val)

    @field_serializer('context_ids')
    def serialize_context_ids(self, uuid_list: List[UUID]) -> List[str]:
        return [str(uuid_val) for uuid_val in uuid_list]
