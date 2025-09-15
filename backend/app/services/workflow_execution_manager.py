"""
Workflow Execution Manager

Manages workflow execution lifecycle and state transitions for the BMAD Core system.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowDefinition
from app.models.workflow_state import (
    WorkflowExecutionStateModel,
    WorkflowExecutionState as ExecutionStateEnum
)
from app.database.models import WorkflowStateDB, ProjectDB
from app.services.workflow_service import WorkflowService
import structlog

logger = structlog.get_logger(__name__)


class WorkflowExecutionManager:
    """
    Manages workflow execution lifecycle and state transitions.

    This class handles the core workflow execution operations including:
    - Starting new workflow executions
    - Pausing and resuming executions
    - Cancelling executions
    - State persistence and recovery
    """

    def __init__(self, db: Session):
        self.db = db
        self.workflow_service = WorkflowService()
        self._active_executions: Dict[str, WorkflowExecutionStateModel] = {}

    async def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionStateModel:
        """
        Start execution of a workflow.

        Args:
            workflow_id: ID of the workflow to execute
            project_id: ID of the project
            context_data: Initial context data

        Returns:
            WorkflowExecutionStateModel representing the started execution

        Raises:
            ValueError: If workflow cannot be started
        """
        try:
            logger.info("Starting workflow execution", workflow_id=workflow_id, project_id=project_id)

            # Load workflow definition
            workflow = self.workflow_service.load_workflow(workflow_id)

            # Create execution state
            execution = WorkflowExecutionStateModel(
                project_id=project_id,
                workflow_id=workflow_id,
                total_steps=len(workflow.sequence),
                context_data=context_data or {},
                status=ExecutionStateEnum.PENDING
            )

            # Initialize steps
            for i, step in enumerate(workflow.sequence):
                from app.models.workflow_state import WorkflowStepExecutionState
                execution_step = WorkflowStepExecutionState(
                    step_index=i,
                    agent=step.agent
                )
                execution.steps.append(execution_step)

            # Persist execution state
            self._persist_execution_state(execution)

            # Cache active execution
            self._active_executions[execution.execution_id] = execution

            # Mark as started
            execution.mark_started()
            self._persist_execution_state(execution)

            logger.info("Workflow execution started",
                       execution_id=execution.execution_id,
                       workflow_id=workflow_id,
                       total_steps=len(workflow.sequence))

            return execution

        except Exception as e:
            logger.error("Failed to start workflow execution",
                        workflow_id=workflow_id,
                        project_id=project_id,
                        error=str(e))
            raise ValueError(f"Failed to start workflow execution: {str(e)}")

    async def pause_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """
        Pause a workflow execution.

        Args:
            execution_id: ID of the workflow execution
            reason: Reason for pausing

        Returns:
            True if paused successfully
        """
        execution = self._get_execution_state(execution_id)
        if not execution:
            return False

        execution.pause(reason)
        self._persist_execution_state(execution)

        logger.info("Workflow execution paused", execution_id=execution_id, reason=reason)
        return True

    async def resume_workflow_execution(self, execution_id: str) -> bool:
        """
        Resume a paused workflow execution.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            True if resumed successfully
        """
        execution = self._get_execution_state(execution_id)
        if not execution or not execution.can_resume():
            return False

        execution.resume()
        self._persist_execution_state(execution)

        logger.info("Workflow execution resumed", execution_id=execution_id)
        return True

    async def cancel_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """
        Cancel a workflow execution.

        Args:
            execution_id: ID of the workflow execution
            reason: Reason for cancellation

        Returns:
            True if cancelled successfully
        """
        execution = self._get_execution_state(execution_id)
        if not execution:
            return False

        execution.cancel(reason)
        self._persist_execution_state(execution)

        logger.info("Workflow execution cancelled", execution_id=execution_id, reason=reason)
        return True

    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a workflow execution.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            Dictionary with execution status information
        """
        execution = self._get_execution_state(execution_id)
        if not execution:
            return None

        workflow = self.workflow_service.load_workflow(execution.workflow_id)

        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": execution.project_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "total_steps": execution.total_steps,
            "completed_steps": len(execution.get_completed_steps()),
            "pending_steps": len(execution.get_pending_steps()),
            "failed_steps": len(execution.get_failed_steps()),
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "error_message": execution.error_message,
            "workflow_name": workflow.name,
            "workflow_description": workflow.description,
            "can_resume": execution.can_resume(),
            "is_complete": execution.is_complete()
        }

    def recover_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """
        Recover a workflow execution from persisted state.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            Recovered WorkflowExecutionStateModel or None if not found
        """
        try:
            # Load from database
            db_state = self.db.query(WorkflowStateDB).filter(
                WorkflowStateDB.execution_id == execution_id
            ).first()

            if not db_state:
                return None

            # Convert database model to Pydantic model
            execution = WorkflowExecutionStateModel(
                execution_id=db_state.execution_id,
                project_id=str(db_state.project_id),
                workflow_id=db_state.workflow_id,
                status=ExecutionStateEnum(db_state.status),
                current_step=db_state.current_step,
                total_steps=db_state.total_steps,
                steps=db_state.steps_data or [],
                context_data=db_state.context_data or {},
                created_artifacts=db_state.created_artifacts or [],
                error_message=db_state.error_message,
                started_at=db_state.started_at.isoformat() if db_state.started_at else None,
                completed_at=db_state.completed_at.isoformat() if db_state.completed_at else None,
                created_at=db_state.created_at.isoformat(),
                updated_at=db_state.updated_at.isoformat()
            )

            # Cache recovered execution
            self._active_executions[execution_id] = execution

            logger.info("Workflow execution recovered", execution_id=execution_id)
            return execution

        except Exception as e:
            logger.error("Failed to recover workflow execution",
                        execution_id=execution_id,
                        error=str(e))
            return None

    def _get_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Get execution state from cache or recover from database."""
        # Check cache first
        if execution_id in self._active_executions:
            return self._active_executions[execution_id]

        # Try to recover from database
        return self.recover_workflow_execution(execution_id)

    def _persist_execution_state(self, execution: WorkflowExecutionStateModel) -> None:
        """Persist execution state to database."""
        try:
            # Convert to database format
            steps_data = [step.model_dump() for step in execution.steps]

            # Find existing record or create new
            db_state = self.db.query(WorkflowStateDB).filter(
                WorkflowStateDB.execution_id == execution.execution_id
            ).first()

            if db_state:
                # Update existing
                db_state.status = execution.status.value
                db_state.current_step = execution.current_step
                db_state.total_steps = execution.total_steps
                db_state.steps_data = steps_data
                db_state.context_data = execution.context_data
                db_state.created_artifacts = execution.created_artifacts
                db_state.error_message = execution.error_message
                db_state.started_at = datetime.fromisoformat(execution.started_at) if execution.started_at else None
                db_state.completed_at = datetime.fromisoformat(execution.completed_at) if execution.completed_at else None
                db_state.updated_at = datetime.now(timezone.utc)
            else:
                # Create new
                db_state = WorkflowStateDB(
                    project_id=UUID(execution.project_id),
                    workflow_id=execution.workflow_id,
                    execution_id=execution.execution_id,
                    status=execution.status.value,
                    current_step=execution.current_step,
                    total_steps=execution.total_steps,
                    steps_data=steps_data,
                    context_data=execution.context_data,
                    created_artifacts=execution.created_artifacts,
                    error_message=execution.error_message,
                    started_at=datetime.fromisoformat(execution.started_at) if execution.started_at else None,
                    completed_at=datetime.fromisoformat(execution.completed_at) if execution.completed_at else None
                )
                self.db.add(db_state)

            self.db.commit()

        except Exception as e:
            logger.error("Failed to persist execution state",
                        execution_id=execution.execution_id,
                        error=str(e))
            self.db.rollback()
            raise
