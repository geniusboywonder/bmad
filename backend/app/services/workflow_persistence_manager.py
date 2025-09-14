"""
Workflow Persistence Manager

Handles workflow state persistence and recovery mechanisms.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowExecutionState as ExecutionStateEnum
from app.database.models import WorkflowStateDB
import structlog

logger = structlog.get_logger(__name__)


class WorkflowPersistenceManager:
    """
    Handles workflow state persistence and recovery.

    This class manages the persistence of workflow execution states to the database
    and provides recovery mechanisms for interrupted executions.
    """

    def __init__(self, db: Session):
        self.db = db

    def persist_execution_state(self, execution: WorkflowExecutionStateModel) -> None:
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
                db_state.updated_at = datetime.utcnow()
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

            logger.info("Workflow execution recovered", execution_id=execution_id)
            return execution

        except Exception as e:
            logger.error("Failed to recover workflow execution",
                        execution_id=execution_id,
                        error=str(e))
            return None

    def get_execution_state(self, execution_id: str, cache: Optional[dict] = None) -> Optional[WorkflowExecutionStateModel]:
        """Get execution state from cache or recover from database."""
        # Check cache first if provided
        if cache and execution_id in cache:
            return cache[execution_id]

        # Try to recover from database
        return self.recover_workflow_execution(execution_id)

    def cleanup_old_executions(self, days_old: int = 30) -> int:
        """
        Clean up old workflow executions.

        Args:
            days_old: Remove executions older than this many days

        Returns:
            Number of executions cleaned up
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            deleted_count = self.db.query(WorkflowStateDB).filter(
                WorkflowStateDB.created_at < cutoff_date,
                WorkflowStateDB.status.in_(["completed", "failed", "cancelled"])
            ).delete()

            if deleted_count > 0:
                self.db.commit()

            logger.info("Cleaned up old workflow executions",
                       deleted_count=deleted_count,
                       days_old=days_old)

            return deleted_count

        except Exception as e:
            logger.error("Failed to cleanup old workflow executions", error=str(e))
            self.db.rollback()
            return 0

    def get_execution_statistics(self, project_id: Optional[str] = None) -> dict:
        """
        Get workflow execution statistics.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            Dictionary with execution statistics
        """
        try:
            query = self.db.query(WorkflowStateDB)

            if project_id:
                query = query.filter(WorkflowStateDB.project_id == UUID(project_id))

            total_executions = query.count()
            completed_executions = query.filter(WorkflowStateDB.status == "completed").count()
            failed_executions = query.filter(WorkflowStateDB.status == "failed").count()
            running_executions = query.filter(WorkflowStateDB.status == "running").count()
            paused_executions = query.filter(WorkflowStateDB.status == "paused").count()

            return {
                "total_executions": total_executions,
                "completed_executions": completed_executions,
                "failed_executions": failed_executions,
                "running_executions": running_executions,
                "paused_executions": paused_executions,
                "success_rate": (completed_executions / total_executions) if total_executions > 0 else 0
            }

        except Exception as e:
            logger.error("Failed to get execution statistics", error=str(e))
            return {
                "total_executions": 0,
                "completed_executions": 0,
                "failed_executions": 0,
                "running_executions": 0,
                "paused_executions": 0,
                "success_rate": 0
            }
