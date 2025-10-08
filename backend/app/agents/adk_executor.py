"""ADK Agent Executor - Executes ADK agents with BMAD enterprise controls.

This module provides ADK agent execution for HITL-controlled tasks.
Replaces the abandoned MAF integration with proven ADK implementation.
"""

from typing import Dict, Any, List
import structlog
import json
import uuid
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact
from app.utils.agent_prompt_loader import agent_prompt_loader
from app.services.hitl_counter_service import HitlCounterService

logger = structlog.get_logger(__name__)


class ADKAgentExecutor:
    """Executes ADK agents with BMAD enterprise controls."""

    def __init__(self, agent_type: str):
        """Initialize ADK executor for specific agent type.

        Args:
            agent_type: Type of agent (analyst, architect, coder, tester, deployer, orchestrator)
        """
        self.agent_type = agent_type
        self.logger = logger.bind(agent_type=agent_type)

        # Get agent configuration
        from app.settings import settings

        # Get model for this agent type
        model_attr = f"{agent_type}_agent_model"
        provider_attr = f"{agent_type}_agent_provider"

        self.model = getattr(settings, model_attr, settings.llm_model)
        self.provider = getattr(settings, provider_attr, settings.llm_provider)

        # Load agent instructions from markdown file
        self.instructions = agent_prompt_loader.get_agent_prompt(agent_type)

        # Create ADK LlmAgent
        self.adk_agent = LlmAgent(
            name=agent_type,
            model=LiteLlm(model=self.model),
            instruction=self.instructions
        )

        self.logger.info("ADK agent executor initialized",
                        model=self.model,
                        provider=self.provider)

    async def execute_task(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute task using ADK agent.

        Args:
            task: Task to execute
            handoff: Handoff schema with agent coordination info
            context_artifacts: Context artifacts for the task

        Returns:
            Task execution result with status and output
        """
        try:
            # Prepare context message from artifacts
            context_messages = []
            for artifact in context_artifacts:
                context_messages.append({
                    "role": "system",
                    "content": f"Context: {artifact.artifact_type}\n{artifact.content}"
                })

            # Prepare user message with task instructions
            user_message = self._prepare_task_message(task, handoff)

            # Initialize HITL Counter Service
            hitl_counter_service = HitlCounterService()

            # --- HITL Governor Logic ---
            # Check if the agent's action is allowed
            is_action_allowed, _ = hitl_counter_service.check_and_decrement_counter(task.project_id)

            if not is_action_allowed:
                self.logger.warning("HITL Governor: Action limit reached. Overriding user message to instruct LLM to call reconfigureHITL tool.", task_id=str(task.id))

                # Get current settings to pass to the frontend prompt
                current_settings = hitl_counter_service.get_settings(task.project_id)

                # This new instruction overrides the original user_message for this turn.
                user_message = f"""
                Your action limit has been reached. You MUST call the 'reconfigureHITL' tool to ask the user for new settings.
                The current settings are: actionLimit: {current_settings.get('limit')}, isHitlEnabled: {current_settings.get('enabled')}.
                Do not respond with any other text or tools. Call the 'reconfigureHITL' tool now.
                """
            # --- End of HITL Governor Logic ---

            # Execute ADK agent
            self.logger.info("Executing ADK agent",
                           task_id=str(task.id),
                           handoff_from=handoff.from_agent if handoff else None,
                           context_count=len(context_artifacts))

            # ADK agent run - simplified synchronous call
            # For async execution, use: response = await self.adk_agent.run_async(user_message)
            response = self.adk_agent.run(user_message)

            # Extract response content
            result_content = self._extract_response_content(response)

            self.logger.info("ADK agent execution complete",
                           task_id=str(task.id),
                           success=True,
                           response_length=len(result_content))

            return {
                "status": "completed",
                "success": True,
                "output": result_content,
                "agent_type": self.agent_type,
                "task_id": str(task.id),
                "model_used": self.model
            }

        except Exception as e:
            self.logger.error("ADK agent execution failed",
                            task_id=str(task.id),
                            error=str(e),
                            exc_info=True)

            return {
                "status": "failed",
                "success": False,
                "error": str(e),
                "agent_type": self.agent_type,
                "task_id": str(task.id)
            }

    def _prepare_task_message(self, task: Task, handoff: HandoffSchema) -> str:
        """Prepare task message for ADK agent.

        Args:
            task: Task to execute
            handoff: Handoff schema with coordination info

        Returns:
            Formatted task message
        """
        message_parts = []

        # Add handoff context if available
        if handoff:
            message_parts.append(f"**Handoff from {handoff.from_agent}**")
            if handoff.context:
                message_parts.append(f"Context: {handoff.context}")
            if handoff.deliverables:
                message_parts.append(f"Expected deliverables: {', '.join(handoff.deliverables)}")

        # Add task instructions
        message_parts.append(f"**Task**: {task.instructions}")

        # Add expected outputs if specified
        if task.expected_outputs:
            message_parts.append(f"**Expected outputs**: {task.expected_outputs}")

        return "\n\n".join(message_parts)

    def _extract_response_content(self, response) -> str:
        """Extract content from ADK agent response.

        Args:
            response: ADK agent response object

        Returns:
            Extracted text content
        """
        # ADK response structure varies by version
        # Try multiple extraction methods

        # Method 1: Direct string response
        if isinstance(response, str):
            return response

        # Method 2: Response object with content attribute
        if hasattr(response, 'content'):
            return str(response.content)

        # Method 3: Response object with text attribute
        if hasattr(response, 'text'):
            return str(response.text)

        # Method 4: Response object with message attribute
        if hasattr(response, 'message'):
            if isinstance(response.message, str):
                return response.message
            if hasattr(response.message, 'content'):
                return str(response.message.content)

        # Fallback: stringify the response
        return str(response)
