"""LLM retry logic with exponential backoff.

This module provides robust retry mechanisms for LLM API calls with intelligent
backoff strategies and comprehensive error classification.
"""

import asyncio
import time
from typing import Callable, Any, List, Type, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import structlog
from functools import wraps

logger = structlog.get_logger(__name__)


class RetryableErrorType(str, Enum):
    """Classification of retryable error types."""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    TEMPORARY_FAILURE = "temporary_failure"
    SERVICE_UNAVAILABLE = "service_unavailable"


class NonRetryableErrorType(str, Enum):
    """Classification of non-retryable error types."""
    AUTHENTICATION = "authentication" 
    INVALID_API_KEY = "invalid_api_key"
    PERMISSION_DENIED = "permission_denied"
    INVALID_REQUEST = "invalid_request"
    PERMANENT_FAILURE = "permanent_failure"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 8.0   # Maximum delay cap
    backoff_multiplier: float = 2.0  # Exponential multiplier
    jitter: bool = True      # Add randomization to prevent thundering herd
    
    # Exception types that should trigger retries
    retryable_exceptions: List[str] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                'TimeoutError',
                'ConnectionError', 
                'ConnectTimeout',
                'ReadTimeout',
                'HTTPStatusError',  # For HTTP 5xx errors
                'RateLimitError',
                'ServiceUnavailableError'
            ]


@dataclass 
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    delay: float
    error_type: str
    error_message: str
    timestamp: float
    recoverable: bool


@dataclass
class RetryResult:
    """Result of retry operation with metadata."""
    success: bool
    result: Any = None
    total_attempts: int = 0
    total_time: float = 0.0
    attempts: List[RetryAttempt] = None
    final_error: Optional[Exception] = None
    
    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []


