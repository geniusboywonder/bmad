"""Unit tests for LLM reliability features.

This module tests the response validation, retry logic, and usage tracking
components to ensure robust LLM integration.
"""

import pytest
import json
import time
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from app.services.llm_validation import (
    LLMResponseValidator, ValidationResult, ValidationError, ValidationErrorType
)
from app.services.llm_retry import (
    LLMRetryHandler, RetryConfig, RetryResult, RetryAttempt
)
from app.services.llm_monitoring import (
    LLMUsageTracker, UsageMetrics, CostBreakdown, LLMProvider
)


class TestLLMResponseValidator:
    """Test suite for LLM response validation and sanitization."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return LLMResponseValidator(max_response_size=1000)
    
    @pytest.mark.asyncio
    async def test_validate_valid_json_response(self, validator):
        """Test validation of valid JSON response."""
        response = '{"status": "completed", "data": {"result": "success"}}'
        
        result = await validator.validate_response(response, "json")
        
        assert result.is_valid
        assert result.sanitized_content is not None
        assert isinstance(result.sanitized_content, dict)
        assert result.sanitized_content["status"] == "completed"
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_json_response(self, validator):
        """Test validation of invalid JSON response."""
        response = '{"status": "completed", "data": invalid_json}'
        
        result = await validator.validate_response(response, "json")
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.INVALID_JSON
        assert result.errors[0].recoverable
    
    @pytest.mark.asyncio
    async def test_validate_oversized_response(self, validator):
        """Test validation of response exceeding size limit."""
        response = "x" * 2000  # Exceeds 1000 character limit
        
        result = await validator.validate_response(response, "text")
        
        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].error_type == ValidationErrorType.CONTENT_TOO_LARGE
        assert not result.errors[0].recoverable
    
    @pytest.mark.asyncio
    async def test_detect_malicious_content(self, validator):
        """Test detection of potentially malicious content."""
        malicious_responses = [
            '<script>alert("xss")</script>',
            'javascript:void(0)',
            'onclick="malicious()"',
            'eval("dangerous_code")',
            'setTimeout(function(){}, 0)'
        ]
        
        for response in malicious_responses:
            result = await validator.validate_response(response, "text")
            
            assert not result.is_valid
            assert any(e.error_type == ValidationErrorType.MALICIOUS_CONTENT for e in result.errors)
    
    @pytest.mark.asyncio 
    async def test_sanitize_content_dict(self, validator):
        """Test sanitization of dictionary content."""
        content = {
            "safe_text": "This is safe",
            "malicious_script": "<script>alert('bad')</script>",
            "nested": {
                "also_malicious": "javascript:void(0)",
                "safe_number": 42
            },
            "list_content": [
                "safe item",
                "<script>bad</script>",
                {"nested_bad": "eval('dangerous')"}
            ]
        }
        
        sanitized = await validator.sanitize_content(content)
        
        assert sanitized["safe_text"] == "This is safe"
        assert "<script>" not in sanitized["malicious_script"]
        assert "javascript:" not in sanitized["nested"]["also_malicious"]
        assert sanitized["nested"]["safe_number"] == 42
        assert "<script>" not in sanitized["list_content"][1]
        assert "eval(" not in sanitized["list_content"][2]["nested_bad"]
    
    @pytest.mark.asyncio
    async def test_handle_validation_failure_json_recovery(self, validator):
        """Test recovery from JSON validation failure."""
        response = 'Some text before {"valid": "json", "number": 123} some text after'
        error = ValidationError(ValidationErrorType.INVALID_JSON, "JSON parsing failed", True)
        
        recovered = await validator.handle_validation_failure(response, error)
        
        # Should extract the valid JSON portion
        recovered_data = json.loads(recovered)
        assert recovered_data["valid"] == "json"
        assert recovered_data["number"] == 123
    
    @pytest.mark.asyncio
    async def test_handle_validation_failure_malicious_recovery(self, validator):
        """Test recovery from malicious content."""
        response = 'Safe text <script>alert("bad")</script> more safe text'
        error = ValidationError(ValidationErrorType.MALICIOUS_CONTENT, "Malicious content detected", True)
        
        recovered = await validator.handle_validation_failure(response, error)
        
        recovered_data = json.loads(recovered)
        assert recovered_data["type"] == "sanitized"
        assert "<script>" not in recovered_data["content"]
        assert "Safe text" in recovered_data["content"]
    
    @pytest.mark.asyncio
    async def test_auto_format_detection(self, validator):
        """Test automatic format detection."""
        # JSON-like response
        json_response = '{"key": "value"}'
        result = await validator.validate_response(json_response, "auto")
        assert result.is_valid
        assert isinstance(result.sanitized_content, dict)
        
        # Plain text response
        text_response = "This is plain text"
        result = await validator.validate_response(text_response, "auto")
        assert result.is_valid
        assert result.sanitized_content["type"] == "text"


class TestLLMRetryHandler:
    """Test suite for LLM retry logic with exponential backoff."""
    
    @pytest.fixture
    def retry_config(self):
        """Create retry configuration for testing."""
        return RetryConfig(
            max_retries=3,
            base_delay=0.1,  # Shorter delays for testing
            max_delay=1.0,
            jitter=False  # Disable jitter for predictable tests
        )
    
    @pytest.fixture
    def retry_handler(self, retry_config):
        """Create retry handler for testing."""
        return LLMRetryHandler(retry_config)
    
    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self, retry_handler):
        """Test successful call that doesn't need retry."""
        mock_result = "success"
        
        async def successful_call():
            return mock_result
        
        result = await retry_handler.execute_with_retry(successful_call)
        
        assert result.success
        assert result.result == mock_result
        assert result.total_attempts == 1
        assert len(result.attempts) == 0  # No retry attempts
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout_error(self, retry_handler):
        """Test retry behavior on timeout errors."""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Request timed out")
            return "success_after_retries"
        
        start_time = time.time()
        result = await retry_handler.execute_with_retry(failing_then_success)
        elapsed = time.time() - start_time
        
        assert result.success
        assert result.result == "success_after_retries"
        assert result.total_attempts == 3
        assert len(result.attempts) == 2  # 2 failed attempts before success
        assert elapsed >= 0.3  # Should have waited (0.1 + 0.2 seconds)
    
    @pytest.mark.asyncio
    async def test_permanent_failure_after_max_retries(self, retry_handler):
        """Test permanent failure after exhausting retries."""
        
        async def always_fails():
            raise ConnectionError("Network unreachable")
        
        result = await retry_handler.execute_with_retry(always_fails)
        
        assert not result.success
        assert result.total_attempts == 4  # Initial + 3 retries
        assert len(result.attempts) == 4
        assert isinstance(result.final_error, ConnectionError)
    
    @pytest.mark.asyncio
    async def test_non_retryable_error_immediate_failure(self, retry_handler):
        """Test immediate failure for non-retryable errors."""
        
        async def auth_error():
            raise Exception("Invalid API key")
        
        # Mock the should_retry method to return False for this error
        with patch.object(retry_handler, 'should_retry', return_value=False):
            result = await retry_handler.execute_with_retry(auth_error)
        
        assert not result.success
        assert result.total_attempts == 1  # No retries
        assert len(result.attempts) == 1
    
    def test_calculate_backoff_delay(self, retry_handler):
        """Test exponential backoff delay calculation."""
        # Test exponential progression: 0.1, 0.2, 0.4, 0.8, 1.0 (capped)
        delays = [retry_handler.calculate_backoff_delay(i) for i in range(1, 6)]
        
        assert delays[0] == 0.1  # Base delay
        assert delays[1] == 0.2  # Base * 2
        assert delays[2] == 0.4  # Base * 4  
        assert delays[3] == 0.8  # Base * 8
        assert delays[4] == 1.0  # Capped at max_delay
    
    @pytest.mark.asyncio
    async def test_should_retry_classification(self, retry_handler):
        """Test error classification for retry decisions."""
        # Retryable errors
        retryable_errors = [
            TimeoutError("Request timeout"),
            ConnectionError("Network error"),
            Exception("Service unavailable")  # Generic exceptions are retryable by default
        ]
        
        for error in retryable_errors:
            should_retry = await retry_handler.should_retry(error, 0, 3)
            assert should_retry, f"Expected {type(error).__name__} to be retryable"
        
        # Test max retries exceeded
        should_retry = await retry_handler.should_retry(TimeoutError("timeout"), 3, 3)
        assert not should_retry
    
    def test_retry_stats_tracking(self, retry_handler):
        """Test retry statistics tracking."""
        # Initial stats should be empty
        stats = retry_handler.get_retry_stats()
        assert stats['total_calls'] == 0
        assert stats['successful_calls'] == 0
        assert stats['failed_calls'] == 0
        
        # Stats are updated by execute_with_retry in real usage
        # This test would need to be integration-style to test the full flow


