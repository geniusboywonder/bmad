"""Base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get a list of available models for the provider."""
        pass
