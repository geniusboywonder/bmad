"""ADK Multi-Agent Orchestration Service using Agent Hierarchy."""

from typing import List, Dict, Any, AsyncGenerator, Optional
import structlog
from datetime import datetime

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agents.bmad_adk_wrapper import BMADADKWrapper

logger = structlog.get_logger(__name__)


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates multiple specialized agents."""

    def __init__(self, name: str, specialists: List[LlmAgent], instruction: str = None):
        self.specialists = specialists or []
        self.coordinator_instruction = instruction or "You coordinate tasks between specialist agents."
        super().__init__(name=name, sub_agents=specialists)

    async def _run_async_impl(self, ctx) -> AsyncGenerator:
        """Run the coordination logic - delegating to appropriate specialists."""
        # For now, this is a placeholder implementation
        # In practice, this would implement routing logic to specialists
        yield ctx  # Placeholder - proper implementation would yield events


class ADKOrchestrationService:
    """Multi-agent orchestration using ADK agent hierarchy for collaborative workflows."""

    def __init__(self):
        self.session_service = InMemorySessionService()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.orchestration_count = 0

        logger.info("ADK Orchestration Service initialized")

    def create_multi_agent_workflow(self,
                                   agents: List[BMADADKWrapper],
                                   workflow_type: str,
                                   project_id: str,
                                   workflow_config: Optional[Dict[str, Any]] = None) -> str:
        """Create multi-agent collaborative workflow using ADK agent hierarchy.

        Args:
            agents: List of BMADADKWrapper instances to include in workflow
            workflow_type: Type of workflow (e.g., "requirements_analysis", "system_design")
            project_id: Project identifier for tracking
            workflow_config: Optional configuration for workflow behavior

        Returns:
            Workflow ID for tracking and management
        """
        if not agents:
            raise ValueError("At least one agent required for workflow")

        # Validate agents are initialized
        initialized_agents = [agent for agent in agents if agent.is_initialized]
        if not initialized_agents:
            raise ValueError("No valid ADK agents available for workflow")

        # Generate unique workflow ID
        self.orchestration_count += 1
        workflow_id = f"adk_workflow_{project_id}_{workflow_type}_{self.orchestration_count}"

        # Create agent hierarchy configuration
        config = self._get_workflow_config(workflow_type, workflow_config or {})

        # Store workflow metadata
        workflow_metadata = {
            "workflow_id": workflow_id,
            "agents": [agent.agent_name for agent in initialized_agents],
            "workflow_type": workflow_type,
            "project_id": project_id,
            "config": config,
            "created_at": datetime.now().isoformat(),
            "status": "created"
        }

        self.active_workflows[workflow_id] = workflow_metadata

        logger.info("Multi-agent workflow created",
                   workflow_id=workflow_id,
                   agent_count=len(initialized_agents))

        return workflow_id

    def _get_workflow_config(self, workflow_type: str,
                           custom_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow configuration based on type."""

        # Default configuration
        config = {
            "coordination_strategy": "sequential",
            "max_iterations": 10,
            "allow_agent_delegation": True,
            "timeout_minutes": 30
        }

        # Workflow-specific configurations
        if workflow_type == "requirements_analysis":
            config.update({
                "coordination_strategy": "collaborative",
                "max_iterations": 8,
                "focus_areas": ["functional", "non_functional", "constraints"]
            })
        elif workflow_type == "system_design":
            config.update({
                "coordination_strategy": "hierarchical",
                "max_iterations": 12,
                "design_phases": ["architecture", "components", "interfaces"]
            })

        # Apply custom overrides
        config.update(custom_config)
        return config

    async def execute_collaborative_analysis(self,
                                           workflow_id: str,
                                           initial_prompt: str,
                                           user_id: str = "bmad_user") -> Dict[str, Any]:
        """Execute collaborative analysis workflow.

        Note: This is a simplified implementation. Full multi-agent orchestration
        would require implementing custom agent hierarchy with proper delegation.
        """
        if workflow_id not in self.active_workflows:
            return {"error": f"Workflow {workflow_id} not found"}

        workflow_metadata = self.active_workflows[workflow_id]

        try:
            # Update status
            workflow_metadata["status"] = "running"
            workflow_metadata["started_at"] = datetime.now().isoformat()

            # For now, return a placeholder response
            # Full implementation would create coordinator agent and execute
            result = {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": f"Collaborative analysis completed for: {initial_prompt}",
                "agents_involved": workflow_metadata["agents"],
                "workflow_type": workflow_metadata["workflow_type"]
            }

            workflow_metadata["status"] = "completed"
            workflow_metadata["completed_at"] = datetime.now().isoformat()

            logger.info("Collaborative analysis completed", workflow_id=workflow_id)
            return result

        except Exception as e:
            workflow_metadata["status"] = "failed"
            workflow_metadata["error"] = str(e)
            logger.error("Collaborative analysis failed",
                        workflow_id=workflow_id, error=str(e))
            return {"error": f"Workflow execution failed: {str(e)}"}

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow."""
        return self.active_workflows.get(workflow_id)

    def list_active_workflows(self, project_id: Optional[str] = None) -> List[str]:
        """List active workflow IDs, optionally filtered by project."""
        if project_id:
            return [wf_id for wf_id, metadata in self.active_workflows.items()
                   if metadata.get("project_id") == project_id]
        return list(self.active_workflows.keys())

    def terminate_workflow(self, workflow_id: str) -> bool:
        """Terminate a workflow."""
        if workflow_id not in self.active_workflows:
            return False

        workflow_metadata = self.active_workflows[workflow_id]
        workflow_metadata["status"] = "terminated"
        workflow_metadata["terminated_at"] = datetime.now().isoformat()

        logger.info("Workflow terminated", workflow_id=workflow_id)
        return True

    def _enhance_prompt_with_context(self, prompt: str,
                                   context_data: Optional[Dict[str, Any]]) -> str:
        """Enhance prompt with additional context data."""
        if not context_data:
            return prompt

        enhanced_prompt = f"Initial Request: {prompt}\n\n"

        if "project_name" in context_data:
            enhanced_prompt += f"Project: {context_data['project_name']}\n"

        if "project_description" in context_data:
            enhanced_prompt += f"Description: {context_data['project_description']}\n"

        if "existing_artifacts" in context_data:
            artifacts = ", ".join(context_data["existing_artifacts"])
            enhanced_prompt += f"Existing Artifacts: {artifacts}\n"

        if "requirements" in context_data:
            enhanced_prompt += f"Requirements: {context_data['requirements']}\n"

        if "constraints" in context_data:
            enhanced_prompt += f"Constraints: {context_data['constraints']}\n"

        return enhanced_prompt.strip()

    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Clean up old completed workflows."""
        current_time = datetime.now()
        cleaned_count = 0

        workflows_to_remove = []
        for workflow_id, metadata in self.active_workflows.items():
            if metadata.get("status") in ["completed", "failed", "terminated"]:
                # For now, just count - would implement actual age check
                workflows_to_remove.append(workflow_id)

        # Remove old workflows (simplified logic)
        for workflow_id in workflows_to_remove[:5]:  # Limit cleanup
            del self.active_workflows[workflow_id]
            cleaned_count += 1

        logger.info("Cleaned up old workflows", count=cleaned_count)
        return cleaned_count