"""
AutoGen Agent Factory - Handles agent creation and configuration.

Responsible for creating and configuring AutoGen agents with proper type-specific
system messages and LLM configurations. Implements TR-09: Load AutoGen agent
configurations from backend/app/agents/ directory.
"""

from typing import Dict, Any, List
from pathlib import Path
import re
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
        # Handle both project root and backend directory contexts
        if Path("backend/app").exists():
            self.bmad_core_path = Path("backend/app")
        else:
            self.bmad_core_path = Path("app")
        self.agent_configs = {}

        # Load AutoGen configurations on initialization (TR-09)
        self._load_autogen_configs()

        logger.info("Agent factory initialized with BMAD core configs",
                   configs_loaded=len(self.agent_configs))

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

    def _load_autogen_configs(self) -> None:
        """Load AutoGen agent configurations from backend/app/agents/ directory (TR-09)."""

        agents_path = self.bmad_core_path / "agents"

        if not agents_path.exists():
            logger.warning("BMAD Core agents directory not found",
                         path=str(agents_path))
            return

        logger.info("Loading AutoGen configurations from BMAD Core",
                   path=str(agents_path))

        config_files_found = 0
        for config_file in agents_path.glob("*.md"):
            try:
                agent_name = config_file.stem
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse agent configuration from markdown
                config = self._parse_agent_config(content, agent_name)
                if config:
                    self.agent_configs[agent_name] = config
                    config_files_found += 1
                    logger.debug("Loaded agent configuration",
                               agent_name=agent_name,
                               config_keys=list(config.keys()))

            except Exception as e:
                logger.error("Failed to load agent configuration",
                           file=str(config_file),
                           error=str(e))

        logger.info("AutoGen configurations loaded",
                   total_configs=config_files_found,
                   agents_configured=list(self.agent_configs.keys()))

    def _parse_agent_config(self, content: str, agent_name: str) -> Dict[str, Any]:
        """Parse agent configuration from markdown content."""

        config = {
            "agent_name": agent_name,
            "system_message": "",
            "llm_config": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7
            },
            "tools": [],
            "capabilities": [],
            "responsibilities": []
        }

        # Extract system message from markdown
        system_message = self._extract_system_message(content)
        if system_message:
            config["system_message"] = system_message

        # Extract LLM configuration
        llm_config = self._extract_llm_config(content)
        if llm_config:
            config["llm_config"].update(llm_config)

        # Extract tools and capabilities
        tools = self._extract_tools(content)
        if tools:
            config["tools"] = tools

        capabilities = self._extract_capabilities(content)
        if capabilities:
            config["capabilities"] = capabilities

        responsibilities = self._extract_responsibilities(content)
        if responsibilities:
            config["responsibilities"] = responsibilities

        # Extract agent-specific settings
        settings = self._extract_agent_settings(content)
        if settings:
            config.update(settings)

        logger.debug("Parsed agent configuration",
                   agent_name=agent_name,
                   has_system_message=bool(config["system_message"]),
                   tools_count=len(config["tools"]),
                   capabilities_count=len(config["capabilities"]))

        return config

    def _extract_system_message(self, content: str) -> str:
        """Extract system message from agent configuration markdown."""

        # Look for system message section
        patterns = [
            r"## System Message\s*\n(.*?)(?=\n##|\Z)",
            r"### System Message\s*\n(.*?)(?=\n###|\Z)",
            r"# System Message\s*\n(.*?)(?=\n#|\Z)",
            r"System Message:\s*\n(.*?)(?=\n\w+:|\Z)"
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                system_message = match.group(1).strip()
                # Clean up markdown formatting
                system_message = re.sub(r'^```.*?\n', '', system_message, flags=re.MULTILINE)
                system_message = re.sub(r'\n```$', '', system_message, flags=re.MULTILINE)
                return system_message

        # Fallback: extract from description or first paragraph
        description_match = re.search(r"(?:description|role):\s*(.+?)(?:\n\n|\Z)", content, re.IGNORECASE | re.DOTALL)
        if description_match:
            return description_match.group(1).strip()

        return ""

    def _extract_llm_config(self, content: str) -> Dict[str, Any]:
        """Extract LLM configuration from agent markdown."""

        llm_config = {}

        # Extract model configuration
        model_match = re.search(r"model:\s*([^\n]+)", content, re.IGNORECASE)
        if model_match:
            llm_config["model"] = model_match.group(1).strip()

        # Extract provider
        provider_match = re.search(r"provider:\s*([^\n]+)", content, re.IGNORECASE)
        if provider_match:
            llm_config["provider"] = provider_match.group(1).strip()

        # Extract temperature
        temp_match = re.search(r"temperature:\s*([0-9.]+)", content, re.IGNORECASE)
        if temp_match:
            llm_config["temperature"] = float(temp_match.group(1))

        # Extract max tokens
        tokens_match = re.search(r"max_tokens:\s*(\d+)", content, re.IGNORECASE)
        if tokens_match:
            llm_config["max_tokens"] = int(tokens_match.group(1))

        return llm_config

    def _extract_tools(self, content: str) -> List[str]:
        """Extract tools list from agent configuration."""

        tools = []

        # Look for tools section
        tools_section = re.search(r"## Tools\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if tools_section:
            tools_content = tools_section.group(1)
            # Extract list items
            tool_matches = re.findall(r"[-*]\s*([^\n]+)", tools_content)
            tools.extend([tool.strip() for tool in tool_matches])

        # Look for tools in YAML-like format
        tools_yaml = re.search(r"tools:\s*\n((?:\s*[-*]\s*[^\n]+\n?)+)", content, re.IGNORECASE)
        if tools_yaml:
            tool_matches = re.findall(r"[-*]\s*([^\n]+)", tools_yaml.group(1))
            tools.extend([tool.strip() for tool in tool_matches])

        return list(set(tools))  # Remove duplicates

    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities list from agent configuration."""

        capabilities = []

        # Look for capabilities section
        cap_section = re.search(r"## Capabilities\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if cap_section:
            cap_content = cap_section.group(1)
            cap_matches = re.findall(r"[-*]\s*([^\n]+)", cap_content)
            capabilities.extend([cap.strip() for cap in cap_matches])

        return capabilities

    def _extract_responsibilities(self, content: str) -> List[str]:
        """Extract responsibilities list from agent configuration."""

        responsibilities = []

        # Look for responsibilities section
        resp_section = re.search(r"## Responsibilities\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if resp_section:
            resp_content = resp_section.group(1)
            resp_matches = re.findall(r"[-*]\s*([^\n]+)", resp_content)
            responsibilities.extend([resp.strip() for resp in resp_matches])

        return responsibilities

    def _extract_agent_settings(self, content: str) -> Dict[str, Any]:
        """Extract additional agent settings from configuration."""

        settings = {}

        # Extract timeout settings
        timeout_match = re.search(r"timeout:\s*(\d+)", content, re.IGNORECASE)
        if timeout_match:
            settings["timeout"] = int(timeout_match.group(1))

        # Extract retry settings
        retry_match = re.search(r"max_retries:\s*(\d+)", content, re.IGNORECASE)
        if retry_match:
            settings["max_retries"] = int(retry_match.group(1))

        # Extract priority settings
        priority_match = re.search(r"priority:\s*([^\n]+)", content, re.IGNORECASE)
        if priority_match:
            settings["priority"] = priority_match.group(1).strip()

        return settings

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get loaded configuration for specific agent."""

        return self.agent_configs.get(agent_name, {})

    def reload_autogen_configs(self) -> int:
        """Reload AutoGen configurations from backend/app/agents/."""

        self.agent_configs.clear()
        self._load_autogen_configs()

        logger.info("AutoGen configurations reloaded",
                   configs_count=len(self.agent_configs))

        return len(self.agent_configs)

    def validate_agent_configs(self) -> Dict[str, Any]:
        """Validate loaded agent configurations."""

        validation_results = {
            "valid_configs": [],
            "invalid_configs": [],
            "warnings": []
        }

        for agent_name, config in self.agent_configs.items():
            try:
                # Validate required fields
                if not config.get("system_message"):
                    validation_results["warnings"].append(
                        f"{agent_name}: Missing system message"
                    )

                # Validate LLM config
                llm_config = config.get("llm_config", {})
                if not llm_config.get("model"):
                    validation_results["warnings"].append(
                        f"{agent_name}: Missing LLM model configuration"
                    )

                # Validate provider
                valid_providers = ["openai", "anthropic", "google", "local"]
                if llm_config.get("provider") not in valid_providers:
                    validation_results["warnings"].append(
                        f"{agent_name}: Invalid LLM provider"
                    )

                validation_results["valid_configs"].append(agent_name)

            except Exception as e:
                validation_results["invalid_configs"].append({
                    "agent_name": agent_name,
                    "error": str(e)
                })

        logger.info("Agent configuration validation completed",
                   valid=len(validation_results["valid_configs"]),
                   invalid=len(validation_results["invalid_configs"]),
                   warnings=len(validation_results["warnings"]))

        return validation_results