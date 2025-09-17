"""OpenAI provider."""
import os
from typing import Dict, Any, List

from autogen_ext.models.openai import OpenAIChatCompletionClient

from .base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")

    async def generate(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        client = OpenAIChatCompletionClient(model=model, api_key=self.api_key, **kwargs)
        response = await client.create(messages=messages)
        return response.choices[0].message.content

    def get_models(self) -> List[str]:
        """Get a list of available models for the provider."""
        # This should ideally be a dynamic call to the OpenAI API
        return ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]
