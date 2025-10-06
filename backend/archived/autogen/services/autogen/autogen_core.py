"""
AutoGen Core Service - Main coordination logic with dependency injection.

Handles main AutoGen coordination and delegates to specialized services.
Maintains backward compatibility while following SOLID principles.
"""

from typing import Dict, List, Any
from uuid import UUID
import structlog

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact
from .agent_factory import AgentFactory
from .conversation_manager import ConversationManager

logger = structlog.get_logger(__name__)


class AutoGenCore:
    """
    Core AutoGen service that coordinates specialized components.

    Follows Single Responsibility Principle by delegating specialized tasks
    to focused service components.
    """

    def __init__(self):
        # Initialize specialized services
        self.agent_factory = AgentFactory()
        self.conversation_manager = ConversationManager()

        logger.info("AutoGen core service initialized with specialized components")

    async def execute_task(self, task: Task, handoff: HandoffSchema, context_artifacts: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute a task using AutoGen agents."""

        logger.info("Executing task with AutoGen",
                   task_id=task.task_id,
                   agent_type=task.agent_type)

        try:
            if handoff.is_group_chat and handoff.group_chat_agents:
                # Group chat logic
                return await self._execute_group_chat_task(task, handoff, context_artifacts)
            else:
                # Single agent logic
                return await self._execute_single_agent_task(task, handoff, context_artifacts)

        except Exception as e:
            logger.error("Task execution failed",
                        task_id=task.task_id,
                        error=str(e))
            return {
                "success": False,
                "agent_type": task.agent_type,
                "task_id": str(task.task_id),
                "error": str(e),
                "context_used": [str(artifact.context_id) for artifact in context_artifacts]
            }

    async def _execute_group_chat_task(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute group chat task."""

        agents_for_chat = []
        for agent_type in handoff.group_chat_agents:
            agent = self.agent_factory.get_or_create_agent(agent_type, handoff.instructions)
            agents_for_chat.append(agent)

        return await self.conversation_manager.execute_group_chat(
            agents_for_chat,
            handoff.instructions,
            task,
            handoff,
            context_artifacts
        )

    async def _execute_single_agent_task(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute single agent task."""

        agent = self.agent_factory.get_or_create_agent(task.agent_type, handoff.instructions)

        return await self.conversation_manager.execute_single_agent_conversation(
            agent,
            handoff.instructions,
            task,
            handoff,
            context_artifacts
        )

    def create_agent(self, agent_type: str, system_message: str):
        """Create an AutoGen agent based on agent type."""
        return self.agent_factory.create_agent(agent_type, system_message)

    def cleanup_agent(self, agent_name: str):
        """Clean up an agent and its resources."""
        self.agent_factory.cleanup_agent(agent_name)

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""
        return self.agent_factory.get_agent_status(agent_name)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for monitoring."""
        return self.conversation_manager.get_usage_stats()

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available agents."""
        return self.agent_factory.list_agents()

    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        return {
            "agents_created": len(self.agent_factory.agents),
            "usage_stats": self.conversation_manager.get_usage_stats()
        }