import os
from dataclasses import dataclass, field
from typing import List, Dict, Any

import yaml
import structlog
from sqlalchemy.orm import Session

from app.services.orchestrator.project_manager import ProjectManager

logger = structlog.get_logger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "policy_config.yaml")

@dataclass
class PolicyDecision:
    """Represents the outcome of a policy evaluation."""
    status: str  # "allowed" or "denied"
    reason_code: str = ""
    message: str = ""
    current_phase: str = ""
    allowed_agents: List[str] = field(default_factory=list)

class PhasePolicyService:
    """
    Enforces policies based on the project's current SDLC phase.
    """
    def __init__(self, db: Session):
        self.db = db
        self.project_manager = ProjectManager(db)
        self.policies = self._load_policies()

    def _load_policies(self) -> Dict[str, Any]:
        """Loads policy configuration from a YAML file."""
        try:
            with open(CONFIG_PATH, "r") as f:
                policies = yaml.safe_load(f)
                logger.info("Policy configuration loaded successfully.", policies=policies)
                return policies
        except FileNotFoundError:
            logger.error("Policy configuration file not found.", path=CONFIG_PATH)
            return {}
        except yaml.YAMLError as e:
            logger.error("Error parsing policy configuration file.", error=str(e))
            return {}

    def evaluate(self, project_id: str, agent_type: str) -> PolicyDecision:
        """
        Evaluates if an agent is allowed to act in the project's current phase.

        Args:
            project_id: The ID of the project.
            agent_type: The type of the agent requesting to act.

        Returns:
            A PolicyDecision object with the outcome.
        """
        current_phase = self.project_manager.get_current_phase(project_id)
        if not current_phase:
            return PolicyDecision(
                status="denied",
                reason_code="no_active_phase",
                message=f"Project {project_id} does not have an active phase.",
                current_phase="N/A",
            )

        phase_policy = self.policies.get(current_phase.lower())
        if not phase_policy:
            return PolicyDecision(
                status="denied",
                reason_code="no_policy_for_phase",
                message=f"No policy defined for the current phase: {current_phase}.",
                current_phase=current_phase,
            )

        allowed_agents = phase_policy.get("allowed_agents", [])
        if agent_type in allowed_agents:
            return PolicyDecision(status="allowed", current_phase=current_phase, allowed_agents=allowed_agents)
        else:
            logger.warning(
                "Policy violation: Agent denied.",
                project_id=project_id,
                agent_type=agent_type,
                current_phase=current_phase,
                allowed_agents=allowed_agents,
            )
            return PolicyDecision(
                status="denied",
                reason_code="agent_not_allowed",
                message=f"Agent '{agent_type}' is not allowed in the '{current_phase}' phase.",
                current_phase=current_phase,
                allowed_agents=allowed_agents,
            )