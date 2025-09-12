"""AutoGen agent service for multi-agent orchestration."""

import asyncio
from typing import Dict, List, Any, Optional
from uuid import UUID
import structlog
import autogen_agentchat as autogen

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.models.context import ContextArtifact

logger = structlog.get_logger(__name__)


class AutoGenService:
    """Service for managing AutoGen agents and conversations."""
    
    def __init__(self):
        self.agents: Dict[str, autogen.ConversableAgent] = {}
        self.group_chats: Dict[str, autogen.GroupChat] = {}
        self.managers: Dict[str, autogen.GroupChatManager] = {}
        
    def create_agent(self, agent_type: str, system_message: str, llm_config: dict) -> autogen.ConversableAgent:
        """Create an AutoGen agent based on agent type."""
        
        agent_name = f"{agent_type}_agent"
        
        # Configure LLM settings
        default_llm_config = {
            "model": "gpt-4o-mini",  # Using a more available model
            "temperature": 0.7,
            "timeout": 30,
        }
        default_llm_config.update(llm_config)
        
        # Create the agent
        if agent_type == AgentType.ANALYST.value:
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=f"""You are a business analyst agent. {system_message}
                
                Your responsibilities:
                - Analyze business requirements and user needs
                - Create comprehensive project plans and specifications
                - Define functional and non-functional requirements
                - Validate requirements with stakeholders
                
                Always provide structured, detailed outputs in JSON format.""",
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
            )
        elif agent_type == AgentType.ARCHITECT.value:
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=f"""You are a software architect agent. {system_message}
                
                Your responsibilities:
                - Design system architecture and technical specifications
                - Create implementation plans and task breakdowns
                - Define technology stack and architectural decisions
                - Ensure scalability and maintainability
                
                Always provide structured, technical outputs in JSON format.""",
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
            )
        elif agent_type == AgentType.CODER.value:
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=f"""You are a software developer agent. {system_message}
                
                Your responsibilities:
                - Generate high-quality, production-ready code
                - Follow best practices and coding standards
                - Implement features based on specifications
                - Write clean, maintainable, and well-documented code
                
                Always provide code outputs with proper structure and documentation.""",
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
            )
        elif agent_type == AgentType.TESTER.value:
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=f"""You are a quality assurance tester agent. {system_message}
                
                Your responsibilities:
                - Create comprehensive test plans and test cases
                - Perform code reviews and quality assessments
                - Identify bugs and quality issues
                - Ensure code meets specifications and standards
                
                Always provide detailed test results and recommendations.""",
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
            )
        elif agent_type == AgentType.DEPLOYER.value:
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=f"""You are a deployment and DevOps agent. {system_message}
                
                Your responsibilities:
                - Create deployment strategies and configurations
                - Set up CI/CD pipelines and infrastructure
                - Monitor and maintain deployed applications
                - Ensure security and performance requirements
                
                Always provide deployment logs and status reports.""",
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
            )
        else:
            # Generic agent for other types
            agent = autogen.ConversableAgent(
                name=agent_name,
                system_message=system_message,
                llm_config=default_llm_config,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=3,
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
    
    async def run_single_agent_conversation(self, agent: autogen.ConversableAgent, message: str, task: Task) -> str:
        """Run a conversation with a single agent."""
        
        # For now, we'll simulate the conversation
        # In a full implementation, this would use AutoGen's conversation capabilities
        
        # Simulate different responses based on agent type
        if task.agent_type == AgentType.ANALYST.value:
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
        elif task.agent_type == AgentType.ARCHITECT.value:
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
                "task_type": f"{task.agent_type}_work",
                "status": "completed",
                "deliverables": f"Completed {task.agent_type} work as requested",
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