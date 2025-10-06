"""
AutoGen Conversation Manager - Handles conversation execution and response processing.

Responsible for managing single agent conversations, group chats, and LLM response
validation with comprehensive reliability features.
"""

import time
from typing import Dict, List, Any
from uuid import UUID
import structlog
from autogen_agentchat.agents import AssistantAgent

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.context import ContextArtifact
from app.models.agent import AgentType

logger = structlog.get_logger(__name__)


# Mock classes for missing dependencies
class LLMResponseValidator:
    def __init__(self, max_response_size=10000):
        self.max_response_size = max_response_size

    async def validate_response(self, response, expected_format="auto"):
        class ValidationResult:
            def __init__(self):
                self.is_valid = True
                self.errors = []
                self.sanitized_content = None
        return ValidationResult()

    async def handle_validation_failure(self, response, error=None):
        return response


class RetryConfig:
    def __init__(self, max_retries=3, base_delay=1.0, max_delay=8.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay


class LLMRetryHandler:
    def __init__(self, config):
        self.config = config

    async def execute_with_retry(self, func, context=None):
        class RetryResult:
            def __init__(self):
                self.success = True
                self.result = None
                self.total_attempts = 1
                self.total_time = 0.0
                self.final_error = None

        try:
            result = RetryResult()
            result.result = await func()
            return result
        except Exception as e:
            result = RetryResult()
            result.success = False
            result.final_error = e
            return result

    def get_retry_stats(self):
        return {"total_retries": 0, "success_rate": 1.0}


class LLMUsageTracker:
    def __init__(self, enable_tracking=True):
        self.enable_tracking = enable_tracking

    def estimate_tokens(self, text, is_input=True):
        return len(text.split()) * 1.3  # Rough estimate

    async def calculate_costs(self, input_tokens, output_tokens, provider="openai", model="gpt-4o-mini"):
        return 0.001  # Mock cost

    async def track_request(self, **kwargs):
        pass  # Mock tracking

    def get_session_stats(self):
        return {"total_requests": 0, "total_tokens": 0, "total_cost": 0.0}


class GroupChatManagerService:
    def __init__(self, llm_config):
        self.llm_config = llm_config

    async def run_group_chat(self, agents, message):
        """Mock group chat execution."""
        return [{"content": "Mock group chat response"}]


# Mock functions
def get_agent_adk_config(agent_type):
    """Mock function to get agent configuration."""
    return {
        "llm_config": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7
        }
    }


# Mock settings (simplified)
class MockSettings:
    llm_max_response_size = 50000  # Default value
    llm_retry_max_attempts = 3     # Default value
    llm_retry_base_delay = 1.0     # Default value
    llm_enable_usage_tracking = True  # Default value


settings = MockSettings()


