"""Agent configuration management with ADK feature flags."""

from typing import Dict, Any, Optional
import hashlib
import structlog

from app.models.agent import AgentType

logger = structlog.get_logger(__name__)


# Agent Configuration with Enhanced Multi-LLM Provider Support
AGENT_CONFIGS = {
    "analyst": {
        "use_adk": True,  # Enable ADK for analysts first
        "fallback_to_legacy": True,
        "rollout_percentage": 25,  # Gradual rollout
        "llm_config": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",  # Updated to latest model
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30,
        },
        "instruction": """You are an Analyst agent. Your primary role is to interact with the Context Store to generate a comprehensive project plan, including scope, milestones, artifacts, and requirements gathering methodology. You also generate functional and non-functional requirements and initial user stories.""",
        "tools": [],
        "specialization": "requirements_analysis",
        "context_focus": ["user_input", "requirements", "analysis"]
    },
    "architect": {
        "use_adk": False,  # Enable after analyst validation
        "rollout_percentage": 0,
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30,
        },
        "instruction": """You are an Architect agent. Your primary role is to design the system architecture, define the technology stack, create a high-level database schema, and break down the project into specific, executable coding tasks for the Coder agent.""",
        "tools": [],
        "specialization": "system_design",
        "context_focus": ["requirements", "architecture", "design", "api", "model"]
    },
    "coder": {
        "use_adk": False,
        "rollout_percentage": 0,
        "llm_config": {
            "provider": "gemini",
            "model": "gemini-1.5-pro-latest",  # Updated to latest Gemini model
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30,
        },
        "instruction": """You are a Coder agent. Your primary role is to sequentially generate code for the defined components and functionality, and then review and refine the generated code for quality, adherence to best practices, and integration with the overall architecture.""",
        "tools": [],  # Will be populated in Phase 3
        "specialization": "code_generation",
        "context_focus": ["architecture", "design", "api", "model", "spec"]
    },
    "tester": {
        "use_adk": False,
        "rollout_percentage": 0,
        "llm_config": {
            "provider": "gemini",
            "model": "gemini-1.5-flash-latest",  # Cost-effective model for testing
            "temperature": 0.7,
            "max_tokens": 4096,
            "timeout": 30,
        },
        "instruction": """You are a Tester agent. Your primary role is to analyze the code and write a set of unit tests and integration tests to validate its functionality.""",
        "tools": [],
        "specialization": "quality_assurance",
        "context_focus": ["code", "source", "test", "spec", "requirement"]
    },
    "deployer": {
        "use_adk": False,
        "rollout_percentage": 0,
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",  # Cost-effective model for deployment
            "temperature": 0.7,
            "max_tokens": 2048,
            "timeout": 30,
        },
        "instruction": """You are a Deployer agent. Your primary role is to set up the necessary infrastructure, deploy the application, and perform a final health check on the deployed application to confirm it is running as expected.""",
        "tools": [],
        "specialization": "infrastructure_deployment",
        "context_focus": ["code", "source", "deployment", "config"]
    }
}


