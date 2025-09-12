"""WebSocket connection manager."""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import structlog

from .events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Store active connections by project ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections for global broadcasts
        self.all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, project_id: str = None):
        """Accept a WebSocket connection."""
        await websocket.accept()
        
        if project_id:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)
        
        self.all_connections.add(websocket)
        logger.info("WebSocket connected", project_id=project_id)
    
    def disconnect(self, websocket: WebSocket, project_id: str = None):
        """Remove a WebSocket connection."""
        if project_id and project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        self.all_connections.discard(websocket)
        logger.info("WebSocket disconnected", project_id=project_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)
    
    async def send_event(self, event: WebSocketEvent, websocket: WebSocket):
        """Send a WebSocket event to a specific connection."""
        try:
            await websocket.send_text(event.model_dump_json())
        except WebSocketDisconnect:
            self.disconnect(websocket)
    
    async def broadcast_to_project(self, event: WebSocketEvent, project_id: str):
        """Broadcast an event to all connections for a specific project."""
        if project_id not in self.active_connections:
            return
        
        message = event.model_dump_json()
        disconnected = set()
        
        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket, project_id)
        
        logger.info("Event broadcasted to project", 
                   project_id=project_id, 
                   event_type=event.event_type,
                   connections=len(self.active_connections[project_id]))
    
    async def broadcast_global(self, event: WebSocketEvent):
        """Broadcast an event to all active connections."""
        message = event.model_dump_json()
        disconnected = set()
        
        for websocket in self.all_connections:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)
        
        logger.info("Event broadcasted globally", 
                   event_type=event.event_type,
                   connections=len(self.all_connections))
    
    def get_connection_count(self, project_id: str = None) -> int:
        """Get the number of active connections."""
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return len(self.all_connections)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
