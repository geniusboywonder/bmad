"""Enhanced agent service integrating factory pattern with existing infrastructure."""

from typing import Dict, Any, List, Optional
from uuid import UUID
import structlog
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.agents.factory import get_agent_factory
from app.agents.base_agent import BaseAgent
from app.services.context_store import ContextStoreService
from app.services.agent_status_service import AgentStatusService

logger = structlog.get_logger(__name__)


class AgentService:
    """Enhanced agent service with factory pattern integration and workflow management.
    
    This service provides a high-level interface for agent management, integrating
    the agent factory pattern with existing infrastructure services including:
    - Agent lifecycle management and status tracking
    - Context artifact management and handoff execution
    - Task execution coordination with AutoGen integration
    - Error handling and recovery with comprehensive logging
    """
    
    def __init__(self, db: Session):
        """Initialize agent service with factory and infrastructure dependencies."""
        self.db = db
        self.agent_factory = get_agent_factory()
        self.context_store = ContextStoreService(db)
        self.agent_status_service = AgentStatusService()

        # Register all agent classes with the factory
        self._register_all_agents()

        logger.info("Agent service initialized with factory pattern integration")
    
    def _register_all_agents(self) -> None:
        """Register all agent classes with the agent factory."""
        
        try:
            # Import all agent classes
            from app.agents.orchestrator import OrchestratorAgent
            from app.agents.analyst import AnalystAgent
            from app.agents.architect import ArchitectAgent
            from app.agents.coder import CoderAgent
            from app.agents.tester import TesterAgent
            from app.agents.deployer import DeployerAgent
            
            # Register each agent type with the factory
            self.agent_factory.register_agent(AgentType.ORCHESTRATOR, OrchestratorAgent)
            self.agent_factory.register_agent(AgentType.ANALYST, AnalystAgent)
            self.agent_factory.register_agent(AgentType.ARCHITECT, ArchitectAgent)
            self.agent_factory.register_agent(AgentType.CODER, CoderAgent)
            self.agent_factory.register_agent(AgentType.TESTER, TesterAgent)
            self.agent_factory.register_agent(AgentType.DEPLOYER, DeployerAgent)
            
            logger.info("All agent classes registered with factory",
                       registered_types=[t.value for t in self.agent_factory.get_registered_types()])
            
        except Exception as e:
            logger.error("Failed to register agent classes with factory", error=str(e))
            raise
    
    async def execute_task_with_agent(self, task: Task, handoff: Optional[HandoffSchema] = None) -> Dict[str, Any]:
        """Execute a task using the appropriate agent with comprehensive workflow management.
        
        Args:
            task: Task to execute with agent specifications
            handoff: Optional handoff schema with context and instructions
            
        Returns:
            Task execution result with status, output, and created artifacts
        """
        logger.info("Executing task with agent",
                   task_id=task.task_id,
                   agent_type=task.agent_type,
                   project_id=task.project_id)
        
        try:
            # Validate agent type
            agent_type = AgentType(task.agent_type)
            
            # Update agent status to working
            await self.agent_status_service.set_agent_working(
                agent_type, task.task_id, task.project_id
            )
            
            # Get or create agent instance
            agent = await self._get_agent_instance(agent_type, task)
            
            # Retrieve context artifacts
            context_artifacts = await self._get_task_context(task, handoff)
            
            # Execute task with the agent
            execution_result = await agent.execute_task(task, context_artifacts)
            
            # Process execution results
            processed_result = await self._process_execution_result(
                task, execution_result, context_artifacts
            )
            
            # Update agent status based on result
            if processed_result.get("success", False):
                await self.agent_status_service.set_agent_idle(agent_type, task.project_id)
                logger.info("Task execution completed successfully",
                           task_id=task.task_id,
                           agent_type=agent_type.value)
            else:
                error_msg = processed_result.get("error", "Unknown execution error")
                await self.agent_status_service.set_agent_error(
                    agent_type, error_msg, task.task_id, task.project_id
                )
                logger.error("Task execution failed",
                            task_id=task.task_id,
                            agent_type=agent_type.value,
                            error=error_msg)
            
            return processed_result
            
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Agent service execution error: {str(e)}"
            
            try:
                agent_type = AgentType(task.agent_type)
                await self.agent_status_service.set_agent_error(
                    agent_type, error_msg, task.task_id, task.project_id
                )
            except:
                # Fallback if agent type is invalid
                pass
            
            logger.error("Agent service task execution failed",
                        task_id=task.task_id,
                        agent_type=task.agent_type,
                        error=str(e))
            
            return {
                "success": False,
                "agent_type": task.agent_type,
                "task_id": str(task.task_id),
                "error": error_msg,
                "context_used": []
            }
    
    async def create_agent_handoff(self, from_agent_type: AgentType, to_agent_type: AgentType,
                                 task: Task, additional_context: Optional[List[ContextArtifact]] = None) -> HandoffSchema:
        """Create structured handoff between agents with context management.
        
        Args:
            from_agent_type: Source agent type creating the handoff
            to_agent_type: Target agent type receiving the handoff
            task: Current task context for the handoff
            additional_context: Optional additional context artifacts
            
        Returns:
            HandoffSchema with structured handoff information
        """
        logger.info("Creating agent handoff",
                   from_agent=from_agent_type.value,
                   to_agent=to_agent_type.value,
                   task_id=task.task_id)
        
        try:
            # Get source agent instance
            from_agent = await self._get_agent_instance(from_agent_type, task)
            
            # Gather context artifacts
            context_artifacts = additional_context or []
            
            # Add task-related context if available
            task_context = await self._get_task_context(task, None)
            context_artifacts.extend(task_context)
            
            # Create handoff using source agent
            handoff = await from_agent.create_handoff(to_agent_type, task, context_artifacts)
            
            logger.info("Agent handoff created successfully",
                       handoff_id=handoff.handoff_id,
                       from_agent=from_agent_type.value,
                       to_agent=to_agent_type.value)
            
            return handoff
            
        except Exception as e:
            logger.error("Failed to create agent handoff",
                        from_agent=from_agent_type.value,
                        to_agent=to_agent_type.value,
                        task_id=task.task_id,
                        error=str(e))
            raise
    
    async def get_agent_status_summary(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get comprehensive status summary for all agents.
        
        Args:
            project_id: Optional project ID to filter status
            
        Returns:
            Dictionary with agent status information and factory statistics
        """
        try:
            # Get agent status from status service
            agent_statuses = self.agent_status_service.get_all_agent_statuses()
            
            # Get factory information
            factory_status = self.agent_factory.get_factory_status()
            
            # Combine information
            status_summary = {
                "agent_statuses": {
                    agent_type.value: {
                        "status": status.status.value,
                        "current_task_id": str(status.current_task_id) if status.current_task_id else None,
                        "last_activity": status.last_activity.isoformat(),
                        "error_message": status.error_message
                    }
                    for agent_type, status in agent_statuses.items()
                },
                "factory_status": factory_status,
                "active_agents": len([s for s in agent_statuses.values() 
                                    if s.status.value in ["working", "waiting_for_hitl"]]),
                "total_registered_types": factory_status["total_registered"],
                "project_filter": str(project_id) if project_id else None
            }
            
            return status_summary
            
        except Exception as e:
            logger.error("Failed to get agent status summary", error=str(e))
            return {
                "error": str(e),
                "agent_statuses": {},
                "factory_status": {},
                "active_agents": 0,
                "total_registered_types": 0
            }
    
    async def reset_agent_status(self, agent_type: AgentType, project_id: Optional[UUID] = None) -> bool:
        """Reset agent status to idle state.
        
        Args:
            agent_type: Agent type to reset
            project_id: Optional project context
            
        Returns:
            True if reset successful, False otherwise
        """
        try:
            await self.agent_status_service.set_agent_idle(agent_type, project_id)
            
            # Remove agent instance to force recreation
            self.agent_factory.remove_agent(agent_type)
            
            logger.info("Agent status reset successfully",
                       agent_type=agent_type.value,
                       project_id=str(project_id) if project_id else None)
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset agent status",
                        agent_type=agent_type.value,
                        error=str(e))
            return False
    
    async def _get_agent_instance(self, agent_type: AgentType, task: Task) -> BaseAgent:
        """Get or create agent instance with appropriate configuration.
        
        Args:
            agent_type: Type of agent to get/create
            task: Task context for configuration
            
        Returns:
            Agent instance ready for task execution
        """
        # Determine LLM configuration based on agent type and task
        llm_config = self._get_llm_config_for_agent(agent_type, task)
        
        # Get or create agent instance
        agent = self.agent_factory.create_agent(agent_type, llm_config)
        
        return agent
    
    def _get_llm_config_for_agent(self, agent_type: AgentType, task: Task) -> Dict[str, Any]:
        """Get LLM configuration optimized for specific agent type.
        
        Args:
            agent_type: Agent type for configuration
            task: Task context for optimization
            
        Returns:
            LLM configuration dictionary
        """
        # Base configuration
        base_config = {
            "model": "gpt-4o-mini",  # Default available model
            "temperature": 0.7,
            "timeout": 30,
        }
        
        # Agent-specific optimizations
        agent_configs = {
            AgentType.ORCHESTRATOR: {"temperature": 0.3, "model": "gpt-4o-mini"},
            AgentType.ANALYST: {"temperature": 0.4, "model": "gpt-4o-mini"},  # Would prefer Claude
            AgentType.ARCHITECT: {"temperature": 0.2, "model": "gpt-4o-mini"},  # Would prefer GPT-4
            AgentType.CODER: {"temperature": 0.3, "model": "gpt-4o-mini"},
            AgentType.TESTER: {"temperature": 0.3, "model": "gpt-4o-mini"},
            AgentType.DEPLOYER: {"temperature": 0.2, "model": "gpt-4o-mini"},
        }
        
        # Apply agent-specific configuration
        if agent_type in agent_configs:
            base_config.update(agent_configs[agent_type])
        
        return base_config
    
    async def _get_task_context(self, task: Task, handoff: Optional[HandoffSchema]) -> List[ContextArtifact]:
        """Retrieve context artifacts for task execution.
        
        Args:
            task: Task requiring context
            handoff: Optional handoff with context IDs
            
        Returns:
            List of context artifacts for the task
        """
        context_artifacts = []
        
        try:
            # Get context from handoff if provided
            if handoff and handoff.context_ids:
                handoff_artifacts = await self.context_store.get_artifacts_by_ids(handoff.context_ids)
                context_artifacts.extend(handoff_artifacts)
            
            # Get additional context from task if specified
            if hasattr(task, 'context_ids') and task.context_ids:
                task_artifacts = await self.context_store.get_artifacts_by_ids(task.context_ids)
                context_artifacts.extend(task_artifacts)
            
            # Get project-wide context if no specific context provided
            if not context_artifacts and task.project_id:
                project_artifacts = await self.context_store.get_artifacts_by_project(task.project_id)
                # Limit to most recent artifacts to avoid overwhelming context
                context_artifacts = project_artifacts[-10:] if project_artifacts else []
            
            logger.debug("Retrieved task context",
                        task_id=task.task_id,
                        context_count=len(context_artifacts))
            
        except Exception as e:
            logger.warning("Failed to retrieve some task context",
                          task_id=task.task_id,
                          error=str(e))
            # Continue with available context
        
        return context_artifacts
    
    async def _process_execution_result(self, task: Task, execution_result: Dict[str, Any],
                                      context_artifacts: List[ContextArtifact]) -> Dict[str, Any]:
        """Process agent execution result and create context artifacts.
        
        Args:
            task: Executed task
            execution_result: Result from agent execution
            context_artifacts: Context used for execution
            
        Returns:
            Processed execution result with artifact creation
        """
        try:
            # Extract agent output for artifact creation
            agent_output = execution_result.get("output", {})
            
            if agent_output and execution_result.get("success", False):
                # Create context artifact from agent output
                artifact = ContextArtifact(
                    project_id=task.project_id,
                    source_agent=AgentType(task.agent_type),
                    artifact_type="AGENT_OUTPUT",  # Using existing enum value
                    content=agent_output,
                    artifact_metadata={
                        "task_id": str(task.task_id),
                        "agent_type": task.agent_type,
                        "execution_timestamp": execution_result.get("timestamp"),
                        "context_input_count": len(context_artifacts)
                    }
                )
                
                # Store the artifact
                stored_artifact = await self.context_store.create_artifact(artifact)
                
                # Add artifact ID to execution result
                execution_result["created_artifact_id"] = str(stored_artifact.context_id)
                
                logger.info("Created context artifact from agent output",
                           task_id=task.task_id,
                           artifact_id=stored_artifact.context_id,
                           agent_type=task.agent_type)
            
            return execution_result
            
        except Exception as e:
            logger.warning("Failed to process execution result",
                          task_id=task.task_id,
                          error=str(e))
            # Return original result if processing fails
            return execution_result
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status information.
        
        Returns:
            Service status with factory and infrastructure information
        """
        try:
            return {
                "service_initialized": True,
                "factory_status": self.agent_factory.get_factory_status(),
                "context_store_available": self.context_store is not None,
                "agent_status_service_available": self.agent_status_service is not None,
                "registered_agent_types": [t.value for t in self.agent_factory.get_registered_types()],
                "active_agent_instances": len(self.agent_factory.get_active_agents())
            }
        except Exception as e:
            return {
                "service_initialized": False,
                "error": str(e),
                "factory_status": {},
                "registered_agent_types": [],
                "active_agent_instances": 0
            }


