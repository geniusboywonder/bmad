"""
Consolidated Workflow Executor - Execution engine and HITL integration.

Handles workflow execution coordination, HITL integration, and event dispatching.
Consolidates functionality from workflow/execution_engine.py, workflow_hitl_integrator.py,
and workflow/event_dispatcher.py, workflow/state_manager.py, workflow/sdlc_orchestrator.py.
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
from app.models.hitl import HitlRequest
from app.services.workflow_service_consolidated import ConsolidatedWorkflowService
from app.services.workflow_step_processor import WorkflowStepProcessor
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class WorkflowExecutor:
    """
    Consolidated workflow executor handling execution coordination and HITL integration.
    
    Combines execution engine, HITL integration, event dispatching, state management,
    and SDLC orchestration into a single, focused service following SOLID principles.
    """

    def __init__(self, db: Session):
        self.db = db
        self.workflow_service = ConsolidatedWorkflowService(db)
        self.step_processor = WorkflowStepProcessor(db)
        
        # Lazy import to avoid circular dependency
        self._hitl_service = None

    @property
    def hitl_service(self):
        """Lazy-loaded HITL service to avoid circular imports."""
        if self._hitl_service is None:
            from app.services.hitl_approval_service import HitlApprovalService
            self._hitl_service = HitlApprovalService(self.db)
        return self._hitl_service

    # ========== WORKFLOW EXECUTION ENGINE ==========

    async def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: UUID,
        context_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start workflow execution."""
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
            execution = self.create_execution_state(
                execution_id=execution_id,
                workflow_id=workflow_id,
                project_id=str(project_id),
                workflow_definition=workflow_definition,
                initial_context=context_data
            )

            # Update state to running
            execution = self.update_execution_state(
                execution_id,
                state=WorkflowExecutionState.RUNNING
            )

            # Emit workflow started event
            await self.emit_workflow_started(execution, workflow_definition)

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
            self.fail_execution(
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
        """Execute a specific workflow step."""
        execution = self.get_execution_state(execution_id)
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

        self.persist_execution_state(execution)

        # Emit step completed event
        await self.emit_workflow_step_completed(
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
        """Execute multiple workflow steps in parallel."""
        execution = self.get_execution_state(execution_id)
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

            self.persist_execution_state(execution)

            # Emit events for completed steps
            for i, result in enumerate(processed_results):
                await self.emit_workflow_step_completed(
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
        """Pause workflow execution."""
        success = self.pause_execution(execution_id, reason)

        if success:
            execution = self.get_execution_state(execution_id)
            if execution:
                await self.emit_workflow_paused(execution, reason)

        return success

    async def resume_workflow_execution(self, execution_id: str) -> bool:
        """Resume paused workflow execution."""
        success = self.resume_execution(execution_id)

        if success:
            execution = self.get_execution_state(execution_id)
            if execution:
                await self.emit_workflow_resumed(execution)
                # Continue executing remaining steps
                await self._execute_workflow_steps(execution)

        return success

    async def cancel_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """Cancel workflow execution."""
        return self.cancel_execution(execution_id, reason)

    def recover_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Recover workflow execution from persistence."""
        return self.recover_execution_state(execution_id)

    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        return self.get_execution_status(execution_id)

    # ========== HITL INTEGRATION ==========

    async def check_hitl_triggers_after_step(
        self,
        execution: WorkflowExecutionStateModel,
        step_result: Dict[str, Any]
    ) -> Optional[HitlRequest]:
        """Check for HITL triggers after step completion."""
        try:
            # Get project oversight level
            oversight_level = self.hitl_service.get_oversight_level(execution.project_id)

            # Prepare trigger context
            trigger_context = {
                "oversight_level": oversight_level,
                "current_phase": self._get_current_workflow_phase(execution),
                "step_index": execution.current_step_index,
                "agent_type": self._get_current_agent(execution),
                "confidence_score": step_result.get("confidence_score", 0.8),
                "error_type": step_result.get("error_type"),
                "conflict_detected": step_result.get("conflict_detected", False),
                "auto_resolution_attempts": step_result.get("auto_resolution_attempts", 0),
                "budget_usage_percent": step_result.get("budget_usage_percent", 0),
                "violation_type": step_result.get("safety_violation_type"),
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id
            }

            # Check for HITL triggers
            hitl_request = await self.hitl_service.check_hitl_triggers(
                project_id=UUID(execution.project_id),
                task_id=UUID(execution.execution_id),
                agent_type=self._get_current_agent(execution),
                trigger_context=trigger_context
            )

            if hitl_request:
                logger.info("HITL trigger activated after step completion",
                           execution_id=execution.execution_id,
                           step_index=execution.current_step_index,
                           hitl_request_id=str(hitl_request.request_id))

            return hitl_request

        except Exception as e:
            logger.error("Failed to check HITL triggers after step",
                        execution_id=execution.execution_id,
                        step_index=execution.current_step_index,
                        error=str(e))
            return None

    async def pause_workflow_for_hitl(
        self,
        execution: WorkflowExecutionStateModel,
        hitl_request: HitlRequest,
        reason: str
    ) -> bool:
        """Pause workflow execution for HITL approval."""
        try:
            # Update execution status
            execution.pause(reason)

            # Persist the updated state
            self.persist_execution_state(execution)

            logger.info("Workflow paused for HITL approval",
                       execution_id=execution.execution_id,
                       hitl_request_id=str(hitl_request.request_id),
                       reason=reason)

            return True

        except Exception as e:
            logger.error("Failed to pause workflow for HITL",
                        execution_id=execution.execution_id,
                        hitl_request_id=str(hitl_request.request_id),
                        error=str(e))
            return False

    async def resume_workflow_after_hitl(
        self,
        project_id: UUID,
        task_id: Optional[UUID],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resume workflow after HITL response."""
        try:
            # Find execution by task_id (which should be execution_id)
            execution_id = str(task_id) if task_id else None
            if not execution_id:
                return {"status": "error", "message": "No execution ID provided"}

            execution = self.get_execution_state(execution_id)
            if not execution:
                return {"status": "error", "message": f"Execution {execution_id} not found"}

            # Update execution context with HITL response
            execution.context_data.update(context_data)

            # Resume execution
            execution.resume()
            self.persist_execution_state(execution)

            logger.info("Workflow resumed after HITL response",
                       execution_id=execution_id)

            return {"status": "success", "message": "Workflow resumed after HITL response"}

        except Exception as e:
            logger.error("Failed to resume workflow after HITL",
                        project_id=str(project_id),
                        task_id=str(task_id) if task_id else None,
                        error=str(e))
            return {"status": "error", "message": f"Failed to resume workflow: {str(e)}"}

    async def get_workflow_hitl_status(self, execution_id: str) -> Dict[str, Any]:
        """Get HITL status for a workflow execution."""
        try:
            # Get pending HITL requests for this execution
            pending_requests = await self.hitl_service.get_pending_hitl_requests()

            # Filter for this execution
            execution_hitl_requests = [
                req for req in pending_requests
                if req.task_id and str(req.task_id) == execution_id
            ]

            return {
                "execution_id": execution_id,
                "pending_hitl_count": len(execution_hitl_requests),
                "has_pending_hitl": len(execution_hitl_requests) > 0,
                "pending_requests": [
                    {
                        "request_id": str(req.request_id),
                        "question": req.question,
                        "status": req.status.value,
                        "created_at": req.created_at.isoformat()
                    }
                    for req in execution_hitl_requests
                ]
            }

        except Exception as e:
            logger.error("Failed to get workflow HITL status",
                        execution_id=execution_id,
                        error=str(e))
            return {
                "execution_id": execution_id,
                "pending_hitl_count": 0,
                "has_pending_hitl": False,
                "pending_requests": [],
                "error": str(e)
            }

    # ========== STATE MANAGEMENT ==========

    def create_execution_state(
        self,
        execution_id: str,
        workflow_id: str,
        project_id: str,
        workflow_definition: Dict[str, Any],
        initial_context: Dict[str, Any]
    ) -> WorkflowExecutionStateModel:
        """Create new execution state."""
        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            project_id=project_id,
            workflow_id=workflow_id,
            status=WorkflowExecutionState.PENDING,
            workflow_definition=workflow_definition,
            context_data=initial_context
        )

        self.persist_execution_state(execution)
        return execution

    def update_execution_state(
        self,
        execution_id: str,
        state: WorkflowExecutionState,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionStateModel:
        """Update execution state."""
        execution = self.get_execution_state(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = state
        if error_message:
            execution.error_message = error_message
        if metadata:
            execution.context_data.update(metadata)

        self.persist_execution_state(execution)
        return execution

    def pause_execution(self, execution_id: str, reason: str) -> bool:
        """Pause execution."""
        execution = self.get_execution_state(execution_id)
        if not execution:
            return False

        execution.pause(reason)
        self.persist_execution_state(execution)
        return True

    def resume_execution(self, execution_id: str) -> bool:
        """Resume execution."""
        execution = self.get_execution_state(execution_id)
        if not execution or not execution.can_resume():
            return False

        execution.resume()
        self.persist_execution_state(execution)
        return True

    def cancel_execution(self, execution_id: str, reason: str) -> bool:
        """Cancel execution."""
        execution = self.get_execution_state(execution_id)
        if not execution:
            return False

        execution.cancel(reason)
        self.persist_execution_state(execution)
        return True

    def fail_execution(
        self,
        execution_id: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark execution as failed."""
        execution = self.get_execution_state(execution_id)
        if not execution:
            return False

        execution.mark_failed(error_message)
        if metadata:
            execution.context_data.update(metadata)

        self.persist_execution_state(execution)
        return True

    def complete_execution(
        self,
        execution_id: str,
        final_results: Dict[str, Any]
    ) -> bool:
        """Mark execution as completed."""
        execution = self.get_execution_state(execution_id)
        if not execution:
            return False

        execution.mark_completed()
        execution.context_data["final_results"] = final_results

        self.persist_execution_state(execution)
        return True

    def get_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Get execution state."""
        return self.workflow_service._get_execution_state(execution_id)

    def persist_execution_state(self, execution: WorkflowExecutionStateModel) -> None:
        """Persist execution state."""
        self.workflow_service.persist_execution_state(execution)

    def recover_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Recover execution state."""
        return self.workflow_service.recover_workflow_execution(execution_id)

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status."""
        return self.workflow_service.get_workflow_execution_status(execution_id)

    # ========== EVENT DISPATCHING ==========

    async def emit_workflow_started(
        self,
        execution: WorkflowExecutionStateModel,
        workflow_definition: Dict[str, Any]
    ) -> None:
        """Emit workflow started event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_STARTED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "workflow_id": execution.workflow_id,
                    "workflow_name": workflow_definition.get("name", "Unknown"),
                    "total_steps": execution.total_steps,
                    "started_at": execution.started_at
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow started event",
                        execution_id=execution.execution_id,
                        error=str(e))

    async def emit_workflow_step_completed(
        self,
        execution: WorkflowExecutionStateModel,
        step_index: int,
        step_result: Dict[str, Any]
    ) -> None:
        """Emit workflow step completed event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_STEP_COMPLETED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "step_index": step_index,
                    "step_result": step_result,
                    "current_step": execution.current_step_index,
                    "total_steps": execution.total_steps
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow step completed event",
                        execution_id=execution.execution_id,
                        step_index=step_index,
                        error=str(e))

    async def emit_workflow_paused(
        self,
        execution: WorkflowExecutionStateModel,
        reason: str
    ) -> None:
        """Emit workflow paused event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_PAUSED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "reason": reason,
                    "current_step": execution.current_step_index,
                    "paused_at": datetime.now(timezone.utc).isoformat()
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow paused event",
                        execution_id=execution.execution_id,
                        error=str(e))

    async def emit_workflow_resumed(
        self,
        execution: WorkflowExecutionStateModel
    ) -> None:
        """Emit workflow resumed event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_RESUMED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "current_step": execution.current_step_index,
                    "resumed_at": datetime.now(timezone.utc).isoformat()
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow resumed event",
                        execution_id=execution.execution_id,
                        error=str(e))

    async def emit_workflow_completed(
        self,
        execution: WorkflowExecutionStateModel,
        final_results: Dict[str, Any]
    ) -> None:
        """Emit workflow completed event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_COMPLETED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "final_results": final_results,
                    "completed_at": execution.completed_at,
                    "total_steps": execution.total_steps
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow completed event",
                        execution_id=execution.execution_id,
                        error=str(e))

    async def emit_workflow_failed(
        self,
        execution: WorkflowExecutionStateModel,
        error_message: str
    ) -> None:
        """Emit workflow failed event."""
        try:
            event = WebSocketEvent(
                type=EventType.WORKFLOW_FAILED,
                project_id=UUID(execution.project_id),
                data={
                    "execution_id": execution.execution_id,
                    "error_message": error_message,
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                    "current_step": execution.current_step_index
                }
            )

            await websocket_manager.broadcast_to_project(
                UUID(execution.project_id),
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit workflow failed event",
                        execution_id=execution.execution_id,
                        error=str(e))

    async def emit_hitl_triggered(
        self,
        project_id: UUID,
        execution_id: str,
        hitl_request_id: UUID,
        reason: str
    ) -> None:
        """Emit HITL triggered event."""
        try:
            event = WebSocketEvent(
                type=EventType.HITL_REQUEST_CREATED,
                project_id=project_id,
                data={
                    "execution_id": execution_id,
                    "hitl_request_id": str(hitl_request_id),
                    "reason": reason,
                    "triggered_at": datetime.now(timezone.utc).isoformat()
                }
            )

            await websocket_manager.broadcast_to_project(
                project_id,
                event.model_dump()
            )

        except Exception as e:
            logger.error("Failed to emit HITL triggered event",
                        execution_id=execution_id,
                        hitl_request_id=str(hitl_request_id),
                        error=str(e))

    # ========== SDLC ORCHESTRATION ==========

    async def execute_sdlc_workflow(
        self,
        project_id: UUID,
        requirements: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute SDLC workflow."""
        return await self.start_workflow_execution(
            workflow_id="greenfield-fullstack",
            project_id=project_id,
            context_data={"requirements": requirements},
            execution_id=execution_id
        )

    def get_sdlc_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get SDLC workflow status."""
        return self.get_workflow_execution_status(execution_id)

    # ========== AGENT HANDOFF GENERATION ==========

    async def generate_agent_handoff(
        self,
        execution_id: str,
        from_agent: str,
        to_agent: str,
        task_description: str,
        context_artifacts: List[UUID],
        metadata: Optional[Dict[str, Any]] = None
    ) -> HandoffSchema:
        """Generate agent handoff for workflow step."""
        execution = self.get_execution_state(execution_id)
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
            project_id=UUID(execution.project_id),
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

    # ========== PRIVATE HELPER METHODS ==========

    async def _execute_workflow_steps(self, execution: WorkflowExecutionStateModel) -> Dict[str, Any]:
        """Execute all workflow steps sequentially."""
        try:
            workflow_definition = execution.workflow_definition
            steps = workflow_definition.get("steps", [])

            while (execution.current_step_index < len(steps) and
                   execution.status == WorkflowExecutionState.RUNNING):

                # Check if workflow is paused
                if execution.status == WorkflowExecutionState.PAUSED:
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
                    self.fail_execution(
                        execution.execution_id,
                        error_message,
                        {"failed_step": execution.current_step_index}
                    )

                    execution = self.get_execution_state(execution.execution_id)
                    await self.emit_workflow_failed(
                        execution, error_message
                    )
                    break

                # Refresh execution state
                execution = self.get_execution_state(execution.execution_id)

            # Check if workflow completed successfully
            if (execution.current_step_index >= len(steps) and
                execution.status == WorkflowExecutionState.RUNNING):

                final_results = {
                    "completed_steps": len(execution.step_results),
                    "total_steps": len(steps),
                    "step_results": execution.step_results,
                    "context_data": execution.context_data
                }

                self.complete_execution(execution.execution_id, final_results)
                execution = self.get_execution_state(execution.execution_id)

                await self.emit_workflow_completed(execution, final_results)

                return final_results

            return {
                "status": execution.status.value,
                "completed_steps": len(execution.step_results),
                "total_steps": len(steps)
            }

        except Exception as e:
            logger.error(
                "Failed to execute workflow steps",
                execution_id=execution.execution_id,
                error=str(e)
            )

            self.fail_execution(
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
            hitl_request = await self.check_hitl_triggers_after_step(
                execution, step_result
            )

            if hitl_request:
                # Pause workflow for HITL
                self.pause_execution(
                    execution.execution_id,
                    "HITL approval required"
                )

                # Emit HITL triggered event
                await self.emit_hitl_triggered(
                    UUID(execution.project_id),
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

    def _get_current_agent(self, execution: WorkflowExecutionStateModel) -> str:
        """Get current agent for execution."""
        steps = execution.workflow_definition.get("steps", [])
        if execution.current_step_index < len(steps):
            current_step = steps[execution.current_step_index]
            return current_step.get("agent", "unknown")
        return "completed"