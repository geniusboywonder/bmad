"""LLM response validation and sanitization service.

This module provides comprehensive validation and sanitization for LLM responses
to ensure Context Store integrity and prevent malicious content injection.
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ValidationErrorType(str, Enum):
    """Types of validation errors."""
    INVALID_JSON = "invalid_json"
    CONTENT_TOO_LARGE = "content_too_large"
    MALICIOUS_CONTENT = "malicious_content"
    MISSING_REQUIRED_FIELDS = "missing_required_fields"
    INVALID_DATA_TYPE = "invalid_data_type"


@dataclass
class ValidationError:
    """Validation error with context and recovery information."""
    error_type: ValidationErrorType
    message: str
    recoverable: bool = True
    context: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of response validation with sanitized content."""
    is_valid: bool
    sanitized_content: Optional[Dict[str, Any]] = None
    original_content: Optional[str] = None
    errors: List[ValidationError] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class LLMResponseValidator:
    """Validates and sanitizes LLM responses before Context Store persistence.
    
    This class implements comprehensive validation including:
    - JSON structure validation
    - Content sanitization (malicious script removal)
    - Size limit enforcement
    - Data type validation
    - Error recovery strategies
    """
    
    def __init__(self, max_response_size: int = 50000):
        """Initialize validator with configuration.
        
        Args:
            max_response_size: Maximum allowed response size in characters
        """
        self.max_response_size = max_response_size
        
        # Patterns for detecting potentially malicious content
        self.malicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                # JavaScript URLs
            r'on\w+\s*=',                 # Event handlers
            r'eval\s*\(',                 # eval() calls
            r'Function\s*\(',             # Function constructor
            r'setTimeout\s*\(',           # setTimeout calls
            r'setInterval\s*\(',          # setInterval calls
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.malicious_patterns]
    
    async def validate_response(self, response: str, expected_format: str = "json") -> ValidationResult:
        """Validate LLM response against expected format and safety rules.
        
        Args:
            response: Raw LLM response string
            expected_format: Expected format ("json", "text", or "auto")
            
        Returns:
            ValidationResult with validation status and sanitized content
        """
        logger.debug("Validating LLM response", 
                    response_length=len(response) if response else 0,
                    expected_format=expected_format)
        
        if not response:
            return ValidationResult(
                is_valid=False,
                errors=[ValidationError(
                    ValidationErrorType.MISSING_REQUIRED_FIELDS,
                    "Empty response received",
                    recoverable=False
                )]
            )
        
        # Check size limits
        if len(response) > self.max_response_size:
            return ValidationResult(
                is_valid=False,
                original_content=response[:100] + "...",  # Truncated for logging
                errors=[ValidationError(
                    ValidationErrorType.CONTENT_TOO_LARGE,
                    f"Response size {len(response)} exceeds limit {self.max_response_size}",
                    recoverable=False,
                    context={"size": len(response), "limit": self.max_response_size}
                )]
            )
        
        # Check for malicious content
        malicious_error = self._check_malicious_content(response)
        if malicious_error:
            return ValidationResult(
                is_valid=False,
                original_content=response[:200] + "...",
                errors=[malicious_error]
            )
        
        # Validate based on expected format
        if expected_format == "json":
            return await self._validate_json_response(response)
        elif expected_format == "text":
            return await self._validate_text_response(response)
        else:  # auto-detect
            return await self._auto_validate_response(response)
    
    async def sanitize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize content dictionary for safe storage.
        
        Args:
            content: Content dictionary to sanitize
            
        Returns:
            Sanitized content dictionary
        """
        if not isinstance(content, dict):
            logger.warning("Content sanitization: non-dict content", content_type=type(content))
            return {"sanitized_content": str(content)}
        
        sanitized = {}
        
        for key, value in content.items():
            # Sanitize key
            clean_key = self._sanitize_string(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = self._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = await self.sanitize_content(value)
            elif isinstance(value, list):
                sanitized[clean_key] = await self._sanitize_list(value)
            else:
                # Numbers, booleans, None - pass through
                sanitized[clean_key] = value
        
        return sanitized
    
    async def handle_validation_failure(self, response: str, error: ValidationError) -> str:
        """Handle validation failures with recovery strategies.
        
        Args:
            response: Original response that failed validation
            error: Validation error details
            
        Returns:
            Recovered response string or fallback response
        """
        logger.warning("Handling validation failure",
                      error_type=error.error_type,
                      error_message=error.message,
                      recoverable=error.recoverable)
        
        if not error.recoverable:
            return self._generate_fallback_response(error)
        
        # Try recovery strategies based on error type
        if error.error_type == ValidationErrorType.INVALID_JSON:
            return await self._recover_invalid_json(response)
        elif error.error_type == ValidationErrorType.MALICIOUS_CONTENT:
            return await self._recover_malicious_content(response)
        else:
            return self._generate_fallback_response(error)
    
    def _check_malicious_content(self, content: str) -> Optional[ValidationError]:
        """Check content for potentially malicious patterns."""
        for pattern in self.compiled_patterns:
            if pattern.search(content):
                return ValidationError(
                    ValidationErrorType.MALICIOUS_CONTENT,
                    f"Potentially malicious content detected: {pattern.pattern}",
                    recoverable=True,
                    context={"pattern": pattern.pattern}
                )
        return None
    
    async def _validate_json_response(self, response: str) -> ValidationResult:
        """Validate JSON response format."""
        try:
            parsed = json.loads(response)
            
            # Sanitize the parsed content
            sanitized = await self.sanitize_content(parsed if isinstance(parsed, dict) else {"content": parsed})
            
            return ValidationResult(
                is_valid=True,
                sanitized_content=sanitized,
                original_content=response[:200] + "..." if len(response) > 200 else response
            )
            
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                original_content=response[:200] + "..." if len(response) > 200 else response,
                errors=[ValidationError(
                    ValidationErrorType.INVALID_JSON,
                    f"JSON parsing failed: {str(e)}",
                    recoverable=True,
                    context={"json_error": str(e)}
                )]
            )
    
    async def _validate_text_response(self, response: str) -> ValidationResult:
        """Validate plain text response."""
        sanitized_text = self._sanitize_string(response)
        
        return ValidationResult(
            is_valid=True,
            sanitized_content={"content": sanitized_text, "type": "text"},
            original_content=response[:200] + "..." if len(response) > 200 else response
        )
    
    async def _auto_validate_response(self, response: str) -> ValidationResult:
        """Auto-detect response format and validate accordingly."""
        # Try JSON first
        response_stripped = response.strip()
        if (response_stripped.startswith('{') and response_stripped.endswith('}')) or \
           (response_stripped.startswith('[') and response_stripped.endswith(']')):
            json_result = await self._validate_json_response(response)
            if json_result.is_valid:
                return json_result
        
        # Fall back to text validation
        return await self._validate_text_response(response)
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string content by removing malicious patterns."""
        if not isinstance(text, str):
            return str(text)
        
        sanitized = text
        
        # Remove malicious patterns
        for pattern in self.compiled_patterns:
            sanitized = pattern.sub('', sanitized)
        
        # Additional cleanup
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)  # Control chars
        
        return sanitized.strip()
    
    async def _sanitize_list(self, items: List[Any]) -> List[Any]:
        """Sanitize list items."""
        sanitized = []
        
        for item in items:
            if isinstance(item, str):
                sanitized.append(self._sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(await self.sanitize_content(item))
            elif isinstance(item, list):
                sanitized.append(await self._sanitize_list(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    async def _recover_invalid_json(self, response: str) -> str:
        """Try to recover from invalid JSON by extracting JSON-like content."""
        # Look for JSON-like patterns
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                json.loads(json_match.group())
                return json_match.group()
            except json.JSONDecodeError:
                pass
        
        # If can't recover, return as text content
        return json.dumps({
            "content": self._sanitize_string(response),
            "type": "recovered_text",
            "note": "Original response was not valid JSON"
        })
    
    async def _recover_malicious_content(self, response: str) -> str:
        """Recover from malicious content by aggressive sanitization."""
        sanitized_text = self._sanitize_string(response)
        
        return json.dumps({
            "content": sanitized_text,
            "type": "sanitized",
            "note": "Content was sanitized due to security concerns"
        })
    
    def _generate_fallback_response(self, error: ValidationError) -> str:
        """Generate a safe fallback response."""
        fallback_content = {
            "error": "validation_failed",
            "error_type": error.error_type,
            "message": "Response validation failed, using fallback",
            "details": error.message,
            "timestamp": "auto-generated"
        }
        
        return json.dumps(fallback_content)