"""Agent task processing with Celery."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from celery import current_task
import structlog
import asyncio
from uuid import UUID

from .celery_app import celery_app
from app.models.task import Task, TaskStatus
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.models.context import ContextArtifact
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
from app.services.autogen_service import AutoGenService
from app.services.context_store import ContextStoreService
from app.database.connection import get_session
from app.database.models import TaskDB

logger = structlog.get_logger(__name__)


def validate_task_data(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize task data input.

    Args:
        task_data: Raw task data dictionary

    Returns:
        Validated and normalized task data

    Raises:
        ValueError: If required fields are missing or invalid
    """
    required_fields = ["task_id", "project_id", "agent_type", "instructions"]

    # Check required fields
    for field in required_fields:
        if field not in task_data or not task_data[field]:
            raise ValueError(f"Missing required field: {field}")

    # Validate UUID format
    try:
        task_uuid = UUID(task_data["task_id"])
    except (ValueError, TypeError):
        raise ValueError(f"Invalid task_id format: {task_data['task_id']}")

    try:
        project_uuid = UUID(task_data["project_id"])
    except (ValueError, TypeError):
        raise ValueError(f"Invalid project_id format: {task_data['project_id']}")

    # Validate context_ids if provided
    context_uuids = []
    if "context_ids" in task_data and task_data["context_ids"]:
        for cid in task_data["context_ids"]:
            try:
                context_uuids.append(UUID(cid))
            except (ValueError, TypeError):
                raise ValueError(f"Invalid context_id format: {cid}")

    return {
        "task_id": task_uuid,
        "project_id": project_uuid,
        "agent_type": task_data["agent_type"],
        "instructions": task_data["instructions"],
        "context_ids": context_uuids,
        "from_agent": task_data.get("from_agent", "orchestrator"),
        "expected_outputs": task_data.get("expected_outputs", ["task_result"]),
        "priority": task_data.get("priority", 1)
    }


@celery_app.task(bind=True, name="app.tasks.agent_tasks.process_agent_task", autoretry_for=(Exception,), retry_kwargs={'max_retries': 5}, retry_backoff=True)
def process_agent_task(self, task_data: Dict[str, Any]):
    """
    Process an agent task asynchronously with real agent execution.

    Args:
        task_data: Dictionary containing task information
    """
    validated_data = validate_task_data(task_data)
    task_uuid = validated_data["task_id"]
    project_uuid = validated_data["project_id"]
    agent_type = validated_data["agent_type"]
    instructions = validated_data["instructions"]
    context_uuids = validated_data["context_ids"]
    from_agent = validated_data["from_agent"]
    expected_outputs = validated_data["expected_outputs"]
    priority = validated_data["priority"]

    logger.info("Starting agent task",
                task_id=str(task_uuid),
                agent_type=agent_type,
                project_id=str(project_uuid))

    with get_session() as db:
        # Update task status to WORKING in database
        task_db = db.query(TaskDB).filter(TaskDB.id == task_uuid).first()
        if task_db:
            task_db.status = TaskStatus.WORKING
            task_db.started_at = datetime.now(timezone.utc)
            db.commit()
            logger.info("Task status updated to WORKING", task_id=str(task_uuid))

        # Emit task started event via WebSocket
        event = WebSocketEvent(
            event_type=EventType.TASK_STARTED,
            project_id=project_uuid,
            task_id=task_uuid,
            agent_type=agent_type,
            data={
                "status": "working",
                "message": f"{agent_type} agent started processing task",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

        # Send WebSocket event asynchronously
        asyncio.run(websocket_manager.broadcast_event(event))
        logger.info("Task started event broadcast", task_id=str(task_uuid))

        # Create Task object for agent processing
        task = Task(
            task_id=task_uuid,
            project_id=project_uuid,
            agent_type=agent_type,
            status=TaskStatus.WORKING,
            instructions=instructions,
            context_ids=context_uuids
        )

        # Create HandoffSchema for agent processing
        handoff = HandoffSchema(
            handoff_id=task_uuid,  # Use task_id as handoff_id for simplicity
            project_id=project_uuid,
            from_agent=from_agent,
            to_agent=agent_type,
            phase="task_execution",
            instructions=instructions,
            context_ids=task.context_ids,
            expected_outputs=expected_outputs,
            priority=priority
        )

        # Initialize services
        autogen_service = AutoGenService()
        context_store = ContextStoreService(db)

        # Get context artifacts
        context_artifacts = []
        if task.context_ids:
            context_artifacts = context_store.get_artifacts_by_ids(task.context_ids)

        # Execute task with real agent processing
        logger.info("Executing task with AutoGen service", task_id=str(task_uuid))
        result = asyncio.run(autogen_service.execute_task(task, handoff, context_artifacts))

        # Update task status based on result
        if result.get("success", False):
            # Update database task status to COMPLETED
            if task_db:
                task_db.status = TaskStatus.COMPLETED
                task_db.output = result
                task_db.completed_at = datetime.now(timezone.utc)
                db.commit()

            # Create output artifact
            output_artifact = context_store.create_artifact(
                project_id=project_uuid,
                source_agent=agent_type,
                artifact_type="agent_output",
                content=result
            )

            # Emit task completed event
            event = WebSocketEvent(
                event_type=EventType.TASK_COMPLETED,
                project_id=project_uuid,
                task_id=task_uuid,
                agent_type=agent_type,
                data={
                    "status": "completed",
                    "output": result,
                    "artifact_id": str(output_artifact.context_id),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            asyncio.run(websocket_manager.broadcast_event(event))
            logger.info("Task completed successfully", task_id=str(task_uuid))

        else:
            # Handle task failure
            error_message = result.get("error", "Unknown error occurred")

            # Update database task status to FAILED
            if task_db:
                task_db.status = TaskStatus.FAILED
                task_db.error_message = error_message
                task_db.completed_at = datetime.now(timezone.utc)
                db.commit()

            # Emit task failed event
            event = WebSocketEvent(
                event_type=EventType.TASK_FAILED,
                project_id=project_uuid,
                task_id=task_uuid,
                agent_type=agent_type,
                data={
                    "status": "failed",
                    "error": error_message,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            asyncio.run(websocket_manager.broadcast_event(event))
            logger.error("Task failed", task_id=str(task_uuid), error=error_message)

            # Re-raise exception to trigger Celery retry
            raise Exception(f"Task execution failed: {error_message}")

        return result
