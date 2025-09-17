"""
HITL Trigger Manager

Manages HITL trigger conditions and evaluation logic for the Human-in-the-Loop system.
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.hitl import HitlStatus, HitlRequest, HitlHistoryEntry
from app.database.models import HitlRequestDB
from app.services.audit_service import AuditService
import structlog

logger = structlog.get_logger(__name__)


class OversightLevel:
    """Oversight level configuration for HITL triggers."""

    HIGH = "high"      # All major decisions require approval
    MEDIUM = "medium"  # Critical decisions and conflicts require approval
    LOW = "low"        # Only errors and emergency situations require approval


class HitlTriggerCondition:
    """HITL trigger condition enumeration."""

    PHASE_COMPLETION = "phase_completion"
    QUALITY_THRESHOLD = "quality_threshold"
    CONFLICT_DETECTED = "conflict_detected"
    AGENT_ERROR = "agent_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    SAFETY_VIOLATION = "safety_violation"
    MANUAL_REQUEST = "manual_request"


class HitlTriggerManager:
    """
    Manages HITL trigger conditions and evaluation logic.

    This class handles the evaluation of various trigger conditions that determine
    when human intervention is required in the workflow execution process.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

        # Default configuration
        self.default_oversight_level = OversightLevel.MEDIUM
        self.default_timeout_hours = 24
        self.quality_threshold = 0.7  # 70% confidence threshold

        # Trigger condition configurations
        self.trigger_configs = {
            HitlTriggerCondition.PHASE_COMPLETION: {
                "enabled": True,
                "phases": ["design", "build", "validate", "launch"]
            },
            HitlTriggerCondition.QUALITY_THRESHOLD: {
                "enabled": True,
                "threshold": 0.7,
                "require_approval_below": True
            },
            HitlTriggerCondition.CONFLICT_DETECTED: {
                "enabled": True,
                "max_auto_resolution_attempts": 3
            },
            HitlTriggerCondition.AGENT_ERROR: {
                "enabled": True,
                "error_types": ["validation_error", "execution_error", "timeout_error"]
            },
            HitlTriggerCondition.BUDGET_EXCEEDED: {
                "enabled": True,
                "threshold_percent": 0.9  # 90% of budget
            },
            HitlTriggerCondition.SAFETY_VIOLATION: {
                "enabled": True,
                "violation_types": ["content_safety", "code_security", "data_privacy"]
            }
        }

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
        oversight_level = trigger_context.get("oversight_level", self.default_oversight_level)

        # Check each trigger condition based on oversight level
        for condition, config in self.trigger_configs.items():
            if not config.get("enabled", False):
                continue

            should_trigger = await self._evaluate_trigger_condition(
                condition, config, project_id, task_id, agent_type, trigger_context, oversight_level
            )

            if should_trigger:
                logger.info("HITL trigger condition met",
                           condition=condition,
                           project_id=str(project_id),
                           task_id=str(task_id),
                           agent_type=agent_type)

                return await self._create_hitl_request(
                    project_id, task_id, agent_type, condition, trigger_context
                )

        return None

    async def _evaluate_trigger_condition(
        self,
        condition: str,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Evaluate a specific HITL trigger condition."""

        if condition == HitlTriggerCondition.PHASE_COMPLETION:
            return await self._check_phase_completion_trigger(
                config, project_id, task_id, trigger_context, oversight_level
            )

        elif condition == HitlTriggerCondition.QUALITY_THRESHOLD:
            return await self._check_quality_threshold_trigger(
                config, project_id, task_id, agent_type, trigger_context, oversight_level
            )

        elif condition == HitlTriggerCondition.CONFLICT_DETECTED:
            return await self._check_conflict_detection_trigger(
                config, project_id, task_id, trigger_context, oversight_level
            )

        elif condition == HitlTriggerCondition.AGENT_ERROR:
            return await self._check_agent_error_trigger(
                config, project_id, task_id, trigger_context, oversight_level
            )

        elif condition == HitlTriggerCondition.BUDGET_EXCEEDED:
            return await self._check_budget_exceeded_trigger(
                config, project_id, agent_type, trigger_context, oversight_level
            )

        elif condition == HitlTriggerCondition.SAFETY_VIOLATION:
            return await self._check_safety_violation_trigger(
                config, project_id, task_id, trigger_context, oversight_level
            )

        return False

    async def _check_phase_completion_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if phase completion requires HITL approval."""

        current_phase = trigger_context.get("current_phase")
        if not current_phase:
            return False

        # Check if this phase requires approval
        phases_requiring_approval = config.get("phases", [])

        if current_phase not in phases_requiring_approval:
            return False

        # Apply oversight level filtering
        if oversight_level == OversightLevel.LOW:
            return False  # Low oversight doesn't require phase approvals
        elif oversight_level == OversightLevel.MEDIUM:
            # Medium oversight only requires approval for critical phases
            critical_phases = ["build", "launch"]
            return current_phase in critical_phases
        elif oversight_level == OversightLevel.HIGH:
            return True  # High oversight requires approval for all configured phases

        return False

    async def _check_quality_threshold_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if quality threshold requires HITL approval."""

        confidence_score = trigger_context.get("confidence_score")
        if confidence_score is None:
            return False

        threshold = config.get("threshold", self.quality_threshold)
        require_approval_below = config.get("require_approval_below", True)

        if require_approval_below:
            quality_issue = confidence_score < threshold
        else:
            quality_issue = confidence_score > threshold

        if not quality_issue:
            return False

        # Apply oversight level filtering
        if oversight_level == OversightLevel.LOW:
            return False  # Low oversight doesn't require quality approvals
        elif oversight_level == OversightLevel.MEDIUM:
            return confidence_score < (threshold * 0.8)  # Only very low confidence
        elif oversight_level == OversightLevel.HIGH:
            return True  # High oversight requires approval for any quality issue

        return False

    async def _check_conflict_detection_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if conflict detection requires HITL approval."""

        conflict_detected = trigger_context.get("conflict_detected", False)
        auto_resolution_attempts = trigger_context.get("auto_resolution_attempts", 0)
        max_attempts = config.get("max_auto_resolution_attempts", 3)

        if not conflict_detected:
            return False

        if auto_resolution_attempts < max_attempts:
            return False  # Still attempting auto-resolution

        # Apply oversight level filtering
        if oversight_level == OversightLevel.LOW:
            return False  # Low oversight doesn't require conflict approvals
        else:
            return True  # Medium/High oversight requires conflict approval

    async def _check_agent_error_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if agent error requires HITL approval."""

        error_type = trigger_context.get("error_type")
        if not error_type:
            return False

        error_types_requiring_approval = config.get("error_types", [])

        if error_type not in error_types_requiring_approval:
            return False

        # Apply oversight level filtering
        if oversight_level == OversightLevel.LOW:
            # Low oversight only requires approval for critical errors
            critical_errors = ["execution_error", "timeout_error"]
            return error_type in critical_errors
        else:
            return True  # Medium/High oversight requires approval for configured errors

    async def _check_budget_exceeded_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        agent_type: str,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if budget exceeded requires HITL approval."""

        budget_usage_percent = trigger_context.get("budget_usage_percent", 0)
        threshold_percent = config.get("threshold_percent", 0.9)

        if budget_usage_percent < threshold_percent:
            return False

        # Apply oversight level filtering
        if oversight_level == OversightLevel.LOW:
            return False  # Low oversight doesn't require budget approvals
        else:
            return True  # Medium/High oversight requires budget approval

    async def _check_safety_violation_trigger(
        self,
        config: Dict[str, Any],
        project_id: UUID,
        task_id: UUID,
        trigger_context: Dict[str, Any],
        oversight_level: str
    ) -> bool:
        """Check if safety violation requires HITL approval."""

        violation_type = trigger_context.get("violation_type")
        if not violation_type:
            return False

        violation_types_requiring_approval = config.get("violation_types", [])

        if violation_type not in violation_types_requiring_approval:
            return False

        # Safety violations always require approval regardless of oversight level
        return True

    async def _create_hitl_request(
        self,
        project_id: UUID,
        task_id: UUID,
        agent_type: str,
        condition: str,
        trigger_context: Dict[str, Any]
    ) -> HitlRequest:
        """Create a HITL request based on trigger condition."""

        # Generate appropriate question based on condition
        question = self._generate_hitl_question(condition, trigger_context)

        # Get available options based on condition
        options = self._get_hitl_options(condition)

        # Calculate expiration time
        timeout_hours = trigger_context.get("timeout_hours", self.default_timeout_hours)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=timeout_hours)

        # Create HITL request
        hitl_request = HitlRequestDB(
            project_id=project_id,
            task_id=task_id,
            question=question,
            options=options,
            status=HitlStatus.PENDING,
            expires_at=expires_at
        )

        self.db.add(hitl_request)
        self.db.commit()
        self.db.refresh(hitl_request)

        # Create initial history entry
        history_entry = HitlHistoryEntry(
            timestamp=datetime.now(timezone.utc),
            action="created",
            content={"trigger_condition": condition, "trigger_context": trigger_context},
            comment=f"HITL request created due to {condition}"
        )

        if not hitl_request.history:
            hitl_request.history = []
        hitl_request.history.append(history_entry.model_dump(mode="json"))
        self.db.commit()

        # Log audit event
        await self.audit_service.log_hitl_event(
            hitl_request_id=hitl_request.id,
            event_type=self.audit_service.EventType.HITL_REQUEST_CREATED,
            event_source=self.audit_service.EventSource.SYSTEM,
            event_data={
                "condition": condition,
                "agent_type": agent_type,
                "question": question,
                "options": options,
                "expires_at": expires_at.isoformat()
            },
            project_id=project_id,
            metadata={
                "trigger_context": trigger_context,
                "oversight_level": trigger_context.get("oversight_level", self.default_oversight_level)
            }
        )

        logger.info("HITL request created",
                   request_id=str(hitl_request.id),
                   condition=condition,
                   project_id=str(project_id),
                   task_id=str(task_id))

        return HitlRequest.from_db(hitl_request)

    def _generate_hitl_question(self, condition: str, trigger_context: Dict[str, Any]) -> str:
        """Generate appropriate HITL question based on trigger condition."""

        if condition == HitlTriggerCondition.PHASE_COMPLETION:
            phase = trigger_context.get("current_phase", "unknown")
            return f"Please review and approve the completion of the {phase} phase."

        elif condition == HitlTriggerCondition.QUALITY_THRESHOLD:
            confidence = trigger_context.get("confidence_score", 0)
            return f"Agent confidence score is {confidence:.2f}, which is below the quality threshold. Please review and approve."

        elif condition == HitlTriggerCondition.CONFLICT_DETECTED:
            conflict_type = trigger_context.get("conflict_type", "unknown")
            return f"A conflict has been detected ({conflict_type}). Please review and resolve."

        elif condition == HitlTriggerCondition.AGENT_ERROR:
            error_type = trigger_context.get("error_type", "unknown")
            return f"An agent error has occurred ({error_type}). Please review and approve next steps."

        elif condition == HitlTriggerCondition.BUDGET_EXCEEDED:
            usage_percent = trigger_context.get("budget_usage_percent", 0)
            return f"Budget usage has exceeded {usage_percent:.1f}%. Please review and approve next steps."

        elif condition == HitlTriggerCondition.SAFETY_VIOLATION:
            violation_type = trigger_context.get("violation_type", "unknown")
            return f"A safety violation has been detected ({violation_type}). Please review and approve."

        elif condition == HitlTriggerCondition.MANUAL_REQUEST:
            return trigger_context.get("custom_question", "Please review this request.")

        return "Please review and provide approval."

    def _get_hitl_options(self, condition: str) -> List[str]:
        """Get available options for HITL request based on condition."""

        base_options = ["Approve", "Reject", "Amend"]

        if condition == HitlTriggerCondition.CONFLICT_DETECTED:
            return ["Approve Resolution", "Reject Resolution", "Provide Alternative Solution"]

        elif condition == HitlTriggerCondition.AGENT_ERROR:
            return ["Retry Task", "Skip Task", "Modify Task", "Cancel Workflow"]

        elif condition == HitlTriggerCondition.BUDGET_EXCEEDED:
            return ["Continue with Caution", "Reduce Scope", "Pause Project", "Cancel Project"]

        elif condition == HitlTriggerCondition.SAFETY_VIOLATION:
            return ["Approve with Mitigation", "Reject and Fix", "Escalate to Security Team"]

        return base_options

    def configure_trigger_condition(
        self,
        condition: str,
        enabled: bool,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Configure a HITL trigger condition."""

        if condition not in self.trigger_configs:
            raise ValueError(f"Unknown trigger condition: {condition}")

        self.trigger_configs[condition]["enabled"] = enabled

        if config:
            self.trigger_configs[condition].update(config)

        logger.info("HITL trigger condition configured",
                   condition=condition,
                   enabled=enabled,
                   config=config)


# Backward compatibility alias
HITLTriggerManager = HitlTriggerManager
