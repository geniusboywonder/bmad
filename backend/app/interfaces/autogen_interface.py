"""
AutoGen Service Interface - Interface definitions for AutoGen services.

Defines interfaces for all AutoGen-related services following Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from autogen_agentchat.agents import AssistantAgent

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact


class IAutoGenCore(ABC):
    """Interface for AutoGen core coordination service."""

    @abstractmethod
    async def execute_task(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute a task using AutoGen agents."""
        pass

    @abstractmethod
    def create_agent(self, agent_type: str, system_message: str) -> AssistantAgent:
        """Create an AutoGen agent based on agent type."""
        pass

    @abstractmethod
    def cleanup_agent(self, agent_name: str):
        """Clean up an agent and its resources."""
        pass

    @abstractmethod
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for monitoring."""
        pass


class IAgentFactory(ABC):
    """Interface for AutoGen agent creation and management."""

    @abstractmethod
    def create_agent(self, agent_type: str, system_message: str) -> AssistantAgent:
        """Create an AutoGen agent based on agent type."""
        pass

    @abstractmethod
    def get_or_create_agent(self, agent_type: str, system_message: str) -> AssistantAgent:
        """Get existing agent or create a new one."""
        pass

    @abstractmethod
    def cleanup_agent(self, agent_name: str):
        """Clean up an agent and its resources."""
        pass

    @abstractmethod
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""
        pass

    @abstractmethod
    def get_agent_by_name(self, agent_name: str) -> AssistantAgent:
        """Get agent by name."""
        pass

    @abstractmethod
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available agents."""
        pass


class IConversationManager(ABC):
    """Interface for AutoGen conversation management."""

    @abstractmethod
    async def execute_group_chat(
        self,
        agents: List[AssistantAgent],
        message: str,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute group chat conversation."""
        pass

    @abstractmethod
    async def execute_single_agent_conversation(
        self,
        agent: AssistantAgent,
        message: str,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute single agent conversation."""
        pass

    @abstractmethod
    def prepare_context_message(
        self,
        context_artifacts: List[ContextArtifact],
        handoff: HandoffSchema
    ) -> str:
        """Prepare context message from artifacts for the agent."""
        pass

    @abstractmethod
    async def run_single_agent_conversation(
        self,
        agent: AssistantAgent,
        message: str,
        task: Task
    ) -> str:
        """Run a conversation with a single agent with comprehensive reliability features."""
        pass

    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for monitoring."""
        pass