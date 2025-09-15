#!/usr/bin/env python3
"""Input Validation for ADK System.

This module provides comprehensive input validation for all ADK components,
ensuring security, data integrity, and preventing common vulnerabilities.
"""

import inspect
import re
from functools import wraps
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
import structlog

from adk_logging import adk_logger

logger = adk_logger


def validate_input(*validators) -> Callable:
    """Decorator for input validation."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _validate_and_call(func, validators, args, kwargs, is_async=True)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _validate_and_call(func, validators, args, kwargs, is_async=False)

        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _validate_and_call(func: Callable, validators: tuple, args: tuple,
                           kwargs: dict, is_async: bool) -> Any:
    """Validate inputs and call function."""
    # Extract function arguments
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    # Validate each argument
    for validator in validators:
        validator_name = validator.__name__
        if validator_name in bound_args.arguments:
            value = bound_args.arguments[validator_name]
            try:
                validator(value)
            except Exception as e:
                logger.log_error_with_context(
                    e, f"input_validation_{func.__name__}",
                    validator=validator_name,
                    invalid_value=str(value)[:100]  # Truncate for security
                )
                raise ValueError(f"Invalid input for {validator_name}: {e}")

    # Call the function
    if is_async:
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)


# Validation functions
def validate_agent_type(value: str) -> None:
    """Validate agent type."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Agent type must be a non-empty string")

    valid_types = ["analyst", "architect", "developer", "tester", "deployer"]
    if value not in valid_types:
        raise ValueError(f"Invalid agent type: {value}. Must be one of {valid_types}")


def validate_model_name(value: str) -> None:
    """Validate model name."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Model name must be a non-empty string")

    valid_models = [
        "gemini-2.0-flash", "gemini-1.5-pro", "gpt-4-turbo",
        "claude-3-opus", "gpt-4", "claude-3-sonnet"
    ]
    if value not in valid_models:
        raise ValueError(f"Invalid model: {value}. Must be one of {valid_models}")


def validate_user_id(value: Optional[str]) -> None:
    """Validate user ID."""
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("User ID must be a non-empty string if provided")

        # Check for basic security patterns
        if len(value) > 100:
            raise ValueError("User ID too long (max 100 characters)")

        # Check for potentially dangerous characters
        if re.search(r'[<>"/\\&\'\x00-\x1f\x7f-\x9f]', value):
            raise ValueError("User ID contains invalid characters")


def validate_project_id(value: Optional[str]) -> None:
    """Validate project ID."""
    if value is not None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Project ID must be a non-empty string if provided")

        if len(value) > 100:
            raise ValueError("Project ID too long (max 100 characters)")

        # Check for potentially dangerous characters
        if re.search(r'[<>"/\\&\'\x00-\x1f\x7f-\x9f]', value):
            raise ValueError("Project ID contains invalid characters")


def validate_task_description(value: str) -> None:
    """Validate task description."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Task description must be a non-empty string")

    if len(value) > 10000:
        raise ValueError("Task description too long (max 10000 characters)")

    # Check for basic security patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'vbscript:',                  # VBScript URLs
        r'on\w+\s*=',                  # Event handlers
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError("Task description contains potentially dangerous content")


def validate_requirements_text(value: str) -> None:
    """Validate requirements text."""
    if not isinstance(value, str):
        raise ValueError("Requirements text must be a string")

    if len(value) > 50000:
        raise ValueError("Requirements text too long (max 50000 characters)")

    # Allow empty requirements for optional fields
    if value and len(value.strip()) == 0:
        raise ValueError("Requirements text cannot be only whitespace")


def validate_complexity(value: str) -> None:
    """Validate complexity level."""
    if not isinstance(value, str):
        raise ValueError("Complexity must be a string")

    valid_levels = ["low", "medium", "high"]
    if value not in valid_levels:
        raise ValueError(f"Invalid complexity: {value}. Must be one of {valid_levels}")


def validate_cost_sensitivity(value: str) -> None:
    """Validate cost sensitivity level."""
    if not isinstance(value, str):
        raise ValueError("Cost sensitivity must be a string")

    valid_levels = ["cost_optimized", "balanced", "performance_optimized"]
    if value not in valid_levels:
        raise ValueError(f"Invalid cost sensitivity: {value}. Must be one of {valid_levels}")


def validate_positive_number(value: Union[int, float]) -> None:
    """Validate positive number."""
    try:
        num_value = float(value)
        if num_value <= 0:
            raise ValueError("Value must be positive")
    except (TypeError, ValueError):
        raise ValueError("Value must be a positive number")


def validate_percentage(value: Union[int, float]) -> None:
    """Validate percentage (0-100)."""
    try:
        num_value = float(value)
        if not (0 <= num_value <= 100):
            raise ValueError("Percentage must be between 0 and 100")
    except (TypeError, ValueError):
        raise ValueError("Percentage must be a number between 0 and 100")


def validate_email(value: str) -> None:
    """Validate email address."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Email must be a non-empty string")

    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValueError("Invalid email format")

    if len(value) > 254:  # RFC 5321 limit
        raise ValueError("Email address too long")


def validate_url(value: str) -> None:
    """Validate URL."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("URL must be a non-empty string")

    # Basic URL validation
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, value):
        raise ValueError("Invalid URL format")

    if len(value) > 2000:
        raise ValueError("URL too long")


