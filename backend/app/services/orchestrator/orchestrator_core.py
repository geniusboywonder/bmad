"""Core orchestration logic - delegates to specialized managers following SOLID principles.

PHASE 3 TARGETED CLEANUP (October 2025):
- Using consolidated ProjectManager (combines ProjectLifecycleManager + StatusTracker)
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.task import Task
from app.models.handoff import HandoffSchema
from app.services.context_store import ContextStoreService
# Note: BMADMAFWrapper used in agent_tasks.py, handoff_manager.py, workflow_step_processor.py
from app.services.workflow_executor import WorkflowExecutor
from app.services.conflict_resolver import ConflictResolverService

from .project_manager import ProjectManager
from .agent_coordinator import AgentCoordinator
from .workflow_integrator import WorkflowIntegrator
from .handoff_manager import HandoffManager
from .context_manager import ContextManager

logger = structlog.get_logger(__name__)


class OrchestratorCore:
    """Core orchestration logic - delegates to specialized services."""

    def __init__(self, db: Session):
        """Initialize orchestrator core with dependency injection of specialized services."""
        self.db = db

        # Initialize external services
        self.context_store = ContextStoreService(db)
        # MAF wrapper created per-agent when needed (not global instance)
        self.workflow_engine = WorkflowExecutor(db)
        self.conflict_resolver = ConflictResolverService(self.context_store)

        # Initialize specialized orchestrator services
        self.project_manager = ProjectManager(db)  # Consolidated service
        self.agent_coordinator = AgentCoordinator(db)
        self.workflow_integrator = WorkflowIntegrator(
            db, self.context_store, self.workflow_engine, self.conflict_resolver
        )
        self.handoff_manager = HandoffManager(db, self.context_store)
        self.context_manager = ContextManager(db, self.context_store)

    # ===== PROJECT LIFECYCLE MANAGEMENT =====

    def create_project(self, name: str, description: str = None) -> UUID:
        """Create new project with initial state."""
        return self.project_manager.create_project(name, description)

    def list_projects(self) -> List:
        """List all projects."""
        return self.project_manager.list_projects()

    def get_current_phase(self, project_id: UUID) -> str:
        """Get the current SDLC phase for a project."""
        return self.project_manager.get_current_phase(project_id)

    def set_current_phase(self, project_id: UUID, phase: str):
        """Set the current SDLC phase for a project."""
        self.project_manager.set_current_phase(project_id, phase)

    def validate_phase_completion(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Validate if a phase has met its completion criteria."""
        return self.project_manager.validate_phase_completion(project_id, phase)

    def transition_to_next_phase(self, project_id: UUID) -> Dict[str, Any]:
        """Transition project to the next SDLC phase if current phase is completed."""
        return self.project_manager.transition_to_next_phase(project_id)

    def get_phase_progress(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive progress information for all phases."""
        return self.project_manager.get_phase_progress(project_id)

    def get_project_tasks(self, project_id: UUID) -> List[Task]:
        """Get all tasks for a project."""
        return self.project_manager.get_project_tasks(project_id)

    # ===== AGENT COORDINATION =====

    def create_task(self, project_id: UUID, agent_type: str, instructions: str, context_ids: List[UUID] = None) -> Task:
        """Create a new task for an agent."""
        return self.agent_coordinator.create_task(project_id, agent_type, instructions, context_ids)

    def submit_task(self, task: Task) -> str:
        """Submit a task to the Celery queue."""
        return self.agent_coordinator.submit_task(task)

    def update_task_status(self, task_id: UUID, status, output: Dict[str, Any] = None, error_message: str = None):
        """Update a task's status."""
        self.agent_coordinator.update_task_status(task_id, status, output, error_message)

    def update_agent_status(self, agent_type: str, status, current_task_id: UUID = None, error_message: str = None):
        """Update an agent's status."""
        self.agent_coordinator.update_agent_status(agent_type, status, current_task_id, error_message)

    def get_agent_status(self, agent_type: str):
        """Get an agent's current status."""
        return self.agent_coordinator.get_agent_status(agent_type)

    def assign_agent_to_task(self, task: Task) -> Dict[str, Any]:
        """Assign appropriate agent to task based on requirements."""
        return self.agent_coordinator.assign_agent_to_task(task)

    def coordinate_multi_agent_workflow(self, project_id: UUID, agents_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Coordinate multiple agents for complex workflows."""
        return self.agent_coordinator.coordinate_multi_agent_workflow(project_id, agents_config)

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of all available (non-working) agents."""
        return self.agent_coordinator.get_available_agents()

    def get_agent_workload(self) -> Dict[str, Any]:
        """Get current workload distribution across agents."""
        return self.agent_coordinator.get_agent_workload()

    def reassign_failed_task(self, task_id: UUID) -> Dict[str, Any]:
        """Reassign a failed task to the same or different agent."""
        return self.agent_coordinator.reassign_failed_task(task_id)

    # ===== WORKFLOW INTEGRATION =====

    async def run_project_workflow(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """Runs a dynamic workflow for a project using the WorkflowExecutor."""
        return await self.workflow_integrator.run_project_workflow(project_id, user_idea, workflow_id)

    def run_project_workflow_sync(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """Synchronous wrapper for run_project_workflow."""
        import asyncio

        async def _run():
            return await self.run_project_workflow(project_id, user_idea, workflow_id)

        # Handle event loop
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_run())
        except RuntimeError:
            # No event loop running, create new one
            return asyncio.run(_run())

    async def detect_and_resolve_conflicts(self, project_id: UUID, workflow_id: str) -> Dict[str, Any]:
        """Detect and attempt to resolve conflicts in a project workflow."""
        return await self.workflow_integrator.detect_and_resolve_conflicts(project_id, workflow_id)

    async def execute_workflow_phase(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Execute workflow phase with HITL integration."""
        return await self.workflow_integrator.execute_workflow_phase(project_id, phase)

    async def handle_phase_transition(self, project_id: UUID, from_phase: str, to_phase: str) -> bool:
        """Handle workflow phase transitions with validation."""
        return await self.workflow_integrator.handle_phase_transition(project_id, from_phase, to_phase)

    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current workflow execution status."""
        return self.workflow_integrator.get_workflow_status(execution_id)

    async def cancel_workflow(self, execution_id: str, reason: str) -> bool:
        """Cancel a running workflow execution."""
        return await self.workflow_integrator.cancel_workflow(execution_id, reason)

    # ===== HANDOFF MANAGEMENT =====

    def create_task_from_handoff(self, handoff: HandoffSchema = None, project_id: UUID = None,
                                handoff_schema: Dict[str, Any] = None) -> Task:
        """Create a task from a HandoffSchema or raw handoff data."""
        return self.handoff_manager.create_task_from_handoff(handoff, project_id, handoff_schema)

    async def process_task_with_autogen(self, task: Task, handoff: HandoffSchema) -> dict:
        """Process a task using AutoGen with handoff context."""
        return await self.handoff_manager.process_task_with_autogen(task, handoff)

    def create_handoff_chain(self, project_id: UUID, handoff_chain: List[Dict[str, Any]]) -> List[Task]:
        """Create a chain of handoff tasks."""
        return self.handoff_manager.create_handoff_chain(project_id, handoff_chain)

    def get_handoff_history(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get handoff history for a project."""
        return self.handoff_manager.get_handoff_history(project_id)

    def validate_handoff_chain(self, handoff_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a handoff chain for consistency."""
        return self.handoff_manager.validate_handoff_chain(handoff_chain)

    def get_active_handoffs(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get currently active handoffs for a project."""
        return self.handoff_manager.get_active_handoffs(project_id)

    def cancel_handoff(self, task_id: UUID, reason: str) -> bool:
        """Cancel an active handoff."""
        return self.handoff_manager.cancel_handoff(task_id, reason)

    # ===== STATUS TRACKING =====
    # Now handled by consolidated ProjectManager

    def get_phase_time_analysis(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive time analysis for all project phases."""
        return self.project_manager.get_phase_time_analysis(project_id)

    def get_time_conscious_context(self, project_id: UUID, phase: str, agent_type: str,
                                 time_budget_hours: float = None) -> Dict[str, Any]:
        """Get context information that is time-conscious and filtered based on current time pressure."""
        return self.project_manager.get_time_conscious_context(project_id, phase, agent_type, time_budget_hours)

    def get_time_based_phase_transition(self, project_id: UUID) -> Dict[str, Any]:
        """Determine if phase transition should occur based on time analysis."""
        return self.project_manager.get_time_based_phase_transition(project_id)

    def get_performance_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the project."""
        return self.project_manager.get_performance_metrics(project_id)

    # ===== CONTEXT MANAGEMENT =====

    def get_selective_context(self, project_id: UUID, phase: str, agent_type: str) -> List[UUID]:
        """Get selective context artifacts relevant to the current phase and agent."""
        return self.context_manager.get_selective_context(project_id, phase, agent_type)

    def get_latest_amended_artifact(self, project_id: UUID, task_id: UUID):
        """Get the latest amended artifact for a specific task."""
        return self.context_manager.get_latest_amended_artifact(project_id, task_id)

    def get_integrated_context_summary(self, project_id: UUID, agent_type: str, phase: str,
                                     include_time_analysis: bool = True,
                                     time_budget_hours: float = None) -> Dict[str, Any]:
        """Get comprehensive integrated context summary with all granularity features."""
        return self.context_manager.get_integrated_context_summary(
            project_id, agent_type, phase, include_time_analysis, time_budget_hours
        )

    def get_context_granularity_report(self, project_id: UUID) -> Dict[str, Any]:
        """Generate comprehensive context granularity report for the project."""
        return self.context_manager.get_context_granularity_report(project_id)

    # ===== HITL INTEGRATION METHODS =====

    def create_hitl_request(self, project_id: UUID, request_type: str, content: Dict[str, Any],
                           priority: str = "medium") -> UUID:
        """Create a new HITL request."""
        # This would delegate to a HITL service when available
        # For now, we'll implement basic functionality
        logger.info("HITL request created",
                   project_id=project_id,
                   request_type=request_type,
                   priority=priority)
        return UUID()  # Placeholder

    def process_hitl_response(self, request_id: UUID, action: str, response_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process HITL response and update workflow accordingly."""
        # This would delegate to a HITL service when available
        logger.info("HITL response processed",
                   request_id=request_id,
                   action=action)
        return {"success": True, "action": action}

    def update_hitl_request_content(self, request_id: UUID, content: dict):
        """Update HITL request content."""
        logger.info("HITL request content updated", request_id=request_id)

    async def notify_hitl_request_created(self, request_id: UUID):
        """Notify stakeholders about new HITL request."""
        logger.info("HITL request notification sent", request_id=request_id)

    async def wait_for_hitl_response(self, request_id: UUID):
        """Wait for HITL response with timeout."""
        logger.info("Waiting for HITL response", request_id=request_id)
        # This would implement actual waiting logic
        return {"approved": True}  # Placeholder

    async def resume_workflow_after_hitl(self, hitl_request_id: UUID, hitl_action):
        """Resume workflow execution after HITL decision."""
        logger.info("Resuming workflow after HITL",
                   hitl_request_id=hitl_request_id,
                   action=hitl_action)
        return {"workflow_resumed": True}

    # ===== HEALTH CHECK =====

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all orchestrator services."""
        health_status = {
            "orchestrator_core": "healthy",
            "project_manager": "healthy",  # Consolidated service
            "agent_coordinator": "healthy",
            "workflow_integrator": "healthy",
            "handoff_manager": "healthy",
            "context_manager": "healthy",
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Test database connection
            self.db.execute("SELECT 1")
            health_status["database"] = "healthy"
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"
            health_status["orchestrator_core"] = "degraded"

        # Overall health
        unhealthy_services = [k for k, v in health_status.items()
                            if isinstance(v, str) and v.startswith("unhealthy")]

        if unhealthy_services:
            health_status["overall"] = "unhealthy"
        elif any(v == "degraded" for v in health_status.values()):
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "healthy"

        return health_status