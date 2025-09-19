"""
Context Artifact Model for BMAD Core Template System

This module defines the ContextArtifact model for managing context artifacts
in the mixed-granularity context store system.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ContextArtifact(BaseModel):
    """
    Context artifact model for storing and managing context artifacts.

    This model represents artifacts that can be stored, retrieved, and managed
    within the context store system with mixed-granularity support.
    """

    id: str = Field(..., description="Unique identifier for the artifact")
    project_id: str = Field(..., description="Project ID this artifact belongs to")
    type: str = Field(..., description="Type of artifact (requirements, architecture, etc.)")
    content: str = Field(..., description="Content of the artifact")
    granularity: str = Field(default="atomic", description="Granularity level (atomic, sectioned, conceptual)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "content": self.content,
            "granularity": self.granularity,
            "metadata": self.metadata
        }
