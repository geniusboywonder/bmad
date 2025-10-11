"""
Custom ADK LlmAgent that is aware of project policy gates and the HITL (Human-in-the-Loop) governor.
"""

import json
import asyncio
from uuid import UUID
from typing import List, Optional

import structlog
from google.adk.agents import LlmAgent
from a2a.types import Message

from app.database.connection import get_session_local
from app.services.hitl_counter_service import HitlCounterService
from app.services.orchestrator.phase_policy_service import PhasePolicyService, PolicyDecision
from app.websocket.events import WebSocketEvent, EventType
from app.websocket.manager import websocket_manager

logger = structlog.get_logger(__name__)


class HITLAwareLlmAgent(LlmAgent):
    """
    Intercepts policy violations and HITL tool calls before standard execution.
    """

    def run(self, messages: List[Message], **kwargs) -> Message:
        """
        Overrides the default run method to handle policy checks and HITL tool results.
        """
        session_id = kwargs.get("session_id")
        project_id = self._extract_project_id(session_id)
        logger.debug(
            "HITLAwareLlmAgent invocation",
            agent=self.name,
            session_id=session_id,
            extracted_project_id=str(project_id) if project_id else None,
            message_roles=[message.role for message in messages],
        )

        if messages:
            decision = self._evaluate_policy(project_id)
            if decision and decision.status == "denied":
                logger.warning(
                    "Policy violation intercepted",
                    project_id=str(project_id) if project_id else None,
                    agent_type=self.name,
                    current_phase=decision.current_phase,
                    allowed_agents=decision.allowed_agents,
                )
                self._broadcast_policy_violation(project_id, decision)
                allowed_text = ", ".join(decision.allowed_agents) or "None"
                violation_message = (
                    "🚫 **Policy Violation**\n\n"
                    f"{decision.message}\n\n"
                    f"**Current Phase:** {decision.current_phase}\n"
                    f"**Allowed Agents:** {allowed_text}"
                )
                return Message(role="assistant", content=violation_message)

        if messages and messages[-1].role == "tool" and messages[-1].name == "reconfigureHITL":
            logger.info("HITL-aware agent detected 'reconfigureHITL' tool call result.")

            tool_message = messages[-1]

            try:
                if not project_id:
                    project_id = self._extract_project_id(kwargs.get("session_id"))
                if not project_id:
                    raise ValueError("Project ID missing from session.")

                response_data = json.loads(tool_message.content)
                new_limit = response_data.get("newLimit")
                new_status = response_data.get("newStatus")

                logger.info(
                    "Processing HITL reconfiguration from tool call.",
                    project_id=str(project_id),
                    new_limit=new_limit,
                    new_status=new_status,
                )

                hitl_service = HitlCounterService()
                hitl_service.update_settings(
                    project_id=project_id,
                    new_limit=new_limit,
                    new_status=new_status,
                )

                new_messages = messages[:-2]
                logger.info("Retrying original user request after HITL reconfiguration.", project_id=str(project_id))
                return super().run(messages=new_messages, **kwargs)

            except (json.JSONDecodeError, ValueError, TypeError) as exc:
                logger.error("Failed to process 'reconfigureHITL' tool result.", error=str(exc))
                new_messages = messages[:-1]
                return super().run(messages=new_messages, **kwargs)

        return super().run(messages=messages, **kwargs)

    def _extract_project_id(self, session_id: Optional[str]) -> Optional[UUID]:
        if not session_id:
            return None
        try:
            return UUID(session_id)
        except (ValueError, TypeError):
            pass

        if "-agent-" in session_id:
            candidate = session_id.split("-agent-")[0]
            try:
                return UUID(candidate)
            except ValueError:
                logger.debug("Failed to parse project ID from session", session_id=session_id)
        return None

    def _evaluate_policy(self, project_id: Optional[UUID]) -> Optional[PolicyDecision]:
        if project_id is None:
            allowed = ["analyst", "orchestrator"]
            if self.name in allowed:
                return PolicyDecision(
                    status="allowed",
                    current_phase="unknown",
                    allowed_agents=allowed,
                    message="Allowed without project context."
                )
            return PolicyDecision(
                status="denied",
                reason_code="missing_project",
                message="Project context is missing; only analyst or orchestrator may run until a project is selected.",
                current_phase="unknown",
                allowed_agents=allowed,
            )

        SessionLocal = get_session_local()
        session = SessionLocal()
        try:
            service = PhasePolicyService(session)
            return service.evaluate(str(project_id), self.name)
        except Exception as exc:
            logger.error(
                "Failed to evaluate policy",
                project_id=str(project_id),
                agent_type=self.name,
                error=str(exc),
                exc_info=True,
            )
            return None
        finally:
            session.close()

    def _broadcast_policy_violation(self, project_id: Optional[UUID], decision: PolicyDecision) -> None:
        if project_id is None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.debug("No running loop for policy violation broadcast", project_id=str(project_id))
            return

        event = WebSocketEvent(
            event_type=EventType.POLICY_VIOLATION,
            project_id=project_id,
            data={
                "status": decision.status,
                "reason_code": decision.reason_code,
                "message": decision.message,
                "current_phase": decision.current_phase,
                "allowed_agents": decision.allowed_agents,
            },
        )
        loop.create_task(websocket_manager.broadcast_to_project(project_id, event))
