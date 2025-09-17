"""Factory for LLM providers."""
from typing import Dict, Type

from .base_provider import BaseProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider

class ProviderFactory:
    """Factory to get LLM providers."""

    _providers: Dict[str, Type[BaseProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GeminiProvider,
    }

    @staticmethod
    def get_provider(provider_name: str) -> BaseProvider:
        """Get a provider by name."""
        provider = ProviderFactory._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider()
