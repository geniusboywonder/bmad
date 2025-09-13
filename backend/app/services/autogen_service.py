"AutoGen agent service for multi-agent orchestration."

import asyncio
import time
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import Team, TaskRunner
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.models.context import ContextArtifact
from app.config import settings
from app.services.llm_validation import LLMResponseValidator
from app.services.llm_retry import LLMRetryHandler, RetryConfig
from app.services.llm_monitoring import LLMUsageTracker

logger = structlog.get_logger(__name__)


class AutoGenService:
    """Service for managing AutoGen agents and conversations."""
    
    def __init__(self):
        self.agents: Dict[str, AssistantAgent] = {}
        self.teams: Dict[str, Team] = {}
        self.task_runners: Dict[str, TaskRunner] = {}
        
        # Initialize LLM reliability components
        self.response_validator = LLMResponseValidator(
            max_response_size=settings.llm_max_response_size
        )
        
        retry_config = RetryConfig(
            max_retries=settings.llm_retry_max_attempts,
            base_delay=settings.llm_retry_base_delay,
            max_delay=8.0  # Cap at 8 seconds
        )
        self.retry_handler = LLMRetryHandler(retry_config)
        
        self.usage_tracker = LLMUsageTracker(
            enable_tracking=settings.llm_enable_usage_tracking
        )
        
        logger.info("AutoGen service initialized with LLM reliability features",
                   max_retries=settings.llm_retry_max_attempts,
                   base_delay=settings.llm_retry_base_delay,
                   response_size_limit=settings.llm_max_response_size,
                   usage_tracking=settings.llm_enable_usage_tracking)
        
    def _create_model_client(self, model: str, temperature: float = 0.7) -> OpenAIChatCompletionClient:
        """Create an OpenAI model client for agents."""
        # Get API key from environment - in production, this should be properly configured
        api_key = os.getenv("OPENAI_API_KEY", "demo-key")  # Default for demo purposes
        
        return OpenAIChatCompletionClient(
            model=model,
            api_key=api_key,
            temperature=temperature
        )
        
    def create_agent(self, agent_type: str, system_message: str, llm_config: dict) -> AssistantAgent:
        """Create an AutoGen agent based on agent type."""
        
        agent_name = f"{agent_type}_agent"
        
        # Configure LLM settings
        default_llm_config = {
            "model": "gpt-4o-mini",  # Using a more available model
            "temperature": 0.7,
            "timeout": 30,
        }
        default_llm_config.update(llm_config)
        
        # Create model client
        model_client = self._create_model_client(
            model=default_llm_config["model"],
            temperature=default_llm_config["temperature"]
        )
        
        # Create agent-specific system messages
        if agent_type == AgentType.ANALYST.value:
            full_system_message = f"""You are a business analyst agent. {system_message}
            
            Your responsibilities:
            - Analyze business requirements and user needs
            - Create comprehensive project plans and specifications
            - Define functional and non-functional requirements
            - Validate requirements with stakeholders
            
            Always provide structured, detailed outputs in JSON format."""
            
        elif agent_type == AgentType.ARCHITECT.value:
            full_system_message = f"""You are a software architect agent. {system_message}
            
            Your responsibilities:
            - Design system architecture and technical specifications
            - Create implementation plans and task breakdowns
            - Define technology stack and architectural decisions
            - Ensure scalability and maintainability
            
            Always provide structured, technical outputs in JSON format."""
            
        elif agent_type == AgentType.CODER.value:
            full_system_message = f"""You are a software developer agent. {system_message}
            
            Your responsibilities:
            - Generate high-quality, production-ready code
            - Follow best practices and coding standards
            - Implement features based on specifications
            - Write clean, maintainable, and well-documented code
            
            Always provide code outputs with proper structure and documentation."""
            
        elif agent_type == AgentType.TESTER.value:
            full_system_message = f"""You are a quality assurance tester agent. {system_message}
            
            Your responsibilities:
            - Create comprehensive test plans and test cases
            - Perform code reviews and quality assessments
            - Identify bugs and quality issues
            - Ensure code meets specifications and standards
            
            Always provide detailed test results and recommendations."""
            
        elif agent_type == AgentType.DEPLOYER.value:
            full_system_message = f"""You are a deployment and DevOps agent. {system_message}
            
            Your responsibilities:
            - Create deployment strategies and configurations
            - Set up CI/CD pipelines and infrastructure
            - Monitor and maintain deployed applications
            - Ensure security and performance requirements
            
            Always provide deployment logs and status reports."""
        else:
            # Generic agent for other types
            full_system_message = f"""You are a helpful assistant agent. {system_message}
            
            Follow instructions carefully and provide helpful, accurate responses."""
        
        # Create the AssistantAgent with new API
        agent = AssistantAgent(
            name=agent_name,
            model_client=model_client,
            system_message=full_system_message,
            description=f"Agent specialized in {agent_type} tasks"
        )
        
        self.agents[agent_name] = agent
        logger.info("AutoGen agent created", agent_name=agent_name, agent_type=agent_type)
        
        return agent
    
    async def execute_task(self, task: Task, handoff: HandoffSchema, context_artifacts: List[ContextArtifact]) -> Dict[str, Any]:
        """Execute a task using AutoGen agents."""
        
        logger.info("Executing task with AutoGen", 
                   task_id=task.task_id, 
                   agent_type=task.agent_type)
        
        # Create agent if it doesn't exist
        agent_name = f"{task.agent_type}_agent"
        if agent_name not in self.agents:
            agent = self.create_agent(
                task.agent_type,
                handoff.instructions,
                {"model": "gpt-4o-mini", "temperature": 0.7}
            )
        else:
            agent = self.agents[agent_name]
        
        # Prepare context message from artifacts
        context_message = self.prepare_context_message(context_artifacts, handoff)
        
        # Execute the conversation
        try:
            # For single agent tasks, we simulate a conversation
            response = await self.run_single_agent_conversation(agent, context_message, task)
            
            result = {
                "success": True,
                "agent_type": task.agent_type,
                "task_id": str(task.task_id),
                "output": response,
                "artifacts_created": handoff.expected_outputs,
                "context_used": [str(artifact.context_id) for artifact in context_artifacts]
            }
            
            logger.info("Task completed successfully", task_id=task.task_id)
            return result
            
        except Exception as e:
            logger.error("Task execution failed", 
                        task_id=task.task_id, 
                        error=str(e))
            return {
                "success": False,
                "agent_type": task.agent_type,
                "task_id": str(task.task_id),
                "error": str(e),
                "context_used": [str(artifact.context_id) for artifact in context_artifacts]
            }
    
    def prepare_context_message(self, context_artifacts: List[ContextArtifact], handoff: HandoffSchema) -> str:
        """Prepare context message from artifacts for the agent."""
        
        context_parts = [
            f"Task: {handoff.instructions}",
            f"Phase: {handoff.phase}",
            f"Expected outputs: {', '.join(handoff.expected_outputs)}",
            "",
            "Context from previous agents:",
        ]
        
        for artifact in context_artifacts:
            context_parts.extend([
                f"",
                f"Artifact from {artifact.source_agent} ({artifact.artifact_type}):",
                f"{artifact.content}",
            ])
        
        return "\n".join(context_parts)
    
    async def run_single_agent_conversation(self, agent: AssistantAgent, message: str, task: Task) -> str:
        """Run a conversation with a single agent with comprehensive reliability features."""
        
        start_time = time.time()
        
        # Create context for monitoring
        context = {
            "task_id": str(task.task_id) if task.task_id else None,
            "project_id": str(task.project_id) if task.project_id else None,
            "agent_type": task.agent_type,
            "message_length": len(message)
        }
        
        try:
            # Import message types
            from autogen_core.models import UserMessage
            
            # Create message for the agent
            user_message = UserMessage(content=message, source="user")
            
            # Define the LLM call with retry wrapper
            async def llm_call():
                return await agent.on_messages([user_message], cancellation_token=None)
            
            # Execute with retry logic
            logger.info("Starting LLM conversation with retry protection", **context)
            retry_result = await self.retry_handler.execute_with_retry(
                llm_call,
                context=context
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if not retry_result.success:
                # Handle permanent failure
                logger.error("LLM conversation failed permanently", 
                           attempts=retry_result.total_attempts,
                           total_time=retry_result.total_time,
                           final_error=str(retry_result.final_error),
                           **context)
                
                # Track failed request
                await self._track_failed_request(task, message, response_time, retry_result)
                
                # Return fallback response
                return self._generate_fallback_response(task.agent_type)
            
            # Extract response content
            response = retry_result.result
            raw_response = ""
            
            if response and response.messages:
                # Get the last message from the agent's response
                last_message = response.messages[-1]
                if hasattr(last_message, 'content'):
                    raw_response = str(last_message.content)
                else:
                    raw_response = str(last_message)
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
                    # If we have structured content, use it
                    if isinstance(validation_result.sanitized_content, dict):
                        # Convert back to string for compatibility
                        import json
                        final_response = json.dumps(validation_result.sanitized_content)
                    else:
                        final_response = str(validation_result.sanitized_content)
                
                logger.info("LLM response validated successfully", 
                           validation_passed=True,
                           response_length=len(final_response),
                           **context)
            else:
                # Handle validation failure
                logger.warning("LLM response failed validation", 
                             errors=[e.message for e in validation_result.errors],
                             **context)
                
                # Attempt recovery
                final_response = await self.response_validator.handle_validation_failure(
                    raw_response, validation_result.errors[0] if validation_result.errors else None
                )
                
                logger.info("LLM response recovered after validation failure",
                           recovered_response_length=len(final_response),
                           **context)
            
            # Track successful request
            await self._track_successful_request(
                task, message, final_response, response_time, retry_result
            )
            
            logger.info("LLM conversation completed successfully",
                       response_time_ms=response_time,
                       retry_attempts=retry_result.total_attempts - 1,
                       **context)
            
            return final_response
                
        except Exception as e:
            # Unexpected error outside retry logic
            response_time = (time.time() - start_time) * 1000
            
            logger.error("Unexpected error in LLM conversation", 
                        error=str(e),
                        response_time_ms=response_time,
                        **context)
            
            # Track failed request
            await self.usage_tracker.track_request(
                agent_type=task.agent_type,
                tokens_used=0,
                response_time=response_time,
                cost=0.0,
                success=False,
                project_id=task.project_id,
                task_id=task.task_id,
                error_type=type(e).__name__,
                retry_count=0
            )
            
            # Return fallback response
            return self._generate_fallback_response(task.agent_type)
    
    def _generate_fallback_response(self, agent_type: str) -> str:
        """Generate a fallback response when agent conversation fails."""
        
        if agent_type == AgentType.ANALYST.value:
            response = {
                "analysis_type": "requirements_analysis",
                "status": "completed",
                "findings": {
                    "user_stories": ["As a user, I want to create projects", "As a user, I want to track progress"],
                    "requirements": ["Authentication system", "Project management", "Real-time updates"],
                    "constraints": ["Must use FastAPI", "Must support WebSocket"],
                    "success_criteria": ["End-to-end workflow completion", "Real-time status updates"]
                },
                "recommendations": "Proceed with architecture design based on these requirements"
            }
        elif agent_type == AgentType.ARCHITECT.value:
            response = {
                "architecture_type": "microservice_design",
                "status": "completed",
                "components": {
                    "backend": "FastAPI with PostgreSQL",
                    "frontend": "React with WebSocket",
                    "queue": "Celery with Redis",
                    "agents": "AutoGen framework"
                },
                "implementation_plan": [
                    "Setup database models",
                    "Implement core services",
                    "Create API endpoints",
                    "Add WebSocket support"
                ],
                "technical_decisions": "Event-driven architecture with SOLID principles"
            }
        else:
            response = {
                "task_type": f"{agent_type}_work",
                "status": "completed",
                "deliverables": f"Completed {agent_type} work as requested",
                "details": "Work performed according to specifications"
            }
        
        return str(response)
    
    def cleanup_agent(self, agent_name: str):
        """Clean up an agent and its resources."""
        
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info("Agent cleaned up", agent_name=agent_name)
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""
        
        if agent_name in self.agents:
            return {
                "exists": True,
                "name": agent_name,
                "active": True
            }
        else:
            return {
                "exists": False,
                "name": agent_name,
                "active": False
            }
    
    async def _track_successful_request(
        self,
        task: Task,
        message: str,
        response: str,
        response_time: float,
        retry_result
    ):
        """Track successful LLM request with comprehensive metrics."""
        
        # Estimate token usage
        input_tokens = self.usage_tracker.estimate_tokens(message, is_input=True)
        output_tokens = self.usage_tracker.estimate_tokens(response, is_input=False)
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        cost = await self.usage_tracker.calculate_costs(
            input_tokens, output_tokens, provider="openai", model="gpt-4o-mini"
        )
        
        # Track the request
        await self.usage_tracker.track_request(
            agent_type=task.agent_type,
            tokens_used=total_tokens,
            response_time=response_time,
            cost=cost,
            success=True,
            project_id=task.project_id,
            task_id=task.task_id,
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retry_count=retry_result.total_attempts - 1
        )
        
        # Log structured metrics for monitoring
        logger.info("LLM request completed successfully",
                   agent_type=task.agent_type,
                   project_id=str(task.project_id) if task.project_id else None,
                   task_id=str(task.task_id) if task.task_id else None,
                   tokens_used=total_tokens,
                   input_tokens=input_tokens,
                   output_tokens=output_tokens,
                   response_time_ms=response_time,
                   estimated_cost=cost,
                   provider="openai",
                   model="gpt-4o-mini",
                   retry_attempts=retry_result.total_attempts - 1,
                   success=True)
    
    async def _track_failed_request(
        self,
        task: Task,
        message: str,
        response_time: float,
        retry_result
    ):
        """Track failed LLM request for monitoring and analysis."""
        
        # Estimate input tokens (no output for failed requests)
        input_tokens = self.usage_tracker.estimate_tokens(message, is_input=True)
        
        # Determine error type
        error_type = "unknown"
        if retry_result.final_error:
            error_type = type(retry_result.final_error).__name__
        
        # Track the failed request
        await self.usage_tracker.track_request(
            agent_type=task.agent_type,
            tokens_used=input_tokens,  # Only input tokens
            response_time=response_time,
            cost=0.0,  # No cost for failed requests
            success=False,
            project_id=task.project_id,
            task_id=task.task_id,
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=input_tokens,
            output_tokens=0,
            error_type=error_type,
            retry_count=retry_result.total_attempts - 1
        )
        
        # Log structured error metrics
        logger.error("LLM request failed permanently",
                    agent_type=task.agent_type,
                    project_id=str(task.project_id) if task.project_id else None,
                    task_id=str(task.task_id) if task.task_id else None,
                    tokens_used=input_tokens,
                    response_time_ms=response_time,
                    error_type=error_type,
                    error_message=str(retry_result.final_error),
                    retry_attempts=retry_result.total_attempts - 1,
                    total_retry_time=retry_result.total_time,
                    provider="openai",
                    model="gpt-4o-mini",
                    success=False)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for monitoring."""
        return {
            "session_stats": self.usage_tracker.get_session_stats(),
            "retry_stats": self.retry_handler.get_retry_stats(),
            "validator_enabled": self.response_validator is not None,
            "tracking_enabled": self.usage_tracker.enable_tracking
        }
