"""Agent task processing with Celery."""

from datetime import datetime, timezone, timedelta
import time
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
from app.agents.adk_executor import ADKAgentExecutor  # ADK-only architecture
from app.services.context_store import ContextStoreService
from app.services.hitl_counter_service import HitlCounterService
from app.database.connection import get_session
from app.database.models import TaskDB, HitlAgentApprovalDB

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
        "priority": task_data.get("priority", 1),
        "estimated_tokens": task_data.get("estimated_tokens", 100)
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

    db_gen = get_session()
    db = next(db_gen)
    try:
        # Ensure task exists in database before proceeding
        task_db = db.query(TaskDB).filter(TaskDB.id == task_uuid).first()
        if not task_db:
            # Create task record if it doesn't exist (race condition fix)
            task_db = TaskDB(
                id=task_uuid,
                project_id=project_uuid,
                agent_type=agent_type,
                status=TaskStatus.WORKING,
                instructions=instructions,
                context_ids=context_uuids,
                started_at=datetime.now(timezone.utc)
            )
            db.add(task_db)
            logger.info("Created missing task record", task_id=str(task_uuid))
        else:
            # Update existing task status to WORKING
            task_db.status = TaskStatus.WORKING
            task_db.started_at = datetime.now(timezone.utc)
            logger.info("Updated task status to WORKING", task_id=str(task_uuid))

        db.commit()  # Critical: commit before HITL operations

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
        adk_executor = ADKAgentExecutor(agent_type=agent_type)
        context_store = ContextStoreService(db)

        # Get context artifacts
        context_artifacts = []
        if task.context_ids:
            context_artifacts = context_store.get_artifacts_by_ids(task.context_ids)

        # CRITICAL SECURITY FIX: Use HITL controls for agent execution
        logger.info("Executing task with HITL safety controls", task_id=str(task_uuid))
        
        # Import HITL safety service
        from app.services.hitl_safety_service import HITLSafetyService, AgentExecutionDenied, BudgetLimitExceeded, EmergencyStopActivated
        
        hitl_service = HITLSafetyService()
        
        try:
            # Check for emergency stops
            if asyncio.run(hitl_service._is_emergency_stopped()):
                raise EmergencyStopActivated("Emergency stop is active")
            
            # Check budget limits
            estimated_tokens = validated_data.get("estimated_tokens", 100)
            budget_check = asyncio.run(hitl_service.check_budget_limits(
                project_uuid, agent_type, estimated_tokens
            ))
            if not budget_check.approved:
                raise BudgetLimitExceeded(f"Budget limit exceeded: {budget_check.reason}")
            
            # Check if approval already exists for this task to prevent duplicates
                existing_approval = db.query(HitlAgentApprovalDB).filter(
                    HitlAgentApprovalDB.task_id == task_uuid,
                    HitlAgentApprovalDB.status.in_(["PENDING", "APPROVED"])
                ).first()

                if existing_approval:
                    logger.info("Using existing HITL approval record",
                               task_id=str(task_uuid),
                               approval_id=str(existing_approval.id),
                               status=existing_approval.status)
                    approval_id = existing_approval.id
                    approval_record = existing_approval
                else:
                    # Create pre-execution approval record
                    estimated_cost = float(estimated_tokens * 0.00015)
                    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
                    approval_record = HitlAgentApprovalDB(
                        project_id=project_uuid,
                        task_id=task_uuid,
                        agent_type=agent_type,
                        request_type="PRE_EXECUTION",
                        request_data={
                            "instructions": instructions,
                            "estimated_tokens": estimated_tokens,
                            "context_ids": [str(cid) for cid in context_uuids],
                            "agent_type": agent_type
                        },
                        estimated_tokens=estimated_tokens,
                        estimated_cost=estimated_cost,
                        expires_at=expires_at,
                        status="PENDING"
                    )
                    db.add(approval_record)
                    db.commit()
                    approval_id = approval_record.id
                    logger.info("Created HITL approval record", task_id=str(task_uuid), approval_id=str(approval_id))

                # Broadcast HITL approval request event
                hitl_event = WebSocketEvent(
                    event_type=EventType.HITL_REQUEST_CREATED,
                    project_id=project_uuid,
                    task_id=task_uuid,
                    agent_type=agent_type,
                    data={
                        "approval_id": str(approval_id),
                        "agent_type": agent_type,
                        "request_type": "PRE_EXECUTION",
                        "estimated_tokens": estimated_tokens,
                        "estimated_cost": estimated_cost,
                        "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
                        "request_data": {
                            "instructions": instructions,
                            "estimated_tokens": estimated_tokens,
                            "context_ids": [str(cid) for cid in context_uuids],
                            "agent_type": agent_type
                        },
                        "message": f"HITL approval required for {agent_type} agent execution",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
                asyncio.run(websocket_manager.broadcast_event(hitl_event))
                logger.info("HITL approval request event broadcast", task_id=str(task_uuid), approval_id=str(approval_id))

                # Wait for human approval by polling database
                logger.info("Waiting for HITL pre-execution approval", task_id=str(task_uuid), approval_id=str(approval_id))
                timeout_minutes = 30
                poll_interval = 5
                max_polls = (timeout_minutes * 60) // poll_interval

                for poll_count in range(max_polls):
                    db.refresh(approval_record)
                    if approval_record.status == "APPROVED":
                        approval_granted = True
                        approval_comment = approval_record.user_comment
                        break
                    elif approval_record.status == "REJECTED":
                        approval_granted = False
                        approval_comment = approval_record.user_comment or "Request rejected"
                        break
                    elif approval_record.status == "EXPIRED":
                        approval_granted = False
                        approval_comment = "Request expired"
                        break
                    time.sleep(poll_interval)

            if not approval_granted:
                if approval_comment:
                    raise AgentExecutionDenied(f"Human rejected agent execution: {approval_comment}")
                else:
                    raise AgentExecutionDenied("HITL approval timed out after 30 minutes")

            logger.info("HITL pre-execution approval granted", task_id=str(task_uuid), comment=approval_comment)

            # Execute task with ADK agent executor
            result = asyncio.run(adk_executor.execute_task(task, handoff, context_artifacts))

            # Skip response approval for simple tasks - pre-execution approval is sufficient
            # Response approval would create a duplicate HITL message
            logger.info("Skipping response approval - using pre-execution approval only",
                       task_id=str(task_uuid),
                       pre_execution_approval_id=str(approval_id))

            # Update budget usage
            if result.get("success", False):
                tokens_used = result.get("tokens_used", estimated_tokens)
                asyncio.run(hitl_service.update_budget_usage(
                    project_uuid, agent_type, tokens_used
                ))

        except (AgentExecutionDenied, BudgetLimitExceeded, EmergencyStopActivated) as e:
            logger.error("HITL safety control blocked task execution", task_id=str(task_uuid), error=str(e))
            result = {
                "success": False,
                "agent_type": agent_type,
                "task_id": str(task_uuid),
                "error": str(e),
                "blocked_by_hitl": True,
                "context_used": [str(artifact.context_id) for artifact in context_artifacts]
            }
        except Exception as e:
            logger.error("Unexpected error during HITL-controlled execution", task_id=str(task_uuid), error=str(e))
            result = {
                "success": False,
                "agent_type": agent_type,
                "task_id": str(task_uuid),
                "error": str(e),
                "context_used": [str(artifact.context_id) for artifact in context_artifacts]
            }

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

            # Send agent chat message with the result
            agent_output = result.get("output", "Task completed successfully")
            if isinstance(agent_output, dict):
                agent_output = agent_output.get("message", str(agent_output))

            chat_event = WebSocketEvent(
                event_type=EventType.AGENT_CHAT_MESSAGE,
                project_id=project_uuid,
                task_id=task_uuid,
                agent_type=agent_type,
                data={
                    "agent_type": agent_type,
                    "message": str(agent_output),
                    "message_type": "response",
                    "requires_response": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": str(task_uuid)
                }
            )

            asyncio.run(websocket_manager.broadcast_event(chat_event))
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

    finally:
        # Properly close the database session
        try:
            next(db_gen)
        except StopIteration:
            pass

    return result
