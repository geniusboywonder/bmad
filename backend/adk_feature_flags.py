#!/usr/bin/env python3
"""ADK Feature Flags and Agent Selection for BMAD System.

This module implements feature flags for seamless switching between ADK and BMAD agents,
enabling gradual rollout and rollback capabilities during Phase 5 migration.
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class AgentImplementation(Enum):
    """Available agent implementations."""
    BMAD_LEGACY = "bmad_legacy"
    ADK_ENHANCED = "adk_enhanced"


class FeatureFlagStatus(Enum):
    """Feature flag status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLOUT = "rollout"
    EXPERIMENT = "experiment"


class ADKFeatureFlags:
    """Manages feature flags for ADK migration and rollout."""

    def __init__(self, config_file: str = "adk_feature_flags.json"):
        self.config_file = config_file
        self.flags = self._load_flags()
        self.agent_mappings = {
            "analyst": {
                "bmad_legacy": "BMADAnalystAgent",
                "adk_enhanced": "ADKAnalystAgent"
            },
            "architect": {
                "bmad_legacy": "BMADArchitectAgent",
                "adk_enhanced": "ADKArchitectAgent"
            },
            "developer": {
                "bmad_legacy": "BMADDeveloperAgent",
                "adk_enhanced": "ADKDeveloperAgent"
            },
            "tester": {
                "bmad_legacy": "BMADTesterAgent",
                "adk_enhanced": "ADKTesterAgent"
            },
            "deployer": {
                "bmad_legacy": "BMADDeployerAgent",
                "adk_enhanced": "ADKDeployerAgent"
            }
        }

    def _load_flags(self) -> Dict[str, Any]:
        """Load feature flags from configuration file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load feature flags: {e}")

        # Default configuration
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "global_flags": {
                "adk_migration_enabled": False,
                "rollback_mode": False,
                "emergency_stop": False
            },
            "agent_flags": {
                "analyst_adk_enabled": False,
                "architect_adk_enabled": False,
                "developer_adk_enabled": False,
                "tester_adk_enabled": False,
                "deployer_adk_enabled": False
            },
            "rollout_flags": {
                "canary_percentage": 0,
                "user_whitelist": [],
                "project_whitelist": [],
                "gradual_rollout_schedule": {}
            },
            "monitoring_flags": {
                "performance_monitoring": True,
                "error_tracking": True,
                "audit_logging": True,
                "real_time_alerts": True
            }
        }

    def save_flags(self) -> None:
        """Save feature flags to configuration file."""
        self.flags["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.flags, f, indent=2, default=str)
            logger.info("Feature flags saved successfully")
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")

    def is_adk_enabled_for_agent(self, agent_type: str, user_id: Optional[str] = None,
                                project_id: Optional[str] = None) -> bool:
        """Check if ADK is enabled for a specific agent type."""
        if self.flags["global_flags"]["emergency_stop"]:
            logger.warning("Emergency stop activated - using legacy agents only")
            return False

        if self.flags["global_flags"]["rollback_mode"]:
            logger.info("Rollback mode activated - using legacy agents only")
            return False

        if not self.flags["global_flags"]["adk_migration_enabled"]:
            return False

        # Check agent-specific flag
        agent_flag_key = f"{agent_type}_adk_enabled"
        if not self.flags["agent_flags"].get(agent_flag_key, False):
            return False

        # Check canary rollout
        canary_percentage = self.flags["rollout_flags"]["canary_percentage"]
        if canary_percentage > 0:
            # Simple canary logic based on user/project ID hash
            canary_seed = (user_id or "") + (project_id or "")
            canary_value = hash(canary_seed) % 100
            if canary_value >= canary_percentage:
                return False

        # Check whitelist
        user_whitelist = self.flags["rollout_flags"]["user_whitelist"]
        project_whitelist = self.flags["rollout_flags"]["project_whitelist"]

        if user_whitelist and user_id not in user_whitelist:
            return False

        if project_whitelist and project_id not in project_whitelist:
            return False

        return True

    def get_agent_implementation(self, agent_type: str, user_id: Optional[str] = None,
                               project_id: Optional[str] = None) -> str:
        """Get the agent implementation to use for the given context."""
        # Handle invalid agent types gracefully
        if agent_type not in self.agent_mappings:
            logger.warning(f"Invalid agent type: {agent_type}, using fallback")
            return f"BMAD{agent_type.title()}Agent"  # Return a fallback implementation

        if self.is_adk_enabled_for_agent(agent_type, user_id, project_id):
            return self.agent_mappings[agent_type]["adk_enhanced"]
        else:
            return self.agent_mappings[agent_type]["bmad_legacy"]

    def enable_adk_for_agent(self, agent_type: str, canary_percentage: int = 0) -> None:
        """Enable ADK for a specific agent type."""
        agent_flag_key = f"{agent_type}_adk_enabled"
        self.flags["agent_flags"][agent_flag_key] = True

        if canary_percentage > 0:
            self.flags["rollout_flags"]["canary_percentage"] = canary_percentage

        self.save_flags()
        logger.info(f"ADK enabled for {agent_type} agent", canary_percentage=canary_percentage)

    def disable_adk_for_agent(self, agent_type: str) -> None:
        """Disable ADK for a specific agent type (rollback)."""
        agent_flag_key = f"{agent_type}_adk_enabled"
        self.flags["agent_flags"][agent_flag_key] = False
        self.save_flags()
        logger.info(f"ADK disabled for {agent_type} agent (rollback)")

    def enable_global_rollback(self) -> None:
        """Enable global rollback mode."""
        self.flags["global_flags"]["rollback_mode"] = True
        self.save_flags()
        logger.warning("Global rollback mode activated - all agents using legacy implementation")

    def disable_global_rollback(self) -> None:
        """Disable global rollback mode."""
        self.flags["global_flags"]["rollback_mode"] = False
        self.save_flags()
        logger.info("Global rollback mode deactivated")

    def emergency_stop(self) -> None:
        """Activate emergency stop - forces all agents to legacy implementation."""
        self.flags["global_flags"]["emergency_stop"] = True
        self.save_flags()
        logger.critical("EMERGENCY STOP ACTIVATED - All agents forced to legacy implementation")

    def reset_emergency_stop(self) -> None:
        """Reset emergency stop."""
        self.flags["global_flags"]["emergency_stop"] = False
        self.save_flags()
        logger.info("Emergency stop reset")

    def get_rollout_status(self) -> Dict[str, Any]:
        """Get comprehensive rollout status."""
        enabled_agents = []
        disabled_agents = []

        for agent_type in self.agent_mappings.keys():
            if self.flags["agent_flags"].get(f"{agent_type}_adk_enabled", False):
                enabled_agents.append(agent_type)
            else:
                disabled_agents.append(agent_type)

        return {
            "global_migration_enabled": self.flags["global_flags"]["adk_migration_enabled"],
            "rollback_mode": self.flags["global_flags"]["rollback_mode"],
            "emergency_stop": self.flags["global_flags"]["emergency_stop"],
            "enabled_agents": enabled_agents,
            "disabled_agents": disabled_agents,
            "canary_percentage": self.flags["rollout_flags"]["canary_percentage"],
            "whitelist_users": len(self.flags["rollout_flags"]["user_whitelist"]),
            "whitelist_projects": len(self.flags["rollout_flags"]["project_whitelist"]),
            "last_updated": self.flags["last_updated"]
        }

    def add_to_whitelist(self, user_id: Optional[str] = None,
                        project_id: Optional[str] = None) -> None:
        """Add user or project to whitelist for ADK rollout."""
        if user_id:
            if user_id not in self.flags["rollout_flags"]["user_whitelist"]:
                self.flags["rollout_flags"]["user_whitelist"].append(user_id)
                logger.info(f"User {user_id} added to ADK whitelist")

        if project_id:
            if project_id not in self.flags["rollout_flags"]["project_whitelist"]:
                self.flags["rollout_flags"]["project_whitelist"].append(project_id)
                logger.info(f"Project {project_id} added to ADK whitelist")

        self.save_flags()

    def remove_from_whitelist(self, user_id: Optional[str] = None,
                            project_id: Optional[str] = None) -> None:
        """Remove user or project from whitelist."""
        if user_id and user_id in self.flags["rollout_flags"]["user_whitelist"]:
            self.flags["rollout_flags"]["user_whitelist"].remove(user_id)
            logger.info(f"User {user_id} removed from ADK whitelist")

        if project_id and project_id in self.flags["rollout_flags"]["project_whitelist"]:
            self.flags["rollout_flags"]["project_whitelist"].remove(project_id)
            logger.info(f"Project {project_id} removed from ADK whitelist")

        self.save_flags()


# Global feature flags instance
feature_flags = ADKFeatureFlags()


def get_agent_implementation(agent_type: str, user_id: Optional[str] = None,
                           project_id: Optional[str] = None) -> str:
    """Convenience function to get agent implementation."""
    return feature_flags.get_agent_implementation(agent_type, user_id, project_id)


def is_adk_enabled(agent_type: str, user_id: Optional[str] = None,
                  project_id: Optional[str] = None) -> bool:
    """Convenience function to check if ADK is enabled."""
    return feature_flags.is_adk_enabled_for_agent(agent_type, user_id, project_id)


if __name__ == "__main__":
    # Example usage
    flags = ADKFeatureFlags()

    print("🚀 ADK Feature Flags Management")
    print("=" * 50)

    # Enable global migration
    flags.flags["global_flags"]["adk_migration_enabled"] = True
    flags.save_flags()

    # Enable ADK for analyst agent with 10% canary
    flags.enable_adk_for_agent("analyst", canary_percentage=10)

    # Check rollout status
    status = flags.get_rollout_status()
    print(f"Global Migration: {status['global_migration_enabled']}")
    print(f"Enabled Agents: {status['enabled_agents']}")
    print(f"Canary Percentage: {status['canary_percentage']}%")

    # Test agent selection
    legacy_agent = flags.get_agent_implementation("analyst", "user123", "project456")
    print(f"Selected Agent: {legacy_agent}")

    print("\n✅ Feature flags configured successfully")
