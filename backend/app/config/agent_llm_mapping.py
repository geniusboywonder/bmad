"""Agent-to-LLM Provider Configuration System.

This module provides environment-based configuration for mapping agents to specific LLM providers.
Supports dynamic provider selection based on agent type and task requirements.
"""

import os
from typing import Dict, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GEMINI = "gemini"


class AgentLLMConfig(BaseModel):
    """Configuration for a specific agent's LLM provider assignment."""

    provider: LLMProvider = Field(description="LLM provider to use")
    model: str = Field(description="Specific model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    api_key_env_var: Optional[str] = Field(default=None, description="Environment variable for API key")

    model_config = ConfigDict(use_enum_values=True)


class AgentLLMMapping:
    """Manages agent-to-LLM provider mappings with environment variable support."""

    def __init__(self):
        self._mappings: Dict[str, AgentLLMConfig] = {}
        self._load_mappings()

    def _load_mappings(self):
        """Load agent-to-LLM mappings from environment variables."""

        # Default agent mappings (can be overridden by environment variables)
        default_mappings = {
            "analyst": AgentLLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-5-sonnet-20241022",
                temperature=0.3,  # Lower temperature for analytical work
                api_key_env_var="ANTHROPIC_API_KEY"
            ),
            "architect": AgentLLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o",
                temperature=0.2,  # Very low temperature for technical accuracy
                api_key_env_var="OPENAI_API_KEY"
            ),
            "coder": AgentLLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o",
                temperature=0.1,  # Very low temperature for code generation
                api_key_env_var="OPENAI_API_KEY"
            ),
            "tester": AgentLLMConfig(
                provider=LLMProvider.GEMINI,
                model="gemini-1.5-pro",
                temperature=0.4,  # Moderate temperature for test case generation
                api_key_env_var="GOOGLE_API_KEY"
            ),
            "deployer": AgentLLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o",
                temperature=0.2,  # Low temperature for deployment instructions
                api_key_env_var="OPENAI_API_KEY"
            ),
            "orchestrator": AgentLLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o",
                temperature=0.5,  # Moderate temperature for coordination
                api_key_env_var="OPENAI_API_KEY"
            )
        }

        # Override defaults with environment variables
        for agent_type, default_config in default_mappings.items():
            env_provider = os.getenv(f"{agent_type.upper()}_AGENT_PROVIDER")
            env_model = os.getenv(f"{agent_type.upper()}_AGENT_MODEL")
            env_temperature = os.getenv(f"{agent_type.upper()}_AGENT_TEMPERATURE")
            env_max_tokens = os.getenv(f"{agent_type.upper()}_AGENT_MAX_TOKENS")

            config = AgentLLMConfig(
                provider=LLMProvider(env_provider) if env_provider else default_config.provider,
                model=env_model if env_model else default_config.model,
                temperature=float(env_temperature) if env_temperature else default_config.temperature,
                max_tokens=int(env_max_tokens) if env_max_tokens else default_config.max_tokens,
                api_key_env_var=default_config.api_key_env_var
            )

            self._mappings[agent_type] = config

    def get_agent_config(self, agent_type: str) -> AgentLLMConfig:
        """Get LLM configuration for a specific agent type."""
        if agent_type not in self._mappings:
            raise ValueError(f"No LLM configuration found for agent type: {agent_type}")

        return self._mappings[agent_type]

    def get_all_mappings(self) -> Dict[str, AgentLLMConfig]:
        """Get all agent-to-LLM mappings."""
        return self._mappings.copy()

    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are available."""
        validation_results = {}

        for agent_type, config in self._mappings.items():
            if config.api_key_env_var:
                api_key = os.getenv(config.api_key_env_var)
                validation_results[agent_type] = api_key is not None and len(api_key.strip()) > 0
            else:
                validation_results[agent_type] = True  # No API key required

        return validation_results

    def get_provider_stats(self) -> Dict[str, int]:
        """Get statistics on provider usage across agents."""
        stats = {}
        for config in self._mappings.values():
            provider = config.provider.value
            stats[provider] = stats.get(provider, 0) + 1
        return stats


# Global instance for application-wide use
agent_llm_mapping = AgentLLMMapping()


def get_agent_llm_config(agent_type: str) -> AgentLLMConfig:
    """Convenience function to get agent LLM configuration."""
    return agent_llm_mapping.get_agent_config(agent_type)


def validate_all_api_keys() -> Dict[str, bool]:
    """Convenience function to validate all API keys."""
    return agent_llm_mapping.validate_api_keys()
