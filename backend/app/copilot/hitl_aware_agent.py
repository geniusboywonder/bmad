"""
Custom ADK LlmAgent that is aware of the HITL (Human-in-the-Loop) governor.
"""

import json
import structlog
from uuid import UUID
from typing import List, Dict, Any

from google.adk.agents import LlmAgent
from a2a.types import Message
from app.services.hitl_counter_service import HitlCounterService

logger = structlog.get_logger(__name__)

class HITLAwareLlmAgent(LlmAgent):
    """
    An LlmAgent that intercepts and processes HITL tool calls before standard execution.
    """

    def run(self, messages: List[Message], **kwargs) -> Message:
        """
        Overrides the default run method to handle HITL tool results.

        Args:
            messages: The history of messages in the conversation.
            **kwargs: Additional arguments, including 'session_id'.

        Returns:
            The agent's response message.
        """
        session_id = kwargs.get("session_id")

        if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
            logger.info("HITL-aware agent detected 'reconfigureHITL' tool call result.")

            tool_message = messages[-1]

            try:
                # The project_id is assumed to be the session_id for this implementation.
                project_id = UUID(session_id)

                # The content of the tool message is the JSON response from the frontend.
                response_data = json.loads(tool_message.content)
                new_limit = response_data.get("newLimit")
                new_status = response_data.get("newStatus")

                logger.info(
                    "Processing HITL reconfiguration from tool call.",
                    project_id=str(project_id),
                    new_limit=new_limit,
                    new_status=new_status,
                )

                # Update the settings in Redis using the HitlCounterService.
                hitl_service = HitlCounterService()
                hitl_service.update_settings(
                    project_id=project_id,
                    new_limit=new_limit,
                    new_status=new_status,
                )

                # The original request is now two messages back in the history.
                # We strip off the tool result and the assistant's tool call message
                # to effectively retry the last user message.
                logger.info("Retrying original user request after HITL reconfiguration.", project_id=str(project_id))
                new_messages = messages[:-2]

                # Re-run the agent with the truncated history.
                return super().run(messages=new_messages, **kwargs)

            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.error("Failed to parse 'reconfigureHITL' tool result.", error=str(e))
                # Let the agent proceed, but without the confusing tool message.
                new_messages = messages[:-1]
                return super().run(messages=new_messages, **kwargs)

        # If no HITL tool message is found, proceed with the normal agent execution.
        return super().run(messages=messages, **kwargs)

