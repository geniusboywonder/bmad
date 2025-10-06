"""
BMAD MAF Wrapper - Integration layer for Microsoft Agent Framework with enterprise controls.

This wrapper combines Microsoft Agent Framework (MAF) for agent orchestration
with BMAD's enterprise features: HITL controls, audit trails, and budget management.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import structlog
from datetime import datetime, timezone

from agent_framework import ChatAgent, ChatMessage, Role, TextContent, ChatContext
from google.adk.models.lite_llm import LiteLlm  # ADK for LLM access

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact
from app.services.hitl_safety_service import HITLSafetyService
from app.utils.agent_prompt_loader import agent_prompt_loader
from app.settings import settings

logger = structlog.get_logger(__name__)


class BMADMAFWrapper:
    """
    Integration wrapper combining MAF with BMAD enterprise features.

    This class provides:
    - MAF agent orchestration (replaces AutoGen)
    - ADK LLM access (OpenAI, Anthropic, Google)
    - HITL pre-execution approval
    - Budget tracking and limits
    - Audit trail logging
    """

    def __init__(self, agent_type: str):
        """
        Initialize BMAD MAF wrapper.

        Args:
            agent_type: Type of agent (analyst, architect, coder, tester, deployer, orchestrator)
        """
        self.agent_type = agent_type

        # Load agent instructions from markdown files
        self.instructions = agent_prompt_loader.get_agent_prompt(agent_type)

        # Get agent-specific LLM settings
        provider = getattr(settings, f"{agent_type}_agent_provider", settings.llm_provider)
        model = getattr(settings, f"{agent_type}_agent_model", settings.llm_model)

        # Create MAF ChatAgent with ADK LLM
        self.maf_agent = ChatAgent(
            name=agent_type,
            instructions=self.instructions,
            model=LiteLlm(model=model)
        )

        # BMAD enterprise services
        self.hitl_service = HITLSafetyService()

        logger.info("BMADMAFWrapper initialized",
                   agent_type=agent_type,
                   provider=provider,
                   model=model)

    async def execute_task(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """
        Execute task with full BMAD enterprise controls.

        This is the main entry point that replaces AutoGenService.execute_task().

        Args:
            task: Task to execute
            handoff: Handoff schema with context
            context_artifacts: List of context artifacts

        Returns:
            Dictionary with execution results
        """
        try:
            logger.info("Executing task with MAF agent",
                       task_id=str(task.task_id),
                       agent_type=self.agent_type)

            # 1. HITL Pre-Execution Approval (BMAD responsibility)
            # Note: This is already handled by agent_tasks.py before calling execute_task
            # We don't duplicate HITL approval here

            # 2. Prepare MAF chat context
            chat_context = self._prepare_chat_context(task, handoff, context_artifacts)

            # 3. Execute MAF agent
            maf_response = await self.maf_agent.run(chat_context)

            # 4. Process MAF response
            result = self._process_maf_response(maf_response, task)

            # 5. Log execution (audit trail)
            logger.info("Task executed successfully with MAF",
                       task_id=str(task.task_id),
                       agent_type=self.agent_type,
                       tokens_used=result.get("tokens_used", 0))

            return result

        except Exception as e:
            logger.error("MAF task execution failed",
                        task_id=str(task.task_id),
                        agent_type=self.agent_type,
                        error=str(e))

            return {
                "success": False,
                "agent_type": self.agent_type,
                "task_id": str(task.task_id),
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _prepare_chat_context(
        self,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> ChatContext:
        """Prepare MAF chat context from BMAD task and context."""

        # Build context string from artifacts
        context_str = ""
        if context_artifacts:
            context_str = "\\n\\n".join([
                f"Context {i+1} ({artifact.artifact_type}):\\n{artifact.content}"
                for i, artifact in enumerate(context_artifacts)
            ])

        # Create user message with task instructions and context
        user_message = f"""Task Instructions:
{task.instructions}

Context Information:
{context_str}

Handoff Information:
- From: {handoff.from_agent}
- Phase: {handoff.phase}
- Expected Outputs: {', '.join(handoff.expected_outputs)}
"""

        # Create MAF chat context
        chat_context = ChatContext(
            messages=[
                ChatMessage(
                    role=Role.USER,
                    content=[TextContent(text=user_message)]
                )
            ]
        )

        return chat_context

    def _process_maf_response(
        self,
        maf_response: Any,
        task: Task
    ) -> Dict[str, Any]:
        """Process MAF response into BMAD result format."""

        # Extract text content from MAF response
        output_text = ""
        if hasattr(maf_response, 'messages'):
            for message in maf_response.messages:
                if message.role == Role.ASSISTANT:
                    for content in message.content:
                        if isinstance(content, TextContent):
                            output_text += content.text + "\\n"

        # Extract token usage if available
        tokens_used = 0
        if hasattr(maf_response, 'usage'):
            tokens_used = maf_response.usage.total_tokens if maf_response.usage else 0

        # Build BMAD result format (compatible with AutoGen format)
        result = {
            "success": True,
            "agent_type": self.agent_type,
            "task_id": str(task.task_id),
            "output": {
                "message": output_text.strip(),
                "agent_type": self.agent_type
            },
            "tokens_used": tokens_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "framework": "maf"  # Identifier to distinguish from AutoGen
        }

        return result

    async def validate_with_hitl(
        self,
        project_id: UUID,
        task_id: UUID,
        estimated_tokens: int = 100
    ) -> bool:
        """
        Validate task execution with HITL controls.

        Returns:
            True if approved, False if denied
        """
        try:
            # Check emergency stop
            if await self.hitl_service._is_emergency_stopped():
                logger.warning("Emergency stop active, denying execution",
                              task_id=str(task_id))
                return False

            # Check budget limits
            budget_check = await self.hitl_service.check_budget_limits(
                project_id, self.agent_type, estimated_tokens
            )

            if not budget_check.approved:
                logger.warning("Budget limit exceeded",
                              task_id=str(task_id),
                              reason=budget_check.reason)
                return False

            return True

        except Exception as e:
            logger.error("HITL validation failed",
                        task_id=str(task_id),
                        error=str(e))
            return False
