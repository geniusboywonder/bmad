"""
Workflow Execution Engine - Core execution logic with dependency injection.

Handles main workflow execution coordination and delegates to specialized services.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import asyncio
import structlog

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowExecutionState
from app.models.handoff import HandoffSchema
from app.models.task import Task, TaskStatus
from app.services.workflow_service import WorkflowService
from app.services.workflow_step_processor import WorkflowStepProcessor
from app.services.workflow_hitl_integrator import WorkflowHitlIntegrator

from .state_manager import StateManager
from .event_dispatcher import EventDispatcher
from .sdlc_orchestrator import SdlcOrchestrator

logger = structlog.get_logger(__name__)


class ExecutionEngine:
    """
    Core workflow execution engine that coordinates specialized workflow services.

    Follows Single Responsibility Principle by delegating specialized tasks
    to focused service components.
    """

    def __init__(self, db: Session):
        self.db = db
        self.workflow_service = WorkflowService(db)
        self.step_processor = WorkflowStepProcessor(db)
        self.hitl_integrator = WorkflowHitlIntegrator(db)

        # Initialize specialized services
        self.state_manager = StateManager(db)
        self.event_dispatcher = EventDispatcher(db)
        self.sdlc_orchestrator = SdlcOrchestrator(db)

    async def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: UUID,
        context_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start workflow execution.

        Args:
            workflow_id: Workflow definition identifier
            project_id: Project identifier
            context_data: Initial context data
            execution_id: Optional custom execution ID

        Returns:
            Dictionary containing execution results
        """
        if not execution_id:
            execution_id = str(uuid4())

        logger.info(
            "Starting workflow execution",
            workflow_id=workflow_id,
            project_id=str(project_id),
            execution_id=execution_id
        )

        try:
            # Load workflow definition
            workflow_definition = await self.workflow_service.get_workflow_definition(workflow_id)
            if not workflow_definition:
                raise ValueError(f"Workflow definition not found: {workflow_id}")

            # Create execution state
            execution = self.state_manager.create_execution_state(
                execution_id=execution_id,
                workflow_id=workflow_id,
                project_id=project_id,
                workflow_definition=workflow_definition,
                initial_context=context_data
            )

            # Update state to running
            execution = self.state_manager.update_execution_state(
                execution_id,
                state=WorkflowExecutionState.RUNNING
            )

            # Emit workflow started event
            await self.event_dispatcher.emit_workflow_started(execution, workflow_definition)

            # Execute workflow steps
            result = await self._execute_workflow_steps(execution)

            return {
                "execution_id": execution_id,
                "status": "started",
                "message": "Workflow execution started successfully",
                "result": result
            }

        except Exception as e:
            logger.error(
                "Failed to start workflow execution",
                workflow_id=workflow_id,
                project_id=str(project_id),
                execution_id=execution_id,
                error=str(e)
            )

            # Mark execution as failed
            self.state_manager.fail_execution(
                execution_id,
                f"Failed to start workflow: {str(e)}"
            )

            raise

    async def execute_workflow_step(
        self,
        execution_id: str,
        step_index: int,
        context_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific workflow step.

        Args:
            execution_id: Workflow execution identifier
            step_index: Index of step to execute
            context_data: Optional additional context data

        Returns:
            Dictionary containing step execution results
        """
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            raise ValueError(f"Workflow execution not found: {execution_id}")

        # Update context if provided
        if context_data:
            execution.context_data.update(context_data)

        # Execute the step using step processor
        step_result = await self.step_processor.execute_step(
            execution,
            step_index
        )

        # Update execution state with step result
        execution.step_results.append(step_result)
        execution.current_step_index = step_index + 1

        self.state_manager.persist_execution_state(execution)

        # Emit step completed event
        await self.event_dispatcher.emit_workflow_step_completed(
            execution, step_index, step_result
        )

        # Check HITL triggers after step completion
        await self._check_hitl_triggers_after_step(execution, step_result)

        return step_result

    async def execute_parallel_steps(
        self,
        execution_id: str,
        step_indices: List[int],
        context_data: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple workflow steps in parallel.

        Args:
            execution_id: Workflow execution identifier
            step_indices: List of step indices to execute
            context_data: Optional additional context data

        Returns:
            List of step execution results
        """
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            raise ValueError(f"Workflow execution not found: {execution_id}")

        logger.info(
            "Executing parallel workflow steps",
            execution_id=execution_id,
            step_indices=step_indices
        )

        # Update context if provided
        if context_data:
            execution.context_data.update(context_data)

        # Execute steps in parallel using step processor
        tasks = [
            self.step_processor.execute_step(execution, step_index)
            for step_index in step_indices
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = {
                        "step_index": step_indices[i],
                        "success": False,
                        "error": str(result),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    processed_results.append(error_result)
                    logger.error(
                        "Parallel step execution failed",
                        execution_id=execution_id,
                        step_index=step_indices[i],
                        error=str(result)
                    )
                else:
                    processed_results.append(result)

            # Update execution state
            execution.step_results.extend(processed_results)
            execution.current_step_index = max(step_indices) + 1

            self.state_manager.persist_execution_state(execution)

            # Emit events for completed steps
            for i, result in enumerate(processed_results):
                await self.event_dispatcher.emit_workflow_step_completed(
                    execution, step_indices[i], result
                )

            return processed_results

        except Exception as e:
            logger.error(
                "Failed to execute parallel workflow steps",
                execution_id=execution_id,
                step_indices=step_indices,
                error=str(e)
            )
            raise

    async def pause_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """
        Pause workflow execution.

        Args:
            execution_id: Workflow execution identifier
            reason: Reason for pausing

        Returns:
            True if successfully paused, False otherwise
        """
        success = self.state_manager.pause_execution(execution_id, reason)

        if success:
            execution = self.state_manager.get_execution_state(execution_id)
            if execution:
                await self.event_dispatcher.emit_workflow_paused(execution, reason)

        return success

    async def resume_workflow_execution(self, execution_id: str) -> bool:
        """
        Resume paused workflow execution.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            True if successfully resumed, False otherwise
        """
        success = self.state_manager.resume_execution(execution_id)

        if success:
            execution = self.state_manager.get_execution_state(execution_id)
            if execution:
                await self.event_dispatcher.emit_workflow_resumed(execution)
                # Continue executing remaining steps
                await self._execute_workflow_steps(execution)

        return success

    async def cancel_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """
        Cancel workflow execution.

        Args:
            execution_id: Workflow execution identifier
            reason: Reason for cancellation

        Returns:
            True if successfully cancelled, False otherwise
        """
        return self.state_manager.cancel_execution(execution_id, reason)

    def recover_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """
        Recover workflow execution from persistence.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            Recovered workflow execution state or None if not found
        """
        return self.state_manager.recover_execution_state(execution_id)

    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow execution status.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            Status dictionary or None if not found
        """
        return self.state_manager.get_execution_status(execution_id)

    async def resume_workflow_after_hitl(
        self,
        project_id: UUID,
        task_id: Optional[UUID],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume workflow after HITL response.

        Args:
            project_id: Project identifier
            task_id: Optional task identifier
            context_data: Updated context data

        Returns:
            Dictionary containing resumption results
        """
        return await self.hitl_integrator.resume_workflow_after_hitl(
            project_id, task_id, context_data
        )

    async def generate_agent_handoff(
        self,
        execution_id: str,
        from_agent: str,
        to_agent: str,
        task_description: str,
        context_artifacts: List[UUID],
        metadata: Optional[Dict[str, Any]] = None
    ) -> HandoffSchema:
        """
        Generate agent handoff for workflow step.

        Args:
            execution_id: Workflow execution identifier
            from_agent: Source agent type
            to_agent: Target agent type
            task_description: Task description
            context_artifacts: List of context artifact IDs
            metadata: Optional metadata

        Returns:
            Generated handoff schema
        """
        execution = self.state_manager.get_execution_state(execution_id)
        if not execution:
            raise ValueError(f"Workflow execution not found: {execution_id}")

        handoff_metadata = {
            "workflow_execution_id": execution_id,
            "project_phase": self._get_current_workflow_phase(execution),
            "context_summary": f"Workflow step handoff from {from_agent} to {to_agent}",
            "priority": "normal",
            "expected_outputs": ["task_completion", "step_results"]
        }

        if metadata:
            handoff_metadata.update(metadata)

        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=from_agent,
            to_agent=to_agent,
            project_id=execution.project_id,
            phase=self._get_current_workflow_phase(execution),
            context_ids=context_artifacts,
            instructions=task_description,
            expected_outputs=["task_completion", "step_results"],
            metadata=handoff_metadata,
            created_at=datetime.now(timezone.utc)
        )

        logger.info(
            "Generated agent handoff",
            execution_id=execution_id,
            handoff_id=handoff.handoff_id,
            from_agent=from_agent,
            to_agent=to_agent
        )

        return handoff

    # SDLC workflow methods (delegated to SdlcOrchestrator)
    async def execute_sdlc_workflow(
        self,
        project_id: UUID,
        requirements: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute SDLC workflow."""
        return await self.sdlc_orchestrator.execute_sdlc_workflow(
            project_id, requirements, execution_id
        )

    def get_sdlc_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get SDLC workflow status."""
        return self.sdlc_orchestrator.get_sdlc_workflow_status(execution_id)

    # Private helper methods

    async def _execute_workflow_steps(self, execution: WorkflowExecutionStateModel) -> Dict[str, Any]:
        """Execute all workflow steps sequentially."""
        try:
            workflow_definition = execution.workflow_definition
            steps = workflow_definition.get("steps", [])

            while (execution.current_step_index < len(steps) and
                   execution.state == WorkflowExecutionState.RUNNING):

                # Check if workflow is paused
                if execution.state == WorkflowExecutionState.PAUSED:
                    logger.info(
                        "Workflow execution paused",
                        execution_id=execution.execution_id,
                        current_step=execution.current_step_index
                    )
                    break

                # Execute current step
                step_result = await self.execute_workflow_step(
                    execution.execution_id,
                    execution.current_step_index
                )

                # Check if step failed
                if not step_result.get("success", False):
                    error_message = step_result.get("error", "Step execution failed")
                    self.state_manager.fail_execution(
                        execution.execution_id,
                        error_message,
                        {"failed_step": execution.current_step_index}
                    )

                    execution = self.state_manager.get_execution_state(execution.execution_id)
                    await self.event_dispatcher.emit_workflow_failed(
                        execution, error_message
                    )
                    break

                # Refresh execution state
                execution = self.state_manager.get_execution_state(execution.execution_id)

            # Check if workflow completed successfully
            if (execution.current_step_index >= len(steps) and
                execution.state == WorkflowExecutionState.RUNNING):

                final_results = {
                    "completed_steps": len(execution.step_results),
                    "total_steps": len(steps),
                    "step_results": execution.step_results,
                    "context_data": execution.context_data
                }

                self.state_manager.complete_execution(execution.execution_id, final_results)
                execution = self.state_manager.get_execution_state(execution.execution_id)

                await self.event_dispatcher.emit_workflow_completed(execution, final_results)

                return final_results

            return {
                "status": execution.state.value,
                "completed_steps": len(execution.step_results),
                "total_steps": len(steps)
            }

        except Exception as e:
            logger.error(
                "Failed to execute workflow steps",
                execution_id=execution.execution_id,
                error=str(e)
            )

            self.state_manager.fail_execution(
                execution.execution_id,
                f"Workflow execution failed: {str(e)}"
            )
            raise

    async def _check_hitl_triggers_after_step(
        self,
        execution: WorkflowExecutionStateModel,
        step_result: Dict[str, Any]
    ) -> None:
        """Check HITL triggers after step completion."""
        try:
            hitl_request = await self.hitl_integrator.check_hitl_triggers_after_step(
                execution, step_result
            )

            if hitl_request:
                # Pause workflow for HITL
                self.state_manager.pause_execution(
                    execution.execution_id,
                    "HITL approval required"
                )

                # Emit HITL triggered event
                await self.event_dispatcher.emit_hitl_triggered(
                    execution.project_id,
                    execution.execution_id,
                    hitl_request.id,
                    "Step completion triggered HITL"
                )

        except Exception as e:
            logger.error(
                "Failed to check HITL triggers",
                execution_id=execution.execution_id,
                error=str(e)
            )

    def _get_current_workflow_phase(self, execution: WorkflowExecutionStateModel) -> str:
        """Get current workflow phase."""
        steps = execution.workflow_definition.get("steps", [])
        if execution.current_step_index < len(steps):
            current_step = steps[execution.current_step_index]
            return current_step.get("phase", "unknown")
        return "completed"