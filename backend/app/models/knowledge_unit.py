"""
Knowledge Unit Model for BMAD Core Template System

This module defines the KnowledgeUnit model for managing knowledge units
extracted from context artifacts in the mixed-granularity system.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeUnit(BaseModel):
    """
    Knowledge unit model for storing and managing extracted knowledge.

    This model represents knowledge units that are extracted from context artifacts
    and used for intelligent context injection and relationship mapping.
    """

    id: str = Field(..., description="Unique identifier for the knowledge unit")
    concept: str = Field(..., description="The concept this unit represents")
    type: str = Field(..., description="Type of concept (technical_term, domain_concept, etc.)")
    content: str = Field(..., description="Content/description of the knowledge")
    relationships: List[str] = Field(default_factory=list, description="Relationships to other concepts")
    usage_count: int = Field(default=0, description="Number of times this unit has been used")
    last_accessed: Optional[str] = Field(default=None, description="Last access timestamp")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def track_usage(self) -> None:
        """Track usage of this knowledge unit."""
        from datetime import datetime
        self.usage_count += 1
        self.last_accessed = datetime.now().isoformat()

    def add_relationship(self, target_concept: str) -> None:
        """Add a relationship to another concept."""
        if target_concept not in self.relationships:
            self.relationships.append(target_concept)

    def remove_relationship(self, target_concept: str) -> None:
        """Remove a relationship to another concept."""
        if target_concept in self.relationships:
            self.relationships.remove(target_concept)
