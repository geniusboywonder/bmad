"""Adapter for AutoGen model client."""
from typing import Any, Dict, List, Optional
from autogen_core.base import Agent, Message, ModelClient
from .base_provider import BaseProvider

class AutoGenModelClientAdapter(ModelClient):
    """Adapter to make BaseProvider compatible with AutoGen's ModelClient."""

    def __init__(self, provider: BaseProvider, model: str, **kwargs):
        self.provider = provider
        self.model = model
        self.kwargs = kwargs

    def create(self, params: Dict[str, Any]) -> ModelClient.CompletionMessage:
        """Create a completion."""
        messages = params.get("messages", [])
        response_text = self.provider.generate(self.model, messages, **self.kwargs)
        return ModelClient.CompletionMessage(content=response_text, role="assistant")

    def message_retrieval(self, response: Any) -> List[str]:
        """Retrieve messages from a response."""
        return [response.choices[0].message.content]

    @property
    def model_name(self) -> str:
        return self.model
