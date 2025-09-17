"""
Agent Conflict Models for BMAD Core Template System

This module defines Pydantic models for agent conflicts, resolution strategies,
and conflict tracking in multi-agent workflows.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field


class ConflictType(str, Enum):
    """Enumeration of conflict types that can occur between agents."""
    OUTPUT_CONTRADICTION = "output_contradiction"
    REQUIREMENT_MISMATCH = "requirement_mismatch"
    DESIGN_INCONSISTENCY = "design_inconsistency"
    IMPLEMENTATION_VIOLATION = "implementation_violation"
    RESOURCE_CONTENTION = "resource_contention"
    PRIORITY_CONFLICT = "priority_conflict"
    TIMING_CONFLICT = "timing_conflict"
    DEPENDENCY_VIOLATION = "dependency_violation"


class ConflictSeverity(str, Enum):
    """Enumeration of conflict severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    """Enumeration of conflict resolution statuses."""
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class ResolutionStrategy(str, Enum):
    """Enumeration of conflict resolution strategies."""
    AUTOMATIC_MERGE = "automatic_merge"
    MANUAL_OVERRIDE = "manual_override"
    COMPROMISE = "compromise"
    ESCALATION = "escalation"
    ROLLBACK = "rollback"
    SPLIT_WORK = "split_work"
    PRIORITY_BASED = "priority_based"