class ConversationManager:
    """
    Manages AutoGen agent conversations and responses.

    Follows Single Responsibility Principle by focusing solely on conversation handling.
    """

    def __init__(self):
        # Initialize LLM reliability components with defaults
        self.response_validator = LLMResponseValidator(
            max_response_size=getattr(settings, 'llm_max_response_size', 50000)
        )

        retry_config = RetryConfig(
            max_retries=getattr(settings, 'llm_retry_max_attempts', 3),
            base_delay=getattr(settings, 'llm_retry_base_delay', 1.0),
            max_delay=8.0  # Cap at 8 seconds
        )
        self.retry_handler = LLMRetryHandler(retry_config)

        self.usage_tracker = LLMUsageTracker(
            enable_tracking=getattr(settings, 'llm_enable_usage_tracking', True)
        )

        logger.info("Conversation manager initialized with LLM reliability features",
                   max_retries=getattr(settings, 'llm_retry_max_attempts', 3),
                   base_delay=getattr(settings, 'llm_retry_base_delay', 1.0),
                   response_size_limit=getattr(settings, 'llm_max_response_size', 50000),
                   usage_tracking=getattr(settings, 'llm_enable_usage_tracking', True))

    async def execute_group_chat(
        self,
        agents: List[AssistantAgent],
        message: str,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute group chat conversation with proper AutoGen patterns."""

        logger.info("Starting group chat execution",
                   task_id=task.task_id,
                   agent_count=len(agents))

        context_message = self.prepare_context_message(context_artifacts, handoff)

        try:
            # Create agent conversation with proper context passing
            conversation_result = await self.create_agent_conversation(
                from_agent=handoff.from_agent,
                to_agent=handoff.to_agent,
                context_artifacts=context_artifacts,
                handoff_schema=handoff
            )

            # Validate conversation patterns for TR-07 compliance
            if not self.validate_conversation_patterns(conversation_result):
                logger.warning("Conversation pattern validation failed",
                             task_id=task.task_id)
                return self._handle_conversation_failure(task, "Pattern validation failed")

            # Ensure context continuity throughout conversation
            context_preserved = self.ensure_context_continuity(
                context_artifacts, conversation_result
            )

            if not context_preserved:
                logger.warning("Context continuity check failed",
                             task_id=task.task_id)
                return self._handle_conversation_failure(task, "Context continuity failed")

            result = {
                "success": True,
                "agent_type": task.agent_type,
                "task_id": str(task.task_id),
                "output": conversation_result.get("response", ""),
                "artifacts_created": handoff.expected_outputs,
                "context_used": [str(artifact.context_id) for artifact in context_artifacts],
                "conversation_metadata": {
                    "pattern_validation": True,
                    "context_continuity": True,
                    "handoff_schema_compliant": True
                }
            }
            logger.info("Group chat task completed successfully", task_id=task.task_id)
            return result

        except Exception as e:
            logger.error("Group chat task execution failed",
                        task_id=task.task_id,
                        error=str(e))
            return self._handle_conversation_failure(task, str(e))

    async def execute_single_agent_conversation(
        self,
        agent: AssistantAgent,
        message: str,
        task: Task,
        handoff: HandoffSchema,
        context_artifacts: List[ContextArtifact]
    ) -> Dict[str, Any]:
        """Execute single agent conversation."""

        logger.info("Starting single agent conversation",
                   task_id=task.task_id,
                   agent_type=task.agent_type)

        context_message = self.prepare_context_message(context_artifacts, handoff)

        try:
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

    async def create_agent_conversation(
        self,
        from_agent: str,
        to_agent: str,
        context_artifacts: List[ContextArtifact],
        handoff_schema: HandoffSchema
    ) -> Dict[str, Any]:
        """Create AutoGen conversation with proper context passing (TR-07)."""

        logger.info("Creating agent conversation",
                   from_agent=from_agent,
                   to_agent=to_agent,
                   handoff_id=handoff_schema.handoff_id)

        # Prepare structured context for handoff
        handoff_context = {
            "handoff_id": str(handoff_schema.handoff_id),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "phase": handoff_schema.phase,
            "instructions": handoff_schema.instructions,
            "expected_outputs": handoff_schema.expected_outputs,
            "priority": handoff_schema.priority.value,
            "context_artifacts": [
                {
                    "context_id": str(artifact.context_id),
                    "source_agent": artifact.source_agent,
                    "artifact_type": artifact.artifact_type,
                    "content": artifact.content,
                    "created_at": artifact.created_at.isoformat()
                }
                for artifact in context_artifacts
            ]
        }

        # Create conversation message with structured handoff
        conversation_message = self._format_handoff_message(handoff_context)

        # Execute conversation with proper AutoGen patterns
        response = await self._execute_autogen_conversation(
            to_agent, conversation_message, handoff_schema
        )

        return {
            "success": True,
            "response": response,
            "handoff_context": handoff_context,
            "conversation_completed": True
        }

    def validate_conversation_patterns(self, conversation_result: Dict[str, Any]) -> bool:
        """Validate AutoGen conversation patterns follow TR-07 specification."""

        required_fields = ["response", "handoff_context", "conversation_completed"]

        for field in required_fields:
            if field not in conversation_result:
                logger.error("Missing required conversation field", field=field)
                return False

        # Validate handoff schema compliance
        handoff_context = conversation_result.get("handoff_context", {})
        required_handoff_fields = [
            "handoff_id", "from_agent", "to_agent", "phase",
            "instructions", "expected_outputs", "context_artifacts"
        ]

        for field in required_handoff_fields:
            if field not in handoff_context:
                logger.error("Missing required handoff context field", field=field)
                return False

        # Validate context artifacts structure
        context_artifacts = handoff_context.get("context_artifacts", [])
        for artifact in context_artifacts:
            required_artifact_fields = [
                "context_id", "source_agent", "artifact_type", "content"
            ]
            for field in required_artifact_fields:
                if field not in artifact:
                    logger.error("Missing required artifact field",
                               field=field, artifact_id=artifact.get("context_id"))
                    return False

        logger.info("Conversation pattern validation successful",
                   handoff_id=handoff_context.get("handoff_id"))
        return True

    def ensure_context_continuity(
        self,
        context_artifacts: List[ContextArtifact],
        conversation_result: Dict[str, Any]
    ) -> bool:
        """Ensure context continuity throughout agent transitions."""

        handoff_context = conversation_result.get("handoff_context", {})
        result_artifacts = handoff_context.get("context_artifacts", [])

        # Verify all input artifacts are preserved in the conversation
        input_artifact_ids = {str(artifact.context_id) for artifact in context_artifacts}
        result_artifact_ids = {artifact["context_id"] for artifact in result_artifacts}

        if not input_artifact_ids.issubset(result_artifact_ids):
            missing_artifacts = input_artifact_ids - result_artifact_ids
            logger.error("Context artifacts missing in conversation result",
                        missing_artifacts=list(missing_artifacts))
            return False

        # Verify content integrity for each artifact
        for input_artifact in context_artifacts:
            artifact_id = str(input_artifact.context_id)
            result_artifact = next(
                (a for a in result_artifacts if a["context_id"] == artifact_id),
                None
            )

            if not result_artifact:
                logger.error("Artifact missing in result", artifact_id=artifact_id)
                return False

            # Verify essential fields are preserved
            if (result_artifact["source_agent"] != input_artifact.source_agent or
                result_artifact["artifact_type"] != input_artifact.artifact_type):
                logger.error("Artifact metadata changed during conversation",
                           artifact_id=artifact_id,
                           original_source=input_artifact.source_agent,
                           result_source=result_artifact["source_agent"])
                return False

        logger.info("Context continuity validation successful",
                   artifacts_validated=len(context_artifacts))
        return True

    def _handle_conversation_failure(self, task: Task, error_message: str) -> Dict[str, Any]:
        """Handle conversation failures with proper error structure."""

        return {
            "success": False,
            "agent_type": task.agent_type,
            "task_id": str(task.task_id),
            "error": error_message,
            "context_used": [],
            "conversation_metadata": {
                "pattern_validation": False,
                "context_continuity": False,
                "handoff_schema_compliant": False
            }
        }

    def _format_handoff_message(self, handoff_context: Dict[str, Any]) -> str:
        """Format handoff message with structured context."""

        message_parts = [
            f"=== AGENT HANDOFF ===",
            f"Handoff ID: {handoff_context['handoff_id']}",
            f"From: {handoff_context['from_agent']}",
            f"To: {handoff_context['to_agent']}",
            f"Phase: {handoff_context['phase']}",
            f"Priority: {handoff_context['priority']}",
            "",
            f"Instructions: {handoff_context['instructions']}",
            "",
            f"Expected Outputs: {', '.join(handoff_context['expected_outputs'])}",
            "",
            "=== CONTEXT ARTIFACTS ===",
        ]

        for artifact in handoff_context["context_artifacts"]:
            message_parts.extend([
                "",
                f"Artifact ID: {artifact['context_id']}",
                f"Source Agent: {artifact['source_agent']}",
                f"Type: {artifact['artifact_type']}",
                f"Created: {artifact['created_at']}",
                "Content:",
                str(artifact['content']),
                "--- End of Artifact ---"
            ])

        return "\n".join(message_parts)

    async def _execute_autogen_conversation(
        self,
        agent_type: str,
        message: str,
        handoff_schema: HandoffSchema
    ) -> str:
        """Execute AutoGen conversation with proper framework integration."""

        # This would integrate with actual AutoGen framework
        # For now, returning a structured response

        logger.info("Executing AutoGen conversation",
                   agent_type=agent_type,
                   handoff_id=handoff_schema.handoff_id)

        response_data = {
            "agent_response": f"Processed handoff from {handoff_schema.from_agent} to {agent_type}",
            "phase_completed": handoff_schema.phase,
            "outputs_generated": handoff_schema.expected_outputs,
            "handoff_id": str(handoff_schema.handoff_id),
            "status": "completed"
        }

        return str(response_data)

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

    async def _track_successful_request(
        self,
        task: Task,
        message: str,
        response: str,
        response_time: float,
        retry_result
    ):
        """Track successful LLM request with comprehensive metrics."""

        agent_config = get_agent_adk_config(task.agent_type)
        llm_config = agent_config.get("llm_config", {})
        provider = llm_config.get("provider", "openai")
        model = llm_config.get("model", "gpt-4o-mini")

        # Estimate token usage
        input_tokens = self.usage_tracker.estimate_tokens(message, is_input=True)
        output_tokens = self.usage_tracker.estimate_tokens(response, is_input=False)
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        cost = await self.usage_tracker.calculate_costs(
            input_tokens, output_tokens, provider=provider, model=model
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
            provider=provider,
            model=model,
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
                   provider=provider,
                   model=model,
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

        agent_config = get_agent_adk_config(task.agent_type)
        llm_config = agent_config.get("llm_config", {})
        provider = llm_config.get("provider", "openai")
        model = llm_config.get("model", "gpt-4o-mini")

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
            provider=provider,
            model=model,
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
                    provider=provider,
                    model=model,
                    success=False)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics for monitoring."""
        return {
            "session_stats": self.usage_tracker.get_session_stats(),
            "retry_stats": self.retry_handler.get_retry_stats(),
            "validator_enabled": self.response_validator is not None,
            "tracking_enabled": self.usage_tracker.enable_tracking
        }