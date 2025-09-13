"""Integration tests for AutoGen service with LLM reliability features.

This module tests the complete integration of reliability features
with the AutoGen service in realistic scenarios.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.autogen_service import AutoGenService
from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact
from app.models.agent import AgentType


class TestAutoGenServiceReliability:
    """Integration tests for AutoGen service with reliability features."""
    
    @pytest.fixture
    def autogen_service(self):
        """Create AutoGen service with mocked dependencies."""
        with patch('app.services.autogen_service.settings') as mock_settings:
            # Mock settings for testing
            mock_settings.llm_retry_max_attempts = 2
            mock_settings.llm_retry_base_delay = 0.1
            mock_settings.llm_max_response_size = 1000
            mock_settings.llm_enable_usage_tracking = True
            
            service = AutoGenService()
            return service
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task for testing."""
        task = Mock(spec=Task)
        task.task_id = uuid4()
        task.project_id = uuid4()
        task.agent_type = AgentType.ANALYST.value
        return task
    
    @pytest.fixture
    def mock_handoff(self):
        """Create a mock handoff schema."""
        handoff = Mock(spec=HandoffSchema)
        handoff.instructions = "Analyze the requirements"
        handoff.phase = "analysis"
        handoff.expected_outputs = ["requirements_document"]
        return handoff
    
    @pytest.fixture
    def mock_context_artifacts(self):
        """Create mock context artifacts."""
        artifact = Mock(spec=ContextArtifact)
        artifact.context_id = uuid4()
        artifact.source_agent = "user"
        artifact.artifact_type = "user_input"
        artifact.content = "User requirements for the system"
        return [artifact]
    
    @pytest.mark.asyncio
    async def test_successful_conversation_with_validation(self, autogen_service, mock_task):
        """Test successful LLM conversation with response validation."""
        # Mock the AutoGen agent and response
        mock_agent = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = '{"analysis": "Requirements analysis complete", "status": "success"}'
        mock_response.messages = [mock_message]
        
        # Mock the agent.on_messages method
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        # Test the conversation
        message = "Please analyze these requirements"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Verify response is properly handled
        assert result is not None
        assert "analysis" in result or "Requirements analysis complete" in result
        
        # Verify agent was called
        mock_agent.on_messages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_conversation_with_retry_logic(self, autogen_service, mock_task):
        """Test conversation with retry on timeout error."""
        mock_agent = Mock()
        
        # Mock agent to fail first, then succeed
        call_count = 0
        
        async def mock_on_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Request timeout")
            
            # Success response
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = '{"status": "completed", "retry_success": true}'
            mock_response.messages = [mock_message]
            return mock_response
        
        mock_agent.on_messages = mock_on_messages
        
        # Test conversation with retry
        message = "Test message"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Should succeed after retry
        assert result is not None
        assert call_count == 2  # First failure, then success
        assert "retry_success" in result or "completed" in result
    
    @pytest.mark.asyncio
    async def test_conversation_permanent_failure_fallback(self, autogen_service, mock_task):
        """Test conversation with permanent failure and fallback response."""
        mock_agent = Mock()
        
        # Mock agent to always fail
        mock_agent.on_messages = AsyncMock(side_effect=ConnectionError("Network unreachable"))
        
        # Test conversation
        message = "Test message"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Should return fallback response
        assert result is not None
        # Fallback responses contain specific patterns based on agent type
        assert "analysis" in result.lower() or "requirements" in result.lower()
    
    @pytest.mark.asyncio
    async def test_response_validation_and_sanitization(self, autogen_service, mock_task):
        """Test response validation and sanitization of malicious content."""
        mock_agent = Mock()
        mock_response = Mock()
        mock_message = Mock()
        
        # Response with potentially malicious content
        mock_message.content = '{"result": "Analysis complete", "script": "<script>alert(\\"bad\\")</script>"}'
        mock_response.messages = [mock_message]
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        # Test conversation
        message = "Analyze this"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Response should be sanitized
        assert result is not None
        assert "<script>" not in result
        assert "alert(" not in result
        assert "Analysis complete" in result  # Safe content preserved
    
    @pytest.mark.asyncio
    async def test_invalid_json_response_recovery(self, autogen_service, mock_task):
        """Test recovery from invalid JSON responses."""
        mock_agent = Mock()
        mock_response = Mock()
        mock_message = Mock()
        
        # Invalid JSON response
        mock_message.content = '{"incomplete": json, "missing_quotes": true'
        mock_response.messages = [mock_message]
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        # Test conversation
        message = "Generate response"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Should recover with fallback response
        assert result is not None
        # Should either be recovered JSON or fallback response
        try:
            json.loads(result)
            # If it parses as JSON, recovery worked
        except json.JSONDecodeError:
            # If not JSON, should be fallback response
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_usage_tracking_integration(self, autogen_service, mock_task):
        """Test usage tracking integration with successful requests."""
        mock_agent = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = '{"analysis": "Complete", "tokens": 150}'
        mock_response.messages = [mock_message]
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        # Get initial stats
        initial_stats = autogen_service.get_usage_stats()
        initial_requests = initial_stats["session_stats"]["requests_tracked"]
        
        # Test conversation
        message = "A" * 100  # Known message length for token estimation
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Verify tracking
        final_stats = autogen_service.get_usage_stats()
        assert final_stats["session_stats"]["requests_tracked"] == initial_requests + 1
        assert final_stats["session_stats"]["total_tokens"] > 0
        assert final_stats["session_stats"]["total_cost"] > 0
        assert final_stats["session_stats"]["error_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_error_tracking_integration(self, autogen_service, mock_task):
        """Test usage tracking integration with failed requests."""
        mock_agent = Mock()
        mock_agent.on_messages = AsyncMock(side_effect=Exception("Permanent failure"))
        
        # Get initial stats
        initial_stats = autogen_service.get_usage_stats()
        initial_requests = initial_stats["session_stats"]["requests_tracked"]
        initial_errors = initial_stats["session_stats"]["errors_tracked"]
        
        # Test conversation (will fail permanently)
        message = "Test message"
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, message, mock_task
        )
        
        # Should return fallback response
        assert result is not None
        
        # Verify error tracking
        final_stats = autogen_service.get_usage_stats()
        assert final_stats["session_stats"]["requests_tracked"] == initial_requests + 1
        assert final_stats["session_stats"]["errors_tracked"] == initial_errors + 1
        assert final_stats["session_stats"]["total_cost"] == 0  # No cost for failed requests
    
    @pytest.mark.asyncio
    async def test_complete_task_execution_with_reliability(self, autogen_service, mock_task, mock_handoff, mock_context_artifacts):
        """Test complete task execution with all reliability features."""
        
        # Mock agent creation and conversation
        with patch.object(autogen_service, 'create_agent') as mock_create_agent, \
             patch.object(autogen_service, 'run_single_agent_conversation') as mock_conversation:
            
            # Mock agent
            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent
            
            # Mock successful conversation
            mock_conversation.return_value = '{"analysis_complete": true, "deliverable": "requirements_doc"}'
            
            # Execute task
            result = await autogen_service.execute_task(
                mock_task, mock_handoff, mock_context_artifacts
            )
            
            # Verify successful execution
            assert result["success"] is True
            assert result["agent_type"] == mock_task.agent_type
            assert "analysis_complete" in result["output"] or "requirements_doc" in result["output"]
            
            # Verify agent was created and conversation ran
            mock_create_agent.assert_called_once()
            mock_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_execution_with_conversation_failure(self, autogen_service, mock_task, mock_handoff, mock_context_artifacts):
        """Test task execution when conversation fails."""
        
        with patch.object(autogen_service, 'create_agent') as mock_create_agent, \
             patch.object(autogen_service, 'run_single_agent_conversation') as mock_conversation:
            
            mock_agent = Mock()
            mock_create_agent.return_value = mock_agent
            
            # Mock conversation that raises exception
            mock_conversation.side_effect = Exception("Conversation failed")
            
            # Execute task
            result = await autogen_service.execute_task(
                mock_task, mock_handoff, mock_context_artifacts
            )
            
            # Should handle failure gracefully
            assert result["success"] is False
            assert "error" in result
            assert result["agent_type"] == mock_task.agent_type
    
    @pytest.mark.asyncio
    async def test_agent_reuse_across_tasks(self, autogen_service):
        """Test that agents are reused for efficiency."""
        
        # Create two tasks with same agent type
        task1 = Mock(spec=Task)
        task1.task_id = uuid4()
        task1.agent_type = AgentType.CODER.value
        
        task2 = Mock(spec=Task)
        task2.task_id = uuid4()
        task2.agent_type = AgentType.CODER.value
        
        handoff = Mock(spec=HandoffSchema)
        handoff.instructions = "Code generation task"
        handoff.phase = "development"
        handoff.expected_outputs = ["source_code"]
        
        with patch.object(autogen_service, 'run_single_agent_conversation') as mock_conversation:
            mock_conversation.return_value = '{"code": "generated"}'
            
            # Spy on create_agent to track calls while still allowing real execution
            original_create_agent = autogen_service.create_agent
            create_agent_calls = []
            
            def spy_create_agent(*args, **kwargs):
                create_agent_calls.append((args, kwargs))
                return original_create_agent(*args, **kwargs)
            
            with patch.object(autogen_service, 'create_agent', side_effect=spy_create_agent):
                # Execute first task
                await autogen_service.execute_task(task1, handoff, [])
                
                # Execute second task with same agent type
                await autogen_service.execute_task(task2, handoff, [])
                
                # Agent should only be created once (reused for second task)
                assert len(create_agent_calls) == 1
                assert mock_conversation.call_count == 2
                
                # Verify the agent is in the service's agents dict
                agent_name = f"{AgentType.CODER.value}_agent"
                assert agent_name in autogen_service.agents
    
    def test_get_usage_stats_structure(self, autogen_service):
        """Test usage statistics structure and content."""
        stats = autogen_service.get_usage_stats()
        
        # Verify expected structure
        assert "session_stats" in stats
        assert "retry_stats" in stats
        assert "validator_enabled" in stats
        assert "tracking_enabled" in stats
        
        # Verify session stats structure
        session_stats = stats["session_stats"]
        expected_keys = [
            "requests_tracked", "total_tokens", "total_cost", 
            "errors_tracked", "error_rate", "average_cost_per_request", 
            "average_tokens_per_request"
        ]
        for key in expected_keys:
            assert key in session_stats
        
        # Verify boolean flags
        assert isinstance(stats["validator_enabled"], bool)
        assert isinstance(stats["tracking_enabled"], bool)


