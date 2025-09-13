"""Base agent class with LLM reliability integration."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID
import structlog
from autogen_agentchat.agents import AssistantAgent

from app.models.task import Task
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.services.llm_validation import LLMResponseValidator
from app.services.llm_retry import LLMRetryHandler, RetryConfig
from app.services.llm_monitoring import LLMUsageTracker
from app.config import settings

logger = structlog.get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all BotArmy agents with LLM reliability integration.
    
    This class provides common functionality for all agents including:
    - LLM reliability features (validation, retry, monitoring) from Task 1
    - AutoGen ConversableAgent management
    - Context artifact processing
    - Structured handoff creation
    """
    
    def __init__(self, agent_type: AgentType, llm_config: Dict[str, Any]):
        """Initialize base agent with LLM reliability components.
        
        Args:
            agent_type: The type of agent (ORCHESTRATOR, ANALYST, etc.)
            llm_config: LLM configuration including model, temperature, etc.
        """
        self.agent_type = agent_type
        self.llm_config = llm_config
        
        # LLM Reliability Components from Task 1
        self.response_validator = LLMResponseValidator(
            max_response_size=settings.llm_max_response_size
        )
        
        retry_config = RetryConfig(
            max_retries=settings.llm_retry_max_attempts,
            base_delay=settings.llm_retry_base_delay,
            max_delay=8.0
        )
        self.retry_handler = LLMRetryHandler(retry_config)
        
        self.usage_tracker = LLMUsageTracker(
            enable_tracking=settings.llm_enable_usage_tracking
        )
        
        # AutoGen agent instance (initialized by subclasses)
        self.autogen_agent: Optional[AssistantAgent] = None
        
        logger.info("Base agent initialized", 
                   agent_type=agent_type.value,
                   llm_model=llm_config.get("model", "unknown"))
    
    @abstractmethod
    def _create_system_message(self) -> str:
        """Create agent-specific system message for AutoGen.
        
        Returns:
            System message string that defines the agent's role and behavior.
        """
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute agent-specific task with context artifacts.
        
        Args:
            task: Task to execute
            context: List of context artifacts from previous agents
            
        Returns:
            Execution result with status, output, and created artifacts
        """
        pass
    
    @abstractmethod
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: List[ContextArtifact]) -> HandoffSchema:
        """Create structured handoff to another agent.
        
        Args:
            to_agent: Target agent type for the handoff
            task: Current task being handed off
            context: Context artifacts to pass along
            
        Returns:
            HandoffSchema with structured handoff information
        """
        pass
    
    def _initialize_autogen_agent(self) -> None:
        """Initialize AutoGen ConversableAgent instance.
        
        This method should be called by subclasses after they define their system message.
        """
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        import os
        
        # Create model client
        api_key = os.getenv("OPENAI_API_KEY", "demo-key")
        model_client = OpenAIChatCompletionClient(
            model=self.llm_config.get("model", "gpt-4o-mini"),
            api_key=api_key,
            temperature=self.llm_config.get("temperature", 0.7)
        )
        
        # Create AutoGen agent
        self.autogen_agent = AssistantAgent(
            name=f"{self.agent_type.value}_agent",
            model_client=model_client,
            system_message=self._create_system_message(),
            description=f"Agent specialized in {self.agent_type.value} tasks"
        )
        
        logger.info("AutoGen agent initialized", 
                   agent_name=f"{self.agent_type.value}_agent")
    
    async def _execute_with_reliability(self, message: str, task: Task) -> str:
        """Execute LLM conversation with comprehensive reliability features.
        
        This method integrates Task 1's LLM reliability features including:
        - Retry logic with exponential backoff
        - Response validation and sanitization  
        - Usage tracking and cost monitoring
        - Structured error handling
        
        Args:
            message: Message to send to the agent
            task: Task context for monitoring
            
        Returns:
            Agent response with validation and error handling
        """
        if not self.autogen_agent:
            raise ValueError(f"AutoGen agent not initialized for {self.agent_type.value}")
        
        import time
        from autogen_core.models import UserMessage
        
        start_time = time.time()
        context = {
            "task_id": str(task.task_id) if task.task_id else None,
            "project_id": str(task.project_id) if task.project_id else None,
            "agent_type": self.agent_type.value,
            "message_length": len(message)
        }
        
        try:
            # Create message for the agent
            user_message = UserMessage(content=message, source="user")
            
            # Define LLM call with retry wrapper
            async def llm_call():
                return await self.autogen_agent.on_messages([user_message], cancellation_token=None)
            
            # Execute with retry logic
            logger.info("Starting LLM conversation with reliability features", **context)
            retry_result = await self.retry_handler.execute_with_retry(llm_call, context=context)
            
            response_time = (time.time() - start_time) * 1000
            
            if not retry_result.success:
                # Handle permanent failure
                logger.error("Agent LLM conversation failed permanently", 
                           attempts=retry_result.total_attempts,
                           total_time=retry_result.total_time,
                           final_error=str(retry_result.final_error),
                           **context)
                
                await self._track_failed_request(task, message, response_time, retry_result)
                return self._generate_fallback_response()
            
            # Extract response content
            response = retry_result.result
            raw_response = ""
            
            if response and response.messages:
                last_message = response.messages[-1]
                raw_response = str(last_message.content) if hasattr(last_message, 'content') else str(last_message)
            else:
                logger.warning("No response from agent", **context)
                raw_response = "No response generated"
            
            # Validate and sanitize response
            validation_result = await self.response_validator.validate_response(
                raw_response, expected_format="auto"
            )
            
            if validation_result.is_valid:
                final_response = raw_response
                if validation_result.sanitized_content:
                    if isinstance(validation_result.sanitized_content, dict):
                        import json
                        final_response = json.dumps(validation_result.sanitized_content)
                    else:
                        final_response = str(validation_result.sanitized_content)
                
                logger.info("Agent response validated successfully", 
                           validation_passed=True,
                           response_length=len(final_response),
                           **context)
            else:
                # Handle validation failure
                logger.warning("Agent response failed validation", 
                             errors=[e.message for e in validation_result.errors],
                             **context)
                
                final_response = await self.response_validator.handle_validation_failure(
                    raw_response, validation_result.errors[0] if validation_result.errors else None
                )
                
                logger.info("Agent response recovered after validation failure",
                           recovered_response_length=len(final_response),
                           **context)
            
            # Track successful request
            await self._track_successful_request(task, message, final_response, response_time, retry_result)
            
            logger.info("Agent conversation completed successfully",
                       response_time_ms=response_time,
                       retry_attempts=retry_result.total_attempts - 1,
                       **context)
            
            return final_response
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            logger.error("Unexpected error in agent conversation", 
                        error=str(e),
                        response_time_ms=response_time,
                        **context)
            
            await self.usage_tracker.track_request(
                agent_type=self.agent_type.value,
                tokens_used=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                project_id=task.project_id,
                task_id=task.task_id,
                error_type=type(e).__name__,
                retry_count=0
            )
            
            return self._generate_fallback_response()
    
    def _generate_fallback_response(self) -> str:
        """Generate fallback response when agent conversation fails.
        
        Returns:
            Generic fallback response appropriate for the agent type.
        """
        return f"""{{
            "agent_type": "{self.agent_type.value}",
            "status": "completed_with_fallback",
            "message": "Task completed using fallback response due to LLM service issues",
            "deliverables": "Basic {self.agent_type.value} deliverable",
            "note": "This is a fallback response. Please review and enhance as needed."
        }}"""
    
    async def _track_successful_request(self, task: Task, message: str, response: str, 
                                      response_time: float, retry_result):
        """Track successful LLM request with comprehensive metrics."""
        
        # Estimate token usage
        input_tokens = self.usage_tracker.estimate_tokens(message, is_input=True)
        output_tokens = self.usage_tracker.estimate_tokens(response, is_input=False)
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        cost = await self.usage_tracker.calculate_costs(
            input_tokens, output_tokens, provider="openai", model=self.llm_config.get("model", "gpt-4o-mini")
        )
        
        # Track the request
        await self.usage_tracker.track_request(
            agent_type=self.agent_type.value,
            tokens_used=total_tokens,
            response_time=response_time,
            cost=cost,
            success=True,
            project_id=task.project_id,
            task_id=task.task_id,
            provider="openai",
            model=self.llm_config.get("model", "gpt-4o-mini"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retry_count=retry_result.total_attempts - 1
        )
    
    async def _track_failed_request(self, task: Task, message: str, response_time: float, retry_result):
        """Track failed LLM request for monitoring and analysis."""
        
        input_tokens = self.usage_tracker.estimate_tokens(message, is_input=True)
        error_type = type(retry_result.final_error).__name__ if retry_result.final_error else "unknown"
        
        await self.usage_tracker.track_request(
            agent_type=self.agent_type.value,
            tokens_used=input_tokens,
            response_time=response_time,
            cost=0.0,
            success=False,
            project_id=task.project_id,
            task_id=task.task_id,
            provider="openai",
            model=self.llm_config.get("model", "gpt-4o-mini"),
            input_tokens=input_tokens,
            output_tokens=0,
            error_type=error_type,
            retry_count=retry_result.total_attempts - 1
        )
    
    def prepare_context_message(self, context_artifacts: List[ContextArtifact], 
                              handoff: HandoffSchema) -> str:
        """Prepare context message from artifacts for agent processing.
        
        Args:
            context_artifacts: List of context artifacts
            handoff: Handoff schema with instructions
            
        Returns:
            Formatted context message string
        """
        context_parts = [
            f"Task: {handoff.instructions}",
            f"Phase: {handoff.phase}",
            f"Expected outputs: {', '.join(handoff.expected_outputs)}",
            "",
            "Context from previous agents:",
        ]
        
        for artifact in context_artifacts:
            context_parts.extend([
                "",
                f"Artifact from {artifact.source_agent} ({artifact.artifact_type}):",
                f"{artifact.content}",
            ])
        
        return "\n".join(context_parts)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information and status.
        
        Returns:
            Dictionary with agent type, status, and configuration
        """
        return {
            "agent_type": self.agent_type.value,
            "llm_config": self.llm_config,
            "autogen_initialized": self.autogen_agent is not None,
            "reliability_features": {
                "validator": self.response_validator is not None,
                "retry_handler": self.retry_handler is not None,
                "usage_tracker": self.usage_tracker is not None
            }
        }