class LLMRetryHandler:
    """Handles retry logic with exponential backoff for LLM API calls.
    
    This class implements intelligent retry strategies including:
    - Exponential backoff with configurable parameters
    - Error type classification (retryable vs non-retryable)
    - Jitter to prevent thundering herd problems
    - Comprehensive retry metrics and logging
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry handler with configuration.
        
        Args:
            config: Retry configuration, uses defaults if None
        """
        self.config = config or RetryConfig()
        
        # Pre-compile error type mappings for efficiency
        self._retryable_errors = set(self.config.retryable_exceptions)
        
        # Track retry statistics
        self._retry_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_retries': 0,
            'retry_success_rate': 0.0
        }
    
    async def execute_with_retry(
        self, 
        llm_call: Callable,
        *args,
        max_retries: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetryResult:
        """Execute LLM call with exponential backoff retry logic.
        
        Args:
            llm_call: Callable to execute (async or sync)
            *args: Positional arguments for the callable
            max_retries: Override default max retries
            context: Additional context for logging
            **kwargs: Keyword arguments for the callable
            
        Returns:
            RetryResult with execution results and metadata
        """
        start_time = time.time()
        attempts = []
        effective_max_retries = max_retries or self.config.max_retries
        
        self._retry_stats['total_calls'] += 1
        
        logger.info("Starting LLM call with retry",
                   max_retries=effective_max_retries,
                   context=context or {})
        
        for attempt in range(effective_max_retries + 1):  # +1 for initial attempt
            try:
                # Execute the callable
                if asyncio.iscoroutinefunction(llm_call):
                    result = await llm_call(*args, **kwargs)
                else:
                    result = llm_call(*args, **kwargs)
                
                # Success!
                total_time = time.time() - start_time
                self._retry_stats['successful_calls'] += 1
                
                if attempt > 0:
                    self._retry_stats['total_retries'] += attempt
                    logger.info("LLM call succeeded after retries",
                               attempts=attempt,
                               total_time=total_time,
                               context=context or {})
                
                return RetryResult(
                    success=True,
                    result=result,
                    total_attempts=attempt + 1,
                    total_time=total_time,
                    attempts=attempts
                )
                
            except Exception as e:
                error_type = self._classify_error(e)
                is_retryable = await self.should_retry(e, attempt, effective_max_retries)
                
                attempt_info = RetryAttempt(
                    attempt_number=attempt + 1,
                    delay=0.0,  # Will be set below if retrying
                    error_type=error_type,
                    error_message=str(e),
                    timestamp=time.time(),
                    recoverable=is_retryable
                )
                attempts.append(attempt_info)
                
                logger.warning("LLM call failed",
                             attempt=attempt + 1,
                             error_type=error_type,
                             error_message=str(e),
                             retryable=is_retryable,
                             context=context or {})
                
                # Check if we should retry
                if not is_retryable or attempt >= effective_max_retries:
                    # No more retries
                    total_time = time.time() - start_time
                    self._retry_stats['failed_calls'] += 1
                    
                    if attempt > 0:
                        self._retry_stats['total_retries'] += attempt
                    
                    logger.error("LLM call failed permanently",
                               total_attempts=attempt + 1,
                               total_time=total_time,
                               final_error=str(e),
                               context=context or {})
                    
                    return RetryResult(
                        success=False,
                        total_attempts=attempt + 1,
                        total_time=total_time,
                        attempts=attempts,
                        final_error=e
                    )
                
                # Calculate delay and wait
                delay = self.calculate_backoff_delay(attempt + 1)
                attempt_info.delay = delay
                
                logger.info("Retrying LLM call after delay",
                           attempt=attempt + 1,
                           delay=delay,
                           next_attempt=attempt + 2,
                           context=context or {})
                
                await asyncio.sleep(delay)
        
        # This shouldn't be reached, but just in case
        return RetryResult(
            success=False,
            total_attempts=effective_max_retries + 1,
            total_time=time.time() - start_time,
            attempts=attempts,
            final_error=Exception("Max retries exceeded")
        )
    
    def calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter.
        
        Args:
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (multiplier ^ (attempt - 1))
        delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
        
        # Apply maximum delay cap
        delay = min(delay, self.config.max_delay)
        
        # Add jitter if enabled (±25% randomization)
        if self.config.jitter:
            import random
            jitter_factor = 0.25
            jitter = delay * jitter_factor * (2 * random.random() - 1)  # -25% to +25%
            delay = max(0.1, delay + jitter)  # Ensure minimum 0.1s delay
        
        return delay
    
    async def should_retry(self, exception: Exception, attempt: int, max_retries: int) -> bool:
        """Determine if exception is retryable.
        
        Args:
            exception: Exception that occurred
            attempt: Current attempt number (0-indexed)
            max_retries: Maximum number of retries allowed
            
        Returns:
            True if should retry, False otherwise
        """
        # Check if we've exceeded max retries
        if attempt >= max_retries:
            return False
        
        # Check if error type is retryable
        error_type = type(exception).__name__
        is_retryable = error_type in self._retryable_errors
        
        # Generic Exception should be retryable unless specifically classified otherwise
        if error_type == "Exception":
            is_retryable = True
        
        # Special handling for HTTP errors
        if hasattr(exception, 'status_code'):
            status_code = exception.status_code
            
            # 5xx errors are generally retryable
            if 500 <= status_code < 600:
                is_retryable = True
            # 429 (rate limit) is retryable
            elif status_code == 429:
                is_retryable = True
            # 4xx errors (except 429) are generally not retryable
            elif 400 <= status_code < 500:
                is_retryable = False
        
        # Special handling for timeout errors
        if 'timeout' in str(exception).lower():
            is_retryable = True
        
        # Special handling for connection errors
        if any(keyword in str(exception).lower() for keyword in ['connection', 'network', 'dns']):
            is_retryable = True
        
        logger.debug("Retry decision",
                    exception_type=error_type,
                    exception_message=str(exception),
                    attempt=attempt,
                    max_retries=max_retries,
                    retryable=is_retryable)
        
        return is_retryable
    
    def _classify_error(self, exception: Exception) -> str:
        """Classify error type for logging and metrics."""
        error_msg = str(exception).lower()
        error_type = type(exception).__name__
        
        # Check for specific error patterns
        if 'timeout' in error_msg or 'timed out' in error_msg:
            return RetryableErrorType.TIMEOUT
        elif 'rate limit' in error_msg or '429' in error_msg:
            return RetryableErrorType.RATE_LIMIT
        elif any(keyword in error_msg for keyword in ['connection', 'network', 'dns']):
            return RetryableErrorType.NETWORK
        elif 'service unavailable' in error_msg or '503' in error_msg:
            return RetryableErrorType.SERVICE_UNAVAILABLE
        elif any(keyword in error_msg for keyword in ['auth', 'unauthorized', '401']):
            return NonRetryableErrorType.AUTHENTICATION
        elif 'api key' in error_msg or 'invalid key' in error_msg:
            return NonRetryableErrorType.INVALID_API_KEY
        elif 'permission denied' in error_msg or '403' in error_msg:
            return NonRetryableErrorType.PERMISSION_DENIED
        elif any(keyword in error_msg for keyword in ['bad request', '400', 'invalid']):
            return NonRetryableErrorType.INVALID_REQUEST
        else:
            # Default classification
            if error_type in self._retryable_errors:
                return RetryableErrorType.TEMPORARY_FAILURE
            else:
                return NonRetryableErrorType.PERMANENT_FAILURE
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics for monitoring."""
        stats = self._retry_stats.copy()
        
        # Calculate success rate
        if stats['total_calls'] > 0:
            stats['retry_success_rate'] = stats['successful_calls'] / stats['total_calls']
        
        # Calculate average retries per call
        if stats['total_calls'] > 0:
            stats['average_retries_per_call'] = stats['total_retries'] / stats['total_calls']
        
        return stats
    
    def reset_stats(self):
        """Reset retry statistics."""
        self._retry_stats = {
            'total_calls': 0,
            'successful_calls': 0, 
            'failed_calls': 0,
            'total_retries': 0,
            'retry_success_rate': 0.0
        }


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0
):
    """Decorator to add retry logic to any function.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        max_delay: Maximum delay cap
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            retry_handler = LLMRetryHandler(config)
            result = await retry_handler.execute_with_retry(
                func, *args, **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise result.final_error
        
        return wrapper
    return decorator