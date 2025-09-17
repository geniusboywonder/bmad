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
from app.services.hitl_safety_service import HITLSafetyService, ApprovalTimeoutError
from app.database.models import ResponseApprovalDB
from app.services.response_safety_analyzer import ResponseSafetyAnalyzer
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
        
        # HITL Safety Service for mandatory controls
        self.hitl_service = HITLSafetyService()

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
        """Initialize AutoGen ConversableAgent instance with dynamic provider selection.

        This method uses the agent LLM mapping configuration to select the appropriate
        LLM provider and model based on agent type.
        """
        from app.config.agent_llm_mapping import get_agent_llm_config
        import os

        # Get agent-specific LLM configuration
        try:
            agent_config = get_agent_llm_config(self.agent_type.value)
            logger.info("Using configured LLM provider for agent",
                       agent_type=self.agent_type.value,
                       provider=agent_config.provider,
                       model=agent_config.model)
        except ValueError as e:
            logger.warning("Failed to get agent LLM config, using defaults",
                          agent_type=self.agent_type.value,
                          error=str(e))
            # Fallback to original configuration
            agent_config = self.llm_config

        # Create model client based on provider
        model_client = self._create_model_client(agent_config)

        # Create AutoGen agent
        self.autogen_agent = AssistantAgent(
            name=f"{self.agent_type.value}_agent",
            model_client=model_client,
            system_message=self._create_system_message(),
            description=f"Agent specialized in {self.agent_type.value} tasks"
        )

        logger.info("AutoGen agent initialized with dynamic provider",
                   agent_name=f"{self.agent_type.value}_agent",
                   provider=getattr(agent_config, 'provider', 'unknown'),
                   model=getattr(agent_config, 'model', 'unknown'))

    def _create_model_client(self, agent_config):
        """Create appropriate model client based on provider configuration."""
        from app.config.agent_llm_mapping import AgentLLMConfig, LLMProvider
        import os

        provider = getattr(agent_config, 'provider', LLMProvider.OPENAI)
        model = getattr(agent_config, 'model', 'gpt-4o')
        temperature = getattr(agent_config, 'temperature', 0.7)
        api_key_env_var = getattr(agent_config, 'api_key_env_var', 'OPENAI_API_KEY')

        # Get API key from environment
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            logger.warning(f"API key not found for {api_key_env_var}, using demo key",
                          provider=provider, agent_type=self.agent_type.value)
            api_key = "demo-key"

        # Create appropriate model client based on provider
        if provider == LLMProvider.OPENAI:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            return OpenAIChatCompletionClient(
                model=model,
                api_key=api_key,
                temperature=temperature
            )
        elif provider == LLMProvider.ANTHROPIC:
            from autogen_ext.models.anthropic import AnthropicChatCompletionClient
            return AnthropicChatCompletionClient(
                model=model,
                api_key=api_key,
                temperature=temperature
            )
        elif provider in [LLMProvider.GOOGLE, LLMProvider.GEMINI]:
            from autogen_ext.models.google import GoogleGeminiChatCompletionClient
            return GoogleGeminiChatCompletionClient(
                model=model,
                api_key=api_key,
                temperature=temperature
            )
        else:
            # Default to OpenAI
            logger.warning(f"Unknown provider {provider}, defaulting to OpenAI",
                          agent_type=self.agent_type.value)
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            return OpenAIChatCompletionClient(
                model=model,
                api_key=api_key,
                temperature=temperature
            )
    
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
    
    async def execute_with_hitl_control(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute agent task with mandatory HITL approval at each step.

        This method implements the core HITL safety architecture requiring:
        1. Pre-execution approval from human
        2. Response approval before proceeding
        3. Next step authorization
        4. Budget verification

        Args:
            task: Task to execute
            context: List of context artifacts

        Returns:
            Execution result with HITL safety controls applied

        Raises:
            AgentExecutionDenied: When human denies agent execution
            BudgetLimitExceeded: When budget limits are exceeded
            EmergencyStopActivated: When emergency stop is active
            ApprovalTimeoutError: When approval requests timeout
        """
        from app.services.hitl_safety_service import (
            AgentExecutionDenied,
            BudgetLimitExceeded,
            EmergencyStopActivated
        )

        logger.info("Starting agent execution with HITL controls",
                   agent_type=self.agent_type.value,
                   task_id=str(task.task_id),
                   project_id=str(task.project_id))

        try:
            # Step 1: Request permission to execute
            execution_approval = await self._request_execution_approval(task)
            if not execution_approval:
                raise AgentExecutionDenied("Human rejected agent execution")

            # Step 2: Check budget limits
            estimated_tokens = getattr(task, 'estimated_tokens', 100)
            budget_check = await self.hitl_service.check_budget_limits(
                task.project_id, self.agent_type.value, estimated_tokens
            )
            if not budget_check.approved:
                raise BudgetLimitExceeded(f"Budget limit exceeded: {budget_check.reason}")

            # Step 3: Execute task with monitoring
            result = await self._execute_with_hitl_monitoring(task, context)

            # Step 4: Request approval for response
            response_approval = await self._request_response_approval(task, result)
            if not response_approval:
                # Human rejected the response - return termination result
                return self._create_termination_result("Human rejected agent response")

            # Step 5: Check if next step is needed and request approval
            if self._has_next_step(result):
                next_step_approval = await self._request_next_step_approval(task, result)
                if not next_step_approval:
                    return self._create_termination_result("Human stopped workflow progression")

            # Update budget usage
            tokens_used = result.get('tokens_used', estimated_tokens)
            await self.hitl_service.update_budget_usage(
                task.project_id, self.agent_type.value, tokens_used
            )

            logger.info("Agent execution completed with HITL approval",
                       agent_type=self.agent_type.value,
                       task_id=str(task.task_id),
                       tokens_used=tokens_used)

            return result

        except (AgentExecutionDenied, BudgetLimitExceeded, EmergencyStopActivated, ApprovalTimeoutError):
            # Re-raise HITL-specific exceptions
            raise
        except Exception as e:
            logger.error("Unexpected error during HITL-controlled execution",
                        agent_type=self.agent_type.value,
                        task_id=str(task.task_id),
                        error=str(e))
            raise

    async def _request_execution_approval(self, task: Task) -> bool:
        """Request human approval before executing agent."""
        try:
            approval_id = await self.hitl_service.create_approval_request(
                project_id=task.project_id,
                task_id=task.task_id,
                agent_type=self.agent_type.value,
                request_type="PRE_EXECUTION",
                request_data={
                    "instructions": task.instructions,
                    "estimated_tokens": getattr(task, 'estimated_tokens', 100),
                    "context_ids": getattr(task, 'context_ids', []),
                    "agent_type": self.agent_type.value
                },
                estimated_tokens=getattr(task, 'estimated_tokens', 100)
            )

            # Wait for human approval
            approval = await self.hitl_service.wait_for_approval(approval_id, timeout_minutes=30)
            return approval.approved

        except ApprovalTimeoutError:
            logger.warning("Execution approval request timed out",
                          agent_type=self.agent_type.value,
                          task_id=str(task.task_id))
            return False

    async def _request_response_approval(self, task: Task, result: Dict[str, Any]) -> bool:
        """Request human approval for agent response with advanced safety analysis."""
        try:
            # First, analyze the response for safety and quality
            analysis_result = await self.hitl_service.analyze_agent_response(
                project_id=task.project_id,
                task_id=task.task_id,
                agent_type=self.agent_type.value,
                approval_request_id=None,  # Will be set when approval is created
                response_content=result
            )

            # If response is auto-approved based on safety analysis, skip human approval
            if analysis_result.get("auto_approved", False):
                logger.info("Response auto-approved based on safety analysis",
                           agent_type=self.agent_type.value,
                           task_id=str(task.task_id),
                           safety_score=analysis_result.get("analysis_result", {}).get("content_safety_score", 0))
                return True

            # Create approval request with safety analysis data
            approval_id = await self.hitl_service.create_approval_request(
                project_id=task.project_id,
                task_id=task.task_id,
                agent_type=self.agent_type.value,
                request_type="RESPONSE_APPROVAL",
                request_data={
                    "agent_response": result.get('output', ''),
                    "artifacts": result.get('artifacts', []),
                    "confidence_score": result.get('confidence', 0.0),
                    "tokens_used": result.get('tokens_used', 0),
                    "status": result.get('status', 'unknown'),
                    "safety_analysis": analysis_result.get("analysis_result", {}),
                    "auto_approved": analysis_result.get("auto_approved", False),
                    "requires_manual_review": analysis_result.get("requires_manual_review", True)
                }
            )

            # Update the response approval record with the approval request ID
            if analysis_result.get("response_approval_id"):
                from app.database.connection import get_session
                db = next(get_session())
                try:
                    # Convert string UUID to UUID object for database query
                    response_approval_uuid = UUID(analysis_result["response_approval_id"])
                    db.query(ResponseApprovalDB).filter(
                        ResponseApprovalDB.id == response_approval_uuid
                    ).update({
                        "approval_request_id": approval_id
                    })
                    db.commit()
                finally:
                    db.close()

            approval = await self.hitl_service.wait_for_approval(approval_id, timeout_minutes=15)
            return approval.approved

        except ApprovalTimeoutError:
            logger.warning("Response approval request timed out",
                          agent_type=self.agent_type.value,
                          task_id=str(task.task_id))
            return False

    async def _request_next_step_approval(self, task: Task, result: Dict[str, Any]) -> bool:
        """Request approval before proceeding to next workflow step."""
        try:
            approval_id = await self.hitl_service.create_approval_request(
                project_id=task.project_id,
                task_id=task.task_id,
                agent_type=self.agent_type.value,
                request_type="NEXT_STEP",
                request_data={
                    "current_output": result.get('output', ''),
                    "proposed_next_action": result.get('next_action', ''),
                    "workflow_status": result.get('workflow_status', ''),
                    "completion_percentage": result.get('completion_percentage', 0)
                }
            )

            approval = await self.hitl_service.wait_for_approval(approval_id, timeout_minutes=10)
            return approval.approved

        except ApprovalTimeoutError:
            logger.warning("Next step approval request timed out",
                          agent_type=self.agent_type.value,
                          task_id=str(task.task_id))
            return False

    async def _execute_with_hitl_monitoring(self, task: Task, context: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute task with HITL monitoring and emergency stop checks."""
        # This is a placeholder - subclasses should override this or use execute_task
        return await self.execute_task(task, context)

    def _has_next_step(self, result: Dict[str, Any]) -> bool:
        """Check if the result indicates a next step is needed."""
        return result.get('has_next_step', False) or result.get('next_action', '') != ''

    def _create_termination_result(self, reason: str) -> Dict[str, Any]:
        """Create a termination result when workflow is stopped."""
        return {
            "status": "terminated",
            "output": f"Workflow terminated: {reason}",
            "artifacts": [],
            "confidence": 0.0,
            "tokens_used": 0,
            "termination_reason": reason,
            "agent_type": self.agent_type.value
        }

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
                "usage_tracker": self.usage_tracker is not None,
                "hitl_service": self.hitl_service is not None
            }
        }