class TestAutoGenServiceErrorScenarios:
    """Test error scenarios and edge cases."""
    
    @pytest.fixture
    def autogen_service(self):
        """Create AutoGen service for error testing."""
        with patch('app.services.autogen_service.settings') as mock_settings:
            mock_settings.llm_retry_max_attempts = 1  # Minimal retries for faster tests
            mock_settings.llm_retry_base_delay = 0.01
            mock_settings.llm_max_response_size = 100  # Small for testing oversized responses
            mock_settings.llm_enable_usage_tracking = True
            
            return AutoGenService()
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, autogen_service):
        """Test handling of empty responses from LLM."""
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.messages = []  # Empty messages
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        task = Mock()
        task.task_id = uuid4()
        task.agent_type = AgentType.TESTER.value
        
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, "test message", task
        )
        
        # Should handle empty response gracefully
        assert result is not None
        assert len(result) > 0  # Should provide some fallback content
    
    @pytest.mark.asyncio
    async def test_oversized_response_handling(self, autogen_service):
        """Test handling of oversized responses."""
        mock_agent = Mock()
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = "x" * 200  # Exceeds 100 character limit
        mock_response.messages = [mock_message]
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        task = Mock()
        task.task_id = uuid4()
        task.agent_type = AgentType.ANALYST.value
        
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, "test message", task
        )
        
        # Should handle oversized response (validation failure -> recovery)
        assert result is not None
        # Result should either be truncated or fallback response
    
    @pytest.mark.asyncio
    async def test_malformed_agent_response_structure(self, autogen_service):
        """Test handling of malformed agent response structure."""
        mock_agent = Mock()
        mock_response = Mock()
        
        # Response with malformed message structure
        mock_message = Mock()
        delattr(mock_message, 'content') if hasattr(mock_message, 'content') else None
        mock_response.messages = [mock_message]
        mock_agent.on_messages = AsyncMock(return_value=mock_response)
        
        task = Mock()
        task.task_id = uuid4()
        task.agent_type = AgentType.DEPLOYER.value
        
        result = await autogen_service.run_single_agent_conversation(
            mock_agent, "test message", task
        )
        
        # Should handle malformed response gracefully
        assert result is not None
        assert len(result) > 0


