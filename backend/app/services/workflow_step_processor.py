"""
Workflow Step Processor

Handles individual workflow step execution and agent coordination.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowStep
from app.models.workflow_state import WorkflowExecutionStateModel, WorkflowStepExecutionState
from app.models.task import Task, TaskStatus
from app.models.handoff import HandoffSchema
from app.database.models import TaskDB
from app.services.context_store import ContextStoreService
from app.agents.adk_executor import ADKAgentExecutor  # ADK-only architecture
import structlog

logger = structlog.get_logger(__name__)


class WorkflowStepProcessor:
    """
    Handles individual workflow step execution and agent coordination.

    This class manages the execution of individual workflow steps, including:
    - Agent task creation and execution
    - Context artifact management
    - Step result processing
    - Conditional step evaluation
    """

    def __init__(self, db: Session):
        self.db = db
        self.context_store = ContextStoreService(db)
        # MAF wrapper created per-agent when needed

    async def execute_step(
        self,
        execution: WorkflowExecutionStateModel,
        step: WorkflowStepExecutionState,
        workflow_step: WorkflowStep
    ) -> Dict[str, Any]:
        """
        Execute a workflow step.

        Args:
            execution: Workflow execution state
            step: Step execution state
            workflow_step: Workflow step definition

        Returns:
            Dictionary with step execution results
        """
        try:
            logger.info("Executing workflow step",
                       execution_id=execution.execution_id,
                       step_index=step.step_index,
                       agent=step.agent)

            # Mark step as running
            step.status = "running"
            step.started_at = datetime.now(timezone.utc).isoformat()

            # Check conditional execution
            if workflow_step.condition and not self._evaluate_condition(workflow_step.condition, execution.context_data):
                logger.info("Skipping conditional step",
                           execution_id=execution.execution_id,
                           step_index=step.step_index,
                           condition=workflow_step.condition)
                step.status = "completed"
                step.completed_at = datetime.now(timezone.utc).isoformat()
                return {"status": "skipped", "message": "Step condition not met"}

            # Create task for agent
            task = await self._create_agent_task(
                execution.project_id,
                step.agent,
                workflow_step,
                execution.context_data
            )

            # Execute task with AutoGen
            result = await self._execute_agent_task(task, execution)

            # Update step with results
            step.status = "completed"
            step.completed_at = datetime.now(timezone.utc).isoformat()
            step.result = result
            step.task_id = str(task.task_id)

            # Add created artifacts
            if result.get("artifacts"):
                for artifact_id in result["artifacts"]:
                    step.artifacts_created.append(artifact_id)
                    execution.add_artifact(artifact_id)

            # Update context data with step results
            self._update_context_from_step_result(execution, workflow_step, result)

            logger.info("Workflow step completed",
                       execution_id=execution.execution_id,
                       step_index=step.step_index,
                       agent=step.agent)

            return {
                "status": "completed",
                "step_index": step.step_index,
                "agent": step.agent,
                "result": result
            }

        except Exception as e:
            logger.error("Workflow step execution failed",
                        execution_id=execution.execution_id,
                        step_index=step.step_index,
                        agent=step.agent,
                        error=str(e))

            # Mark step as failed
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.now(timezone.utc).isoformat()

            raise ValueError(f"Step execution failed: {str(e)}")

    async def execute_parallel_steps(
        self,
        execution: WorkflowExecutionStateModel,
        step_indices: List[int],
        workflow_steps: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """
        Execute multiple workflow steps in parallel.

        Args:
            execution: Workflow execution state
            step_indices: List of step indices to execute
            workflow_steps: List of workflow step definitions

        Returns:
            Dictionary with parallel execution results
        """
        import asyncio

        logger.info("Executing parallel workflow steps",
                   execution_id=execution.execution_id,
                   step_indices=step_indices)

        # Create tasks for parallel execution
        tasks = []
        for i, step_index in enumerate(step_indices):
            step = execution.steps[step_index]
            workflow_step = workflow_steps[i]
            task = asyncio.create_task(self.execute_step(execution, step, workflow_step))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        success_count = 0
        failure_count = 0
        step_results = {}

        for i, result in enumerate(results):
            step_index = step_indices[i]
            if isinstance(result, Exception):
                failure_count += 1
                step_results[step_index] = {"status": "failed", "error": str(result)}
            else:
                success_count += 1
                step_results[step_index] = result

        logger.info("Parallel workflow steps completed",
                   execution_id=execution.execution_id,
                   success_count=success_count,
                   failure_count=failure_count)

        return {
            "status": "completed" if failure_count == 0 else "partial_failure",
            "success_count": success_count,
            "failure_count": failure_count,
            "step_results": step_results
        }

    def _evaluate_condition(self, condition: str, context_data: Dict[str, Any]) -> bool:
        """Evaluate a conditional expression against context data."""
        try:
            # Simple condition evaluation - can be extended for complex expressions
            if condition.startswith("context."):
                key = condition[8:]  # Remove "context." prefix
                return bool(context_data.get(key))

            # Support for more complex conditions
            if condition == "always_true":
                return True
            elif condition == "always_false":
                return False
            elif condition.startswith("not_empty:"):
                key = condition[9:]  # Remove "not_empty:" prefix
                value = context_data.get(key)
                return value is not None and str(value).strip() != ""
            elif condition.startswith("equals:"):
                # Format: equals:key,value
                parts = condition[7:].split(",", 1)
                if len(parts) == 2:
                    key, expected_value = parts
                    actual_value = context_data.get(key)
                    return str(actual_value) == expected_value

            # Default to True for unrecognized conditions
            return True

        except Exception as e:
            logger.warning("Failed to evaluate condition",
                          condition=condition,
                          error=str(e))
            return False

    async def _create_agent_task(
        self,
        project_id: str,
        agent_type: str,
        workflow_step: WorkflowStep,
        context_data: Dict[str, Any]
    ) -> Task:
        """Create a task for agent execution."""
        # Generate task instructions from workflow step
        instructions = workflow_step.action or f"Execute {workflow_step.agent} task"

        # Create task record
        task_data = {
            "project_id": UUID(project_id),
            "agent_type": agent_type,
            "instructions": instructions,
            "context_ids": []  # Will be populated with relevant artifacts
        }

        db_task = TaskDB(**task_data)
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        # Convert to Pydantic model
        task = Task(
            task_id=db_task.id,
            project_id=db_task.project_id,
            agent_type=db_task.agent_type,
            status=db_task.status,
            context_ids=[UUID(cid) for cid in db_task.context_ids],
            instructions=db_task.instructions,
            output=db_task.output,
            error_message=db_task.error_message,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at,
            started_at=db_task.started_at,
            completed_at=db_task.completed_at
        )

        return task

    async def _execute_agent_task(
        self,
        task: Task,
        execution: WorkflowExecutionStateModel
    ) -> Dict[str, Any]:
        """Execute a task using AutoGen service."""
        # Get context artifacts
        context_artifacts = []
        if task.context_ids:
            context_artifacts = self.context_store.get_artifacts_by_ids(task.context_ids)

        # Create handoff schema for agent coordination
        handoff = HandoffSchema(
            from_agent="orchestrator",
            to_agent=task.agent_type,
            phase=f"workflow_{execution.workflow_id}",
            instructions=task.instructions,
            context_ids=task.context_ids,
            expected_outputs=["task_result"],
            metadata={
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "step_index": execution.current_step
            }
        )

        # Execute with ADK agent executor
        adk_executor = ADKAgentExecutor(agent_type=task.agent_type)
        result = await adk_executor.execute_task(task, handoff, context_artifacts)

        return result

    def _update_context_from_step_result(
        self,
        execution: WorkflowExecutionStateModel,
        workflow_step: WorkflowStep,
        result: Dict[str, Any]
    ) -> None:
        """Update execution context with step results."""
        if workflow_step.creates:
            # Store step output in context
            execution.context_data[workflow_step.creates] = result

        # Update any other context variables from result
        if result.get("context_updates"):
            execution.context_data.update(result["context_updates"])
