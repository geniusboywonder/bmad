"""WebSocket API endpoints."""

from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import structlog

from app.websocket.manager import websocket_manager

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
            
            # Echo the message back (for testing)
            await websocket_manager.send_personal_message(
                f"Echo: {data}", 
                websocket
            )
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)
        logger.info("WebSocket disconnected", project_id=project_id)
    except Exception as e:
        logger.error("WebSocket error", 
                    project_id=project_id, 
                    error=str(e), 
                    exc_info=True)
        websocket_manager.disconnect(websocket, project_id)
