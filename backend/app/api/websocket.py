"""WebSocket API endpoints."""

import json
from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog

from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType
from app.services.orchestrator.exceptions import PolicyViolationException


router = APIRouter(tags=["websocket"])
logger = structlog.get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: Optional[str] = Query(None, description="Project ID to subscribe to")
):
    """WebSocket endpoint for real-time communication."""

    await websocket_manager.connect(websocket, project_id)

    try:
        while True:
            # Keep the connection alive and handle incoming messages
            data = await websocket.receive_text()

            # In a real implementation, we would handle different message types
            # For now, we'll just log the received data
            logger.info("WebSocket message received",
                       project_id=project_id,
                       data=data)

            # Parse and echo the message back as proper JSON (for testing)
            try:
                parsed_data = json.loads(data) if data.strip().startswith('{') else {"message": data}
                response = {
                    "type": "echo",
                    "data": parsed_data,
                    "timestamp": datetime.now().isoformat(),
                    "project_id": project_id
                }
                await websocket.send_text(json.dumps(response))
            except Exception as e:
                # Send error response as JSON
                error_response = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "project_id": project_id
                }
                await websocket.send_text(json.dumps(error_response))

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)
        logger.info("WebSocket disconnected", project_id=project_id)
    except Exception as e:
        logger.error("WebSocket error",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        websocket_manager.disconnect(websocket, project_id)


@router.websocket("/ws/{project_id}")
async def websocket_project_endpoint(
    websocket: WebSocket,
    project_id: str
):
    """WebSocket endpoint for project-specific real-time communication."""

    await websocket_manager.connect(websocket, project_id)

    try:
        while True:
            # Keep the connection alive and handle incoming messages
            data = await websocket.receive_text()

            # Handle different message types for agent interaction
            logger.info("WebSocket message received",
                       project_id=project_id,
                       data=data)

            # Parse incoming message
            try:
                parsed_data = json.loads(data) if data.strip().startswith('{') else {"message": data, "type": "chat"}

                # Handle chat messages and start_project messages by creating agent tasks
                if parsed_data.get("type") in ["chat", "chat_message", "start_project"] or "message" in parsed_data:
                    logger.info("🔥 WEBSOCKET DEBUG: Message type matches, processing chat message",
                               message_type=parsed_data.get("type"),
                               project_id=project_id)

                    # Extract message content from various formats
                    if parsed_data.get("type") == "start_project":
                        message_content = parsed_data.get("data", {}).get("brief", data)
                    elif parsed_data.get("type") == "chat_message":
                        message_content = parsed_data.get("data", {}).get("message", data)
                    else:
                        message_content = parsed_data.get("message", data)

                    logger.info("🔥 WEBSOCKET DEBUG: Extracted message content",
                               message_content=message_content,
                               project_id=project_id)

                    # Import orchestrator to create agent task
                    from app.services.orchestrator import OrchestratorService
                    from app.database.connection import get_session

                    # Use generator pattern for proper database session handling
                    logger.info("🔥 WEBSOCKET DEBUG: Getting database session", project_id=project_id)
                    db_gen = get_session()
                    db = next(db_gen)
                    try:
                        logger.info("🔥 WEBSOCKET DEBUG: Creating orchestrator service", project_id=project_id)
                        orchestrator = OrchestratorService(db)

                        # Create agent task for chat message
                        agent_type = parsed_data.get("agent_type", "analyst")  # Default to analyst
                        instructions = f"User chat message: {message_content}"

                        logger.info("🔥 WEBSOCKET DEBUG: Creating task",
                                   agent_type=agent_type,
                                   instructions=instructions,
                                   project_id=project_id)

                        try:
                            # Create task via orchestrator
                            task = orchestrator.create_task(
                                project_id=UUID(project_id),
                                agent_type=agent_type,
                                instructions=instructions,
                                context_ids=[]
                            )

                            logger.info("🔥 WEBSOCKET DEBUG: Task created successfully",
                                       task_id=str(task.task_id),
                                       project_id=project_id)

                            # Submit task for processing
                            task_result = orchestrator.assign_agent_to_task(task)
                            logger.info("🔥 WEBSOCKET DEBUG: Task assignment result",
                                       task_result=task_result,
                                       project_id=project_id)

                            # Send confirmation response
                            response = {
                                "type": "agent_task_created",
                                "data": {
                                    "task_id": str(task.task_id),
                                    "agent_type": agent_type,
                                    "message": f"Created task for {agent_type} agent",
                                    "user_message": message_content,
                                    "celery_task_id": task_result.get("celery_task_id") if task_result and task_result.get("success") else None
                                },
                                "timestamp": datetime.now().isoformat(),
                                "project_id": project_id
                            }

                            # Send response immediately after successful task creation and assignment
                            await websocket.send_text(json.dumps(response))

                        except PolicyViolationException as e:
                            logger.warning(
                                "Policy violation caught in WebSocket",
                                project_id=project_id,
                                agent_type=agent_type,
                                decision=e.decision,
                            )
                            # Broadcast the policy violation event to the frontend
                            event = WebSocketEvent(
                                event_type=EventType.POLICY_VIOLATION,
                                project_id=UUID(project_id),
                                data={
                                    "status": e.decision.status,
                                    "reason_code": e.decision.reason_code,
                                    "message": e.decision.message,
                                    "current_phase": e.decision.current_phase,
                                    "allowed_agents": e.decision.allowed_agents,
                                },
                            )
                            await websocket_manager.broadcast_to_project(UUID(project_id), event)
                        except Exception as e:
                            logger.error("🔥 WEBSOCKET DEBUG: Failed to create agent task",
                                       error=str(e),
                                       exc_info=True,
                                       project_id=project_id)
                            response = {
                                "type": "error",
                                "data": {
                                    "error": f"Failed to create agent task: {str(e)}",
                                    "user_message": message_content
                                },
                                "timestamp": datetime.now().isoformat(),
                                "project_id": project_id
                            }
                            # Send error response
                            await websocket.send_text(json.dumps(response))
                    finally:
                        # Properly close the database session
                        try:
                            next(db_gen)
                        except StopIteration:
                            pass


            except Exception as e:
                # Send error response as JSON
                error_response = {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "project_id": project_id
                }
                await websocket.send_text(json.dumps(error_response))
                return


    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)
        logger.info("WebSocket disconnected", project_id=project_id)
    except Exception as e:
        logger.error("WebSocket error",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        websocket_manager.disconnect(websocket, project_id)
