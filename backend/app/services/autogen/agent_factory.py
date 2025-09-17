"""
AutoGen Agent Factory - Handles agent creation and configuration.

Responsible for creating and configuring AutoGen agents with proper type-specific
system messages and LLM configurations.
"""

from typing import Dict, Any
import structlog
from autogen_agentchat.agents import AssistantAgent

from app.models.agent import AgentType
from app.services.agent_team_service import AgentTeamService

logger = structlog.get_logger(__name__)


# Mock functions and classes for missing dependencies
def get_agent_adk_config(agent_type):
    """Mock function to get agent configuration."""
    return {
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    }


class ProviderFactory:
    @staticmethod
    def get_provider(provider_name):
        """Mock provider factory."""
        class MockProvider:
            def __init__(self):
                pass
        return MockProvider()


class AutoGenModelClientAdapter:
    def __init__(self, provider, model, temperature=0.7):
        self.provider = provider
        self.model = model
        self.temperature = temperature


class AgentFactory:
    """
    Factory for creating and configuring AutoGen agents.

    Follows Single Responsibility Principle by focusing solely on agent creation.
    """

    def __init__(self):
        self.agents: Dict[str, AssistantAgent] = {}
        self.agent_team_service = AgentTeamService()

        logger.info("Agent factory initialized")

    def create_agent(self, agent_type: str, system_message: str) -> AssistantAgent:
        """Create an AutoGen agent based on agent type."""

        agent_name = f"{agent_type}_agent"

        team_config = self.agent_team_service.load_team('fullstack')
        agent_config_from_team = team_config.get_agent_by_type(agent_type)

        if not agent_config_from_team:
            # Fallback to adk config if not in team
            agent_config = get_agent_adk_config(agent_type)
            if not agent_config or not agent_config.get("llm_config"):
                raise ValueError(f"LLM config not found for agent type: {agent_type}")
            llm_config = agent_config["llm_config"]
        else:
            llm_config = agent_config_from_team.get("llm_config", {})

        # Create model client
        provider = ProviderFactory.get_provider(llm_config["provider"])
        model_client = AutoGenModelClientAdapter(
            provider=provider,
            model=llm_config["model"],
            temperature=llm_config.get("temperature", 0.7)
        )

        # Create agent-specific system messages
        full_system_message = self._create_agent_system_message(agent_type, system_message)

        # Create the AssistantAgent with new API
        agent = AssistantAgent(
            name=agent_name,
            model_client=model_client,
            system_message=full_system_message,
            description=f"Agent specialized in {agent_type} tasks"
        )

        self.agents[agent_name] = agent
        logger.info("AutoGen agent created", agent_name=agent_name, agent_type=agent_type)

        return agent

    def _create_agent_system_message(self, agent_type: str, system_message: str) -> str:
        """Create agent-specific system messages based on agent type."""

        if agent_type == AgentType.ANALYST.value:
            return f"""You are a business analyst agent. {system_message}

            Your responsibilities:
            - Analyze business requirements and user needs
            - Create comprehensive project plans and specifications
            - Define functional and non-functional requirements
            - Validate requirements with stakeholders

            Always provide structured, detailed outputs in JSON format."""

        elif agent_type == AgentType.ARCHITECT.value:
            return f"""You are a software architect agent. {system_message}

            Your responsibilities:
            - Design system architecture and technical specifications
            - Create implementation plans and task breakdowns
            - Define technology stack and architectural decisions
            - Ensure scalability and maintainability

            Always provide structured, technical outputs in JSON format."""

        elif agent_type == AgentType.CODER.value:
            return f"""You are a software developer agent. {system_message}

            Your responsibilities:
            - Generate high-quality, production-ready code
            - Follow best practices and coding standards
            - Implement features based on specifications
            - Write clean, maintainable, and well-documented code

            Always provide code outputs with proper structure and documentation."""

        elif agent_type == AgentType.TESTER.value:
            return f"""You are a quality assurance tester agent. {system_message}

            Your responsibilities:
            - Create comprehensive test plans and test cases
            - Perform code reviews and quality assessments
            - Identify bugs and quality issues
            - Ensure code meets specifications and standards

            Always provide detailed test results and recommendations."""

        elif agent_type == AgentType.DEPLOYER.value:
            return f"""You are a deployment and DevOps agent. {system_message}

            Your responsibilities:
            - Create deployment strategies and configurations
            - Set up CI/CD pipelines and infrastructure
            - Monitor and maintain deployed applications
            - Ensure security and performance requirements

            Always provide deployment logs and status reports."""
        else:
            # Generic agent for other types
            return f"""You are a helpful assistant agent. {system_message}

            Follow instructions carefully and provide helpful, accurate responses."""

    def get_or_create_agent(self, agent_type: str, system_message: str) -> AssistantAgent:
        """Get existing agent or create a new one."""
        agent_name = f"{agent_type}_agent"

        if agent_name not in self.agents:
            return self.create_agent(agent_type, system_message)

        return self.agents[agent_name]

    def cleanup_agent(self, agent_name: str):
        """Clean up an agent and its resources."""

        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info("Agent cleaned up", agent_name=agent_name)

    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""

        if agent_name in self.agents:
            return {
                "exists": True,
                "name": agent_name,
                "active": True
            }
        else:
            return {
                "exists": False,
                "name": agent_name,
                "active": False
            }

    def get_agent_by_name(self, agent_name: str) -> AssistantAgent:
        """Get agent by name."""
        return self.agents.get(agent_name)

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all available agents."""
        return {
            name: {
                "name": name,
                "active": True,
                "type": name.replace("_agent", "")
            }
            for name in self.agents.keys()
        }