class ADKRolloutManager:
    """Manages gradual ADK rollout with user-based percentage control."""

    def __init__(self):
        self._rollout_configs = AGENT_CONFIGS.copy()
        logger.info("ADK Rollout Manager initialized")

    def should_use_adk(self, agent_type: str, user_id: Optional[str] = None) -> bool:
        """Determine if ADK should be used based on rollout percentage.

        Args:
            agent_type: The agent type to check
            user_id: Optional user ID for consistent rollout (uses hash-based distribution)

        Returns:
            True if ADK should be used, False otherwise
        """
        if agent_type not in self._rollout_configs:
            logger.warning("Unknown agent type for ADK rollout check", agent_type=agent_type)
            return False

        config = self._rollout_configs[agent_type]

        if not config.get("use_adk", False):
            return False

        rollout_pct = config.get("rollout_percentage", 0)

        if rollout_pct >= 100:
            return True
        elif rollout_pct <= 0:
            return False

        # Use user_id for consistent rollout distribution
        if user_id:
            # Create consistent hash for user-based rollout
            hash_value = int(hashlib.md5(f"{agent_type}:{user_id}".encode()).hexdigest(), 16)
            user_rollout_value = hash_value % 100
            should_use = user_rollout_value < rollout_pct

            logger.debug("ADK rollout check with user consistency",
                        agent_type=agent_type,
                        user_id=user_id,
                        rollout_percentage=rollout_pct,
                        user_value=user_rollout_value,
                        should_use_adk=should_use)

            return should_use
        else:
            # Fallback to simple percentage-based rollout
            return rollout_pct > 50  # Simple majority check when no user_id

    def update_rollout_percentage(self, agent_type: str, percentage: int) -> bool:
        """Update rollout percentage for an agent type.

        Args:
            agent_type: The agent type to update
            percentage: New rollout percentage (0-100)

        Returns:
            True if update was successful, False otherwise
        """
        if agent_type not in self._rollout_configs:
            logger.error("Cannot update rollout for unknown agent type", agent_type=agent_type)
            return False

        # Validate percentage range
        if not 0 <= percentage <= 100:
            logger.error("Invalid rollout percentage", agent_type=agent_type, percentage=percentage)
            return False

        old_percentage = self._rollout_configs[agent_type].get("rollout_percentage", 0)
        self._rollout_configs[agent_type]["rollout_percentage"] = percentage

        logger.info("ADK rollout percentage updated",
                   agent_type=agent_type,
                   old_percentage=old_percentage,
                   new_percentage=percentage)

        return True

    def enable_adk_for_agent(self, agent_type: str, enabled: bool = True) -> bool:
        """Enable or disable ADK for a specific agent type.

        Args:
            agent_type: The agent type to enable/disable
            enabled: True to enable, False to disable

        Returns:
            True if update was successful, False otherwise
        """
        if agent_type not in self._rollout_configs:
            logger.error("Cannot enable ADK for unknown agent type", agent_type=agent_type)
            return False

        old_state = self._rollout_configs[agent_type].get("use_adk", False)
        self._rollout_configs[agent_type]["use_adk"] = enabled

        # If disabling, also set rollout to 0
        if not enabled:
            self._rollout_configs[agent_type]["rollout_percentage"] = 0

        logger.info("ADK state changed for agent type",
                   agent_type=agent_type,
                   old_state=old_state,
                   new_state=enabled)

        return True

    def get_rollout_status(self) -> Dict[str, Any]:
        """Get current rollout status for all agent types.

        Returns:
            Dictionary with rollout status for each agent type
        """
        status = {}
        for agent_type, config in self._rollout_configs.items():
            status[agent_type] = {
                "use_adk": config.get("use_adk", False),
                "rollout_percentage": config.get("rollout_percentage", 0),
                "model": config.get("model", "unknown"),
                "fallback_enabled": config.get("fallback_to_legacy", False)
            }

        return status

    def get_agent_config(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get complete configuration for an agent type.

        Args:
            agent_type: The agent type to get config for

        Returns:
            Agent configuration dictionary or None if not found
        """
        return self._rollout_configs.get(agent_type)

    def reset_to_defaults(self) -> None:
        """Reset all configurations to default values."""
        self._rollout_configs = AGENT_CONFIGS.copy()
        logger.info("ADK configurations reset to defaults")

    def get_rollout_metrics(self) -> Dict[str, Any]:
        """Get rollout metrics and statistics.

        Returns:
            Dictionary with rollout metrics
        """
        metrics = {
            "total_agent_types": len(self._rollout_configs),
            "adk_enabled_count": 0,
            "total_rollout_percentage": 0,
            "agent_breakdown": {}
        }

        for agent_type, config in self._rollout_configs.items():
            if config.get("use_adk", False):
                metrics["adk_enabled_count"] += 1
                metrics["total_rollout_percentage"] += config.get("rollout_percentage", 0)

            metrics["agent_breakdown"][agent_type] = {
                "enabled": config.get("use_adk", False),
                "rollout_percentage": config.get("rollout_percentage", 0)
            }

        # Calculate average rollout percentage
        if metrics["adk_enabled_count"] > 0:
            metrics["average_rollout_percentage"] = metrics["total_rollout_percentage"] / metrics["adk_enabled_count"]
        else:
            metrics["average_rollout_percentage"] = 0

        return metrics


# Global rollout manager instance
rollout_manager = ADKRolloutManager()


def get_rollout_manager() -> ADKRolloutManager:
    """Get the global ADK rollout manager instance.

    Returns:
        Global ADKRolloutManager instance
    """
    return rollout_manager


def should_use_adk_for_agent(agent_type: str, user_id: Optional[str] = None) -> bool:
    """Convenience function to check if ADK should be used for an agent.

    Args:
        agent_type: The agent type to check
        user_id: Optional user ID for consistent rollout

    Returns:
        True if ADK should be used, False otherwise
    """
    return rollout_manager.should_use_adk(agent_type, user_id)


def get_agent_adk_config(agent_type: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get ADK configuration for an agent.

    Args:
        agent_type: The agent type to get config for

    Returns:
        Agent ADK configuration or None if not found
    """
    return rollout_manager.get_agent_config(agent_type)
