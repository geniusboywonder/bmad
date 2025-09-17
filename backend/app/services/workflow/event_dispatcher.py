"""
Workflow Event Dispatcher - Handles event management and broadcasting.

Responsible for managing workflow events, WebSocket broadcasting, and event coordination.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.workflow_state import WorkflowExecutionStateModel
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)


class EventDispatcher:
    """
    Manages workflow event dispatching and broadcasting.

    Follows Single Responsibility Principle by focusing solely on event management.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    async def emit_workflow_started(
        self,
        execution: WorkflowExecutionStateModel,
        workflow_definition: Dict[str, Any]
    ) -> None:
        """
        Emit workflow started event.

        Args:
            execution: Workflow execution state
            workflow_definition: Workflow definition
        """
        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "total_steps": len(workflow_definition.get("steps", [])),
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "workflow_name": workflow_definition.get("name", "Unknown Workflow")
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_STARTED,
            execution.project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_started",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "total_steps": event_data["total_steps"]
            }
        )

    async def emit_workflow_step_completed(
        self,
        execution: WorkflowExecutionStateModel,
        step_index: int,
        step_result: Dict[str, Any]
    ) -> None:
        """
        Emit workflow step completed event.

        Args:
            execution: Workflow execution state
            step_index: Index of completed step
            step_result: Step execution result
        """
        total_steps = len(execution.workflow_definition.get("steps", []))
        step_name = execution.workflow_definition.get("steps", [{}])[step_index].get("name", f"Step {step_index + 1}")

        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "step_index": step_index,
            "step_name": step_name,
            "step_result": step_result,
            "total_steps": total_steps,
            "completed_steps": len(execution.step_results),
            "progress_percentage": (len(execution.step_results) / total_steps * 100) if total_steps > 0 else 0,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_STEP_COMPLETED,
            execution.project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_step_completed",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "step_index": step_index,
                "step_name": step_name,
                "step_success": step_result.get("success", False)
            }
        )

    async def emit_workflow_completed(
        self,
        execution: WorkflowExecutionStateModel,
        final_results: Dict[str, Any]
    ) -> None:
        """
        Emit workflow completed event.

        Args:
            execution: Workflow execution state
            final_results: Final workflow results
        """
        total_steps = len(execution.workflow_definition.get("steps", []))
        execution_time = None
        if execution.started_at and execution.completed_at:
            execution_time = (execution.completed_at - execution.started_at).total_seconds()

        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "total_steps": total_steps,
            "completed_steps": len(execution.step_results),
            "final_results": final_results,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time_seconds": execution_time
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_COMPLETED,
            execution.project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_completed",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "execution_time_seconds": execution_time,
                "total_steps": total_steps
            }
        )

    async def emit_workflow_failed(
        self,
        execution: WorkflowExecutionStateModel,
        error_message: str,
        error_details: Dict[str, Any] = None
    ) -> None:
        """
        Emit workflow failed event.

        Args:
            execution: Workflow execution state
            error_message: Error message
            error_details: Additional error details
        """
        total_steps = len(execution.workflow_definition.get("steps", []))

        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "error_message": error_message,
            "error_details": error_details or {},
            "total_steps": total_steps,
            "completed_steps": len(execution.step_results),
            "failed_at_step": execution.current_step_index,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "failed_at": execution.failed_at.isoformat() if execution.failed_at else None
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_FAILED,
            execution.project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_failed",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "error_message": error_message,
                "failed_at_step": execution.current_step_index
            }
        )

    async def emit_workflow_paused(
        self,
        execution: WorkflowExecutionStateModel,
        reason: str
    ) -> None:
        """
        Emit workflow paused event.

        Args:
            execution: Workflow execution state
            reason: Reason for pausing
        """
        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "reason": reason,
            "paused_at_step": execution.current_step_index,
            "paused_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_PAUSED,
            execution.project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_paused",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "reason": reason,
                "paused_at_step": execution.current_step_index
            }
        )

    async def emit_workflow_resumed(
        self,
        execution: WorkflowExecutionStateModel
    ) -> None:
        """
        Emit workflow resumed event.

        Args:
            execution: Workflow execution state
        """
        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "resumed_at_step": execution.current_step_index,
            "resumed_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_EVENT,  # Generic workflow event
            execution.project_id,
            {**event_data, "event_type": "workflow_resumed"}
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_resumed",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "resumed_at_step": execution.current_step_index
            }
        )

    async def emit_sdlc_phase_event(
        self,
        execution: WorkflowExecutionStateModel,
        phase: str,
        phase_results: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> None:
        """
        Emit SDLC phase event.

        Args:
            execution: Workflow execution state
            phase: SDLC phase name
            phase_results: Phase execution results
            metrics: Phase metrics
        """
        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "phase": phase,
            "phase_results": phase_results,
            "metrics": metrics,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_EVENT,  # Generic workflow event
            execution.project_id,
            {**event_data, "event_type": "sdlc_phase_completed"}
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="sdlc_phase_completed",
            project_id=execution.project_id,
            metadata={
                "execution_id": execution.execution_id,
                "phase": phase,
                "metrics": metrics
            }
        )

    async def emit_agent_task_created(
        self,
        project_id: UUID,
        execution_id: str,
        task_id: UUID,
        agent_type: str,
        task_name: str
    ) -> None:
        """
        Emit agent task created event.

        Args:
            project_id: Project identifier
            execution_id: Workflow execution identifier
            task_id: Task identifier
            agent_type: Agent type
            task_name: Task name
        """
        event_data = {
            "execution_id": execution_id,
            "task_id": str(task_id),
            "agent_type": agent_type,
            "task_name": task_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.TASK_STARTED,
            project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_agent_task_created",
            project_id=project_id,
            task_id=task_id,
            metadata={
                "execution_id": execution_id,
                "agent_type": agent_type,
                "task_name": task_name
            }
        )

    async def emit_hitl_triggered(
        self,
        project_id: UUID,
        execution_id: str,
        hitl_request_id: UUID,
        trigger_reason: str
    ) -> None:
        """
        Emit HITL triggered event.

        Args:
            project_id: Project identifier
            execution_id: Workflow execution identifier
            hitl_request_id: HITL request identifier
            trigger_reason: Reason for HITL trigger
        """
        event_data = {
            "execution_id": execution_id,
            "hitl_request_id": str(hitl_request_id),
            "trigger_reason": trigger_reason,
            "triggered_at": datetime.now(timezone.utc).isoformat()
        }

        await self._emit_workflow_event(
            EventType.HITL_REQUEST_CREATED,
            project_id,
            event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="workflow_hitl_triggered",
            project_id=project_id,
            metadata={
                "execution_id": execution_id,
                "hitl_request_id": str(hitl_request_id),
                "trigger_reason": trigger_reason
            }
        )

    # Private helper methods

    async def _emit_workflow_event(
        self,
        event_type: EventType,
        project_id: UUID,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Emit workflow event via WebSocket.

        Args:
            event_type: Type of event
            project_id: Project identifier
            event_data: Event data
        """
        try:
            event = WebSocketEvent(
                type=event_type,
                project_id=project_id,
                data=event_data
            )

            await websocket_manager.broadcast_to_project(
                project_id,
                event.model_dump()
            )

            logger.info(
                "Emitted workflow event",
                event_type=event_type.value,
                project_id=str(project_id),
                execution_id=event_data.get("execution_id")
            )

        except Exception as e:
            logger.error(
                "Failed to emit workflow event",
                event_type=event_type.value,
                project_id=str(project_id),
                error=str(e)
            )

    def create_event_data(
        self,
        execution: WorkflowExecutionStateModel,
        additional_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create standard event data structure.

        Args:
            execution: Workflow execution state
            additional_data: Additional data to include

        Returns:
            Event data dictionary
        """
        event_data = {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "current_step_index": execution.current_step_index,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if additional_data:
            event_data.update(additional_data)

        return event_data

    async def broadcast_custom_event(
        self,
        project_id: UUID,
        event_name: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Broadcast custom workflow event.

        Args:
            project_id: Project identifier
            event_name: Name of the custom event
            event_data: Event data
        """
        custom_event_data = {
            "event_name": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event_data
        }

        await self._emit_workflow_event(
            EventType.WORKFLOW_EVENT,
            project_id,
            custom_event_data
        )

        # Log audit event
        await self.audit_service.log_event(
            event_type="custom_workflow_event",
            project_id=project_id,
            metadata={
                "event_name": event_name,
                "event_data": event_data
            }
        )