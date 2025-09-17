"""Google Gemini provider with comprehensive Vertex AI integration and error handling."""
import os
import asyncio
from typing import Dict, Any, List, Optional
import structlog

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, RetryError, ServiceUnavailable
from google.auth.exceptions import DefaultCredentialsError

from .base_provider import BaseProvider

logger = structlog.get_logger(__name__)

class GeminiProvider(BaseProvider):
    """Google Gemini provider with production-ready Vertex AI integration."""

    # Gemini model configurations with optimal settings
    MODEL_CONFIGS = {
        "gemini-2.0-flash-exp": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 1048576  # 1M tokens
        },
        "gemini-1.5-pro-latest": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 2097152  # 2M tokens
        },
        "gemini-1.5-flash-latest": {
            "max_tokens": 8192,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 1048576  # 1M tokens
        },
        "gemini-1.0-pro": {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": 32768  # 32K tokens
        }
    }

    def __init__(self, api_key: str = None, max_retries: int = 3, timeout: float = 30.0):
        """Initialize Gemini provider with configuration."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not provided. Set GOOGLE_API_KEY environment variable.")

        self.max_retries = max_retries
        self.timeout = timeout

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Set safety settings to be less restrictive for development
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

        logger.info("Gemini provider initialized",
                   max_retries=max_retries,
                   timeout=timeout)

    async def generate(self, model: str, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generate a response from Gemini with comprehensive error handling.

        Args:
            model: Gemini model to use
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

        # Convert messages to Gemini format
        gemini_messages = self._convert_messages(messages)

        # Implement retry logic with exponential backoff
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info("Making Gemini API call",
                           model=model,
                           attempt=attempt + 1,
                           max_attempts=self.max_retries + 1,
                           message_count=len(gemini_messages))

                # Create model with configuration
                generation_config = genai.types.GenerationConfig(
                    temperature=config.get("temperature", 0.7),
                    top_p=config.get("top_p", 0.9),
                    max_output_tokens=config["max_tokens"],
                    candidate_count=1
                )

                gemini_model = genai.GenerativeModel(
                    model_name=model,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )

                # Start chat session for conversation support
                chat = gemini_model.start_chat(history=[])

                # Send messages sequentially to maintain conversation context
                for msg in gemini_messages[:-1]:  # Send all but last as history
                    if msg["role"] == "user":
                        chat.send_message(msg["content"])

                # Send the final message and get response
                final_message = gemini_messages[-1]["content"]
                response = await chat.send_message_async(final_message)

                # Extract text from response
                if response.text:
                    logger.info("Gemini API call successful",
                               model=model,
                               response_length=len(response.text),
                               usage=getattr(response, 'usage_metadata', None))
                    return response.text
                else:
                    raise RuntimeError("Empty response from Gemini API")

            except DefaultCredentialsError as e:
                logger.error("Gemini authentication error", error=str(e))
                raise RuntimeError(f"Gemini authentication failed: {str(e)}")

            except ServiceUnavailable as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning("Gemini service unavailable, retrying",
                                 attempt=attempt + 1,
                                 wait_time=wait_time,
                                 error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Gemini service unavailable, max retries reached", error=str(e))
                    raise RuntimeError(f"Gemini service unavailable: {str(e)}")

            except GoogleAPIError as e:
                # Handle various Google API errors
                error_code = getattr(e, 'code', None)
                if error_code == 429:  # Rate limit
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        logger.warning("Gemini rate limit hit, retrying",
                                     attempt=attempt + 1,
                                     wait_time=wait_time,
                                     error=str(e))
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("Gemini rate limit exceeded, max retries reached", error=str(e))
                        raise RuntimeError(f"Gemini rate limit exceeded: {str(e)}")
                elif error_code == 403:  # Forbidden/Authentication
                    logger.error("Gemini authentication/permission error", error=str(e))
                    raise RuntimeError(f"Gemini authentication failed: {str(e)}")
                else:
                    logger.error("Gemini API error",
                               error=str(e),
                               error_code=error_code)
                    raise RuntimeError(f"Gemini API error: {str(e)}")

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning("Unexpected error in Gemini call, retrying",
                                 attempt=attempt + 1,
                                 wait_time=wait_time,
                                 error=str(e))
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("Unexpected error in Gemini call, max retries reached",
                               error=str(e))
                    break

        # If we get here, all retries failed
        error_msg = f"Gemini API call failed after {self.max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        raise RuntimeError(error_msg)

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert generic message format to Gemini conversation format."""
        gemini_messages = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Gemini uses 'user' and 'model' roles
            if role == "system":
                # System messages can be prepended to first user message
                if gemini_messages:
                    # If we already have messages, combine with first user message
                    first_user_idx = next((i for i, m in enumerate(gemini_messages) if m["role"] == "user"), None)
                    if first_user_idx is not None:
                        gemini_messages[first_user_idx]["content"] = f"System: {content}\n\n{gemini_messages[first_user_idx]['content']}"
                    else:
                        # No user message yet, create one with system content
                        gemini_messages.append({"role": "user", "content": f"System: {content}"})
                else:
                    gemini_messages.append({"role": "user", "content": f"System: {content}"})
                continue
            elif role == "user":
                gemini_role = "user"
            elif role == "assistant":
                gemini_role = "model"
            else:
                # Default to user for unknown roles
                gemini_role = "user"
                logger.warning("Unknown message role, defaulting to user", role=role)

            gemini_messages.append({
                "role": gemini_role,
                "content": content
            })

        return gemini_messages

    def get_models(self) -> List[str]:
        """Get a list of available Gemini models."""
        return list(self.MODEL_CONFIGS.keys())

    def get_model_config(self, model: str) -> Dict[str, Any]:
        """Get configuration for a specific model."""
        return self.MODEL_CONFIGS.get(model, {})

    async def check_health(self) -> Dict[str, Any]:
        """Check the health of the Gemini API."""
        try:
            # Make a minimal API call to test connectivity
            test_messages = [{"role": "user", "content": "Hello"}]

            start_time = asyncio.get_event_loop().time()
            await self.generate("gemini-1.5-flash-latest", test_messages, max_tokens=10)
            response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "provider": "gemini"
            }

        except Exception as e:
            logger.error("Gemini health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "gemini"
            }