def validate_json_string(value: str) -> None:
    """Validate JSON string."""
    if not isinstance(value, str):
        raise ValueError("JSON must be a string")

    try:
        import json
        json.loads(value)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def validate_list_of_strings(value: List[str]) -> None:
    """Validate list of strings."""
    if not isinstance(value, list):
        raise ValueError("Value must be a list")

    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("All list items must be non-empty strings")

        if len(item) > 1000:
            raise ValueError("List item too long (max 1000 characters)")


def validate_dict_structure(value: Dict[str, Any], required_keys: List[str] = None) -> None:
    """Validate dictionary structure."""
    if not isinstance(value, dict):
        raise ValueError("Value must be a dictionary")

    if required_keys:
        missing_keys = [key for key in required_keys if key not in value]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")


class ADKInputValidator:
    """Advanced input validator with security features."""

    def __init__(self):
        self.security_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'vbscript:',                  # VBScript URLs
            r'on\w+\s*=',                  # Event handlers
            r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
            r'<object[^>]*>.*?</object>',  # Object tags
            r'<embed[^>]*>.*?</embed>',    # Embed tags
            r'<\?php.*?\?>',               # PHP tags
            r'union\s+select',             # SQL injection patterns
            r';\s*drop\s+table',           # SQL injection patterns
        ]

    def validate_text_input(self, text: str, max_length: int = 10000,
                           allow_html: bool = False) -> str:
        """Validate and sanitize text input."""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        if len(text) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")

        if not allow_html:
            # Check for dangerous patterns
            for pattern in self.security_patterns:
                if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                    logger.warning("Potentially dangerous content detected in input",
                                 pattern=pattern[:50])
                    raise ValueError("Input contains potentially dangerous content")

        return text.strip()

    def validate_numeric_input(self, value: Any, min_val: float = None,
                              max_val: float = None) -> float:
        """Validate numeric input with range checking."""
        try:
            num_value = float(value)
        except (TypeError, ValueError):
            raise ValueError("Value must be numeric")

        if min_val is not None and num_value < min_val:
            raise ValueError(f"Value must be >= {min_val}")

        if max_val is not None and num_value > max_val:
            raise ValueError(f"Value must be <= {max_val}")

        return num_value

    def validate_choice(self, value: Any, valid_choices: List[Any]) -> Any:
        """Validate that value is in list of valid choices."""
        if value not in valid_choices:
            raise ValueError(f"Value must be one of: {valid_choices}")
        return value

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security."""
        if not isinstance(filename, str):
            raise ValueError("Filename must be a string")

        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            if ext:
                filename = name[:250] + '.' + ext
            else:
                filename = filename[:255]

        return filename


# Global validator instance
input_validator = ADKInputValidator()


# Convenience functions for common validations
def validate_agent_creation_params(agent_type: str, user_id: Optional[str] = None,
                                  project_id: Optional[str] = None) -> None:
    """Validate parameters for agent creation."""
    validate_agent_type(agent_type)
    validate_user_id(user_id)
    validate_project_id(project_id)


def validate_model_selection_params(model_name: str, task_type: str = "analysis",
                                   complexity: str = "medium") -> None:
    """Validate parameters for model selection."""
    validate_model_name(model_name)
    validate_complexity(complexity)

    valid_task_types = ["analysis", "code_generation", "vision_analysis",
                       "complex_reasoning", "creative_writing", "data_processing"]
    if task_type not in valid_task_types:
        raise ValueError(f"Invalid task type: {task_type}. Must be one of {valid_task_types}")


def validate_task_execution_params(task_description: str, agent_type: str) -> None:
    """Validate parameters for task execution."""
    validate_task_description(task_description)
    validate_agent_type(agent_type)


if __name__ == "__main__":
    print("🚀 ADK Input Validation Demo")
    print("=" * 50)

    # Test basic validations
    try:
        validate_agent_type("analyst")
        print("✅ Agent type validation passed")
    except ValueError as e:
        print(f"❌ Agent type validation failed: {e}")

    try:
        validate_model_name("gemini-2.0-flash")
        print("✅ Model name validation passed")
    except ValueError as e:
        print(f"❌ Model name validation failed: {e}")

    try:
        validate_task_description("This is a valid task description for testing.")
        print("✅ Task description validation passed")
    except ValueError as e:
        print(f"❌ Task description validation failed: {e}")

    # Test dangerous content detection
    try:
        validate_task_description("<script>alert('xss')</script>")
        print("❌ Dangerous content validation failed - should have caught XSS")
    except ValueError:
        print("✅ Dangerous content validation passed")

    # Test input validator
    validator = ADKInputValidator()

    try:
        clean_text = validator.validate_text_input("Valid input text")
        print("✅ Text input validation passed")
    except ValueError as e:
        print(f"❌ Text input validation failed: {e}")

    try:
        num_value = validator.validate_numeric_input("42", min_val=0, max_val=100)
        print("✅ Numeric input validation passed")
    except ValueError as e:
        print(f"❌ Numeric input validation failed: {e}")

    print("\n✅ Input validation system working correctly")
