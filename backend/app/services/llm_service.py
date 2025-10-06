"""
LLM Service for BMAD Core

This module provides comprehensive LLM management including:
- Usage tracking and cost monitoring
- Robust retry logic with exponential backoff
- Performance metrics and operational oversight
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple, Callable, Type
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID
import structlog
import json
import re
from functools import wraps
import random

logger = structlog.get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GOOGLE = "google"


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
class UsageMetrics:
    """Individual LLM request metrics."""
    timestamp: datetime
    agent_type: str
    project_id: Optional[UUID]
    task_id: Optional[UUID] 
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    tokens_used: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    response_time_ms: float = 0.0
    estimated_cost: float = 0.0
    success: bool = True
    error_type: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        data = asdict(self)
        # Convert UUID and datetime to strings
        data['timestamp'] = self.timestamp.isoformat()
        if data['project_id']:
            data['project_id'] = str(data['project_id'])
        if data['task_id']:
            data['task_id'] = str(data['task_id'])
        return data


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
                "TimeoutError",
                "ConnectionError", 
                "RateLimitError",
                "ServiceUnavailableError",
                "TemporaryFailureError"
            ]


class LLMService:
    """
    Unified service for LLM operations including monitoring, retry logic, and metrics.
    
    Consolidates functionality from LLMMonitoring and LLMRetry services.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM service.

        Args:
            config: Configuration dictionary with LLM parameters
        """
        # Monitoring configuration
        self.enable_monitoring = config.get("enable_monitoring", True)
        self.cost_tracking = config.get("cost_tracking", True)
        self.performance_tracking = config.get("performance_tracking", True)
        self.alert_thresholds = config.get("alert_thresholds", {
            "cost_per_hour": 10.0,
            "error_rate": 0.1,
            "avg_response_time": 5000  # ms
        })

        # Retry configuration
        self.retry_config = RetryConfig(**config.get("retry_config", {}))
        
        # Provider-specific cost models (tokens per dollar)
        self.cost_models = config.get("cost_models", {
            "openai": {
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # per 1K tokens
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
            },
            "anthropic": {
                "claude-sonnet-4": {"input": 0.003, "output": 0.015},
                "claude-haiku": {"input": 0.00025, "output": 0.00125}
            },
            "google": {
                "gemini-pro": {"input": 0.0005, "output": 0.0015}
            }
        })

        # Metrics storage
        self.usage_metrics: List[UsageMetrics] = []
        self.hourly_costs: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}

        logger.info("LLM service initialized",
                   monitoring=self.enable_monitoring,
                   cost_tracking=self.cost_tracking,
                   max_retries=self.retry_config.max_retries)

    # MONITORING METHODS

    def track_usage(
        self,
        agent_type: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: float,
        success: bool = True,
        error_type: Optional[str] = None,
        retry_count: int = 0,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None
    ) -> UsageMetrics:
        """
        Track LLM usage metrics.

        Args:
            agent_type: Type of agent making the request
            provider: LLM provider (openai, anthropic, google)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            response_time_ms: Response time in milliseconds
            success: Whether the request was successful
            error_type: Type of error if unsuccessful
            retry_count: Number of retries attempted
            project_id: Optional project identifier
            task_id: Optional task identifier

        Returns:
            UsageMetrics object with calculated cost
        """
        if not self.enable_monitoring:
            return None

        # Calculate cost
        estimated_cost = self._calculate_cost(provider, model, input_tokens, output_tokens)

        # Create metrics object
        metrics = UsageMetrics(
            timestamp=datetime.now(timezone.utc),
            agent_type=agent_type,
            project_id=project_id,
            task_id=task_id,
            provider=provider,
            model=model,
            tokens_used=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time_ms=response_time_ms,
            estimated_cost=estimated_cost,
            success=success,
            error_type=error_type,
            retry_count=retry_count
        )

        # Store metrics
        self.usage_metrics.append(metrics)

        # Update hourly costs
        if self.cost_tracking:
            hour_key = metrics.timestamp.strftime("%Y-%m-%d-%H")
            self.hourly_costs[hour_key] = self.hourly_costs.get(hour_key, 0) + estimated_cost

        # Update error counts
        if not success and error_type:
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Check alert thresholds
        self._check_alert_thresholds(metrics)

        logger.info("LLM usage tracked",
                   agent_type=agent_type,
                   provider=provider,
                   model=model,
                   tokens=input_tokens + output_tokens,
                   cost=estimated_cost,
                   success=success)

        return metrics

    def get_usage_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        agent_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get usage summary for specified time period and filters.

        Args:
            start_time: Start of time period (default: last 24 hours)
            end_time: End of time period (default: now)
            agent_type: Filter by agent type
            provider: Filter by provider

        Returns:
            Usage summary with costs, tokens, and performance metrics
        """
        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(timezone.utc)

        # Filter metrics
        filtered_metrics = [
            m for m in self.usage_metrics
            if start_time <= m.timestamp <= end_time
            and (not agent_type or m.agent_type == agent_type)
            and (not provider or m.provider == provider)
        ]

        if not filtered_metrics:
            return {
                "total_requests": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0
            }

        # Calculate summary statistics
        total_requests = len(filtered_metrics)
        total_cost = sum(m.estimated_cost for m in filtered_metrics)
        total_tokens = sum(m.tokens_used for m in filtered_metrics)
        successful_requests = sum(1 for m in filtered_metrics if m.success)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
        avg_response_time = sum(m.response_time_ms for m in filtered_metrics) / total_requests

        # Provider breakdown
        provider_breakdown = {}
        for metrics in filtered_metrics:
            provider = metrics.provider
            if provider not in provider_breakdown:
                provider_breakdown[provider] = {
                    "requests": 0,
                    "cost": 0.0,
                    "tokens": 0
                }
            provider_breakdown[provider]["requests"] += 1
            provider_breakdown[provider]["cost"] += metrics.estimated_cost
            provider_breakdown[provider]["tokens"] += metrics.tokens_used

        return {
            "time_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_requests": total_requests,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "success_rate": round(success_rate, 3),
            "avg_response_time": round(avg_response_time, 2),
            "provider_breakdown": provider_breakdown,
            "error_summary": dict(self.error_counts)
        }

    # RETRY METHODS

    def with_retry(self, retry_config: Optional[RetryConfig] = None):
        """
        Decorator for adding retry logic to LLM API calls.

        Args:
            retry_config: Optional retry configuration override

        Returns:
            Decorator function
        """
        config = retry_config or self.retry_config

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(config.max_retries + 1):
                    try:
                        start_time = time.time()
                        result = await func(*args, **kwargs)
                        
                        # Track successful call
                        response_time = (time.time() - start_time) * 1000
                        if hasattr(self, 'track_usage') and len(args) > 0:
                            # Extract tracking info from args/kwargs if available
                            agent_type = kwargs.get('agent_type', 'unknown')
                            provider = kwargs.get('provider', 'openai')
                            model = kwargs.get('model', 'gpt-4o-mini')
                            
                            self.track_usage(
                                agent_type=agent_type,
                                provider=provider,
                                model=model,
                                input_tokens=kwargs.get('input_tokens', 0),
                                output_tokens=kwargs.get('output_tokens', 0),
                                response_time_ms=response_time,
                                success=True,
                                retry_count=attempt
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        error_type = self._classify_error(e)
                        
                        # Track failed call
                        response_time = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                        if hasattr(self, 'track_usage') and len(args) > 0:
                            agent_type = kwargs.get('agent_type', 'unknown')
                            provider = kwargs.get('provider', 'openai')
                            model = kwargs.get('model', 'gpt-4o-mini')
                            
                            self.track_usage(
                                agent_type=agent_type,
                                provider=provider,
                                model=model,
                                input_tokens=kwargs.get('input_tokens', 0),
                                output_tokens=kwargs.get('output_tokens', 0),
                                response_time_ms=response_time,
                                success=False,
                                error_type=error_type,
                                retry_count=attempt
                            )
                        
                        # Check if error is retryable
                        if not self._is_retryable_error(e) or attempt == config.max_retries:
                            logger.error("LLM call failed permanently",
                                       attempt=attempt + 1,
                                       error_type=error_type,
                                       error=str(e))
                            raise e
                        
                        # Calculate delay with exponential backoff and jitter
                        delay = min(
                            config.base_delay * (config.backoff_multiplier ** attempt),
                            config.max_delay
                        )
                        
                        if config.jitter:
                            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                        
                        logger.warning("LLM call failed, retrying",
                                     attempt=attempt + 1,
                                     max_retries=config.max_retries,
                                     delay=delay,
                                     error_type=error_type,
                                     error=str(e))
                        
                        await asyncio.sleep(delay)
                
                # This should never be reached, but just in case
                raise last_exception
            
            return wrapper
        return decorator

    # PRIVATE HELPER METHODS

    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost for LLM usage."""
        if not self.cost_tracking or provider not in self.cost_models:
            return 0.0

        model_costs = self.cost_models[provider].get(model)
        if not model_costs:
            return 0.0

        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (output_tokens / 1000) * model_costs["output"]
        
        return input_cost + output_cost

    def _check_alert_thresholds(self, metrics: UsageMetrics):
        """Check if metrics exceed alert thresholds."""
        # Check hourly cost threshold
        hour_key = metrics.timestamp.strftime("%Y-%m-%d-%H")
        hourly_cost = self.hourly_costs.get(hour_key, 0)
        
        if hourly_cost > self.alert_thresholds["cost_per_hour"]:
            logger.warning("Hourly cost threshold exceeded",
                          hour=hour_key,
                          cost=hourly_cost,
                          threshold=self.alert_thresholds["cost_per_hour"])

        # Check response time threshold
        if metrics.response_time_ms > self.alert_thresholds["avg_response_time"]:
            logger.warning("Response time threshold exceeded",
                          response_time=metrics.response_time_ms,
                          threshold=self.alert_thresholds["avg_response_time"])

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for tracking and retry logic."""
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Rate limiting errors
        if "rate limit" in error_str or "429" in error_str:
            return RetryableErrorType.RATE_LIMIT
        
        # Timeout errors
        if "timeout" in error_str or "timed out" in error_str:
            return RetryableErrorType.TIMEOUT
        
        # Network errors
        if "connection" in error_str or "network" in error_str:
            return RetryableErrorType.NETWORK
        
        # Service unavailable
        if "503" in error_str or "service unavailable" in error_str:
            return RetryableErrorType.SERVICE_UNAVAILABLE
        
        # Authentication errors (non-retryable)
        if "401" in error_str or "unauthorized" in error_str or "api key" in error_str:
            return NonRetryableErrorType.AUTHENTICATION
        
        # Permission errors (non-retryable)
        if "403" in error_str or "forbidden" in error_str:
            return NonRetryableErrorType.PERMISSION_DENIED
        
        # Invalid request (non-retryable)
        if "400" in error_str or "bad request" in error_str:
            return NonRetryableErrorType.INVALID_REQUEST
        
        # Default to temporary failure (retryable)
        return RetryableErrorType.TEMPORARY_FAILURE

    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        error_type = self._classify_error(error)
        
        # Check if it's a retryable error type
        retryable_types = [
            RetryableErrorType.TIMEOUT,
            RetryableErrorType.RATE_LIMIT,
            RetryableErrorType.NETWORK,
            RetryableErrorType.TEMPORARY_FAILURE,
            RetryableErrorType.SERVICE_UNAVAILABLE
        ]
        
        return error_type in retryable_types

    def clear_metrics(self, older_than_hours: int = 24):
        """Clear old metrics to prevent memory buildup."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
        
        # Clear old usage metrics
        self.usage_metrics = [
            m for m in self.usage_metrics 
            if m.timestamp > cutoff_time
        ]
        
        # Clear old hourly costs
        cutoff_hour = cutoff_time.strftime("%Y-%m-%d-%H")
        self.hourly_costs = {
            k: v for k, v in self.hourly_costs.items()
            if k > cutoff_hour
        }
        
        logger.info("Cleared old metrics",
                   cutoff_time=cutoff_time.isoformat(),
                   remaining_metrics=len(self.usage_metrics))