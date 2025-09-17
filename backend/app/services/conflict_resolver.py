"""
Conflict Resolution Service for BMAD Core Template System

This module implements intelligent conflict detection and resolution for multi-agent
workflows, including automatic resolution strategies and escalation mechanisms.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timezone
from uuid import UUID, uuid4
import structlog
import difflib
import json

from ..models.agent_conflict import (
    AgentConflict,
    ConflictType,
    ConflictSeverity,
    ConflictStatus,
    ResolutionStrategy,
    ConflictParticipant,
    ConflictEvidence,
    ConflictResolution,
    ConflictResolutionResult,
    ConflictPattern
)
from ..models.context import ContextArtifact
from ..models.task import Task
from ..services.context_store import ContextStoreService
from ..services.autogen_service import AutoGenService
from ..services.workflow_engine import WorkflowExecutionEngine

logger = structlog.get_logger(__name__)


class ConflictResolverService:
    """
    Service for detecting, analyzing, and resolving conflicts in multi-agent workflows.

    This service provides comprehensive conflict management including:
    - Automated conflict detection
    - Intelligent resolution strategies
    - Escalation mechanisms
    - Pattern recognition and prevention
    - Conflict tracking and reporting
    """

    def __init__(self, context_store: ContextStoreService, autogen_service: AutoGenService):
        self.context_store = context_store
        self.autogen_service = autogen_service

        # Conflict tracking
        self.active_conflicts: Dict[str, AgentConflict] = {}
        self.conflict_patterns: Dict[str, ConflictPattern] = {}

        # Resolution strategies
        self.resolution_strategies = {
            ResolutionStrategy.AUTOMATIC_MERGE: self._resolve_automatic_merge,
            ResolutionStrategy.MANUAL_OVERRIDE: self._resolve_manual_override,
            ResolutionStrategy.COMPROMISE: self._resolve_compromise,
            ResolutionStrategy.ESCALATION: self._resolve_escalation,
            ResolutionStrategy.ROLLBACK: self._resolve_rollback,
            ResolutionStrategy.SPLIT_WORK: self._resolve_split_work,
            ResolutionStrategy.PRIORITY_BASED: self._resolve_priority_based
        }

        logger.info("Conflict resolver service initialized")

    async def detect_conflicts(
        self,
        project_id: str,
        workflow_id: str,
        artifacts: List[ContextArtifact],
        tasks: List[Task]
    ) -> List[AgentConflict]:
        """
        Detect conflicts in project artifacts and tasks.

        Args:
            project_id: ID of the project to analyze
            workflow_id: ID of the workflow
            artifacts: List of context artifacts to analyze
            tasks: List of tasks to analyze

        Returns:
            List of detected conflicts
        """
        detected_conflicts = []

        logger.info("Starting conflict detection",
                   project_id=project_id,
                   workflow_id=workflow_id,
                   artifact_count=len(artifacts),
                   task_count=len(tasks))

        # Detect output contradictions
        output_conflicts = await self._detect_output_contradictions(artifacts, project_id, workflow_id)
        detected_conflicts.extend(output_conflicts)

        # Detect requirement mismatches
        requirement_conflicts = await self._detect_requirement_mismatches(artifacts, project_id, workflow_id)
        detected_conflicts.extend(requirement_conflicts)

        # Detect design inconsistencies
        design_conflicts = await self._detect_design_inconsistencies(artifacts, project_id, workflow_id)
        detected_conflicts.extend(design_conflicts)

        # Detect implementation violations
        implementation_conflicts = await self._detect_implementation_violations(artifacts, tasks, project_id, workflow_id)
        detected_conflicts.extend(implementation_conflicts)

        # Detect resource contentions
        resource_conflicts = await self._detect_resource_contentions(tasks, project_id, workflow_id)
        detected_conflicts.extend(resource_conflicts)

        # Detect dependency violations
        dependency_conflicts = await self._detect_dependency_violations(artifacts, tasks, project_id, workflow_id)
        detected_conflicts.extend(dependency_conflicts)

        # Register detected conflicts
        for conflict in detected_conflicts:
            self.active_conflicts[conflict.conflict_id] = conflict

            # Check for patterns
            await self._check_conflict_patterns(conflict)

        logger.info("Conflict detection completed",
                   detected_conflicts=len(detected_conflicts),
                   project_id=project_id)

        return detected_conflicts

    async def resolve_conflict(
        self,
        conflict_id: str,
        preferred_strategy: Optional[ResolutionStrategy] = None
    ) -> ConflictResolutionResult:
        """
        Attempt to resolve a detected conflict.

        Args:
            conflict_id: ID of the conflict to resolve
            preferred_strategy: Preferred resolution strategy (optional)

        Returns:
            Result of the resolution attempt
        """
        if conflict_id not in self.active_conflicts:
            raise ValueError(f"Conflict {conflict_id} not found")

        conflict = self.active_conflicts[conflict_id]

        logger.info("Attempting conflict resolution",
                   conflict_id=conflict_id,
                   conflict_type=conflict.conflict_type.value,
                   severity=conflict.severity.value)

        # Determine resolution strategy
        strategy = preferred_strategy or conflict.get_recommended_resolution_strategy()

        # Check if escalation is required
        if conflict.is_escalation_required():
            strategy = ResolutionStrategy.ESCALATION

        # Execute resolution strategy
        try:
            resolution_result = await self._execute_resolution_strategy(conflict, strategy)

            if resolution_result.success:
                # Mark conflict as resolved
                final_resolution = ConflictResolution(
                    strategy=strategy,
                    resolver_agent="conflict_resolver",
                    resolution_details=resolution_result.resolution_details,
                    resolved_content=resolution_result.resolution_details.get("resolved_content"),
                    affected_artifacts=resolution_result.modified_artifacts + resolution_result.new_artifacts
                )
                conflict.mark_resolved(final_resolution)

                logger.info("Conflict resolved successfully",
                           conflict_id=conflict_id,
                           strategy=strategy.value,
                           affected_artifacts=len(final_resolution.affected_artifacts))

            else:
                # Record failed resolution attempt
                conflict.attempt_resolution(
                    strategy=strategy,
                    resolver_agent="conflict_resolver",
                    resolution_details={"error": "Resolution failed", "details": resolution_result.resolution_details}
                )

                # Check if escalation is needed
                if conflict.is_escalation_required():
                    conflict.escalate("Multiple resolution attempts failed")
                    logger.warning("Conflict escalated due to failed resolution",
                                 conflict_id=conflict_id,
                                 attempts=len(conflict.resolution_attempts))

            return resolution_result

        except Exception as e:
            logger.error("Conflict resolution failed",
                        conflict_id=conflict_id,
                        strategy=strategy.value,
                        error=str(e))

            # Record failed attempt
            conflict.attempt_resolution(
                strategy=strategy,
                resolver_agent="conflict_resolver",
                resolution_details={"error": str(e)}
            )

            return ConflictResolutionResult(
                success=False,
                resolution_strategy=strategy,
                resolved_conflict_id=conflict_id,
                resolution_details={"error": str(e)}
            )

    async def _detect_output_contradictions(
        self,
        artifacts: List[ContextArtifact],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect contradictions in agent outputs."""
        conflicts = []

        # Group artifacts by type
        artifacts_by_type = {}
        for artifact in artifacts:
            if artifact.artifact_type not in artifacts_by_type:
                artifacts_by_type[artifact.artifact_type] = []
            artifacts_by_type[artifact.artifact_type].append(artifact)

        # Check for contradictions within each type
        for artifact_type, type_artifacts in artifacts_by_type.items():
            if len(type_artifacts) < 2:
                continue

            # Compare artifacts for contradictions
            for i, artifact1 in enumerate(type_artifacts):
                for j, artifact2 in enumerate(type_artifacts[i+1:], i+1):
                    similarity = self._calculate_content_similarity(
                        artifact1.content, artifact2.content
                    )

                    # Low similarity might indicate contradiction
                    if similarity < 0.5:  # Less than 50% similar
                        conflict = AgentConflict(
                            project_id=project_id,
                            workflow_id=workflow_id,
                            conflict_type=ConflictType.OUTPUT_CONTRADICTION,
                            severity=ConflictSeverity.MEDIUM,
                            title=f"Output contradiction in {artifact_type}",
                            description=f"Conflicting outputs detected between {artifact1.source_agent} and {artifact2.source_agent}",
                            detection_method="content_similarity",
                            detection_confidence=1.0 - similarity
                        )

                        # Add participants
                        conflict.add_participant(
                            agent_type=artifact1.source_agent,
                            role="primary_contributor",
                            confidence_score=0.8
                        )
                        conflict.add_participant(
                            agent_type=artifact2.source_agent,
                            role="conflicting_contributor",
                            confidence_score=0.8
                        )

                        # Add evidence
                        conflict.add_evidence(
                            artifact_id=str(artifact1.context_id),
                            artifact_type=artifact1.artifact_type,
                            source_agent=artifact1.source_agent,
                            conflicting_content=artifact1.content[:200] + "...",
                            context={"similarity_score": similarity}
                        )
                        conflict.add_evidence(
                            artifact_id=str(artifact2.context_id),
                            artifact_type=artifact2.artifact_type,
                            source_agent=artifact2.source_agent,
                            conflicting_content=artifact2.content[:200] + "...",
                            context={"similarity_score": similarity}
                        )

                        conflicts.append(conflict)

        return conflicts

    async def _detect_requirement_mismatches(
        self,
        artifacts: List[ContextArtifact],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect mismatches in requirements across artifacts."""
        conflicts = []

        # Find requirement-related artifacts
        req_artifacts = [a for a in artifacts if "requirement" in a.artifact_type.lower() or "software_specification" in a.artifact_type.lower()]

        if len(req_artifacts) < 2:
            return conflicts

        # Check for requirement conflicts
        for i, artifact1 in enumerate(req_artifacts):
            for j, artifact2 in enumerate(req_artifacts[i+1:], i+1):
                # Look for conflicting requirements
                conflicts_found = self._analyze_requirement_conflicts(
                    artifact1.content, artifact2.content
                )

                if conflicts_found:
                    conflict = AgentConflict(
                        project_id=project_id,
                        workflow_id=workflow_id,
                        conflict_type=ConflictType.REQUIREMENT_MISMATCH,
                        severity=ConflictSeverity.HIGH,
                        title="Requirement mismatch detected",
                        description=f"Conflicting requirements between {artifact1.source_agent} and {artifact2.source_agent}",
                        detection_method="requirement_analysis",
                        detection_confidence=0.9
                    )

                    conflict.add_participant(artifact1.source_agent, "requirement_author")
                    conflict.add_participant(artifact2.source_agent, "requirement_author")

                    conflict.add_evidence(
                        artifact_id=str(artifact1.context_id),
                        artifact_type=artifact1.artifact_type,
                        source_agent=artifact1.source_agent,
                        conflicting_content=str(conflicts_found)
                    )
                    conflict.add_evidence(
                        artifact_id=str(artifact2.context_id),
                        artifact_type=artifact2.artifact_type,
                        source_agent=artifact2.source_agent,
                        conflicting_content=str(conflicts_found)
                    )

                    conflicts.append(conflict)

        return conflicts

    async def _detect_design_inconsistencies(
        self,
        artifacts: List[ContextArtifact],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect inconsistencies in design artifacts."""
        conflicts = []

        # Find design-related artifacts
        design_artifacts = [a for a in artifacts if any(keyword in a.artifact_type.lower()
                                                       for keyword in ["design", "architecture", "api", "model"])]

        if len(design_artifacts) < 2:
            return conflicts

        # Check for design inconsistencies
        for i, artifact1 in enumerate(design_artifacts):
            for j, artifact2 in enumerate(design_artifacts[i+1:], i+1):
                inconsistencies = self._analyze_design_inconsistencies(
                    artifact1.content, artifact2.content
                )

                if inconsistencies:
                    conflict = AgentConflict(
                        project_id=project_id,
                        workflow_id=workflow_id,
                        conflict_type=ConflictType.DESIGN_INCONSISTENCY,
                        severity=ConflictSeverity.HIGH,
                        title="Design inconsistency detected",
                        description=f"Inconsistent design elements between {artifact1.source_agent} and {artifact2.source_agent}",
                        detection_method="design_analysis",
                        detection_confidence=0.85
                    )

                    conflict.add_participant(artifact1.source_agent, "design_contributor")
                    conflict.add_participant(artifact2.source_agent, "design_contributor")

                    conflict.add_evidence(
                        artifact_id=str(artifact1.context_id),
                        artifact_type=artifact1.artifact_type,
                        source_agent=artifact1.source_agent,
                        conflicting_content=str(inconsistencies)
                    )
                    conflict.add_evidence(
                        artifact_id=str(artifact2.context_id),
                        artifact_type=artifact2.artifact_type,
                        source_agent=artifact2.source_agent,
                        conflicting_content=str(inconsistencies)
                    )

                    conflicts.append(conflict)

        return conflicts

    async def _detect_implementation_violations(
        self,
        artifacts: List[ContextArtifact],
        tasks: List[Task],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect violations between implementation and design/requirements."""
        conflicts = []

        # Find implementation artifacts
        impl_artifacts = [a for a in artifacts if "code" in a.artifact_type.lower() or "implementation" in a.artifact_type.lower()]

        # Find design/requirement artifacts
        design_req_artifacts = [a for a in artifacts if any(keyword in a.artifact_type.lower()
                                                          for keyword in ["design", "requirement", "architecture", "api"])]

        for impl_artifact in impl_artifacts:
            for design_artifact in design_req_artifacts:
                violations = self._analyze_implementation_violations(
                    impl_artifact.content, design_artifact.content
                )

                if violations:
                    conflict = AgentConflict(
                        project_id=project_id,
                        workflow_id=workflow_id,
                        conflict_type=ConflictType.IMPLEMENTATION_VIOLATION,
                        severity=ConflictSeverity.CRITICAL,
                        title="Implementation violation detected",
                        description=f"Implementation deviates from design/requirements",
                        detection_method="implementation_analysis",
                        detection_confidence=0.95
                    )

                    conflict.add_participant(impl_artifact.source_agent, "implementer")
                    conflict.add_participant(design_artifact.source_agent, "designer")

                    conflict.add_evidence(
                        artifact_id=str(impl_artifact.context_id),
                        artifact_type=impl_artifact.artifact_type,
                        source_agent=impl_artifact.source_agent,
                        conflicting_content=str(violations)
                    )
                    conflict.add_evidence(
                        artifact_id=str(design_artifact.context_id),
                        artifact_type=design_artifact.artifact_type,
                        source_agent=design_artifact.source_agent,
                        conflicting_content="Design/requirements specification"
                    )

                    conflicts.append(conflict)

        return conflicts

    async def _detect_resource_contentions(
        self,
        tasks: List[Task],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect resource contentions between tasks."""
        conflicts = []

        # Group tasks by resource usage patterns
        resource_usage = {}
        for task in tasks:
            # Simple resource detection based on task instructions
            resources = self._extract_resource_requirements(task.instructions)
            for resource in resources:
                if resource not in resource_usage:
                    resource_usage[resource] = []
                resource_usage[resource].append(task)

        # Check for contentions
        for resource, contending_tasks in resource_usage.items():
            if len(contending_tasks) > 1:
                # Check if tasks overlap in time
                overlapping_tasks = self._find_overlapping_tasks(contending_tasks)

                if overlapping_tasks:
                    conflict = AgentConflict(
                        project_id=project_id,
                        workflow_id=workflow_id,
                        conflict_type=ConflictType.RESOURCE_CONTENTION,
                        severity=ConflictSeverity.MEDIUM,
                        title=f"Resource contention: {resource}",
                        description=f"Multiple tasks contending for resource: {resource}",
                        detection_method="resource_analysis",
                        detection_confidence=0.8
                    )

                    for task in overlapping_tasks:
                        conflict.add_participant(task.agent_type, "resource_user")

                    # Add evidence for each contending task
                    for task in overlapping_tasks:
                        conflict.add_evidence(
                            artifact_id=str(task.task_id),
                            artifact_type="task",
                            source_agent=task.agent_type,
                            conflicting_content=f"Requires resource: {resource}",
                            context={"task_instructions": task.instructions}
                        )

                    conflicts.append(conflict)

        return conflicts

    async def _detect_dependency_violations(
        self,
        artifacts: List[ContextArtifact],
        tasks: List[Task],
        project_id: str,
        workflow_id: str
    ) -> List[AgentConflict]:
        """Detect dependency violations in task execution."""
        conflicts = []

        # Analyze task dependencies
        for task in tasks:
            # Check if task depends on artifacts that don't exist or are outdated
            required_artifacts = self._extract_artifact_dependencies(task.instructions)

            for required_artifact_type in required_artifacts:
                matching_artifacts = [a for a in artifacts if a.artifact_type == required_artifact_type]

                if not matching_artifacts:
                    conflict = AgentConflict(
                        project_id=project_id,
                        workflow_id=workflow_id,
                        task_id=str(task.task_id),
                        conflict_type=ConflictType.DEPENDENCY_VIOLATION,
                        severity=ConflictSeverity.HIGH,
                        title=f"Missing dependency: {required_artifact_type}",
                        description=f"Task requires {required_artifact_type} but none exists",
                        detection_method="dependency_analysis",
                        detection_confidence=0.9
                    )

                    conflict.add_participant(task.agent_type, "dependent_task")

                    conflict.add_evidence(
                        artifact_id=str(task.task_id),
                        artifact_type="task",
                        source_agent=task.agent_type,
                        conflicting_content=f"Requires: {required_artifact_type}",
                        context={"task_instructions": task.instructions}
                    )

                    conflicts.append(conflict)

        return conflicts

    async def _execute_resolution_strategy(
        self,
        conflict: AgentConflict,
        strategy: ResolutionStrategy
    ) -> ConflictResolutionResult:
        """Execute the specified resolution strategy."""

        if strategy not in self.resolution_strategies:
            raise ValueError(f"Unknown resolution strategy: {strategy}")

        logger.info("Executing resolution strategy",
                   conflict_id=conflict.conflict_id,
                   strategy=strategy.value)

        # Execute the strategy
        result = await self.resolution_strategies[strategy](conflict)

        return result

    async def _resolve_automatic_merge(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Attempt automatic merge resolution for simple contradictions."""
        if len(conflict.participants) != 2:
            return ConflictResolutionResult(
                success=False,
                resolution_strategy=ResolutionStrategy.AUTOMATIC_MERGE,
                resolved_conflict_id=conflict.conflict_id,
                resolution_details={"error": "Automatic merge requires exactly 2 participants"}
            )

        # Simple merge strategy: prefer higher confidence participant
        participant1 = conflict.participants[0]
        participant2 = conflict.participants[1]

        winner = participant1 if (participant1.confidence_score or 0) >= (participant2.confidence_score or 0) else participant2

        # Create merged artifact
        merged_content = self._merge_conflicting_content(conflict.evidence)

        new_artifact = self.context_store.create_artifact(
            project_id=conflict.project_id,
            source_agent="conflict_resolver",
            artifact_type="merged_output",
            content=merged_content
        )

        return ConflictResolutionResult(
            success=True,
            resolution_strategy=ResolutionStrategy.AUTOMATIC_MERGE,
            resolved_conflict_id=conflict.conflict_id,
            new_artifacts=[str(new_artifact.context_id)],
            resolution_details={
                "winner_agent": winner.agent_type,
                "merge_method": "confidence_based",
                "merged_content": merged_content
            },
            confidence_score=0.7
        )

    async def _resolve_manual_override(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Resolve conflict through manual override (escalation)."""
        # This would typically create a HITL request
        return ConflictResolutionResult(
            success=False,
            resolution_strategy=ResolutionStrategy.MANUAL_OVERRIDE,
            resolved_conflict_id=conflict.conflict_id,
            resolution_details={"action": "escalated_to_hitl"}
        )

    async def _resolve_compromise(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Resolve conflict through compromise between participants."""
        # Create compromise artifact combining elements from both sides
        compromise_content = self._create_compromise_content(conflict.evidence)

        new_artifact = self.context_store.create_artifact(
            project_id=conflict.project_id,
            source_agent="conflict_resolver",
            artifact_type="compromise_output",
            content=compromise_content
        )

        return ConflictResolutionResult(
            success=True,
            resolution_strategy=ResolutionStrategy.COMPROMISE,
            resolved_conflict_id=conflict.conflict_id,
            new_artifacts=[str(new_artifact.context_id)],
            resolution_details={
                "compromise_method": "content_merge",
                "compromise_content": compromise_content
            },
            confidence_score=0.6
        )

    async def _resolve_escalation(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Escalate conflict for manual resolution."""
        conflict.escalate("Automatic resolution failed")

        return ConflictResolutionResult(
            success=False,
            resolution_strategy=ResolutionStrategy.ESCALATION,
            resolved_conflict_id=conflict.conflict_id,
            resolution_details={"escalation_reason": "Automatic resolution not possible"}
        )

    async def _resolve_rollback(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Resolve conflict through rollback to previous state."""
        # This would require version control integration
        return ConflictResolutionResult(
            success=False,
            resolution_strategy=ResolutionStrategy.ROLLBACK,
            resolved_conflict_id=conflict.conflict_id,
            resolution_details={"error": "Rollback not implemented"}
        )

    async def _resolve_split_work(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Resolve conflict by splitting work between participants."""
        # Create separate artifacts for each participant
        new_artifacts = []

        for i, participant in enumerate(conflict.participants):
            split_content = f"Work assignment for {participant.agent_type}: {conflict.description}"

            artifact = self.context_store.create_artifact(
                project_id=conflict.project_id,
                source_agent="conflict_resolver",
                artifact_type="split_work",
                content=split_content
            )
            new_artifacts.append(str(artifact.context_id))

        return ConflictResolutionResult(
            success=True,
            resolution_strategy=ResolutionStrategy.SPLIT_WORK,
            resolved_conflict_id=conflict.conflict_id,
            new_artifacts=new_artifacts,
            resolution_details={"split_method": "work_division", "assignments": len(conflict.participants)},
            confidence_score=0.8
        )

    async def _resolve_priority_based(self, conflict: AgentConflict) -> ConflictResolutionResult:
        """Resolve conflict based on participant priorities."""
        # Sort participants by priority/confidence
        sorted_participants = sorted(
            conflict.participants,
            key=lambda p: p.confidence_score or 0,
            reverse=True
        )

        winner = sorted_participants[0]

        return ConflictResolutionResult(
            success=True,
            resolution_strategy=ResolutionStrategy.PRIORITY_BASED,
            resolved_conflict_id=conflict.conflict_id,
            resolution_details={
                "winner_agent": winner.agent_type,
                "priority_method": "confidence_based",
                "ranking": [p.agent_type for p in sorted_participants]
            },
            confidence_score=0.75
        )

    async def _check_conflict_patterns(self, conflict: AgentConflict) -> None:
        """Check if conflict matches known patterns."""
        # Simple pattern matching - could be enhanced with ML
        pattern_key = f"{conflict.conflict_type.value}_{conflict.project_id}"

        if pattern_key not in self.conflict_patterns:
            self.conflict_patterns[pattern_key] = ConflictPattern(
                pattern_type=conflict.conflict_type,
                pattern_description=f"Recurring {conflict.conflict_type.value} conflicts in project {conflict.project_id}",
                detection_rules={"project_id": conflict.project_id, "conflict_type": conflict.conflict_type.value}
            )

        self.conflict_patterns[pattern_key].add_occurrence(conflict.conflict_id)

    def _calculate_content_similarity(self, content1, content2) -> float:
        """Calculate similarity between two content objects (string or dict)."""
        if not content1 or not content2:
            return 0.0

        # Convert content to strings for comparison
        if isinstance(content1, dict):
            content1_str = str(content1)
        else:
            content1_str = str(content1)

        if isinstance(content2, dict):
            content2_str = str(content2)
        else:
            content2_str = str(content2)

        # Use difflib for similarity calculation
        similarity = difflib.SequenceMatcher(None, content1_str, content2_str).ratio()
        return similarity

    def _analyze_requirement_conflicts(self, content1, content2) -> Optional[Dict[str, Any]]:
        """Analyze requirements for conflicts."""
        # Simple conflict detection - could be enhanced
        conflicts = []

        # Convert content to strings for analysis
        if isinstance(content1, dict):
            content1_str = str(content1)
        else:
            content1_str = str(content1)

        if isinstance(content2, dict):
            content2_str = str(content2)
        else:
            content2_str = str(content2)

        # Look for contradictory statements
        if "must" in content1_str.lower() and "must not" in content2_str.lower():
            conflicts.append("Conflicting requirements detected")

        return conflicts if conflicts else None

    def _analyze_design_inconsistencies(self, content1, content2) -> Optional[Dict[str, Any]]:
        """Analyze design artifacts for inconsistencies."""
        # Simple inconsistency detection
        inconsistencies = []

        # Convert content to strings for analysis
        if isinstance(content1, dict):
            content1_str = str(content1)
        else:
            content1_str = str(content1)

        if isinstance(content2, dict):
            content2_str = str(content2)
        else:
            content2_str = str(content2)

        # Check for different architectural patterns
        patterns1 = ["microservice", "monolith", "serverless"]
        patterns2 = ["microservice", "monolith", "serverless"]

        found_patterns1 = [p for p in patterns1 if p in content1_str.lower()]
        found_patterns2 = [p for p in patterns2 if p in content2_str.lower()]

        if found_patterns1 and found_patterns2 and set(found_patterns1) != set(found_patterns2):
            inconsistencies.append("Conflicting architectural patterns")

        return inconsistencies if inconsistencies else None

    def _analyze_implementation_violations(self, impl_content: str, design_content: str) -> Optional[Dict[str, Any]]:
        """Analyze implementation against design for violations."""
        violations = []

        # Check for missing required elements
        if "api" in design_content.lower() and "api" not in impl_content.lower():
            violations.append("Missing API implementation")

        if "database" in design_content.lower() and "database" not in impl_content.lower():
            violations.append("Missing database implementation")

        return violations if violations else None

    def _extract_resource_requirements(self, instructions: str) -> List[str]:
        """Extract resource requirements from task instructions."""
        resources = []

        # Simple resource detection
        if "database" in instructions.lower():
            resources.append("database")
        if "api" in instructions.lower():
            resources.append("api")
        if "file" in instructions.lower():
            resources.append("filesystem")

        return resources

    def _find_overlapping_tasks(self, tasks: List[Task]) -> List[Task]:
        """Find tasks that overlap in execution time."""
        # Simple overlap detection - assumes tasks run sequentially
        # In a real system, this would check actual execution times
        return tasks if len(tasks) > 1 else []

    def _extract_artifact_dependencies(self, instructions: str) -> List[str]:
        """Extract artifact dependencies from task instructions."""
        dependencies = []

        if "requirement" in instructions.lower():
            dependencies.append("requirements")
        if "design" in instructions.lower():
            dependencies.append("design")
        if "architecture" in instructions.lower():
            dependencies.append("architecture")

        return dependencies

    def _merge_conflicting_content(self, evidence: List[ConflictEvidence]) -> str:
        """Merge conflicting content from multiple sources."""
        if len(evidence) < 2:
            return evidence[0].conflicting_content if evidence else ""

        # Simple merge strategy
        merged_parts = []
        for ev in evidence:
            merged_parts.append(f"From {ev.source_agent}: {ev.conflicting_content}")

        return "\n\n".join(merged_parts)

    def _create_compromise_content(self, evidence: List[ConflictEvidence]) -> str:
        """Create compromise content from conflicting evidence."""
        compromise = "Compromise Resolution:\n\n"

        for i, ev in enumerate(evidence, 1):
            compromise += f"Option {i} (from {ev.source_agent}):\n{ev.conflicting_content}\n\n"

        compromise += "Recommended: Combine the best elements from each option."

        return compromise

    def get_conflict_statistics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about detected conflicts."""
        conflicts = list(self.active_conflicts.values())

        if project_id:
            conflicts = [c for c in conflicts if c.project_id == project_id]

        stats = {
            "total_conflicts": len(conflicts),
            "resolved_conflicts": len([c for c in conflicts if c.status == ConflictStatus.RESOLVED]),
            "escalated_conflicts": len([c for c in conflicts if c.status == ConflictStatus.ESCALATED]),
            "active_conflicts": len([c for c in conflicts if c.status in [ConflictStatus.DETECTED, ConflictStatus.UNDER_REVIEW]]),
            "conflict_types": {},
            "severity_distribution": {}
        }

        for conflict in conflicts:
            # Count by type
            ctype = conflict.conflict_type.value
            stats["conflict_types"][ctype] = stats["conflict_types"].get(ctype, 0) + 1

            # Count by severity
            severity = conflict.severity.value
            stats["severity_distribution"][severity] = stats["severity_distribution"].get(severity, 0) + 1

        return stats

    def get_conflict_patterns_report(self) -> Dict[str, Any]:
        """Get report on recurring conflict patterns."""
        significant_patterns = [p for p in self.conflict_patterns.values() if p.is_significant()]

        return {
            "total_patterns": len(self.conflict_patterns),
            "significant_patterns": len(significant_patterns),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "type": p.pattern_type.value,
                    "description": p.pattern_description,
                    "frequency": p.get_frequency(),
                    "occurrences": p.occurrences
                }
                for p in significant_patterns
            ]
        }
