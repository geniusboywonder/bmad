"""Context management service - handles context artifact management and granularity features."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import structlog

from app.services.context_store import ContextStoreService

logger = structlog.get_logger(__name__)


class ContextManager:
    """Manages context artifacts and granularity features."""

    def __init__(self, db: Session, context_store: ContextStoreService):
        self.db = db
        self.context_store = context_store

    def get_selective_context(self, project_id: UUID, phase: str, agent_type: str) -> List[UUID]:
        """
        Get selective context artifacts relevant to the current phase and agent.
        Enhanced with advanced context granularity features.

        Args:
            project_id: UUID of the project
            phase: Current SDLC phase
            agent_type: Type of agent requesting context

        Returns:
            List of relevant context artifact IDs
        """
        # Delegate to context store with enhanced filtering
        selective_result = self.context_store.get_selective_context(
            project_id=project_id,
            phase=phase,
            agent_type=agent_type,
            include_metadata=True
        )

        # If context store returns a dict with artifact IDs, extract them
        if isinstance(selective_result, dict) and "artifact_ids" in selective_result:
            return selective_result["artifact_ids"]
        elif isinstance(selective_result, list):
            return selective_result
        else:
            # Fallback to basic artifact retrieval
            all_artifacts = self.context_store.get_artifacts_by_project(project_id)
            return [artifact.artifact_id for artifact in all_artifacts if self._is_artifact_relevant_to_agent(artifact, agent_type, phase)]

    def _is_artifact_relevant_to_agent(self, artifact, agent_type: str, phase: str) -> bool:
        """
        Determine if an artifact is relevant to the given agent and phase.

        Args:
            artifact: Context artifact to evaluate
            agent_type: Type of agent
            phase: Current phase

        Returns:
            Boolean indicating relevance
        """
        # Basic relevance logic - can be enhanced with ML in the future
        artifact_type = getattr(artifact, 'artifact_type', '').lower()
        agent_type_lower = agent_type.lower()
        phase_lower = phase.lower()

        # Agent-specific relevance
        if agent_type_lower == "analyst":
            return artifact_type in ["requirements", "user_input", "analysis", "specification"]
        elif agent_type_lower == "architect":
            return artifact_type in ["requirements", "analysis", "architecture", "design", "specification"]
        elif agent_type_lower == "coder":
            return artifact_type in ["architecture", "design", "code", "implementation", "specification"]
        elif agent_type_lower == "tester":
            return artifact_type in ["code", "test", "specification", "requirements"]
        elif agent_type_lower == "deployer":
            return artifact_type in ["code", "deployment", "configuration", "infrastructure"]

        # Phase-specific relevance
        if phase_lower in ["discovery", "plan"]:
            return artifact_type in ["user_input", "requirements", "analysis"]
        elif phase_lower in ["design"]:
            return artifact_type in ["requirements", "architecture", "design"]
        elif phase_lower in ["build"]:
            return artifact_type in ["architecture", "design", "code"]
        elif phase_lower in ["validate"]:
            return artifact_type in ["code", "test", "specification"]
        elif phase_lower in ["launch"]:
            return artifact_type in ["code", "deployment", "configuration"]

        # Default: include artifact
        return True

    def get_latest_amended_artifact(self, project_id: UUID, task_id: UUID) -> Optional['ContextArtifact']:
        """
        Get the latest amended artifact for a specific task.

        Args:
            project_id: UUID of the project
            task_id: UUID of the task

        Returns:
            Latest amended artifact if available
        """
        # This would be implemented with HITL integration
        # For now, return None indicating no amended artifact
        logger.info("Requested latest amended artifact",
                   project_id=project_id,
                   task_id=task_id)

        # In a full implementation, this would:
        # 1. Query for HITL amendments related to this task
        # 2. Get the latest amended content
        # 3. Create new context artifact with amended content
        # 4. Return the new artifact

        return None

    def get_integrated_context_summary(self, project_id: UUID, agent_type: str, phase: str,
                                     include_time_analysis: bool = True,
                                     time_budget_hours: float = None) -> Dict[str, Any]:
        """
        Get comprehensive integrated context summary with all granularity features.

        Args:
            project_id: UUID of the project
            agent_type: Type of agent requesting context
            phase: Current phase
            include_time_analysis: Whether to include time-based analysis
            time_budget_hours: Optional time budget for context optimization

        Returns:
            Comprehensive context summary with all features
        """
        logger.info("Generating integrated context summary",
                   project_id=project_id,
                   agent_type=agent_type,
                   phase=phase)

        # Get project progress
        from app.services.orchestrator.project_manager import ProjectManager
        project_manager = ProjectManager(self.db)
        phase_progress = project_manager.get_phase_progress(project_id)

        # Get time-conscious context if time analysis is requested
        # ProjectManager now handles both lifecycle and status tracking
        time_conscious_context = {}
        if include_time_analysis:
            time_conscious_context = project_manager.get_time_conscious_context(
                project_id, phase, agent_type, time_budget_hours
            )

        # Get context analytics
        context_analytics = self.context_store.get_context_analytics(project_id)

        # Get context recommendations
        context_recommendations = self.context_store.get_context_recommendations(
            project_id, agent_type, phase
        )

        # Get selective context with advanced filtering
        selective_context = self.context_store.get_selective_context(
            project_id=project_id,
            phase=phase,
            agent_type=agent_type,
            include_metadata=True
        )

        # Calculate optimization metrics
        optimization_score = self._calculate_context_optimization_score(
            time_conscious_context, selective_context, context_analytics
        )

        return {
            "project_id": str(project_id),
            "agent_type": agent_type,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "phase_progress": phase_progress,
            "time_conscious_context": time_conscious_context,
            "context_analytics": context_analytics,
            "context_recommendations": context_recommendations,
            "selective_context": selective_context,
            "optimization_score": optimization_score,
            "context_artifacts_count": len(time_conscious_context.get("context_ids", [])),
            "summary": self._generate_context_summary(
                time_conscious_context, selective_context, context_analytics
            )
        }

    def _calculate_context_optimization_score(self, time_context: Dict[str, Any],
                                            selective_context: Dict[str, Any],
                                            analytics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive context optimization score.

        Args:
            time_context: Time-conscious context data
            selective_context: Selective context data
            analytics: Context analytics data

        Returns:
            Context optimization score breakdown
        """
        scores = {
            "relevance_score": 0.0,
            "efficiency_score": 0.0,
            "completeness_score": 0.0,
            "time_adaptation_score": 0.0,
            "overall_score": 0.0
        }

        # Calculate individual scores
        scores["relevance_score"] = self._assess_context_quality(time_context, selective_context)
        scores["completeness_score"] = self._assess_context_completeness(time_context, analytics)
        scores["time_adaptation_score"] = self._assess_time_adaptation_quality(time_context)
        scores["efficiency_score"] = self._assess_optimization_effectiveness(time_context, selective_context)

        # Calculate overall score (weighted average)
        weights = {
            "relevance_score": 0.3,
            "efficiency_score": 0.25,
            "completeness_score": 0.25,
            "time_adaptation_score": 0.2
        }

        scores["overall_score"] = sum(
            scores[key] * weights[key] for key in weights.keys()
        )

        # Add qualitative assessment
        scores["quality_rating"] = self._get_quality_rating(scores["overall_score"])

        return scores

    def _assess_context_quality(self, time_context: Dict[str, Any], selective_context: Dict[str, Any]) -> float:
        """Assess the quality of context selection."""
        # Simplified quality assessment
        context_count = len(time_context.get("context_ids", []))
        time_pressure = time_context.get("time_pressure", "normal")

        # Quality is inversely related to time pressure and context overload
        base_score = 85.0  # Start with good score

        if time_pressure == "high":
            base_score += 10  # High pressure filtering is good
        elif time_pressure == "medium":
            base_score += 5

        # Penalize context overload
        if context_count > 20:
            base_score -= 15
        elif context_count > 10:
            base_score -= 5

        # Reward optimal context size
        if 3 <= context_count <= 8:
            base_score += 10

        return min(100.0, max(0.0, base_score))

    def _assess_context_completeness(self, time_context: Dict[str, Any], analytics: Dict[str, Any]) -> float:
        """Assess the completeness of context."""
        context_ids = time_context.get("context_ids", [])
        total_artifacts = analytics.get("total_artifacts", len(context_ids))

        if total_artifacts == 0:
            return 0.0

        # Completeness is the ratio of included vs total artifacts
        completeness_ratio = len(context_ids) / total_artifacts

        # Scale to 0-100 with diminishing returns for very high ratios
        if completeness_ratio <= 0.5:
            return completeness_ratio * 160  # Up to 80% for 50% coverage
        else:
            return 80 + (completeness_ratio - 0.5) * 40  # Up to 100% for full coverage

    def _assess_time_adaptation_quality(self, time_context: Dict[str, Any]) -> float:
        """Assess how well context is adapted to time constraints."""
        time_pressure = time_context.get("time_pressure", "normal")
        context_count = len(time_context.get("context_ids", []))

        # Good time adaptation means appropriate context reduction under pressure
        if time_pressure == "normal":
            return 85.0  # Good baseline
        elif time_pressure == "medium":
            # Should have moderate reduction
            if 5 <= context_count <= 10:
                return 90.0
            else:
                return 70.0
        elif time_pressure == "high":
            # Should have significant reduction
            if 2 <= context_count <= 5:
                return 95.0
            else:
                return 60.0

        return 75.0

    def _calculate_diversity_score(self, selective_context: Dict[str, Any]) -> float:
        """Calculate context diversity score based on artifact types."""
        selected_artifacts = selective_context.get("selected_artifacts", [])

        if not selected_artifacts:
            return 0.0

        # Count unique artifact types
        artifact_types = set()
        for artifact in selected_artifacts:
            artifact_type = getattr(artifact, 'artifact_type', 'unknown')
            artifact_types.add(artifact_type)

        # Diversity is good up to a point, then becomes noise
        unique_types = len(artifact_types)
        total_artifacts = len(selected_artifacts)

        if total_artifacts == 0:
            return 0.0

        diversity_ratio = unique_types / total_artifacts

        # Optimal diversity is around 0.3-0.7 (30-70% unique types)
        if 0.3 <= diversity_ratio <= 0.7:
            return 90.0
        elif 0.2 <= diversity_ratio <= 0.8:
            return 75.0
        else:
            return 60.0

    def _assess_optimization_effectiveness(self, time_context: Dict[str, Any], selective_context: Dict[str, Any]) -> float:
        """Assess the effectiveness of context optimization."""
        # Combine multiple factors
        diversity_score = self._calculate_diversity_score(selective_context)
        context_count = len(time_context.get("context_ids", []))

        # Optimization is effective if:
        # 1. Good diversity
        # 2. Reasonable context size
        # 3. Appropriate to time pressure

        effectiveness = diversity_score * 0.5  # Weight diversity at 50%

        # Add context size appropriateness
        if 3 <= context_count <= 12:
            effectiveness += 30
        elif 1 <= context_count <= 15:
            effectiveness += 20
        else:
            effectiveness += 10

        # Add time pressure appropriateness
        time_pressure = time_context.get("time_pressure", "normal")
        if time_pressure == "high" and context_count <= 5:
            effectiveness += 20
        elif time_pressure == "medium" and context_count <= 8:
            effectiveness += 15
        elif time_pressure == "normal":
            effectiveness += 10

        return min(100.0, effectiveness)

    def _get_quality_rating(self, quality_score: float) -> str:
        """Convert numerical quality score to qualitative rating."""
        if quality_score >= 90:
            return "excellent"
        elif quality_score >= 80:
            return "good"
        elif quality_score >= 70:
            return "fair"
        elif quality_score >= 60:
            return "poor"
        else:
            return "needs_improvement"

    def get_context_granularity_report(self, project_id: UUID) -> Dict[str, Any]:
        """
        Generate comprehensive context granularity report for the project.

        Args:
            project_id: UUID of the project

        Returns:
            Complete context granularity report
        """
        logger.info("Generating context granularity report", project_id=project_id)

        # Get all artifacts for analysis
        all_artifacts = self.context_store.get_artifacts_by_project(project_id)

        # Get context analytics
        analytics = self.context_store.get_context_analytics(project_id)

        # Analyze artifact distribution
        artifact_distribution = self._analyze_artifact_distribution(all_artifacts)

        # Analyze context usage patterns
        usage_patterns = self._analyze_context_usage_patterns(project_id)

        # Generate optimization recommendations
        recommendations = self._generate_context_optimization_recommendations(
            analytics, artifact_distribution, usage_patterns
        )

        # Calculate overall scores
        report = {
            "project_id": str(project_id),
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_artifacts": len(all_artifacts),
                "artifact_distribution": artifact_distribution,
                "usage_patterns": usage_patterns,
                "context_density_score": self._calculate_context_density_score(all_artifacts),
                "temporal_distribution_score": self._calculate_temporal_distribution_score(analytics)
            },
            "analytics": analytics,
            "recommendations": recommendations,
            "optimization_opportunities": self._identify_optimization_opportunities(
                artifact_distribution, usage_patterns
            )
        }

        logger.info("Context granularity report generated",
                   project_id=project_id,
                   total_artifacts=len(all_artifacts),
                   recommendations_count=len(recommendations))

        return report

    def _analyze_artifact_distribution(self, artifacts: List) -> Dict[str, Any]:
        """Analyze the distribution of artifacts by type, source, and timing."""
        distribution = {
            "by_type": {},
            "by_source": {},
            "by_age_days": {"0-1": 0, "1-7": 0, "7-30": 0, "30+": 0}
        }

        now = datetime.now()

        for artifact in artifacts:
            # Analyze by type
            artifact_type = getattr(artifact, 'artifact_type', 'unknown')
            distribution["by_type"][artifact_type] = distribution["by_type"].get(artifact_type, 0) + 1

            # Analyze by source
            source = getattr(artifact, 'source_agent', 'unknown')
            distribution["by_source"][source] = distribution["by_source"].get(source, 0) + 1

            # Analyze by age
            created_at = getattr(artifact, 'created_at', now)
            if isinstance(created_at, datetime):
                age_days = (now - created_at).days
                if age_days <= 1:
                    distribution["by_age_days"]["0-1"] += 1
                elif age_days <= 7:
                    distribution["by_age_days"]["1-7"] += 1
                elif age_days <= 30:
                    distribution["by_age_days"]["7-30"] += 1
                else:
                    distribution["by_age_days"]["30+"] += 1

        return distribution

    def _analyze_context_usage_patterns(self, project_id: UUID) -> Dict[str, Any]:
        """Analyze how context is being used across the project."""
        from app.services.orchestrator.project_manager import ProjectManager
        project_manager = ProjectManager(self.db)

        # Get project tasks to analyze context usage
        all_tasks = project_manager.get_project_tasks(project_id)

        usage_patterns = {
            "average_context_per_task": 0,
            "max_context_per_task": 0,
            "agent_context_preferences": {},
            "phase_context_usage": {}
        }

        total_context_usage = 0
        task_count = len(all_tasks)

        for task in all_tasks:
            context_count = len(getattr(task, 'context_ids', []))
            total_context_usage += context_count

            # Track max usage
            if context_count > usage_patterns["max_context_per_task"]:
                usage_patterns["max_context_per_task"] = context_count

            # Track by agent type
            agent_type = task.agent_type
            if agent_type not in usage_patterns["agent_context_preferences"]:
                usage_patterns["agent_context_preferences"][agent_type] = {
                    "total_tasks": 0,
                    "total_context": 0,
                    "average_context": 0
                }

            usage_patterns["agent_context_preferences"][agent_type]["total_tasks"] += 1
            usage_patterns["agent_context_preferences"][agent_type]["total_context"] += context_count

        # Calculate averages
        if task_count > 0:
            usage_patterns["average_context_per_task"] = total_context_usage / task_count

        # Calculate agent averages
        for agent_type, stats in usage_patterns["agent_context_preferences"].items():
            if stats["total_tasks"] > 0:
                stats["average_context"] = stats["total_context"] / stats["total_tasks"]

        return usage_patterns

    def _generate_context_optimization_recommendations(self, analytics: Dict[str, Any],
                                                     distribution: Dict[str, Any],
                                                     usage_patterns: Dict[str, Any]) -> List[str]:
        """Generate context optimization recommendations."""
        recommendations = []

        # Check for context overload
        avg_context = usage_patterns.get("average_context_per_task", 0)
        if avg_context > 15:
            recommendations.append("Consider implementing more aggressive context filtering - average context per task is high")

        # Check for underutilization
        if avg_context < 3:
            recommendations.append("Context usage is low - consider enriching context selection for better task quality")

        # Check agent preferences
        agent_prefs = usage_patterns.get("agent_context_preferences", {})
        for agent_type, stats in agent_prefs.items():
            if stats["average_context"] > 20:
                recommendations.append(f"Agent {agent_type} uses excessive context - implement agent-specific filtering")

        return recommendations

    def _identify_optimization_opportunities(self, distribution: Dict[str, Any], usage_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities."""
        opportunities = []

        # Check for artifact type imbalances
        type_dist = distribution.get("by_type", {})
        total_artifacts = sum(type_dist.values())

        for artifact_type, count in type_dist.items():
            percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
            if percentage > 50:
                opportunities.append({
                    "type": "artifact_type_imbalance",
                    "description": f"Artifact type '{artifact_type}' represents {percentage:.1f}% of all artifacts",
                    "recommendation": "Consider more diverse artifact creation or implement type-based filtering"
                })

        return opportunities

    def _calculate_context_density_score(self, artifacts: List) -> float:
        """Calculate context density score based on artifact characteristics."""
        if not artifacts:
            return 0.0

        # Simple density calculation based on artifact count and estimated size
        total_estimated_tokens = sum(self._estimate_artifact_tokens(artifact) for artifact in artifacts)
        artifact_count = len(artifacts)

        # Ideal density is around 1000-2000 tokens per artifact
        if artifact_count == 0:
            return 0.0

        avg_tokens_per_artifact = total_estimated_tokens / artifact_count

        if 1000 <= avg_tokens_per_artifact <= 2000:
            return 90.0
        elif 500 <= avg_tokens_per_artifact <= 3000:
            return 75.0
        else:
            return 60.0

    def _calculate_temporal_distribution_score(self, analytics: Dict[str, Any]) -> float:
        """Calculate temporal distribution score."""
        # Simplified temporal scoring
        # In a real implementation, this would analyze artifact creation patterns over time
        return 75.0  # Default good score

    def _estimate_artifact_tokens(self, artifact) -> int:
        """Estimate the token count for an artifact."""
        # Simple estimation based on content length
        content = getattr(artifact, 'content', {})
        if isinstance(content, dict):
            content_str = str(content)
        elif isinstance(content, str):
            content_str = content
        else:
            content_str = ""

        # Rough estimation: 1 token per 4 characters
        return len(content_str) // 4

    def _generate_context_summary(self, time_context: Dict[str, Any], selective_context: Dict[str, Any], analytics: Dict[str, Any]) -> str:
        """Generate a human-readable context summary."""
        context_count = len(time_context.get("context_ids", []))
        time_pressure = time_context.get("time_pressure", "normal")

        summary = f"Context optimized for {time_pressure} time pressure with {context_count} artifacts selected. "

        if time_pressure == "high":
            summary += "Aggressive filtering applied for critical tasks only."
        elif time_pressure == "medium":
            summary += "Balanced filtering applied for efficiency."
        else:
            summary += "Comprehensive context provided for thorough analysis."

        return summary