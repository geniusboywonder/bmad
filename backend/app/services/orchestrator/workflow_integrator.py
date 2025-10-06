"""Workflow integration service - integrates orchestrator with workflow engine and handles HITL coordination."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.agent import AgentType
from app.services.context_store import ContextStoreService
from app.services.workflow_executor import WorkflowExecutor
from app.services.conflict_resolver import ConflictResolverService

logger = structlog.get_logger(__name__)


class WorkflowIntegrator:
    """Integrates orchestrator with workflow engine."""

    def __init__(self,
                 db: Session,
                 context_store: ContextStoreService,
                 workflow_engine: WorkflowExecutor,
                 conflict_resolver: ConflictResolverService):
        self.db = db
        self.context_store = context_store
        self.workflow_engine = workflow_engine
        self.conflict_resolver = conflict_resolver

    async def run_project_workflow(self, project_id: UUID, user_idea: str, workflow_id: str = "greenfield-fullstack"):
        """
        Runs a dynamic workflow for a project using the WorkflowExecutor.

        Args:
            project_id: UUID of the project
            user_idea: User's project idea/description
            workflow_id: ID of the workflow to execute (defaults to greenfield-fullstack)
        """
        logger.info("Starting dynamic project workflow",
                   project_id=project_id,
                   workflow_id=workflow_id,
                   user_idea=user_idea[:100])

        try:
            # Create initial context artifact with user idea
            initial_context = {
                "user_idea": user_idea,
                "project_id": str(project_id),
                "workflow_id": workflow_id
            }

            context_artifact = self.context_store.create_artifact(
                project_id=project_id,
                source_agent=AgentType.ORCHESTRATOR.value,
                artifact_type="user_input",
                content=initial_context
            )

            # Start workflow execution
            execution = await self.workflow_engine.start_workflow_execution(
                workflow_id=workflow_id,
                project_id=str(project_id),
                context_data=initial_context
            )

            logger.info("Workflow execution started",
                       execution_id=execution.execution_id,
                       workflow_id=workflow_id,
                       total_steps=execution.total_steps)

            # Execute workflow steps sequentially
            while not execution.is_complete():
                try:
                    # Execute next step
                    result = await self.workflow_engine.execute_workflow_step(execution.execution_id)

                    if result.get("status") == "no_pending_steps":
                        break

                    logger.info("Workflow step completed",
                               execution_id=execution.execution_id,
                               step_index=result.get("step_index"),
                               agent=result.get("agent"))

                    # Check for HITL requirements in step results
                    if result.get("requires_hitl"):
                        hitl_result = await self._handle_workflow_hitl(
                            execution.execution_id,
                            result
                        )
                        if not hitl_result.get("approved", True):
                            logger.warning("Workflow paused for HITL approval",
                                         execution_id=execution.execution_id)
                            break

                except Exception as e:
                    logger.error("Workflow step execution failed",
                               execution_id=execution.execution_id,
                               error=str(e))

                    # Mark execution as failed
                    await self.workflow_engine.cancel_workflow_execution(
                        execution.execution_id,
                        f"Step execution failed: {str(e)}"
                    )
                    raise

            # Check final status
            final_status = self.workflow_engine.get_workflow_execution_status(execution.execution_id)
            if final_status and final_status.get("is_complete"):
                if final_status.get("status") == "completed":
                    logger.info("Workflow execution completed successfully",
                               execution_id=execution.execution_id,
                               total_steps=final_status.get("total_steps"))
                else:
                    logger.warning("Workflow execution completed with failures",
                                 execution_id=execution.execution_id,
                                 failed_steps=final_status.get("failed_steps"))
            else:
                logger.warning("Workflow execution did not complete",
                             execution_id=execution.execution_id)

        except Exception as e:
            logger.error("Project workflow execution failed",
                        project_id=project_id,
                        workflow_id=workflow_id,
                        error=str(e))
            raise

    async def detect_and_resolve_conflicts(self, project_id: UUID, workflow_id: str) -> Dict[str, Any]:
        """
        Detect and attempt to resolve conflicts in a project workflow.

        Args:
            project_id: UUID of the project
            workflow_id: ID of the workflow

        Returns:
            Dictionary with conflict detection and resolution results
        """
        logger.info("Starting conflict detection and resolution",
                   project_id=project_id,
                   workflow_id=workflow_id)

        try:
            # Get project artifacts and tasks
            artifacts = self.context_store.get_artifacts_by_project(project_id)
            from app.services.orchestrator.project_manager import ProjectManager
            project_manager = ProjectManager(self.db)
            tasks = project_manager.get_project_tasks(project_id)

            # Detect conflicts
            detected_conflicts = await self.conflict_resolver.detect_conflicts(
                str(project_id), workflow_id, artifacts, tasks
            )

            resolution_results = []
            successful_resolutions = 0
            escalated_conflicts = 0

            # Attempt to resolve each conflict
            for conflict in detected_conflicts:
                try:
                    # Attempt automatic resolution
                    resolution_result = await self.conflict_resolver.resolve_conflict(conflict.conflict_id)

                    if resolution_result.success:
                        successful_resolutions += 1
                        logger.info("Conflict resolved successfully",
                                   conflict_id=conflict.conflict_id,
                                   strategy=resolution_result.resolution_strategy.value)
                    else:
                        escalated_conflicts += 1
                        logger.warning("Conflict escalated for manual resolution",
                                     conflict_id=conflict.conflict_id,
                                     reason=resolution_result.error_message)

                    resolution_results.append({
                        "conflict_id": conflict.conflict_id,
                        "success": resolution_result.success,
                        "strategy": resolution_result.resolution_strategy.value if resolution_result.resolution_strategy else None,
                        "error": resolution_result.error_message
                    })

                except Exception as e:
                    escalated_conflicts += 1
                    resolution_results.append({
                        "conflict_id": conflict.conflict_id,
                        "success": False,
                        "strategy": None,
                        "error": str(e)
                    })
                    logger.error("Conflict resolution failed",
                               conflict_id=conflict.conflict_id,
                               error=str(e))

            result = {
                "project_id": str(project_id),
                "workflow_id": workflow_id,
                "total_conflicts": len(detected_conflicts),
                "successful_resolutions": successful_resolutions,
                "escalated_conflicts": escalated_conflicts,
                "resolution_results": resolution_results,
                "overall_success": escalated_conflicts == 0
            }

            logger.info("Conflict detection and resolution completed",
                       project_id=project_id,
                       total_conflicts=len(detected_conflicts),
                       successful_resolutions=successful_resolutions,
                       escalated_conflicts=escalated_conflicts)

            return result

        except Exception as e:
            logger.error("Conflict detection and resolution failed",
                        project_id=project_id,
                        workflow_id=workflow_id,
                        error=str(e))
            raise

    async def execute_workflow_phase(self, project_id: UUID, phase: str) -> Dict[str, Any]:
        """Execute workflow phase with HITL integration."""

        logger.info("Executing workflow phase",
                   project_id=project_id,
                   phase=phase)

        try:
            # Get phase configuration from project lifecycle manager
            from app.services.orchestrator.project_manager import ProjectManager, SDLC_PHASES
            project_manager = ProjectManager(self.db)

            if phase not in SDLC_PHASES:
                return {"success": False, "error": f"Invalid phase: {phase}"}

            phase_config = SDLC_PHASES[phase]

            # Create workflow context for this phase
            workflow_context = {
                "project_id": str(project_id),
                "phase": phase,
                "agent_sequence": phase_config["agent_sequence"],
                "completion_criteria": phase_config["completion_criteria"],
                "parallel_execution": phase_config["parallel_execution"]
            }

            # Start phase execution
            execution = await self.workflow_engine.start_workflow_execution(
                workflow_id=f"{phase}_phase",
                project_id=str(project_id),
                context_data=workflow_context
            )

            # Execute agents in sequence or parallel based on configuration
            if phase_config["parallel_execution"]:
                result = await self._execute_parallel_agents(execution, phase_config["agent_sequence"])
            else:
                result = await self._execute_sequential_agents(execution, phase_config["agent_sequence"])

            return {
                "success": True,
                "phase": phase,
                "execution_id": execution.execution_id,
                "result": result
            }

        except Exception as e:
            logger.error("Phase execution failed",
                        project_id=project_id,
                        phase=phase,
                        error=str(e))
            return {
                "success": False,
                "phase": phase,
                "error": str(e)
            }

    async def handle_phase_transition(self, project_id: UUID, from_phase: str, to_phase: str) -> bool:
        """Handle workflow phase transitions with validation."""

        logger.info("Handling phase transition",
                   project_id=project_id,
                   from_phase=from_phase,
                   to_phase=to_phase)

        try:
            # Validate current phase completion
            from app.services.orchestrator.project_manager import ProjectManager
            project_manager = ProjectManager(self.db)

            validation_result = project_manager.validate_phase_completion(project_id, from_phase)

            if not validation_result["valid"]:
                logger.warning("Phase transition blocked - current phase not completed",
                             project_id=project_id,
                             from_phase=from_phase,
                             missing_criteria=validation_result["missing_criteria"])
                return False

            # Perform transition
            transition_result = project_manager.transition_to_next_phase(project_id)

            if transition_result["success"]:
                logger.info("Phase transition completed",
                           project_id=project_id,
                           from_phase=from_phase,
                           to_phase=to_phase)
                return True
            else:
                logger.error("Phase transition failed",
                           project_id=project_id,
                           error=transition_result.get("error"))
                return False

        except Exception as e:
            logger.error("Phase transition handling failed",
                        project_id=project_id,
                        from_phase=from_phase,
                        to_phase=to_phase,
                        error=str(e))
            return False

    async def _handle_workflow_hitl(self, execution_id: str, step_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HITL requirements during workflow execution."""

        logger.info("Handling workflow HITL",
                   execution_id=execution_id)

        # This would integrate with the HITL service
        # For now, return approved by default
        return {"approved": True, "reason": "Auto-approved for workflow continuation"}

    async def _execute_parallel_agents(self, execution, agent_sequence: List[str]) -> Dict[str, Any]:
        """Execute agents in parallel for a workflow phase."""

        logger.info("Executing agents in parallel",
                   execution_id=execution.execution_id,
                   agents=agent_sequence)

        # This would coordinate parallel agent execution
        # Implementation would depend on the workflow engine's capabilities
        results = {}

        for agent_type in agent_sequence:
            # In a real implementation, these would run in parallel
            result = await self.workflow_engine.execute_workflow_step(execution.execution_id)
            results[agent_type] = result

        return results

    async def _execute_sequential_agents(self, execution, agent_sequence: List[str]) -> Dict[str, Any]:
        """Execute agents sequentially for a workflow phase."""

        logger.info("Executing agents sequentially",
                   execution_id=execution.execution_id,
                   agents=agent_sequence)

        results = {}

        for agent_type in agent_sequence:
            result = await self.workflow_engine.execute_workflow_step(execution.execution_id)
            results[agent_type] = result

            # Check if step failed
            if result.get("status") == "failed":
                logger.error("Agent execution failed",
                           agent_type=agent_type,
                           error=result.get("error"))
                break

        return results

    def get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get current workflow execution status."""

        return self.workflow_engine.get_workflow_execution_status(execution_id)

    async def cancel_workflow(self, execution_id: str, reason: str) -> bool:
        """Cancel a running workflow execution."""

        try:
            await self.workflow_engine.cancel_workflow_execution(execution_id, reason)
            logger.info("Workflow cancelled",
                       execution_id=execution_id,
                       reason=reason)
            return True
        except Exception as e:
            logger.error("Failed to cancel workflow",
                        execution_id=execution_id,
                        error=str(e))
            return False