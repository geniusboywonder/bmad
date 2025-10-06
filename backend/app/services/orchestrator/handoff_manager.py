"""Handoff management service - handles agent handoff logic and task transitions."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.task import Task, TaskStatus
from app.models.handoff import HandoffSchema
from app.database.models import TaskDB
from app.agents.adk_executor import ADKAgentExecutor  # ADK-only architecture
from app.services.context_store import ContextStoreService

logger = structlog.get_logger(__name__)


class HandoffManager:
    """Manages agent handoff logic and task transitions."""

    def __init__(self,
                 db: Session,
                 context_store: ContextStoreService):
        self.db = db
        self.context_store = context_store
        # MAF wrapper created per-agent when needed

    def create_task_from_handoff(
        self,
        handoff: HandoffSchema = None,
        project_id: UUID = None,
        handoff_schema: Dict[str, Any] = None
    ) -> Task:
        """Create a task from a HandoffSchema or raw handoff data."""

        if handoff is not None:
            # Original interface - HandoffSchema object
            task = self._create_task_from_handoff_object(handoff)
        elif project_id is not None and handoff_schema is not None:
            # Alternative interface - raw handoff data
            task = self._create_task_from_handoff_data(project_id, handoff_schema)
        else:
            raise ValueError("Either handoff object or (project_id, handoff_schema) must be provided")

        return task

    def _create_task_from_handoff_object(self, handoff: HandoffSchema) -> Task:
        """Create task from HandoffSchema object."""

        # Create the task using AgentCoordinator
        from app.services.orchestrator.agent_coordinator import AgentCoordinator
        agent_coordinator = AgentCoordinator(self.db)

        task = agent_coordinator.create_task(
            project_id=handoff.project_id,
            agent_type=handoff.to_agent,
            instructions=handoff.instructions,
            context_ids=handoff.context_ids
        )

        # Store the handoff metadata with the task - ensure all data is JSON serializable
        handoff_metadata = {
            "handoff_id": str(handoff.handoff_id),
            "from_agent": handoff.from_agent,
            "phase": handoff.phase,
            "expected_outputs": handoff.expected_outputs,
            "metadata": handoff.metadata
        }

        # Update task with handoff metadata
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        if db_task:
            db_task.output = handoff_metadata
            self.db.commit()

        logger.info("Task created from handoff",
                   task_id=task.task_id,
                   handoff_id=handoff.handoff_id,
                   from_agent=handoff.from_agent,
                   to_agent=handoff.to_agent)

        return task

    def _create_task_from_handoff_data(self, project_id: UUID, handoff_schema: Dict[str, Any]) -> Task:
        """Create task from raw handoff data."""

        # Convert context IDs if provided
        context_ids = []
        if handoff_schema.get("context_ids"):
            context_ids = [
                UUID(cid) if isinstance(cid, str) else cid
                for cid in handoff_schema["context_ids"]
            ]

        # Create the task using AgentCoordinator
        from app.services.orchestrator.agent_coordinator import AgentCoordinator
        agent_coordinator = AgentCoordinator(self.db)

        task = agent_coordinator.create_task(
            project_id=project_id,
            agent_type=handoff_schema["to_agent"],
            instructions=handoff_schema.get("task_instructions", handoff_schema.get("instructions", "")),
            context_ids=context_ids
        )

        # For raw handoff schema, store what we have
        handoff_metadata = {
            "handoff_source": "raw_schema",
            "from_agent": handoff_schema.get("from_agent"),
            "to_agent": handoff_schema.get("to_agent"),
            "expected_output": handoff_schema.get("expected_output"),
            "metadata": handoff_schema
        }

        # Update task with handoff metadata
        db_task = self.db.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        if db_task:
            db_task.output = handoff_metadata
            self.db.commit()

        logger.info("Task created from raw handoff schema",
                   task_id=task.task_id,
                   from_agent=handoff_schema.get("from_agent"),
                   to_agent=handoff_schema.get("to_agent"))

        return task

    async def process_task_with_autogen(self, task: Task, handoff: HandoffSchema) -> dict:
        """Process a task using AutoGen with handoff context."""

        logger.info("Processing task with AutoGen",
                   task_id=task.task_id,
                   handoff_id=handoff.handoff_id,
                   from_agent=handoff.from_agent,
                   to_agent=handoff.to_agent)

        try:
            # Get context artifacts for the task
            context_artifacts = []
            for context_id in task.context_ids:
                artifact = self.context_store.get_artifact(context_id)
                if artifact:
                    context_artifacts.append(artifact)

            # Execute task with ADK agent executor
            adk_executor = ADKAgentExecutor(agent_type=handoff.to_agent)
            result = await adk_executor.execute_task(task, handoff, context_artifacts)

            logger.info("Task processed successfully with ADK",
                       task_id=task.task_id,
                       success=result.get("success"))

            return result

        except Exception as e:
            logger.error("Failed to process task with AutoGen",
                        task_id=task.task_id,
                        handoff_id=handoff.handoff_id,
                        error=str(e))
            raise

    def create_handoff_chain(self,
                           project_id: UUID,
                           handoff_chain: List[Dict[str, Any]]) -> List[Task]:
        """Create a chain of handoff tasks."""

        created_tasks = []

        for i, handoff_data in enumerate(handoff_chain):
            try:
                # Add project_id to handoff data
                handoff_data["project_id"] = project_id

                # For chained handoffs, add context from previous task
                if i > 0 and created_tasks:
                    previous_task = created_tasks[-1]
                    if "context_ids" not in handoff_data:
                        handoff_data["context_ids"] = []

                    # Add previous task's output as context
                    handoff_data["context_ids"].extend([str(cid) for cid in previous_task.context_ids])

                # Create task from handoff data
                task = self.create_task_from_handoff(
                    project_id=project_id,
                    handoff_schema=handoff_data
                )

                created_tasks.append(task)

                logger.info("Handoff task created in chain",
                           task_id=task.task_id,
                           chain_position=i,
                           from_agent=handoff_data.get("from_agent"),
                           to_agent=handoff_data.get("to_agent"))

            except Exception as e:
                logger.error("Failed to create handoff task in chain",
                           chain_position=i,
                           handoff_data=handoff_data,
                           error=str(e))
                raise

        logger.info("Handoff chain created",
                   project_id=project_id,
                   total_tasks=len(created_tasks))

        return created_tasks

    def get_handoff_history(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get handoff history for a project."""

        # Get all tasks for the project that have handoff metadata
        db_tasks = self.db.query(TaskDB).filter(
            TaskDB.project_id == project_id,
            TaskDB.output.isnot(None)
        ).all()

        handoff_history = []

        for db_task in db_tasks:
            if db_task.output and isinstance(db_task.output, dict):
                # Check if this task has handoff metadata
                if ("handoff_id" in db_task.output or
                    db_task.output.get("handoff_source") == "raw_schema"):

                    handoff_history.append({
                        "task_id": str(db_task.id),
                        "from_agent": db_task.output.get("from_agent"),
                        "to_agent": db_task.agent_type,
                        "handoff_id": db_task.output.get("handoff_id"),
                        "phase": db_task.output.get("phase"),
                        "status": db_task.status,
                        "created_at": db_task.created_at.isoformat() if db_task.created_at else None,
                        "completed_at": db_task.completed_at.isoformat() if db_task.completed_at else None,
                        "metadata": db_task.output
                    })

        # Sort by creation time
        handoff_history.sort(key=lambda x: x["created_at"] or "")

        return handoff_history

    def validate_handoff_chain(self, handoff_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a handoff chain for consistency."""

        validation_errors = []
        validation_warnings = []

        for i, handoff in enumerate(handoff_chain):
            # Check required fields
            required_fields = ["from_agent", "to_agent", "instructions"]
            for field in required_fields:
                if field not in handoff:
                    validation_errors.append(f"Handoff {i}: Missing required field '{field}'")

            # Check agent sequence consistency
            if i > 0:
                previous_handoff = handoff_chain[i - 1]
                if handoff.get("from_agent") != previous_handoff.get("to_agent"):
                    validation_warnings.append(
                        f"Handoff {i}: from_agent '{handoff.get('from_agent')}' "
                        f"doesn't match previous to_agent '{previous_handoff.get('to_agent')}'"
                    )

        result = {
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "chain_length": len(handoff_chain)
        }

        return result

    def get_active_handoffs(self, project_id: UUID) -> List[Dict[str, Any]]:
        """Get currently active handoffs for a project."""

        # Get working tasks that have handoff metadata
        db_tasks = self.db.query(TaskDB).filter(
            TaskDB.project_id == project_id,
            TaskDB.status == TaskStatus.WORKING,
            TaskDB.output.isnot(None)
        ).all()

        active_handoffs = []

        for db_task in db_tasks:
            if db_task.output and isinstance(db_task.output, dict):
                if ("handoff_id" in db_task.output or
                    db_task.output.get("handoff_source") == "raw_schema"):

                    active_handoffs.append({
                        "task_id": str(db_task.id),
                        "from_agent": db_task.output.get("from_agent"),
                        "to_agent": db_task.agent_type,
                        "handoff_id": db_task.output.get("handoff_id"),
                        "started_at": db_task.started_at.isoformat() if db_task.started_at else None,
                        "instructions": db_task.instructions
                    })

        return active_handoffs

    def cancel_handoff(self, task_id: UUID, reason: str) -> bool:
        """Cancel an active handoff."""

        try:
            db_task = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()

            if not db_task:
                logger.error("Task not found for handoff cancellation", task_id=task_id)
                return False

            if db_task.status not in [TaskStatus.PENDING, TaskStatus.WORKING]:
                logger.warning("Cannot cancel handoff - task not in cancellable state",
                             task_id=task_id,
                             status=db_task.status)
                return False

            # Update task status to cancelled
            from app.services.orchestrator.agent_coordinator import AgentCoordinator
            agent_coordinator = AgentCoordinator(self.db)

            agent_coordinator.update_task_status(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
                error_message=f"Handoff cancelled: {reason}"
            )

            logger.info("Handoff cancelled",
                       task_id=task_id,
                       reason=reason)

            return True

        except Exception as e:
            logger.error("Failed to cancel handoff",
                        task_id=task_id,
                        error=str(e))
            return False