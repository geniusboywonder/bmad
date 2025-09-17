"""
HITL Trigger Processor - Handles trigger evaluation logic.

Responsible for evaluating HITL trigger conditions and determining when
human intervention is required.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.hitl import HitlRequest
from app.services.hitl_trigger_manager import HitlTriggerManager, OversightLevel, HitlTriggerCondition

logger = structlog.get_logger(__name__)


class TriggerProcessor:
    """
    Processes HITL trigger conditions and determines when intervention is needed.

    Follows Single Responsibility Principle by focusing solely on trigger evaluation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.trigger_manager = HitlTriggerManager(db)
        self.trigger_configs = {}
        self.oversight_levels = {}  # Project-specific oversight levels

    async def check_hitl_triggers(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """
        Check if any HITL trigger conditions are met and create request if needed.

        Args:
            project_id: Project identifier
            task_id: Task identifier
            agent_type: Agent type that triggered the check
            trigger_context: Context data for trigger evaluation

        Returns:
            HitlRequest if trigger condition met, None otherwise
        """
        logger.info(
            "Checking HITL triggers",
            project_id=str(project_id),
            task_id=str(task_id),
            agent_type=agent_type
        )

        # Delegate to trigger manager for actual trigger evaluation
        return await self.trigger_manager.check_hitl_triggers(
            project_id, task_id, agent_type, trigger_context
        )

    def configure_trigger_condition(
        self,
        condition_type: str,
        project_id: Optional[UUID] = None,
        config: Dict[str, Any] = None
    ) -> None:
        """
        Configure HITL trigger condition.

        Args:
            condition_type: Type of trigger condition
            project_id: Optional project-specific configuration
            config: Configuration parameters for the trigger
        """
        key = f"{project_id}:{condition_type}" if project_id else condition_type
        self.trigger_configs[key] = config or {}

        logger.info(
            "Configured trigger condition",
            condition_type=condition_type,
            project_id=str(project_id) if project_id else "global",
            config=config
        )

    def set_oversight_level(self, project_id: UUID, level: OversightLevel) -> None:
        """
        Set oversight level for a specific project.

        Args:
            project_id: Project identifier
            level: Oversight level to set
        """
        self.oversight_levels[project_id] = level
        logger.info(
            "Set oversight level",
            project_id=str(project_id),
            level=level.value
        )

    def get_oversight_level(self, project_id: UUID) -> OversightLevel:
        """
        Get oversight level for a project.

        Args:
            project_id: Project identifier

        Returns:
            Oversight level for the project
        """
        return self.oversight_levels.get(project_id, OversightLevel.MEDIUM)

    def evaluate_quality_threshold(
        self,
        trigger_context: Dict[str, Any],
        project_id: UUID
    ) -> bool:
        """
        Evaluate if quality threshold trigger should fire.

        Args:
            trigger_context: Context containing quality metrics
            project_id: Project identifier

        Returns:
            True if trigger should fire, False otherwise
        """
        oversight_level = self.get_oversight_level(project_id)

        # Get quality metrics from context
        confidence_score = trigger_context.get("confidence_score", 1.0)
        quality_score = trigger_context.get("quality_score", 1.0)

        # Define thresholds based on oversight level
        thresholds = {
            OversightLevel.HIGH: {"confidence": 0.8, "quality": 0.9},
            OversightLevel.MEDIUM: {"confidence": 0.6, "quality": 0.7},
            OversightLevel.LOW: {"confidence": 0.4, "quality": 0.5}
        }

        threshold = thresholds.get(oversight_level, thresholds[OversightLevel.MEDIUM])

        should_trigger = (
            confidence_score < threshold["confidence"] or
            quality_score < threshold["quality"]
        )

        if should_trigger:
            logger.info(
                "Quality threshold trigger fired",
                project_id=str(project_id),
                confidence_score=confidence_score,
                quality_score=quality_score,
                oversight_level=oversight_level.value
            )

        return should_trigger

    def evaluate_conflict_detection(
        self,
        trigger_context: Dict[str, Any],
        project_id: UUID
    ) -> bool:
        """
        Evaluate if conflict detection trigger should fire.

        Args:
            trigger_context: Context containing conflict information
            project_id: Project identifier

        Returns:
            True if trigger should fire, False otherwise
        """
        oversight_level = self.get_oversight_level(project_id)

        # Get conflict indicators from context
        has_conflicts = trigger_context.get("has_conflicts", False)
        conflict_severity = trigger_context.get("conflict_severity", "low")

        # Define when to trigger based on oversight level
        trigger_conditions = {
            OversightLevel.HIGH: lambda: has_conflicts,  # Any conflict
            OversightLevel.MEDIUM: lambda: has_conflicts and conflict_severity in ["medium", "high"],
            OversightLevel.LOW: lambda: has_conflicts and conflict_severity == "high"
        }

        condition_func = trigger_conditions.get(
            oversight_level,
            trigger_conditions[OversightLevel.MEDIUM]
        )

        should_trigger = condition_func()

        if should_trigger:
            logger.info(
                "Conflict detection trigger fired",
                project_id=str(project_id),
                has_conflicts=has_conflicts,
                conflict_severity=conflict_severity,
                oversight_level=oversight_level.value
            )

        return should_trigger

    def evaluate_phase_completion(
        self,
        trigger_context: Dict[str, Any],
        project_id: UUID
    ) -> bool:
        """
        Evaluate if phase completion trigger should fire.

        Args:
            trigger_context: Context containing phase information
            project_id: Project identifier

        Returns:
            True if trigger should fire, False otherwise
        """
        oversight_level = self.get_oversight_level(project_id)

        # Get phase information from context
        phase = trigger_context.get("phase", "")
        is_critical_phase = trigger_context.get("is_critical_phase", False)

        # Critical phases that always require approval
        critical_phases = {"requirements", "design", "testing", "deployment"}
        is_phase_critical = phase.lower() in critical_phases or is_critical_phase

        # Define when to trigger based on oversight level
        should_trigger = False

        if oversight_level == OversightLevel.HIGH:
            should_trigger = True  # All phase completions
        elif oversight_level == OversightLevel.MEDIUM:
            should_trigger = is_phase_critical  # Only critical phases
        elif oversight_level == OversightLevel.LOW:
            should_trigger = phase.lower() in {"requirements", "deployment"}  # Only most critical

        if should_trigger:
            logger.info(
                "Phase completion trigger fired",
                project_id=str(project_id),
                phase=phase,
                is_critical_phase=is_phase_critical,
                oversight_level=oversight_level.value
            )

        return should_trigger

    def evaluate_error_condition(
        self,
        trigger_context: Dict[str, Any],
        project_id: UUID
    ) -> bool:
        """
        Evaluate if error condition trigger should fire.

        Args:
            trigger_context: Context containing error information
            project_id: Project identifier

        Returns:
            True if trigger should fire, False otherwise
        """
        oversight_level = self.get_oversight_level(project_id)

        # Get error information from context
        has_errors = trigger_context.get("has_errors", False)
        error_severity = trigger_context.get("error_severity", "low")
        error_count = trigger_context.get("error_count", 0)

        # Define when to trigger based on oversight level
        should_trigger = False

        if oversight_level == OversightLevel.HIGH:
            should_trigger = has_errors  # Any error
        elif oversight_level == OversightLevel.MEDIUM:
            should_trigger = (
                has_errors and
                (error_severity in ["medium", "high"] or error_count > 3)
            )
        elif oversight_level == OversightLevel.LOW:
            should_trigger = (
                has_errors and
                (error_severity == "high" or error_count > 10)
            )

        if should_trigger:
            logger.info(
                "Error condition trigger fired",
                project_id=str(project_id),
                has_errors=has_errors,
                error_severity=error_severity,
                error_count=error_count,
                oversight_level=oversight_level.value
            )

        return should_trigger

    def get_trigger_configuration(
        self,
        condition_type: str,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific trigger condition.

        Args:
            condition_type: Type of trigger condition
            project_id: Optional project-specific configuration

        Returns:
            Configuration dictionary for the trigger
        """
        # Try project-specific configuration first
        if project_id:
            key = f"{project_id}:{condition_type}"
            if key in self.trigger_configs:
                return self.trigger_configs[key]

        # Fall back to global configuration
        return self.trigger_configs.get(condition_type, {})

    def reset_trigger_configuration(self, project_id: Optional[UUID] = None) -> None:
        """
        Reset trigger configuration for a project or globally.

        Args:
            project_id: Project to reset configuration for, or None for global reset
        """
        if project_id:
            # Remove project-specific configurations
            keys_to_remove = [
                key for key in self.trigger_configs.keys()
                if key.startswith(f"{project_id}:")
            ]
            for key in keys_to_remove:
                del self.trigger_configs[key]

            # Reset oversight level
            if project_id in self.oversight_levels:
                del self.oversight_levels[project_id]

            logger.info("Reset trigger configuration for project", project_id=str(project_id))
        else:
            # Reset all configurations
            self.trigger_configs.clear()
            self.oversight_levels.clear()
            logger.info("Reset all trigger configurations")