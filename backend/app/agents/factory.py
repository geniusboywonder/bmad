"""Agent factory for type-based agent instantiation."""

from typing import Dict, Type, Any
import structlog

from app.models.agent import AgentType
from app.agents.base_agent import BaseAgent

logger = structlog.get_logger(__name__)


class AgentFactory:
    """Factory class for creating agents based on agent type.
    
    This factory implements the Factory Pattern to create appropriate agent instances
    based on the requested agent type. It maintains a registry of agent classes
    and provides type-safe agent instantiation.
    """
    
    def __init__(self):
        """Initialize the agent factory with an empty registry."""
        self._agent_classes: Dict[AgentType, Type[BaseAgent]] = {}
        self._agent_instances: Dict[AgentType, BaseAgent] = {}
        
        logger.info("Agent factory initialized")
    
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
                    force_new: bool = False) -> BaseAgent:
        """Create or retrieve an agent instance of the specified type.
        
        Args:
            agent_type: The type of agent to create
            llm_config: LLM configuration for the agent
            force_new: If True, creates a new instance even if one exists
            
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
        
        # Return existing instance if available and not forcing new
        if not force_new and agent_type in self._agent_instances:
            logger.debug("Returning existing agent instance", agent_type=agent_type.value)
            return self._agent_instances[agent_type]
        
        # Create new agent instance
        agent_class = self._agent_classes[agent_type]
        
        try:
            agent_instance = agent_class(agent_type, llm_config)
            self._agent_instances[agent_type] = agent_instance
            
            logger.info("Agent instance created", 
                       agent_type=agent_type.value,
                       agent_class=agent_class.__name__)
            
            return agent_instance
            
        except Exception as e:
            logger.error("Failed to create agent instance", 
                        agent_type=agent_type.value,
                        agent_class=agent_class.__name__,
                        error=str(e))
            raise
    
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
        return {
            "registered_types": [t.value for t in self._agent_classes.keys()],
            "active_instances": [t.value for t in self._agent_instances.keys()],
            "total_registered": len(self._agent_classes),
            "total_active": len(self._agent_instances)
        }


# Global agent factory instance
agent_factory = AgentFactory()


def get_agent_factory() -> AgentFactory:
    """Get the global agent factory instance.
    
    Returns:
        Global AgentFactory instance
    """
    return agent_factory