class TestLLMUsageTracker:
    """Test suite for LLM usage tracking and cost monitoring."""
    
    @pytest.fixture
    def usage_tracker(self):
        """Create usage tracker for testing."""
        return LLMUsageTracker(enable_tracking=True)
    
    @pytest.mark.asyncio
    async def test_track_successful_request(self, usage_tracker):
        """Test tracking of successful LLM request."""
        await usage_tracker.track_request(
            agent_type="analyst",
            tokens_used=150,
            response_time=1500.0,
            cost=0.003,
            success=True,
            provider="openai",
            model="gpt-4o-mini"
        )
        
        stats = usage_tracker.get_session_stats()
        assert stats['requests_tracked'] == 1
        assert stats['total_tokens'] == 150
        assert stats['total_cost'] == 0.003
        assert stats['errors_tracked'] == 0
        assert stats['error_rate'] == 0.0
    
    @pytest.mark.asyncio
    async def test_track_failed_request(self, usage_tracker):
        """Test tracking of failed LLM request."""
        await usage_tracker.track_request(
            agent_type="architect",
            tokens_used=75,  # Only input tokens for failed request
            response_time=2000.0,
            cost=0.0,
            success=False,
            error_type="TimeoutError",
            retry_count=2
        )
        
        stats = usage_tracker.get_session_stats()
        assert stats['requests_tracked'] == 1
        assert stats['errors_tracked'] == 1
        assert stats['error_rate'] == 1.0
        assert stats['total_cost'] == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_openai_costs(self, usage_tracker):
        """Test OpenAI cost calculation."""
        # Test gpt-4o-mini pricing
        cost = await usage_tracker.calculate_costs(
            input_tokens=1000,
            output_tokens=500,
            provider="openai",
            model="gpt-4o-mini"
        )
        
        # Expected: (1000/1000 * 0.00015) + (500/1000 * 0.0006) = 0.00015 + 0.0003 = 0.00045
        expected_cost = 0.00045
        assert abs(cost - expected_cost) < 0.000001
    
    @pytest.mark.asyncio
    async def test_calculate_costs_unknown_model(self, usage_tracker):
        """Test cost calculation with unknown model falls back to default."""
        cost = await usage_tracker.calculate_costs(
            input_tokens=100,
            output_tokens=50,
            provider="openai",
            model="unknown-model"
        )
        
        # Should fall back to first model in pricing table (gpt-4)
        expected_cost = (100/1000 * 0.03) + (50/1000 * 0.06)
        assert abs(cost - expected_cost) < 0.000001
    
    def test_estimate_tokens(self, usage_tracker):
        """Test token estimation from text."""
        # Simple text
        text = "Hello world, this is a test message."
        tokens = usage_tracker.estimate_tokens(text, is_input=True)
        
        # Should be approximately len(text) / 4
        expected_tokens = max(1, len(text) // 4)
        assert abs(tokens - expected_tokens) <= 2  # Allow small variance
    
    def test_estimate_tokens_code(self, usage_tracker):
        """Test token estimation for code content."""
        code = """
        def hello_world():
            return {"message": "Hello, world!"}
        """
        tokens = usage_tracker.estimate_tokens(code, is_input=True)
        
        # Code should have higher token density (1.3x multiplier)
        base_estimate = max(1, len(code) // 4)
        expected_tokens = int(base_estimate * 1.3)
        assert abs(tokens - expected_tokens) <= 3
    
    @pytest.mark.asyncio
    async def test_generate_usage_report_empty_data(self, usage_tracker):
        """Test usage report generation with no data."""
        from uuid import uuid4
        
        project_id = uuid4()
        report = await usage_tracker.generate_usage_report(project_id=project_id)
        
        assert report.project_id == project_id
        assert report.cost_breakdown.total_cost == 0.0
        assert report.cost_breakdown.request_count == 0
        assert len(report.recommendations) > 0
        assert "No usage data" in report.recommendations[0]
    
    @pytest.mark.asyncio
    async def test_detect_usage_anomalies_cost_spike(self, usage_tracker):
        """Test detection of cost spike anomalies."""
        # Add some normal usage
        for i in range(5):
            await usage_tracker.track_request(
                agent_type="tester",
                tokens_used=100,
                response_time=1000.0,
                cost=0.001,  # Normal cost
                success=True
            )
        
        # Add a high-cost request
        await usage_tracker.track_request(
            agent_type="architect",
            tokens_used=5000,
            response_time=10000.0,
            cost=0.1,  # Very high cost
            success=True
        )
        
        anomalies = await usage_tracker.detect_usage_anomalies(lookback_hours=1)
        
        # Should detect cost spike
        cost_spikes = [a for a in anomalies if a["type"] == "cost_spike"]
        assert len(cost_spikes) > 0
        assert cost_spikes[0]["agent_type"] == "architect"
        assert cost_spikes[0]["cost"] == 0.1
    
    @pytest.mark.asyncio
    async def test_detect_usage_anomalies_high_error_rate(self, usage_tracker):
        """Test detection of high error rate anomalies."""
        # Add requests with high error rate (60% failures)
        for i in range(10):
            success = i < 4  # 4 success, 6 failures = 60% error rate
            await usage_tracker.track_request(
                agent_type="coder",
                tokens_used=100,
                response_time=1500.0,
                cost=0.001 if success else 0.0,
                success=success,
                error_type="RateLimitError" if not success else None
            )
        
        anomalies = await usage_tracker.detect_usage_anomalies(lookback_hours=1)
        
        # Should detect high error rate
        error_anomalies = [a for a in anomalies if a["type"] == "high_error_rate"]
        assert len(error_anomalies) > 0
        assert error_anomalies[0]["error_rate"] == 0.6
        assert error_anomalies[0]["severity"] == "high"
    
    def test_session_stats_calculation(self, usage_tracker):
        """Test session statistics calculation."""
        # Manually update stats to test calculation
        usage_tracker.session_stats.update({
            'requests_tracked': 10,
            'total_tokens': 1500,
            'total_cost': 0.05,
            'errors_tracked': 2
        })
        
        stats = usage_tracker.get_session_stats()
        
        assert stats['error_rate'] == 0.2  # 2/10
        assert stats['average_cost_per_request'] == 0.005  # 0.05/10
        assert stats['average_tokens_per_request'] == 150  # 1500/10


class TestIntegrationScenarios:
    """Integration tests for combined LLM reliability features."""
    
    @pytest.fixture
    def validator(self):
        return LLMResponseValidator(max_response_size=1000)
    
    @pytest.fixture 
    def retry_handler(self):
        config = RetryConfig(max_retries=2, base_delay=0.1, jitter=False)
        return LLMRetryHandler(config)
    
    @pytest.fixture
    def usage_tracker(self):
        return LLMUsageTracker(enable_tracking=True)
    
    @pytest.mark.asyncio
    async def test_complete_reliability_workflow(self, validator, retry_handler, usage_tracker):
        """Test complete workflow with all reliability features."""
        # Simulate an LLM call that succeeds after one retry
        call_count = 0
        
        async def llm_call_simulation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("First attempt timeout")
            return '{"status": "completed", "result": "Generated after retry"}'
        
        # Execute with retry
        retry_result = await retry_handler.execute_with_retry(llm_call_simulation)
        
        assert retry_result.success
        assert retry_result.total_attempts == 2
        
        # Validate response
        raw_response = retry_result.result
        validation_result = await validator.validate_response(raw_response, "json")
        
        assert validation_result.is_valid
        assert validation_result.sanitized_content["status"] == "completed"
        
        # Track usage
        await usage_tracker.track_request(
            agent_type="integration_test",
            tokens_used=usage_tracker.estimate_tokens(raw_response),
            response_time=retry_result.total_time * 1000,
            cost=0.002,
            success=True,
            retry_count=retry_result.total_attempts - 1
        )
        
        # Verify tracking
        stats = usage_tracker.get_session_stats()
        assert stats['requests_tracked'] == 1
        assert stats['error_rate'] == 0.0  # Success despite initial failure
    
    @pytest.mark.asyncio
    async def test_complete_failure_scenario(self, validator, retry_handler, usage_tracker):
        """Test complete failure scenario with all components."""
        # Simulate permanent failure
        async def failing_llm_call():
            raise ConnectionError("Permanent network failure")
        
        # Execute with retry
        retry_result = await retry_handler.execute_with_retry(failing_llm_call)
        
        assert not retry_result.success
        assert retry_result.total_attempts == 3  # Initial + 2 retries
        
        # Track failed request
        await usage_tracker.track_request(
            agent_type="failure_test",
            tokens_used=50,  # Only input tokens
            response_time=retry_result.total_time * 1000,
            cost=0.0,
            success=False,
            error_type="ConnectionError",
            retry_count=retry_result.total_attempts - 1
        )
        
        # Verify failure tracking
        stats = usage_tracker.get_session_stats()
        assert stats['requests_tracked'] == 1
        assert stats['errors_tracked'] == 1
        assert stats['error_rate'] == 1.0
        assert stats['total_cost'] == 0.0


# Test fixtures and utilities for mocking AutoGen components
@pytest.fixture
def mock_autogen_response():
    """Mock AutoGen response object."""
    mock_response = Mock()
    mock_message = Mock()
    mock_message.content = '{"task_completed": true, "output": "Test response"}'
    mock_response.messages = [mock_message]
    return mock_response


@pytest.fixture
def mock_task():
    """Mock task object for testing."""
    from uuid import uuid4
    from app.models.task import Task
    
    # Create a mock task with required attributes
    task = Mock(spec=Task)
    task.task_id = uuid4()
    task.project_id = uuid4()
    task.agent_type = "test_agent"
    return task


# Run tests with: python -m pytest tests/unit/test_llm_reliability.py -v