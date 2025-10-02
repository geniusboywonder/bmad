"""
Workflow Service for BMAD Core Template System

This module provides services for loading, executing, and managing workflows
with agent orchestration and handoff management.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from uuid import uuid4, UUID

from ..utils.yaml_parser import YAMLParser, ParserError
from ..models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowExecutionState,
    WorkflowType
)
from ..models.handoff import HandoffSchema
from ..models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Service for managing workflow execution and orchestration.

    This service provides functionality to:
    - Load workflows from YAML files
    - Execute workflows with agent orchestration
    - Manage workflow state and progress
    - Handle agent handoffs and transitions
    - Track workflow execution history
    """

    def __init__(self, workflow_base_path: Optional[Union[str, Path]] = None):
        """
        Initialize the workflow service.

        Args:
            workflow_base_path: Base path for workflow files (defaults to backend/app/workflows)
        """
        self.yaml_parser = YAMLParser()

        if workflow_base_path is None:
            # Default to backend/app/workflows relative to project root
            self.workflow_base_path = Path("backend/app/workflows")
        else:
            self.workflow_base_path = Path(workflow_base_path)

        self._workflow_cache: Dict[str, WorkflowDefinition] = {}
        self._execution_cache: Dict[str, WorkflowExecution] = {}
        self._cache_enabled = True

    def load_workflow(self, workflow_id: str, use_cache: bool = True) -> WorkflowDefinition:
        """
        Load a workflow by its ID.

        Args:
            workflow_id: Unique identifier for the workflow
            use_cache: Whether to use cached workflows

        Returns:
            WorkflowDefinition object

        Raises:
            FileNotFoundError: If workflow file doesn't exist
            ParserError: If workflow parsing fails
        """
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

        # Validate workflow (if method exists - some WorkflowDefinition models may not have it)
        if hasattr(workflow, 'validate_sequence'):
            validation_errors = workflow.validate_sequence()
            if validation_errors:
                logger.warning(f"Workflow validation warnings for '{workflow_id}': {validation_errors}")

        # Cache workflow
        if self._cache_enabled:
            self._workflow_cache[workflow_id] = workflow

        return workflow

    async def get_workflow_definition(self, workflow_id: str) -> WorkflowDefinition:
        """
        Get workflow definition (async alias for load_workflow).
        
        This method provides async compatibility for the execution engine.
        
        Args:
            workflow_id: Unique identifier for the workflow
            
        Returns:
            WorkflowDefinition object
        """
        return self.load_workflow(workflow_id)

    def start_workflow_execution(
        self,
        workflow_id: str,
        project_id: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Start execution of a workflow.

        Args:
            workflow_id: ID of the workflow to execute
            project_id: ID of the project this execution belongs to
            context_data: Additional context data for execution

        Returns:
            WorkflowExecution object representing the started execution

        Raises:
            ValueError: If workflow cannot be started
        """
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

    def get_next_agent(self, execution_id: str) -> Optional[str]:
        """
        Get the next agent in the workflow execution.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            Name of the next agent to execute, or None if workflow is complete
        """
        execution = self._get_execution(execution_id)
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
        """
        Advance the workflow execution to the next step.

        Args:
            execution_id: ID of the workflow execution
            current_agent: Name of the agent that just completed
            result: Result data from the agent's execution
            error_message: Error message if execution failed

        Returns:
            Updated WorkflowExecution object

        Raises:
            ValueError: If execution cannot be advanced
        """
        execution = self._get_execution(execution_id)
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
        """
        Generate a handoff schema for agent transition.

        Args:
            execution_id: ID of the workflow execution
            from_agent: Name of the agent handing off
            to_agent: Name of the agent receiving the handoff
            context_data: Additional context for the handoff

        Returns:
            HandoffSchema object or None if handoff cannot be generated
        """
        try:
            execution = self._get_execution(execution_id)
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

    def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a workflow execution.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            Dictionary with execution status information
        """
        execution = self._get_execution(execution_id)
        if not execution:
            return None

        workflow = self.load_workflow(execution.workflow_id)

        return {
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow_id,
            "project_id": execution.project_id,
            "status": execution.status.value,
            "current_step": execution.current_step,
            "total_steps": len(execution.steps),
            "completed_steps": len([
                step for step in execution.steps
                if step.status == WorkflowExecutionState.COMPLETED
            ]),
            "failed_steps": len([
                step for step in execution.steps
                if step.status == WorkflowExecutionState.FAILED
            ]),
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "error_message": execution.error_message,
            "next_agent": self.get_next_agent(execution_id),
            "workflow_name": workflow.name,
            "workflow_description": workflow.description
        }

    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """
        List all available workflows.

        Returns:
            List of workflow metadata dictionaries
        """
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
        """
        Get metadata for a workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Dictionary with workflow metadata
        """
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

    def validate_workflow_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Validate the current state of a workflow execution.

        Args:
            execution_id: ID of the workflow execution

        Returns:
            Dictionary with validation results
        """
        execution = self._get_execution(execution_id)
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

    def _find_workflow_file(self, workflow_id: str) -> Optional[Path]:
        """
        Find the workflow file for a given workflow ID.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Path to workflow file or None if not found
        """
        # Try different file extensions
        for ext in ['.yaml', '.yml']:
            workflow_file = self.workflow_base_path / f"{workflow_id}{ext}"
            if workflow_file.exists():
                return workflow_file

        return None

    def _get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Get a workflow execution from cache.

        Args:
            execution_id: ID of the execution

        Returns:
            WorkflowExecution object or None if not found
        """
        if self._cache_enabled:
            return self._execution_cache.get(execution_id)
        return None

    def _set_execution(self, execution: WorkflowExecution):
        """
        Store a workflow execution in cache.

        Args:
            execution: WorkflowExecution object to store
        """
        if self._cache_enabled:
            self._execution_cache[execution.execution_id] = execution
