"""
Workflow State Manager - Handles state persistence and recovery.

Responsible for managing workflow execution state, persistence, and recovery operations.
"""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import structlog

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowExecutionState
from app.services.workflow_persistence_manager import WorkflowPersistenceManager

logger = structlog.get_logger(__name__)


class StateManager:
    """
    Manages workflow execution state persistence and recovery.

    Follows Single Responsibility Principle by focusing solely on state management.
    """

    def __init__(self, db: Session):
        self.db = db
        self.persistence_manager = WorkflowPersistenceManager(db)

    def get_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """
        Get workflow execution state by ID.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            Workflow execution state or None if not found
        """
        return self.persistence_manager.get_execution_state(execution_id)

    def persist_execution_state(self, execution: WorkflowExecutionStateModel) -> None:
        """
        Persist workflow execution state to database.

        Args:
            execution: Workflow execution state to persist
        """
        try:
            # Convert UUIDs to strings for JSON serialization
            execution_data = execution.model_dump()
            execution_data = self._convert_uuids_to_strings(execution_data)

            # Update the execution object with converted data
            execution.current_step_index = execution_data["current_step_index"]
            execution.context_data = execution_data["context_data"]
            execution.step_results = execution_data["step_results"]
            execution.metadata = execution_data["metadata"]

            self.persistence_manager.save_execution_state(execution)

            logger.info(
                "Persisted workflow execution state",
                execution_id=execution.execution_id,
                state=execution.state.value,
                current_step=execution.current_step_index
            )

        except Exception as e:
            logger.error(
                "Failed to persist workflow execution state",
                execution_id=execution.execution_id,
                error=str(e)
            )
            raise

    def create_execution_state(
        self,
        execution_id: str,
        workflow_id: str,
        project_id: UUID,
        workflow_definition: Dict[str, Any],
        initial_context: Dict[str, Any]
    ) -> WorkflowExecutionStateModel:
        """
        Create new workflow execution state.

        Args:
            execution_id: Unique execution identifier
            workflow_id: Workflow definition identifier
            project_id: Project identifier
            workflow_definition: Workflow definition
            initial_context: Initial context data

        Returns:
            Created workflow execution state
        """
        execution = WorkflowExecutionStateModel(
            execution_id=execution_id,
            workflow_id=workflow_id,
            project_id=project_id,
            state=WorkflowExecutionState.PENDING,
            current_step_index=0,
            workflow_definition=workflow_definition,
            context_data=initial_context or {},
            step_results=[],
            started_at=datetime.now(timezone.utc),
            metadata={}
        )

        self.persist_execution_state(execution)

        logger.info(
            "Created workflow execution state",
            execution_id=execution_id,
            workflow_id=workflow_id,
            project_id=str(project_id)
        )

        return execution

    def update_execution_state(
        self,
        execution_id: str,
        state: Optional[WorkflowExecutionState] = None,
        current_step_index: Optional[int] = None,
        context_data: Optional[Dict[str, Any]] = None,
        step_results: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecutionStateModel]:
        """
        Update workflow execution state.

        Args:
            execution_id: Workflow execution identifier
            state: New workflow state
            current_step_index: New current step index
            context_data: Updated context data
            step_results: Updated step results
            metadata: Updated metadata

        Returns:
            Updated workflow execution state or None if not found
        """
        execution = self.get_execution_state(execution_id)
        if not execution:
            logger.warning("Workflow execution not found", execution_id=execution_id)
            return None

        # Update fields if provided
        if state is not None:
            execution.state = state
        if current_step_index is not None:
            execution.current_step_index = current_step_index
        if context_data is not None:
            execution.context_data.update(context_data)
        if step_results is not None:
            execution.step_results = step_results
        if metadata is not None:
            execution.metadata.update(metadata)

        # Update timestamps
        execution.updated_at = datetime.now(timezone.utc)
        if state == WorkflowExecutionState.COMPLETED:
            execution.completed_at = datetime.now(timezone.utc)
        elif state == WorkflowExecutionState.FAILED:
            execution.failed_at = datetime.now(timezone.utc)

        self.persist_execution_state(execution)

        logger.info(
            "Updated workflow execution state",
            execution_id=execution_id,
            new_state=state.value if state else "unchanged",
            new_step_index=current_step_index
        )

        return execution

    def recover_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """
        Recover workflow execution state from persistence.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            Recovered workflow execution state or None if not found
        """
        try:
            execution = self.persistence_manager.get_execution_state(execution_id)
            if execution:
                logger.info(
                    "Recovered workflow execution state",
                    execution_id=execution_id,
                    state=execution.state.value,
                    current_step=execution.current_step_index
                )
            return execution

        except Exception as e:
            logger.error(
                "Failed to recover workflow execution state",
                execution_id=execution_id,
                error=str(e)
            )
            return None

    def pause_execution(self, execution_id: str, reason: str) -> bool:
        """
        Pause workflow execution.

        Args:
            execution_id: Workflow execution identifier
            reason: Reason for pausing

        Returns:
            True if successfully paused, False otherwise
        """
        execution = self.update_execution_state(
            execution_id,
            state=WorkflowExecutionState.PAUSED,
            metadata={"pause_reason": reason, "paused_at": datetime.now(timezone.utc).isoformat()}
        )

        if execution:
            logger.info(
                "Paused workflow execution",
                execution_id=execution_id,
                reason=reason
            )
            return True

        return False

    def resume_execution(self, execution_id: str) -> bool:
        """
        Resume paused workflow execution.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            True if successfully resumed, False otherwise
        """
        execution = self.get_execution_state(execution_id)
        if not execution or execution.state != WorkflowExecutionState.PAUSED:
            logger.warning(
                "Cannot resume workflow execution",
                execution_id=execution_id,
                current_state=execution.state.value if execution else "not_found"
            )
            return False

        updated_execution = self.update_execution_state(
            execution_id,
            state=WorkflowExecutionState.RUNNING,
            metadata={"resumed_at": datetime.now(timezone.utc).isoformat()}
        )

        if updated_execution:
            logger.info(
                "Resumed workflow execution",
                execution_id=execution_id
            )
            return True

        return False

    def cancel_execution(self, execution_id: str, reason: str) -> bool:
        """
        Cancel workflow execution.

        Args:
            execution_id: Workflow execution identifier
            reason: Reason for cancellation

        Returns:
            True if successfully cancelled, False otherwise
        """
        execution = self.update_execution_state(
            execution_id,
            state=WorkflowExecutionState.CANCELLED,
            metadata={
                "cancel_reason": reason,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }
        )

        if execution:
            logger.info(
                "Cancelled workflow execution",
                execution_id=execution_id,
                reason=reason
            )
            return True

        return False

    def complete_execution(self, execution_id: str, final_results: Dict[str, Any]) -> bool:
        """
        Mark workflow execution as completed.

        Args:
            execution_id: Workflow execution identifier
            final_results: Final execution results

        Returns:
            True if successfully completed, False otherwise
        """
        execution = self.update_execution_state(
            execution_id,
            state=WorkflowExecutionState.COMPLETED,
            metadata={
                "final_results": final_results,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        )

        if execution:
            logger.info(
                "Completed workflow execution",
                execution_id=execution_id
            )
            return True

        return False

    def fail_execution(self, execution_id: str, error_message: str, error_details: Dict[str, Any] = None) -> bool:
        """
        Mark workflow execution as failed.

        Args:
            execution_id: Workflow execution identifier
            error_message: Error message
            error_details: Additional error details

        Returns:
            True if successfully marked as failed, False otherwise
        """
        execution = self.update_execution_state(
            execution_id,
            state=WorkflowExecutionState.FAILED,
            metadata={
                "error_message": error_message,
                "error_details": error_details or {},
                "failed_at": datetime.now(timezone.utc).isoformat()
            }
        )

        if execution:
            logger.error(
                "Failed workflow execution",
                execution_id=execution_id,
                error_message=error_message
            )
            return True

        return False

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow execution status summary.

        Args:
            execution_id: Workflow execution identifier

        Returns:
            Status summary dictionary or None if not found
        """
        execution = self.get_execution_state(execution_id)
        if not execution:
            return None

        total_steps = len(execution.workflow_definition.get("steps", []))
        completed_steps = len(execution.step_results)

        return {
            "execution_id": execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": str(execution.project_id),
            "state": execution.state.value,
            "current_step_index": execution.current_step_index,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "updated_at": execution.updated_at.isoformat() if execution.updated_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "failed_at": execution.failed_at.isoformat() if execution.failed_at else None,
            "metadata": execution.metadata
        }

    def cleanup_old_executions(self, days_old: int = 30) -> int:
        """
        Clean up old workflow executions.

        Args:
            days_old: Number of days after which executions are considered old

        Returns:
            Number of executions cleaned up
        """
        return self.persistence_manager.cleanup_old_executions(days_old)

    def get_execution_statistics(self, project_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get workflow execution statistics.

        Args:
            project_id: Optional project filter

        Returns:
            Statistics dictionary
        """
        return self.persistence_manager.get_execution_statistics(project_id)

    # Private helper methods

    def _convert_uuids_to_strings(self, data: Any) -> Any:
        """Convert UUID objects to strings for JSON serialization."""
        if isinstance(data, UUID):
            return str(data)
        elif isinstance(data, dict):
            return {key: self._convert_uuids_to_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_uuids_to_strings(item) for item in data]
        else:
            return data