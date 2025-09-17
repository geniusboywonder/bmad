"""Anthropic Claude provider with comprehensive error handling and retry logic."""
import os
import asyncio
from typing import Dict, Any, List, Optional
import structlog

import anthropic
from anthropic import APIError, APIConnectionError, RateLimitError, AuthenticationError

from .base_provider import BaseProvider

logger = structlog.get_logger(__name__)

class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider with production-ready features."""

    # Claude model configurations with optimal settings
    MODEL_CONFIGS = {
        "claude-3-5-sonnet-20241022": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 200000
        },
        "claude-3-5-haiku-20241022": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 200000
        },
        "claude-3-opus-20240229": {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 200000
        },
        "claude-3-sonnet-20240229": {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 200000
        }
    }

    def __init__(self, api_key: str = None, max_retries: int = 3, timeout: float = 30.0):
        """Initialize Anthropic provider with configuration."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")

        self.max_retries = max_retries
        self.timeout = timeout
        self.client = anthropic.AsyncAnthropic(
            api_key=self.api_key,
            max_retries=0,  # We handle retries ourselves
            timeout=self.timeout
        )

        logger.info("Anthropic provider initialized",
                   max_retries=max_retries,
                   timeout=timeout)

    async def generate(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from Claude with comprehensive error handling.

        Args:
            model: Claude model to use
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Generated response text

        Raises:
            ValueError: For invalid parameters
            RuntimeError: For API errors after retries
        """
        if model not in self.MODEL_CONFIGS:
            raise ValueError(f"Unsupported model: {model}. Available: {list(self.MODEL_CONFIGS.keys())}")

        # Get model configuration
        model_config = self.MODEL_CONFIGS[model]

        # Override with provided kwargs
        config = {**model_config, **kwargs}

        # Validate max_tokens doesn't exceed model limit
        if config.get("max_tokens", 0) > model_config["max_tokens"]:
            config["max_tokens"] = model_config["max_tokens"]
            logger.warning("Requested max_tokens exceeds model limit, using model maximum",
                         requested=kwargs.get("max_tokens"),
                         model_limit=model_config["max_tokens"])

        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)

        # Implement retry logic with exponential backoff
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info("Making Anthropic API call",
                           model=model,
                           attempt=attempt + 1,
                           max_attempts=self.max_retries + 1,
                           message_count=len(anthropic_messages))

                response = await self.client.messages.create(
                    model=model,
                    max_tokens=config["max_tokens"],
                    temperature=config.get("temperature", 0.7),
                    top_p=config.get("top_p", 0.9),
                    messages=anthropic_messages,
                    system=config.get("system", "")  # System message support
                )

                # Extract text from response
                if response.content and len(response.content) > 0:
                    text_content = response.content[0].text
                    logger.info("Anthropic API call successful",
                               model=model,
                               response_length=len(text_content),
                               usage=response.usage.model_dump() if response.usage else None)
                    return text_content
                else:
                    raise RuntimeError("Empty response from Anthropic API")

            except AuthenticationError as e:
                logger.error("Anthropic authentication error", error=str(e))
                raise RuntimeError(f"Anthropic authentication failed: {str(e)}")

            except RateLimitError as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning("Anthropic rate limit hit, retrying",
                                 attempt=attempt + 1,
                                 wait_time=wait_time,
                                 error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Anthropic rate limit exceeded, max retries reached", error=str(e))
                    raise RuntimeError(f"Anthropic rate limit exceeded: {str(e)}")

            except APIConnectionError as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning("Anthropic connection error, retrying",
                                 attempt=attempt + 1,
                                 wait_time=wait_time,
                                 error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Anthropic connection failed, max retries reached", error=str(e))
                    raise RuntimeError(f"Anthropic connection failed: {str(e)}")

            except APIError as e:
                logger.error("Anthropic API error",
                           error=str(e),
                           status_code=getattr(e, 'status_code', None))
                raise RuntimeError(f"Anthropic API error: {str(e)}")

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning("Unexpected error in Anthropic call, retrying",
                                 attempt=attempt + 1,
                                 wait_time=wait_time,
                                 error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Unexpected error in Anthropic call, max retries reached",
                               error=str(e))
                    break

        # If we get here, all retries failed
        error_msg = f"Anthropic API call failed after {self.max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        raise RuntimeError(error_msg)

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Convert generic message format to Anthropic format."""
        anthropic_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Map roles to Anthropic format
            if role == "system":
                # System messages are handled separately in Anthropic
                continue
            elif role == "user":
                anthropic_role = "user"
            elif role == "assistant":
                anthropic_role = "assistant"
            else:
                # Default to user for unknown roles
                anthropic_role = "user"
                logger.warning("Unknown message role, defaulting to user", role=role)

            anthropic_messages.append({
                "role": anthropic_role,
                "content": content
            })

        return anthropic_messages

    def get_models(self) -> List[str]:
        """Get a list of available Claude models."""
        return list(self.MODEL_CONFIGS.keys())

    def get_model_config(self, model: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.MODEL_CONFIGS.get(model, {})

    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the Anthropic API."""
        try:
            # Make a minimal API call to test connectivity
            test_messages = [{"role": "user", "content": "Hello"}]

            start_time = asyncio.get_event_loop().time()
            await self.generate("claude-3-5-haiku-20241022", test_messages, max_tokens=10)
            response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "provider": "anthropic"
            }

        except Exception as e:
            logger.error("Anthropic health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "anthropic"
            }