class TestAutoGenServicePerformance:
    """Performance and load testing scenarios."""
    
    @pytest.fixture
    def autogen_service(self):
        """Create AutoGen service for performance testing."""
        with patch('app.services.autogen_service.settings') as mock_settings:
            mock_settings.llm_retry_max_attempts = 1
            mock_settings.llm_retry_base_delay = 0.01
            mock_settings.llm_max_response_size = 10000
            mock_settings.llm_enable_usage_tracking = True
            
            return AutoGenService()
    
    @pytest.mark.asyncio
    async def test_concurrent_conversations(self, autogen_service):
        """Test handling of concurrent LLM conversations."""
        
        async def create_mock_conversation(agent_type, delay=0.1):
            mock_agent = Mock()
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = f'{{"agent": "{agent_type}", "completed": true}}'
            mock_response.messages = [mock_message]
            
            # Add artificial delay to simulate real LLM response time
            async def delayed_response(*args, **kwargs):
                await asyncio.sleep(delay)
                return mock_response
            
            mock_agent.on_messages = delayed_response
            
            task = Mock()
            task.task_id = uuid4()
            task.agent_type = agent_type
            
            return await autogen_service.run_single_agent_conversation(
                mock_agent, f"Task for {agent_type}", task
            )
        
        # Run multiple conversations concurrently
        tasks = [
            create_mock_conversation(AgentType.ANALYST.value),
            create_mock_conversation(AgentType.ARCHITECT.value),
            create_mock_conversation(AgentType.CODER.value),
            create_mock_conversation(AgentType.TESTER.value)
        ]
        
        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        
        # All should complete successfully
        assert len(results) == 4
        for result in results:
            assert result is not None
            assert len(result) > 0
        
        # Should complete faster than sequential execution due to concurrency
        # With 0.1s delay each, sequential would take 0.4s, concurrent should be ~0.1s
        assert elapsed_time < 0.3
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_tracking(self, autogen_service):
        """Test memory usage doesn't grow excessively with usage tracking."""
        import gc
        
        # Perform many operations to test memory usage
        for i in range(20):  # Reduced from 100 for faster testing
            mock_agent = Mock()
            mock_response = Mock()
            mock_message = Mock()
            mock_message.content = f'{{"iteration": {i}, "data": "test_data"}}'
            mock_response.messages = [mock_message]
            mock_agent.on_messages = AsyncMock(return_value=mock_response)
            
            task = Mock()
            task.task_id = uuid4()
            task.agent_type = AgentType.CODER.value
            
            await autogen_service.run_single_agent_conversation(
                mock_agent, f"Message {i}", task
            )
        
        # Force garbage collection
        gc.collect()
        
        # Check that stats are being tracked
        stats = autogen_service.get_usage_stats()
        assert stats["session_stats"]["requests_tracked"] == 20
        
        # Memory usage test would require more sophisticated monitoring
        # For now, just verify the system is still responsive
        assert stats["session_stats"]["total_tokens"] > 0
        assert stats["session_stats"]["total_cost"] > 0


# Utility functions for testing
def create_test_task(agent_type: str = AgentType.ANALYST.value):
    """Create a test task with minimal required fields."""
    task = Mock(spec=Task)
    task.task_id = uuid4()
    task.project_id = uuid4()
    task.agent_type = agent_type
    return task


def create_test_handoff(instructions: str = "Test instructions"):
    """Create a test handoff schema."""
    handoff = Mock(spec=HandoffSchema)
    handoff.instructions = instructions
    handoff.phase = "test_phase"
    handoff.expected_outputs = ["test_output"]
    return handoff


# Run tests with: python -m pytest tests/integration/test_autogen_reliability.py -v