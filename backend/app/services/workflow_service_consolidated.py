"""
Consolidated Workflow Service - Main workflow management and execution.

Handles workflow loading, execution management, and state persistence.
Consolidates functionality from workflow_service.py, workflow_execution_manager.py, 
and workflow_persistence_manager.py.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from uuid import uuid4, UUID
from sqlalchemy.orm import Session

from ..utils.yaml_parser import YAMLParser, ParserError
from ..models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowExecutionState,
    WorkflowType
)
from ..models.workflow_state import (
    WorkflowExecutionStateModel,
    WorkflowExecutionState as ExecutionStateEnum
)
from ..models.handoff import HandoffSchema
from ..models.task import Task, TaskStatus
from ..database.models import WorkflowStateDB, ProjectDB
import structlog

logger = structlog.get_logger(__name__)


class ConsolidatedWorkflowService:
    """
    Consolidated workflow service handling complete workflow lifecycle.
    
    Combines workflow loading, execution management, and state persistence
    into a single, focused service following SOLID principles.
    """

    def __init__(self, db: Session, workflow_base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the consolidated workflow service.

        Args:
            db: Database session
            workflow_base_path: Base path for workflow files (defaults to backend/app/workflows)
        """
        self.db = db
        self.yaml_parser = YAMLParser()

        if workflow_base_path is None:
            # Default to backend/app/workflows relative to project root
            self.workflow_base_path = Path("backend/app/workflows")
        else:
            self.workflow_base_path = Path(workflow_base_path)

        self._workflow_cache: Dict[str, WorkflowDefinition] = {}
        self._execution_cache: Dict[str, WorkflowExecutionStateModel] = {}
        self._cache_enabled = True

    # ========== WORKFLOW LOADING AND MANAGEMENT ==========

    def load_workflow(self, workflow_id: str, use_cache: bool = True) -> WorkflowDefinition:
        """Load a workflow by its ID."""
        # Check cache first
        if use_cache and self._cache_enabled and workflow_id in self._workflow_cache:
            logger.debug(f"Loading workflow '{workflow_id}' from cache")
            return self._workflow_cache[workflow_id]

        # Find workflow file
        workflow_file = self._find_workflow_file(workflow_id)
        if not workflow_file:
            raise FileNotFoundError(f"Workflow '{workflow_id}' not found")

        # Load and parse workflow
        logger.info(f"Loading workflow '{workflow_id}' from {workflow_file}")
        workflow = self.yaml_parser.load_workflow(workflow_file)

        # Validate workflow (if method exists)
        if hasattr(workflow, 'validate_sequence'):
            validation_errors = workflow.validate_sequence()
            if validation_errors:
                logger.warning(f"Workflow validation warnings for '{workflow_id}': {validation_errors}")

        # Cache workflow
        if self._cache_enabled:
            self._workflow_cache[workflow_id] = workflow

        return workflow

    async def get_workflow_definition(self, workflow_id: str) -> WorkflowDefinition:
        """Get workflow definition (async alias for load_workflow)."""
        return self.load_workflow(workflow_id)

    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        workflows = []

        try:
            if self.workflow_base_path.exists():
                for workflow_file in self.workflow_base_path.glob("*.yaml"):
                    try:
                        workflow_id = workflow_file.stem
                        workflow = self.load_workflow(workflow_id)
                        workflows.append({
                            "id": workflow.id,
                            "name": workflow.name,
                            "description": workflow.description,
                            "type": workflow.type.value,
                            "project_types": workflow.project_types,
                            "steps_count": len(workflow.sequence),
                            "agents": list(set(step.agent for step in workflow.sequence))
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load workflow '{workflow_file}': {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")

        return workflows

    def get_workflow_metadata(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a workflow."""
        try:
            workflow = self.load_workflow(workflow_id)

            return {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "type": workflow.type.value,
                "project_types": workflow.project_types,
                "steps_count": len(workflow.sequence),
                "agents": list(set(step.agent for step in workflow.sequence)),
                "has_flow_diagram": bool(workflow.flow_diagram),
                "has_handoff_prompts": bool(workflow.handoff_prompts),
                "metadata": workflow.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get metadata for workflow '{workflow_id}': {str(e)}")
            return None

    # ========== WORKFLOW EXECUTION MANAGEMENT ==========

    async def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionStateModel:
        """Start execution of a workflow."""
        try:
            logger.info("Starting workflow execution", workflow_id=workflow_id, project_id=project_id)

            # Load workflow definition
            workflow = self.load_workflow(workflow_id)

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
            self.persist_execution_state(execution)

            # Cache active execution
            self._execution_cache[execution.execution_id] = execution

            # Mark as started
            execution.mark_started()
            self.persist_execution_state(execution)

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

    def start_workflow_execution_legacy(
        self,
        workflow_id: str,
        project_id: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Start execution of a workflow (legacy format for backward compatibility)."""
        try:
            # Load workflow
            workflow = self.load_workflow(workflow_id)

            # Create execution instance
            execution_id = str(uuid4())
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                project_id=project_id,
                execution_id=execution_id,
                status=WorkflowExecutionState.PENDING,
                context_data=context_data or {},
                started_at=datetime.now(timezone.utc).isoformat()
            )

            # Initialize execution steps
            execution.steps = []
            for i, step in enumerate(workflow.sequence):
                execution_step = WorkflowExecutionStep(
                    step_index=i,
                    agent=step.agent,
                    status=WorkflowExecutionState.PENDING
                )
                execution.steps.append(execution_step)

            # Cache execution
            if self._cache_enabled:
                self._execution_cache[execution_id] = execution

            logger.info(f"Started workflow execution '{execution_id}' for workflow '{workflow_id}'")
            return execution

        except Exception as e:
            logger.error(f"Failed to start workflow execution for '{workflow_id}': {str(e)}")
            raise ValueError(f"Failed to start workflow execution: {str(e)}")

    async def pause_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """Pause a workflow execution."""
        execution = self._get_execution_state(execution_id)
        if not execution:
            return False

        execution.pause(reason)
        self.persist_execution_state(execution)

        logger.info("Workflow execution paused", execution_id=execution_id, reason=reason)
        return True

    async def resume_workflow_execution(self, execution_id: str) -> bool:
        """Resume a paused workflow execution."""
        execution = self._get_execution_state(execution_id)
        if not execution or not execution.can_resume():
            return False

        execution.resume()
        self.persist_execution_state(execution)

        logger.info("Workflow execution resumed", execution_id=execution_id)
        return True

    async def cancel_workflow_execution(self, execution_id: str, reason: str) -> bool:
        """Cancel a workflow execution."""
        execution = self._get_execution_state(execution_id)
        if not execution:
            return False

        execution.cancel(reason)
        self.persist_execution_state(execution)

        logger.info("Workflow execution cancelled", execution_id=execution_id, reason=reason)
        return True

    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow execution."""
        execution = self._get_execution_state(execution_id)
        if not execution:
            return None

        workflow = self.load_workflow(execution.workflow_id)

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

    # ========== LEGACY WORKFLOW EXECUTION METHODS ==========

    def get_next_agent(self, execution_id: str) -> Optional[str]:
        """Get the next agent in the workflow execution (legacy method)."""
        execution = self._get_execution_legacy(execution_id)
        if not execution:
            return None

        # Find the first pending step
        for step in execution.steps:
            if step.status == WorkflowExecutionState.PENDING:
                return step.agent

        return None

    def advance_workflow_execution(
        self,
        execution_id: str,
        current_agent: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> WorkflowExecution:
        """Advance the workflow execution to the next step (legacy method)."""
        execution = self._get_execution_legacy(execution_id)
        if not execution:
            raise ValueError(f"Execution '{execution_id}' not found")

        # Find and update the current step
        current_step = None
        for step in execution.steps:
            if step.agent == current_agent and step.status == WorkflowExecutionState.RUNNING:
                current_step = step
                break

        if not current_step:
            raise ValueError(f"No running step found for agent '{current_agent}' in execution '{execution_id}'")

        # Update step status
        current_step.completed_at = datetime.now(timezone.utc).isoformat()
        if error_message:
            current_step.status = WorkflowExecutionState.FAILED
            current_step.error_message = error_message
            execution.status = WorkflowExecutionState.FAILED
            execution.error_message = error_message
        else:
            current_step.status = WorkflowExecutionState.COMPLETED
            current_step.result = result

            # Check if all steps are completed
            if all(step.status == WorkflowExecutionState.COMPLETED for step in execution.steps):
                execution.status = WorkflowExecutionState.COMPLETED
                execution.completed_at = datetime.now(timezone.utc).isoformat()

        # Update execution in cache
        if self._cache_enabled:
            self._execution_cache[execution_id] = execution

        logger.info(f"Advanced workflow execution '{execution_id}' for agent '{current_agent}'")
        return execution

    def generate_handoff(
        self,
        execution_id: str,
        from_agent: str,
        to_agent: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> Optional[HandoffSchema]:
        """Generate a handoff schema for agent transition (legacy method)."""
        try:
            execution = self._get_execution_legacy(execution_id)
            if not execution:
                return None

            workflow = self.load_workflow(execution.workflow_id)

            # Get handoff prompt from workflow
            handoff_prompt = workflow.get_handoff_prompt(from_agent, to_agent)
            if not handoff_prompt:
                # Generate a default handoff prompt
                handoff_prompt = f"Please continue the workflow from {from_agent} to {to_agent}."

            # Find the next step in the workflow
            next_step = None
            for step in workflow.sequence:
                if step.agent == to_agent:
                    next_step = step
                    break

            if not next_step:
                return None

            # Create handoff schema
            # Convert project_id to UUID safely
            try:
                if isinstance(execution.project_id, UUID):
                    project_uuid = execution.project_id
                elif isinstance(execution.project_id, str):
                    project_uuid = UUID(execution.project_id)
                else:
                    # Fallback for invalid project_id
                    project_uuid = uuid4()
                    logger.warning(f"Invalid project_id type for execution {execution_id}, using fallback UUID")
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert project_id to UUID for execution {execution_id}: {str(e)}")
                project_uuid = uuid4()

            handoff = HandoffSchema(
                handoff_id=uuid4(),
                from_agent=from_agent,
                to_agent=to_agent,
                project_id=project_uuid,
                phase=f"workflow_{execution.workflow_id}",
                instructions=handoff_prompt,
                context_ids=[],  # Would be populated with actual artifact IDs
                expected_outputs=[next_step.creates] if next_step.creates else [],
                metadata={
                    "execution_id": execution_id,
                    "workflow_id": execution.workflow_id,
                    "step_index": next((
                        i for i, step in enumerate(execution.steps)
                        if step.agent == to_agent
                    ), -1)
                }
            )

            logger.info(f"Generated handoff from '{from_agent}' to '{to_agent}' for execution '{execution_id}'")
            return handoff

        except Exception as e:
            logger.error(f"Failed to generate handoff for execution '{execution_id}': {str(e)}")
            return None

    # ========== STATE PERSISTENCE ==========

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

    def recover_workflow_execution(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Recover a workflow execution from persisted state."""
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
            self._execution_cache[execution_id] = execution

            logger.info("Workflow execution recovered", execution_id=execution_id)
            return execution

        except Exception as e:
            logger.error("Failed to recover workflow execution",
                        execution_id=execution_id,
                        error=str(e))
            return None

    def cleanup_old_executions(self, days_old: int = 30) -> int:
        """Clean up old workflow executions."""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

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
        """Get workflow execution statistics."""
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

    # ========== VALIDATION AND UTILITIES ==========

    def validate_workflow_execution(self, execution_id: str) -> Dict[str, Any]:
        """Validate the current state of a workflow execution."""
        execution = self._get_execution_legacy(execution_id)
        if not execution:
            return {"valid": False, "errors": ["Execution not found"]}

        errors = []
        warnings = []

        try:
            workflow = self.load_workflow(execution.workflow_id)

            # Check step consistency
            for i, step in enumerate(execution.steps):
                if i >= len(workflow.sequence):
                    errors.append(f"Execution has more steps than workflow defines")
                    break

                workflow_step = workflow.sequence[i]
                if step.agent != workflow_step.agent:
                    errors.append(f"Step {i} agent mismatch: execution has '{step.agent}', workflow has '{workflow_step.agent}'")

            # Check for orphaned steps
            if len(execution.steps) > len(workflow.sequence):
                errors.append("Execution has more steps than workflow defines")

            # Check execution state consistency
            completed_steps = [step for step in execution.steps if step.status == WorkflowExecutionState.COMPLETED]
            if completed_steps and not execution.started_at:
                warnings.append("Execution has completed steps but no start time")

            if execution.status == WorkflowExecutionState.COMPLETED and not execution.completed_at:
                warnings.append("Execution is marked completed but has no completion time")

        except Exception as e:
            errors.append(f"Validation failed: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def clear_cache(self):
        """Clear all caches."""
        self._workflow_cache.clear()
        self._execution_cache.clear()
        logger.info("Workflow cache cleared")

    def enable_cache(self, enabled: bool = True):
        """Enable or disable caching."""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        logger.info(f"Workflow cache {'enabled' if enabled else 'disabled'}")

    # ========== PRIVATE HELPER METHODS ==========

    def _find_workflow_file(self, workflow_id: str) -> Optional[Path]:
        """Find the workflow file for a given workflow ID."""
        # Try different file extensions
        for ext in ['.yaml', '.yml']:
            workflow_file = self.workflow_base_path / f"{workflow_id}{ext}"
            if workflow_file.exists():
                return workflow_file

        return None

    def _get_execution_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Get execution state from cache or recover from database."""
        # Check cache first
        if self._cache_enabled and execution_id in self._execution_cache:
            return self._execution_cache[execution_id]

        # Try to recover from database
        return self.recover_workflow_execution(execution_id)

    def _get_execution_legacy(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution from cache (legacy format)."""
        if self._cache_enabled:
            return self._execution_cache.get(execution_id)
        return None

    def _set_execution(self, execution: WorkflowExecution):
        """Store a workflow execution in cache (legacy format)."""
        if self._cache_enabled:
            self._execution_cache[execution.execution_id] = execution