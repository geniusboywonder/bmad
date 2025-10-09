"""AG-UI ADK Runtime - CopilotKit integration for BMAD ADK agents.

This module bridges BMAD's ADK agents with the CopilotKit frontend via AG-UI protocol.
"""

from typing import Dict, Any, Optional
from uuid import UUID
import structlog

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from app.utils.agent_prompt_loader import agent_prompt_loader
from app.copilot.hitl_aware_agent import HITLAwareLlmAgent

# Don't import settings at module level to avoid circular imports
# Settings will be imported inside functions when needed

logger = structlog.get_logger(__name__)


class BMADAGUIRuntime:
    """AG-UI Runtime for BMAD ADK agents with enterprise controls."""

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.adk_agents: Dict[str, ADKAgent] = {}



    def setup_fastapi_endpoints_sync(self, app: FastAPI):
        """Add AG-UI protocol endpoints to FastAPI app (synchronous version).

        NOTE: This must be called AFTER FastAPI app creation but BEFORE app.run()
        add_adk_fastapi_endpoint() requires synchronous registration.
        """

        # Import settings here to avoid circular imports
        from app.settings import settings
        import os

        # Set API keys in environment for AG-UI ADK to pick up
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        # Create agents using environment-configured models and dynamic prompts from markdown files
        # HITL instructions are now embedded in each agent's .md file
        analyst = HITLAwareLlmAgent(
            name="analyst",
            model=LiteLlm(model=settings.analyst_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("analyst")
        )

        architect = HITLAwareLlmAgent(
            name="architect",
            model=LiteLlm(model=settings.architect_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("architect")
        )

        coder = HITLAwareLlmAgent(
            name="coder",
            model=LiteLlm(model=settings.coder_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("coder")
        )

        orchestrator = HITLAwareLlmAgent(
            name="orchestrator",
            model=LiteLlm(model=settings.analyst_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("orchestrator")
        )

        tester = HITLAwareLlmAgent(
            name="tester",
            model=LiteLlm(model=settings.tester_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("tester")
        )

        deployer = HITLAwareLlmAgent(
            name="deployer",
            model=LiteLlm(model=settings.deployer_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("deployer")
        )

        # Wrap with ADK agents
        analyst_adk = ADKAgent(adk_agent=analyst, app_name="bmad_analyst", session_timeout_seconds=3600)
        architect_adk = ADKAgent(adk_agent=architect, app_name="bmad_architect", session_timeout_seconds=3600)
        coder_adk = ADKAgent(adk_agent=coder, app_name="bmad_coder", session_timeout_seconds=3600)
        orchestrator_adk = ADKAgent(adk_agent=orchestrator, app_name="bmad_orchestrator", session_timeout_seconds=3600)
        tester_adk = ADKAgent(adk_agent=tester, app_name="bmad_tester", session_timeout_seconds=3600)
        deployer_adk = ADKAgent(adk_agent=deployer, app_name="bmad_deployer", session_timeout_seconds=3600)

        # Store agents in dict
        self.adk_agents = {
            "analyst": analyst_adk,
            "architect": architect_adk,
            "coder": coder_adk,
            "orchestrator": orchestrator_adk,
            "tester": tester_adk,
            "deployer": deployer_adk
        }

        # Register each agent at a unique path
        # Frontend will use /api/copilotkit/{agent_name} based on selectedAgent state
        add_adk_fastapi_endpoint(app, analyst_adk, path="/api/copilotkit/analyst")
        add_adk_fastapi_endpoint(app, architect_adk, path="/api/copilotkit/architect")
        add_adk_fastapi_endpoint(app, coder_adk, path="/api/copilotkit/coder")
        add_adk_fastapi_endpoint(app, orchestrator_adk, path="/api/copilotkit/orchestrator")
        add_adk_fastapi_endpoint(app, tester_adk, path="/api/copilotkit/tester")
        add_adk_fastapi_endpoint(app, deployer_adk, path="/api/copilotkit/deployer")

        logger.info("AG-UI protocol endpoints registered synchronously",
                   endpoints=["/api/copilotkit/analyst", "/api/copilotkit/architect", "/api/copilotkit/coder",
                            "/api/copilotkit/orchestrator", "/api/copilotkit/tester", "/api/copilotkit/deployer"])


# Global runtime instance
bmad_agui_runtime = BMADAGUIRuntime()
