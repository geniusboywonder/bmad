"""Agent factory for type-based agent instantiation."""

from typing import Dict, Type, Any, Optional
import structlog

from app.models.agent import AgentType
from app.agents.base_agent import BaseAgent
from app.agents.bmad_adk_wrapper import BMADADKWrapper

logger = structlog.get_logger(__name__)


class AgentFactory:
    """Enhanced factory class for creating agents based on agent type with ADK support.

    This factory implements the Factory Pattern to create appropriate agent instances
    based on the requested agent type. It supports both legacy agents and ADK-based agents
    with feature flag control for gradual rollout.
    """

    def __init__(self):
        """Initialize the agent factory with an empty registry."""
        self._agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
        self._agent_instances: Dict[AgentType, BaseAgent] = {}
        self._adk_agent_configs: Dict[AgentType, Dict[str, Any]] = {}

        # Initialize ADK agent configurations
        self._initialize_adk_configs()

        logger.info("Agent factory initialized with ADK support")

    def _initialize_adk_configs(self):
        """Initialize ADK agent configurations for each agent type."""
        self._adk_agent_configs = {
            AgentType.ANALYST: {
                "model": "gemini-2.0-flash",
                "instruction": self._get_analyst_instruction(),
                "tools": [],
                "use_adk": True,
                "rollout_percentage": 25  # Gradual rollout
            },
            AgentType.ARCHITECT: {
                "model": "gemini-2.0-flash",
                "instruction": self._get_architect_instruction(),
                "tools": [],
                "use_adk": False,  # Enable after analyst validation
                "rollout_percentage": 0
            },
            AgentType.CODER: {
                "model": "gemini-2.0-flash",
                "instruction": self._get_coder_instruction(),
                "tools": self._get_coder_tools(),
                "use_adk": False,
                "rollout_percentage": 0
            },
            AgentType.TESTER: {
                "model": "gemini-2.0-flash",
                "instruction": self._get_tester_instruction(),
                "tools": [],
                "use_adk": False,
                "rollout_percentage": 0
            },
            AgentType.DEPLOYER: {
                "model": "gemini-2.0-flash",
                "instruction": self._get_deployer_instruction(),
                "tools": [],
                "use_adk": False,
                "rollout_percentage": 0
            }
        }

    def _get_analyst_instruction(self) -> str:
        """Get analyst agent instruction for ADK."""
        from app.utils.agent_prompt_loader import agent_prompt_loader
        return agent_prompt_loader.get_agent_prompt("analyst")

    def _get_architect_instruction(self) -> str:
        """Get architect agent instruction for ADK."""
        from app.utils.agent_prompt_loader import agent_prompt_loader
        return agent_prompt_loader.get_agent_prompt("architect")

    def _get_coder_instruction(self) -> str:
        """Get coder agent instruction for ADK."""
        from app.utils.agent_prompt_loader import agent_prompt_loader
        return agent_prompt_loader.get_agent_prompt("coder")

    def _get_tester_instruction(self) -> str:
        """Get tester agent instruction for ADK."""
        from app.utils.agent_prompt_loader import agent_prompt_loader
        return agent_prompt_loader.get_agent_prompt("tester")

    def _get_deployer_instruction(self) -> str:
        """Get deployer agent instruction for ADK."""
        from app.utils.agent_prompt_loader import agent_prompt_loader
        return agent_prompt_loader.get_agent_prompt("deployer")

    def _get_coder_tools(self) -> list:
        """Get tools for coder agent."""
        # This will be expanded in Phase 3 with actual tool implementations
        return []

    def register_agent(self, agent_type: AgentType, agent_class: Type[BaseAgent]) -> None:
        """Register an agent class for a specific agent type.

        Args:
            agent_type: The agent type enum value
            agent_class: The agent class that inherits from BaseAgent

        Raises:
            ValueError: If agent_class doesn't inherit from BaseAgent
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class {agent_class.__name__} must inherit from BaseAgent")

        self._agent_classes[agent_type] = agent_class
        logger.info("Agent class registered",
                   agent_type=agent_type.value,
                   agent_class=agent_class.__name__)

    def create_agent(self, agent_type: AgentType, llm_config: Dict[str, Any],
                    force_new: bool = False, use_adk: Optional[bool] = None) -> BaseAgent:
        """Create or retrieve an agent instance of the specified type with ADK support.

        Args:
            agent_type: The type of agent to create
            llm_config: LLM configuration for the agent
            force_new: If True, creates a new instance even if one exists
            use_adk: Override ADK usage (None = use config default)

        Returns:
            Agent instance of the requested type

        Raises:
            ValueError: If agent type is not registered
        """
        # Check if agent type is registered
        if agent_type not in self._agent_classes:
            available_types = [t.value for t in self._agent_classes.keys()]
            raise ValueError(f"Agent type {agent_type.value} not registered. "
                           f"Available types: {available_types}")

        # Determine if ADK should be used
        should_use_adk = self._should_use_adk(agent_type, use_adk)

        # Return existing instance if available and not forcing new
        if not force_new and agent_type in self._agent_instances:
            existing_agent = self._agent_instances[agent_type]
            # Check if existing agent matches ADK preference
            if hasattr(existing_agent, 'is_adk_agent') and existing_agent.is_adk_agent == should_use_adk:
                logger.debug("Returning existing agent instance", agent_type=agent_type.value)
                return existing_agent

        # Create new agent instance
        agent_class = self._agent_classes[agent_type]

        try:
            if should_use_adk and agent_type in self._adk_agent_configs:
                # Create ADK agent
                agent_instance = self._create_adk_agent(agent_type, llm_config)
                agent_instance.is_adk_agent = True
            else:
                # Create legacy agent
                agent_instance = agent_class(agent_type, llm_config)
                agent_instance.is_adk_agent = False

            self._agent_instances[agent_type] = agent_instance

            logger.info("Agent instance created",
                       agent_type=agent_type.value,
                       agent_class=agent_class.__name__,
                       is_adk_agent=getattr(agent_instance, 'is_adk_agent', False))

            return agent_instance

        except Exception as e:
            logger.error("Failed to create agent instance",
                        agent_type=agent_type.value,
                        agent_class=agent_class.__name__,
                        error=str(e))
            raise

    def _should_use_adk(self, agent_type: AgentType, override: Optional[bool]) -> bool:
        """Determine if ADK should be used for the given agent type."""
        if override is not None:
            return override

        if agent_type not in self._adk_agent_configs:
            return False

        config = self._adk_agent_configs[agent_type]
        if not config.get("use_adk", False):
            return False

        # Check rollout percentage (simple hash-based rollout)
        rollout_pct = config.get("rollout_percentage", 0)
        if rollout_pct >= 100:
            return True
        elif rollout_pct <= 0:
            return False

        # Use agent type hash for consistent rollout
        import hashlib
        hash_value = int(hashlib.md5(agent_type.value.encode()).hexdigest(), 16)
        return (hash_value % 100) < rollout_pct

    def _create_adk_agent(self, agent_type: AgentType, llm_config: Dict[str, Any]) -> BMADADKWrapper:
        """Create an ADK-based agent instance."""
        config = self._adk_agent_configs[agent_type]

        # Merge with provided LLM config
        adk_config = {
            "model": llm_config.get("model", config["model"]),
            "instruction": llm_config.get("instruction", config["instruction"]),
            "tools": llm_config.get("tools", config["tools"])
        }

        wrapper = BMADADKWrapper(
            agent_name=f"{agent_type.value}_adk_agent",
            agent_type=agent_type.value,
            model=adk_config["model"],
            instruction=adk_config["instruction"],
            tools=adk_config["tools"]
        )

        return wrapper

    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get an existing agent instance.

        Args:
            agent_type: The type of agent to retrieve

        Returns:
            Agent instance of the requested type

        Raises:
            ValueError: If agent instance doesn't exist
        """
        if agent_type not in self._agent_instances:
            raise ValueError(f"No agent instance exists for type {agent_type.value}. "
                           f"Call create_agent() first.")

        return self._agent_instances[agent_type]

    def has_agent(self, agent_type: AgentType) -> bool:
        """Check if an agent instance exists for the given type.

        Args:
            agent_type: The agent type to check

        Returns:
            True if agent instance exists, False otherwise
        """
        return agent_type in self._agent_instances

    def remove_agent(self, agent_type: AgentType) -> None:
        """Remove an agent instance from the factory.

        Args:
            agent_type: The agent type to remove
        """
        if agent_type in self._agent_instances:
            del self._agent_instances[agent_type]
            logger.info("Agent instance removed", agent_type=agent_type.value)

    def get_registered_types(self) -> list[AgentType]:
        """Get list of registered agent types.

        Returns:
            List of registered agent types
        """
        return list(self._agent_classes.keys())

    def get_active_agents(self) -> Dict[AgentType, BaseAgent]:
        """Get all active agent instances.

        Returns:
            Dictionary mapping agent types to agent instances
        """
        return self._agent_instances.copy()

    def clear_all_agents(self) -> None:
        """Clear all agent instances from the factory."""
        self._agent_instances.clear()
        logger.info("All agent instances cleared")

    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory status information.

        Returns:
            Dictionary with factory status and statistics
        """
        adk_status = {}
        for agent_type, config in self._adk_agent_configs.items():
            adk_status[agent_type.value] = {
                "use_adk": config.get("use_adk", False),
                "rollout_percentage": config.get("rollout_percentage", 0),
                "has_instance": agent_type in self._agent_instances,
                "is_adk_instance": False
            }
            if agent_type in self._agent_instances:
                instance = self._agent_instances[agent_type]
                adk_status[agent_type.value]["is_adk_instance"] = getattr(instance, 'is_adk_agent', False)

        return {
            "registered_types": [t.value for t in self._agent_classes.keys()],
            "active_instances": [t.value for t in self._agent_instances.keys()],
            "total_registered": len(self._agent_classes),
            "total_active": len(self._agent_instances),
            "adk_status": adk_status
        }

    def update_adk_rollout(self, agent_type: AgentType, rollout_percentage: int) -> None:
        """Update ADK rollout percentage for an agent type.

        Args:
            agent_type: The agent type to update
            rollout_percentage: New rollout percentage (0-100)
        """
        if agent_type in self._adk_agent_configs:
            self._adk_agent_configs[agent_type]["rollout_percentage"] = max(0, min(100, rollout_percentage))
            logger.info("ADK rollout updated",
                       agent_type=agent_type.value,
                       rollout_percentage=rollout_percentage)


# Global agent factory instance
agent_factory = AgentFactory()


def get_agent_factory() -> AgentFactory:
    """Get the global agent factory instance.

    Returns:
        Global AgentFactory instance
    """
    return agent_factory