class ConflictParticipant(BaseModel):
    """Represents an agent or component involved in a conflict."""

    agent_type: str = Field(..., description="Type of agent involved")
    agent_id: Optional[str] = Field(None, description="Specific agent instance ID")
    role: str = Field(..., description="Role of the participant in the conflict")
    confidence_score: Optional[float] = Field(None, description="Confidence score of the participant's output")
    contribution_weight: float = Field(default=1.0, description="Weight of this participant's contribution")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConflictEvidence(BaseModel):
    """Evidence supporting a conflict detection."""

    artifact_id: str = Field(..., description="ID of the artifact containing conflicting information")
    artifact_type: str = Field(..., description="Type of artifact")
    source_agent: str = Field(..., description="Agent that created the artifact")
    conflicting_content: str = Field(..., description="The specific conflicting content")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the evidence")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConflictResolution(BaseModel):
    """Represents a proposed or applied resolution for a conflict."""

    strategy: ResolutionStrategy = Field(..., description="Resolution strategy used")
    resolver_agent: Optional[str] = Field(None, description="Agent that performed the resolution")
    resolution_details: Dict[str, Any] = Field(default_factory=dict, description="Details of the resolution")
    resolved_content: Optional[str] = Field(None, description="The resolved content after applying the strategy")
    affected_artifacts: List[str] = Field(default_factory=list, description="IDs of artifacts affected by resolution")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentConflict(BaseModel):
    """
    Complete model representing a conflict between agents in a workflow.

    This model captures all aspects of a conflict including detection,
    participants, evidence, resolution attempts, and final outcome.
    """

    conflict_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the conflict")
    project_id: str = Field(..., description="ID of the project where conflict occurred")
    workflow_id: str = Field(..., description="ID of the workflow where conflict occurred")
    task_id: Optional[str] = Field(None, description="ID of the task where conflict occurred")

    conflict_type: ConflictType = Field(..., description="Type of conflict detected")
    severity: ConflictSeverity = Field(default=ConflictSeverity.MEDIUM, description="Severity level of the conflict")
    status: ConflictStatus = Field(default=ConflictStatus.DETECTED, description="Current status of the conflict")

    title: str = Field(..., description="Human-readable title describing the conflict")
    description: str = Field(..., description="Detailed description of the conflict")

    participants: List[ConflictParticipant] = Field(default_factory=list, description="Agents involved in the conflict")
    evidence: List[ConflictEvidence] = Field(default_factory=list, description="Evidence supporting the conflict detection")

    detection_method: str = Field(default="automated", description="Method used to detect the conflict")
    detection_confidence: float = Field(default=0.0, description="Confidence score of the conflict detection")

    resolution_attempts: List[ConflictResolution] = Field(default_factory=list, description="Attempts made to resolve the conflict")
    final_resolution: Optional[ConflictResolution] = Field(None, description="Final resolution applied")

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = Field(None, description="Timestamp when conflict was resolved")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the conflict")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_participant(self, agent_type: str, role: str, **kwargs) -> None:
        """Add a participant to the conflict."""
        participant = ConflictParticipant(
            agent_type=agent_type,
            role=role,
            **kwargs
        )
        self.participants.append(participant)
        self._update_timestamp()

    def add_evidence(self, artifact_id: str, artifact_type: str, source_agent: str,
                    conflicting_content: str, **kwargs) -> None:
        """Add evidence to support the conflict."""
        evidence = ConflictEvidence(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            source_agent=source_agent,
            conflicting_content=conflicting_content,
            **kwargs
        )
        self.evidence.append(evidence)
        self._update_timestamp()

    def attempt_resolution(self, strategy: ResolutionStrategy, resolver_agent: str,
                          resolution_details: Dict[str, Any], **kwargs) -> None:
        """Record a resolution attempt."""
        resolution = ConflictResolution(
            strategy=strategy,
            resolver_agent=resolver_agent,
            resolution_details=resolution_details,
            **kwargs
        )
        self.resolution_attempts.append(resolution)
        self._update_timestamp()

    def mark_resolved(self, final_resolution: ConflictResolution) -> None:
        """Mark the conflict as resolved."""
        self.final_resolution = final_resolution
        self.status = ConflictStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc).isoformat()
        self._update_timestamp()

    def escalate(self, reason: str) -> None:
        """Escalate the conflict for manual intervention."""
        self.status = ConflictStatus.ESCALATED
        self.metadata["escalation_reason"] = reason
        self.metadata["escalated_at"] = datetime.now(timezone.utc).isoformat()
        self._update_timestamp()

    def dismiss(self, reason: str) -> None:
        """Dismiss the conflict as not requiring resolution."""
        self.status = ConflictStatus.DISMISSED
        self.metadata["dismissal_reason"] = reason
        self.metadata["dismissed_at"] = datetime.now(timezone.utc).isoformat()
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get a summary of the conflict for reporting."""
        return {
            "conflict_id": self.conflict_id,
            "type": self.conflict_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "participant_count": len(self.participants),
            "evidence_count": len(self.evidence),
            "resolution_attempts": len(self.resolution_attempts),
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "project_id": self.project_id,
            "workflow_id": self.workflow_id
        }

    def calculate_resolution_complexity(self) -> float:
        """Calculate the complexity of resolving this conflict."""
        # Base complexity from conflict type
        type_complexity = {
            ConflictType.OUTPUT_CONTRADICTION: 0.3,
            ConflictType.REQUIREMENT_MISMATCH: 0.4,
            ConflictType.DESIGN_INCONSISTENCY: 0.5,
            ConflictType.IMPLEMENTATION_VIOLATION: 0.6,
            ConflictType.RESOURCE_CONTENTION: 0.7,
            ConflictType.PRIORITY_CONFLICT: 0.5,
            ConflictType.TIMING_CONFLICT: 0.4,
            ConflictType.DEPENDENCY_VIOLATION: 0.8
        }

        # Severity multiplier
        severity_multiplier = {
            ConflictSeverity.LOW: 1.0,
            ConflictSeverity.MEDIUM: 1.2,
            ConflictSeverity.HIGH: 1.5,
            ConflictSeverity.CRITICAL: 2.0
        }

        # Participant complexity
        participant_complexity = min(len(self.participants) * 0.1, 0.5)

        # Evidence complexity
        evidence_complexity = min(len(self.evidence) * 0.05, 0.3)

        base_complexity = type_complexity.get(self.conflict_type, 0.5)
        severity_mult = severity_multiplier.get(self.severity, 1.2)

        total_complexity = (base_complexity * severity_mult) + participant_complexity + evidence_complexity

        return min(total_complexity, 1.0)  # Cap at 1.0

    def is_escalation_required(self) -> bool:
        """Determine if the conflict requires escalation."""
        # Critical severity always requires escalation
        if self.severity == ConflictSeverity.CRITICAL:
            return True

        # High severity with multiple failed resolution attempts
        if self.severity == ConflictSeverity.HIGH and len(self.resolution_attempts) >= 2:
            return True

        # Complex conflicts with high resolution complexity
        if self.calculate_resolution_complexity() > 0.7:
            return True

        # Conflicts that have been unresolved for too long
        if self.status == ConflictStatus.UNDER_REVIEW:
            created_time = datetime.fromisoformat(self.created_at)
            hours_since_creation = (datetime.now(timezone.utc) - created_time).total_seconds() / 3600
            if hours_since_creation > 24:  # 24 hours
                return True

        return False

    def get_recommended_resolution_strategy(self) -> ResolutionStrategy:
        """Get the recommended resolution strategy based on conflict characteristics."""

        # For critical conflicts, always escalate
        if self.severity == ConflictSeverity.CRITICAL:
            return ResolutionStrategy.ESCALATION

        # For simple contradictions, try automatic merge
        if self.conflict_type == ConflictType.OUTPUT_CONTRADICTION and len(self.participants) == 2:
            return ResolutionStrategy.AUTOMATIC_MERGE

        # For requirement mismatches, use compromise
        if self.conflict_type == ConflictType.REQUIREMENT_MISMATCH:
            return ResolutionStrategy.COMPROMISE

        # For resource contentions, use priority-based resolution
        if self.conflict_type == ConflictType.RESOURCE_CONTENTION:
            return ResolutionStrategy.PRIORITY_BASED

        # For dependency violations, rollback might be necessary
        if self.conflict_type == ConflictType.DEPENDENCY_VIOLATION:
            return ResolutionStrategy.ROLLBACK

        # Default to manual override for complex cases
        return ResolutionStrategy.MANUAL_OVERRIDE


class ConflictResolutionResult(BaseModel):
    """Result of a conflict resolution attempt."""

    success: bool = Field(..., description="Whether the resolution was successful")
    resolution_strategy: ResolutionStrategy = Field(..., description="Strategy used for resolution")
    resolved_conflict_id: str = Field(..., description="ID of the resolved conflict")
    new_artifacts: List[str] = Field(default_factory=list, description="IDs of newly created artifacts")
    modified_artifacts: List[str] = Field(default_factory=list, description="IDs of modified artifacts")
    resolution_details: Dict[str, Any] = Field(default_factory=dict, description="Details of the resolution process")
    confidence_score: float = Field(default=0.0, description="Confidence in the resolution")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ConflictPattern(BaseModel):
    """Pattern for detecting recurring conflicts."""

    pattern_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the pattern")
    pattern_type: ConflictType = Field(..., description="Type of conflicts this pattern detects")
    pattern_description: str = Field(..., description="Description of the conflict pattern")
    detection_rules: Dict[str, Any] = Field(..., description="Rules for detecting this pattern")
    frequency_threshold: int = Field(default=3, description="Minimum frequency to be considered a pattern")
    occurrences: List[str] = Field(default_factory=list, description="IDs of conflicts matching this pattern")
    prevention_strategy: Optional[str] = Field(None, description="Strategy to prevent this pattern")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add_occurrence(self, conflict_id: str) -> None:
        """Add a conflict occurrence to this pattern."""
        if conflict_id not in self.occurrences:
            self.occurrences.append(conflict_id)

    def get_frequency(self) -> int:
        """Get the frequency of this pattern."""
        return len(self.occurrences)

    def is_significant(self) -> bool:
        """Check if this pattern is significant enough to warrant attention."""
        return self.get_frequency() >= self.frequency_threshold
