"""
Hybrid MAF + ADK AG-UI Runtime - CopilotKit integration for BMAD.

This uses ADK for AG-UI protocol (frontend compatibility) but MAF for backend execution.
Frontend → ADK AG-UI protocol → Backend MAF execution with HITL controls.
"""

from typing import Dict, Any, Optional
from uuid import UUID
import structlog
from fastapi import FastAPI

# AG-UI protocol via ADK (MAF doesn't have AG-UI support yet)
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from app.utils.agent_prompt_loader import agent_prompt_loader
# Note: BMADMAFWrapper not imported here - only used in agent_tasks.py

logger = structlog.get_logger(__name__)


class BMADMAFAGUIRuntime:
    """
    Hybrid runtime: ADK for AG-UI protocol + MAF for backend execution.

    Architecture:
    - Frontend: CopilotKit uses AG-UI protocol
    - Protocol Layer: ADK handles AG-UI GraphQL (works with CopilotKit)
    - Execution Layer: MAF handles actual agent execution (via BMADMAFWrapper)
    - HITL Layer: BMAD enterprise controls in agent_tasks.py
    """

    def __init__(self):
        self.adk_agents: Dict[str, ADKAgent] = {}

    def setup_fastapi_endpoints_with_hitl(self, app: FastAPI):
        """
        Setup AG-UI endpoints that use ADK protocol but MAF execution.

        Note: Backend execution (agent_tasks.py) uses MAF via BMADMAFWrapper.
        This runtime only provides CopilotKit frontend interface via ADK AG-UI.
        """
        from app.settings import settings
        import os

        # Set API keys for ADK LLM access
        if settings.openai_api_key:
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        if settings.google_api_key:
            os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        if settings.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        # Create ADK agents for AG-UI protocol (frontend interface)
        # Note: These are ONLY for CopilotKit UI, not for actual execution
        # Actual execution happens in agent_tasks.py via BMADMAFWrapper

        analyst = LlmAgent(
            name="analyst",
            model=LiteLlm(model=settings.analyst_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("analyst")
        )

        architect = LlmAgent(
            name="architect",
            model=LiteLlm(model=settings.architect_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("architect")
        )

        coder = LlmAgent(
            name="coder",
            model=LiteLlm(model=settings.coder_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("coder")
        )

        orchestrator = LlmAgent(
            name="orchestrator",
            model=LiteLlm(model=settings.analyst_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("orchestrator")
        )

        tester = LlmAgent(
            name="tester",
            model=LiteLlm(model=settings.tester_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("tester")
        )

        deployer = LlmAgent(
            name="deployer",
            model=LiteLlm(model=settings.deployer_agent_model),
            instruction=agent_prompt_loader.get_agent_prompt("deployer")
        )

        # Wrap with ADK agents for AG-UI protocol
        analyst_adk = ADKAgent(adk_agent=analyst, app_name="bmad_analyst", session_timeout_seconds=3600)
        architect_adk = ADKAgent(adk_agent=architect, app_name="bmad_architect", session_timeout_seconds=3600)
        coder_adk = ADKAgent(adk_agent=coder, app_name="bmad_coder", session_timeout_seconds=3600)
        orchestrator_adk = ADKAgent(adk_agent=orchestrator, app_name="bmad_orchestrator", session_timeout_seconds=3600)
        tester_adk = ADKAgent(adk_agent=tester, app_name="bmad_tester", session_timeout_seconds=3600)
        deployer_adk = ADKAgent(adk_agent=deployer, app_name="bmad_deployer", session_timeout_seconds=3600)

        # Add AG-UI endpoints for CopilotKit frontend
        add_adk_fastapi_endpoint(app, analyst_adk, path="/api/copilotkit/analyst")
        add_adk_fastapi_endpoint(app, architect_adk, path="/api/copilotkit/architect")
        add_adk_fastapi_endpoint(app, coder_adk, path="/api/copilotkit/coder")
        add_adk_fastapi_endpoint(app, orchestrator_adk, path="/api/copilotkit/orchestrator")
        add_adk_fastapi_endpoint(app, tester_adk, path="/api/copilotkit/tester")
        add_adk_fastapi_endpoint(app, deployer_adk, path="/api/copilotkit/deployer")

        logger.info("Hybrid MAF+ADK AG-UI endpoints registered",
                   protocol="ADK AG-UI (CopilotKit frontend)",
                   execution="MAF (via BMADMAFWrapper in agent_tasks.py)",
                   endpoints=["/api/copilotkit/analyst", "/api/copilotkit/architect", "/api/copilotkit/coder",
                            "/api/copilotkit/orchestrator", "/api/copilotkit/tester", "/api/copilotkit/deployer"])


# Global hybrid runtime instance
bmad_maf_agui_runtime = BMADMAFAGUIRuntime()
