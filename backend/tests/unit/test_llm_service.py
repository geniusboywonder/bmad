"""
Test suite for consolidated LLMService.
Covers usage tracking, retry logic, and cost monitoring.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID

from app.services.llm_service import (
    LLMService, 
    LLMProvider, 
    UsageMetrics, 
    RetryConfig,
    RetryableErrorType,
    NonRetryableErrorType
)
from tests.utils.database_test_utils import DatabaseTestManager


class TestLLMService:
    """Test consolidated LLM operations service."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService instance."""
        return LLMService()
    
    @pytest.fixture
    def sample_usage_metrics(self):
        """Sample usage metrics for testing."""
        return UsageMetrics(
            timestamp=datetime.now(timezone.utc),
            agent_type="analyst",
            project_id=uuid4(),
            task_id=uuid4(),
            provider="openai",
            model="gpt-4o-mini",
            tokens_used=150,
            input_tokens=100,
            output_tokens=50,
            response_time_ms=1250.5,
            estimated_cost=0.0025,
            success=True
        )
    
    @pytest.fixture
    def retry_config(self):
        """Standard retry configuration for testing."""
        return RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=8.0,
            backoff_multiplier=2.0,
            jitter=True
        )

    # Usage Tracking Tests
    
    @pytest.mark.real_data
    def test_track_usage_basic(self, llm_service, sample_usage_metrics):
        """Test basic usage tracking."""
        # Track usage
        llm_service.track_usage(
            agent_type=sample_usage_metrics.agent_type,
            provider=sample_usage_metrics.provider,
            model=sample_usage_metrics.model,
            tokens=sample_usage_metrics.tokens_used,
            response_time=sample_usage_metrics.response_time_ms,
            project_id=sample_usage_metrics.project_id,
            task_id=sample_usage_metrics.task_id,
            success=sample_usage_metrics.success,
            estimated_cost=sample_usage_metrics.estimated_cost
        )
        
        # Verify usage was recorded
        assert len(llm_service.usage_history) == 1
        
        recorded_usage = llm_service.usage_history[0]
        assert recorded_usage.agent_type == sample_usage_metrics.agent_type
        assert recorded_usage.provider == sample_usage_metrics.provider
        assert recorded_usage.tokens_used == sample_usage_metrics.tokens_used
        assert recorded_usage.success == sample_usage_metrics.success

    @pytest.mark.real_data
    def test_track_usage_multiple_providers(self, llm_service):
        """Test usage tracking across multiple providers."""
        providers_data = [
            ("openai", "gpt-4o", 100, 0.002),
            ("anthropic", "claude-3-5-sonnet", 150, 0.003),
            ("google", "gemini-1.5-pro", 120, 0.0025)
        ]
        
        for provider, model, tokens, cost in providers_data:
            llm_service.track_usage(
                agent_type="analyst",
                provider=provider,
                model=model,
                tokens=tokens,
                response_time=1000.0,
                estimated_cost=cost
            )
        
        # Verify all providers tracked
        assert len(llm_service.usage_history) == 3
        
        providers_tracked = {usage.provider for usage in llm_service.usage_history}
        assert providers_tracked == {"openai", "anthropic", "google"}

    @pytest.mark.real_data
    def test_get_usage_summary(self, llm_service):
        """Test usage summary generation."""
        # Add some usage data
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        # Track multiple requests
        for i in range(5):
            llm_service.track_usage(
                agent_type="analyst",
                provider="openai",
                model="gpt-4o-mini",
                tokens=100 + i * 10,
                response_time=1000.0 + i * 100,
                estimated_cost=0.002 + i * 0.001
            )
        
        summary = llm_service.get_usage_summary(start_time, end_time)
        
        # Verify summary structure
        assert isinstance(summary, dict)
        assert "total_requests" in summary
        assert "total_tokens" in summary
        assert "total_cost" in summary
        assert "average_response_time" in summary
        assert "provider_breakdown" in summary
        assert "agent_breakdown" in summary
        
        # Verify summary data
        assert summary["total_requests"] == 5
        assert summary["total_tokens"] == 600  # 100+110+120+130+140
        assert summary["total_cost"] > 0

    @pytest.mark.real_data
    def test_get_usage_summary_empty_period(self, llm_service):
        """Test usage summary for period with no data."""
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        summary = llm_service.get_usage_summary(start_time, end_time)
        
        assert summary["total_requests"] == 0
        assert summary["total_tokens"] == 0
        assert summary["total_cost"] == 0.0
        assert summary["average_response_time"] == 0.0

    @pytest.mark.real_data
    def test_clear_metrics(self, llm_service):
        """Test clearing usage metrics."""
        # Add some usage data
        llm_service.track_usage(
            agent_type="analyst",
            provider="openai",
            model="gpt-4o-mini",
            tokens=100,
            response_time=1000.0
        )
        
        assert len(llm_service.usage_history) == 1
        
        # Clear metrics
        llm_service.clear_metrics()
        
        assert len(llm_service.usage_history) == 0

    # Retry Logic Tests
    
    @pytest.mark.external_service
    async def test_with_retry_decorator_success(self, llm_service, retry_config):
        """Test retry decorator with successful operation."""
        call_count = 0
        
        @llm_service.with_retry(retry_config)
        async def successful_operation():
            nonlocal call_count
            call_count += 1
            return {"success": True, "data": "test_result"}
        
        result = await successful_operation()
        
        # Should succeed on first try
        assert call_count == 1
        assert result["success"] is True
        assert result["data"] == "test_result"

    @pytest.mark.external_service
    async def test_with_retry_decorator_retryable_error(self, llm_service, retry_config):
        """Test retry decorator with retryable errors."""
        call_count = 0
        
        @llm_service.with_retry(retry_config)
        async def failing_then_succeeding_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Temporary timeout")
            return {"success": True, "retry_count": call_count}
        
        result = await failing_then_succeeding_operation()
        
        # Should succeed after retries
        assert call_count == 3
        assert result["success"] is True
        assert result["retry_count"] == 3

    @pytest.mark.external_service
    async def test_with_retry_decorator_non_retryable_error(self, llm_service, retry_config):
        """Test retry decorator with non-retryable errors."""
        call_count = 0
        
        @llm_service.with_retry(retry_config)
        async def non_retryable_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid API key")  # Non-retryable error
        
        with pytest.raises(ValueError, match="Invalid API key"):
            await non_retryable_operation()
        
        # Should not retry for non-retryable errors
        assert call_count == 1

    @pytest.mark.external_service
    async def test_with_retry_decorator_max_retries_exceeded(self, llm_service):
        """Test retry decorator when max retries exceeded."""
        retry_config = RetryConfig(max_retries=2, base_delay=0.1)
        call_count = 0
        
        @llm_service.with_retry(retry_config)
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            await always_failing_operation()
        
        # Should try initial + max_retries times
        assert call_count == 3  # 1 initial + 2 retries

    @pytest.mark.external_service
    async def test_with_retry_exponential_backoff(self, llm_service):
        """Test retry decorator uses exponential backoff."""
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=0.1,
            backoff_multiplier=2.0,
            jitter=False  # Disable jitter for predictable timing
        )
        
        call_times = []
        
        @llm_service.with_retry(retry_config)
        async def timing_operation():
            call_times.append(time.time())
            raise TimeoutError("Always fails")
        
        with pytest.raises(TimeoutError):
            await timing_operation()
        
        # Verify exponential backoff timing
        assert len(call_times) == 4  # 1 initial + 3 retries
        
        # Check delays between calls (approximately)
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Should be approximately 0.1, 0.2, 0.4 seconds
        assert 0.08 <= delays[0] <= 0.15  # ~0.1s
        assert 0.18 <= delays[1] <= 0.25  # ~0.2s  
        assert 0.35 <= delays[2] <= 0.45  # ~0.4s

    # Cost Monitoring Tests
    
    @pytest.mark.mock_data
    def test_cost_calculation_openai(self, llm_service):
        """Test cost calculation for OpenAI."""
        cost = llm_service.calculate_cost(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=1000,
            output_tokens=500
        )
        
        # OpenAI pricing should be calculated correctly
        assert isinstance(cost, float)
        assert cost > 0
        
        # Cost should increase with more tokens
        higher_cost = llm_service.calculate_cost(
            provider="openai",
            model="gpt-4o-mini", 
            input_tokens=2000,
            output_tokens=1000
        )
        assert higher_cost > cost

    @pytest.mark.mock_data
    def test_cost_calculation_anthropic(self, llm_service):
        """Test cost calculation for Anthropic."""
        cost = llm_service.calculate_cost(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert isinstance(cost, float)
        assert cost > 0

    @pytest.mark.mock_data
    def test_cost_calculation_google(self, llm_service):
        """Test cost calculation for Google."""
        cost = llm_service.calculate_cost(
            provider="google",
            model="gemini-1.5-pro",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert isinstance(cost, float)
        assert cost > 0

    @pytest.mark.mock_data
    def test_cost_calculation_unknown_provider(self, llm_service):
        """Test cost calculation for unknown provider."""
        cost = llm_service.calculate_cost(
            provider="unknown_provider",
            model="unknown_model",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Should return 0 for unknown providers
        assert cost == 0.0

    # Usage Metrics Model Tests
    
    @pytest.mark.mock_data
    def test_usage_metrics_to_dict(self, sample_usage_metrics):
        """Test UsageMetrics to_dict conversion."""
        metrics_dict = sample_usage_metrics.to_dict()
        
        # Verify structure
        assert isinstance(metrics_dict, dict)
        assert "timestamp" in metrics_dict
        assert "agent_type" in metrics_dict
        assert "provider" in metrics_dict
        assert "tokens_used" in metrics_dict
        
        # Verify data types after conversion
        assert isinstance(metrics_dict["timestamp"], str)
        assert isinstance(metrics_dict["project_id"], str)
        assert isinstance(metrics_dict["task_id"], str)
        assert isinstance(metrics_dict["tokens_used"], int)

    # Retry Configuration Tests
    
    @pytest.mark.mock_data
    def test_retry_config_defaults(self):
        """Test RetryConfig default values."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 8.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True
        assert isinstance(config.retryable_exceptions, list)

    @pytest.mark.mock_data
    def test_retry_config_custom_values(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=16.0,
            backoff_multiplier=3.0,
            jitter=False,
            retryable_exceptions=["CustomError"]
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 16.0
        assert config.backoff_multiplier == 3.0
        assert config.jitter is False
        assert config.retryable_exceptions == ["CustomError"]

    # Error Classification Tests
    
    @pytest.mark.mock_data
    def test_error_classification_retryable(self, llm_service):
        """Test classification of retryable errors."""
        retryable_errors = [
            TimeoutError("Request timeout"),
            ConnectionError("Network connection failed"),
            Exception("RateLimitError: Too many requests")
        ]
        
        for error in retryable_errors:
            is_retryable = llm_service._is_retryable_error(error)
            assert is_retryable is True

    @pytest.mark.mock_data
    def test_error_classification_non_retryable(self, llm_service):
        """Test classification of non-retryable errors."""
        non_retryable_errors = [
            ValueError("Invalid API key"),
            KeyError("Missing required parameter"),
            TypeError("Invalid parameter type")
        ]
        
        for error in non_retryable_errors:
            is_retryable = llm_service._is_retryable_error(error)
            assert is_retryable is False

    # Performance and Monitoring Tests
    
    @pytest.mark.real_data
    def test_usage_tracking_performance(self, llm_service):
        """Test performance of usage tracking with many requests."""
        start_time = time.time()
        
        # Track many usage records
        for i in range(1000):
            llm_service.track_usage(
                agent_type="analyst",
                provider="openai",
                model="gpt-4o-mini",
                tokens=100,
                response_time=1000.0
            )
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        
        # Should complete within reasonable time
        assert elapsed_ms < 1000  # Less than 1 second
        assert len(llm_service.usage_history) == 1000

    @pytest.mark.real_data
    def test_usage_summary_performance(self, llm_service):
        """Test performance of usage summary generation."""
        # Add substantial usage data
        for i in range(500):
            llm_service.track_usage(
                agent_type=f"agent_{i % 5}",
                provider=["openai", "anthropic", "google"][i % 3],
                model="test_model",
                tokens=100 + i,
                response_time=1000.0 + i
            )
        
        start_time = time.time()
        
        summary = llm_service.get_usage_summary(
            datetime.now(timezone.utc) - timedelta(hours=1),
            datetime.now(timezone.utc)
        )
        
        end_time = time.time()
        elapsed_ms = (end_time - start_time) * 1000
        
        # Should generate summary quickly
        assert elapsed_ms < 500  # Less than 500ms
        assert summary["total_requests"] == 500

    # Integration Tests
    
    @pytest.mark.real_data
    @pytest.mark.external_service
    async def test_llm_service_full_workflow(self, llm_service):
        """Test complete LLM service workflow with retry and tracking."""
        retry_config = RetryConfig(max_retries=2, base_delay=0.1)
        
        @llm_service.with_retry(retry_config)
        async def mock_llm_request():
            # Simulate LLM request
            await asyncio.sleep(0.1)  # Simulate network delay
            return {
                "response": "Generated text",
                "usage": {
                    "input_tokens": 50,
                    "output_tokens": 25,
                    "total_tokens": 75
                }
            }
        
        # Execute request
        result = await mock_llm_request()
        
        # Track the usage
        llm_service.track_usage(
            agent_type="analyst",
            provider="openai",
            model="gpt-4o-mini",
            tokens=result["usage"]["total_tokens"],
            response_time=100.0,
            success=True
        )
        
        # Verify workflow completed
        assert result["response"] == "Generated text"
        assert len(llm_service.usage_history) == 1
        
        # Verify usage was tracked correctly
        usage = llm_service.usage_history[0]
        assert usage.tokens_used == 75
        assert usage.success is True