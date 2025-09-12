"""Handoff schema models for agent-to-agent communication."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class HandoffPhase(str, Enum):
    """Phases of the software development lifecycle."""
    ANALYSIS = "analysis"
    ARCHITECTURE = "architecture"
    CODING = "coding"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    REVIEW = "review"


class HandoffPriority(str, Enum):
    """Priority levels for handoff tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffSchema(BaseModel):
    """Schema for handoff information between agents."""
    
    from_agent: str = Field(description="Agent type that is handing off the task")
    to_agent: str = Field(description="Agent type that will receive the task")
    phase: HandoffPhase = Field(description="Current phase of development")
    instructions: str = Field(description="Specific instructions for the receiving agent")
    context_summary: str = Field(description="Summary of work completed so far")
    expected_outputs: List[str] = Field(description="Expected deliverables from the receiving agent")
    priority: HandoffPriority = Field(default=HandoffPriority.MEDIUM, description="Priority level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies that must be satisfied")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Criteria for accepting the work")
    
    class Config:
        use_enum_values = True