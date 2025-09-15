"""WebSocket connection manager with priority notifications."""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta, timezone
import structlog
from enum import Enum

from .events import WebSocketEvent, EventType
from app.database.models import WebSocketNotificationDB
from app.database.connection import get_session

logger = structlog.get_logger(__name__)


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PriorityNotification:
    """Represents a priority notification."""

    def __init__(
        self,
        event: WebSocketEvent,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        expires_at: Optional[datetime] = None,
        max_retries: int = 3
    ):
        self.event = event
        self.priority = priority
        self.expires_at = expires_at
        self.max_retries = max_retries
        self.retry_count = 0
        self.created_at = datetime.now(timezone.utc)
        self.delivered_at: Optional[datetime] = None


class WebSocketManager:
    """Manages WebSocket connections and broadcasting with priority notifications."""
    
    def __init__(self):
        # Store active connections by project ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections for global broadcasts
        self.all_connections: Set[WebSocket] = set()
        # Priority notification queues
        self.priority_queues: Dict[str, List[PriorityNotification]] = {
            "CRITICAL": [],
            "HIGH": [],
            "NORMAL": [],
            "LOW": []
        }
        # Notification delivery tracking
        self.pending_notifications: Dict[str, PriorityNotification] = {}
    
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

    async def broadcast_event(self, event: WebSocketEvent):
        """Broadcast an event to appropriate connections based on project_id."""
        if event.project_id:
            # Broadcast to project-specific connections
            await self.broadcast_to_project(event, str(event.project_id))
        else:
            # Broadcast globally if no project_id
            await self.broadcast_global(event)
    
    def get_connection_count(self, project_id: str = None) -> int:
        """Get the number of active connections."""
        if project_id:
            return len(self.active_connections.get(project_id, set()))
        return len(self.all_connections)

    async def send_priority_notification(
        self,
        event: WebSocketEvent,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        project_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        max_retries: int = 3
    ) -> str:
        """Send a priority notification with guaranteed delivery."""

        notification = PriorityNotification(
            event=event,
            priority=priority,
            expires_at=expires_at,
            max_retries=max_retries
        )

        notification_id = f"{priority.value}_{event.event_type}_{datetime.now(timezone.utc).timestamp()}"

        # Add to appropriate priority queue
        self.priority_queues[priority.value].append(notification)
        self.pending_notifications[notification_id] = notification

        # Persist notification for guaranteed delivery
        await self._persist_notification(notification, notification_id, project_id)

        # Attempt immediate delivery
        success = await self._deliver_priority_notification(notification, project_id)

        if success:
            notification.delivered_at = datetime.now(timezone.utc)
            await self._mark_notification_delivered(notification_id)
            logger.info("Priority notification delivered immediately",
                       notification_id=notification_id,
                       priority=priority.value,
                       event_type=event.event_type)
        else:
            # Schedule retry
            asyncio.create_task(self._retry_notification_delivery(notification_id, project_id))

        return notification_id

    async def _deliver_priority_notification(
        self,
        notification: PriorityNotification,
        project_id: Optional[str] = None
    ) -> bool:
        """Deliver a priority notification."""

        try:
            if project_id and project_id in self.active_connections:
                await self.broadcast_to_project(notification.event, project_id)
            else:
                await self.broadcast_global(notification.event)
            return True
        except Exception as e:
            logger.error("Failed to deliver priority notification",
                        error=str(e),
                        event_type=notification.event.event_type)
            return False

    async def _retry_notification_delivery(self, notification_id: str, project_id: Optional[str]):
        """Retry delivery of a failed notification."""

        notification = self.pending_notifications.get(notification_id)
        if not notification:
            return

        # Check if notification has expired
        if notification.expires_at and datetime.now(timezone.utc) > notification.expires_at:
            logger.warning("Notification expired, removing from retry queue",
                          notification_id=notification_id)
            await self._mark_notification_expired(notification_id)
            return

        # Implement exponential backoff
        delay = 2 ** notification.retry_count  # 1s, 2s, 4s, 8s...

        while notification.retry_count < notification.max_retries:
            await asyncio.sleep(delay)

            success = await self._deliver_priority_notification(notification, project_id)
            if success:
                notification.delivered_at = datetime.now(timezone.utc)
                await self._mark_notification_delivered(notification_id)
                logger.info("Priority notification delivered on retry",
                           notification_id=notification_id,
                           retry_count=notification.retry_count,
                           event_type=notification.event.event_type)
                return

            notification.retry_count += 1
            delay = min(delay * 2, 300)  # Cap at 5 minutes

        # Max retries exceeded
        logger.error("Priority notification failed after max retries",
                    notification_id=notification_id,
                    max_retries=notification.max_retries,
                    event_type=notification.event.event_type)

        await self._mark_notification_failed(notification_id)

    async def _persist_notification(
        self,
        notification: PriorityNotification,
        notification_id: str,
        project_id: Optional[str]
    ):
        """Persist notification to database for guaranteed delivery."""

        db = next(get_session())
        try:
            db_notification = WebSocketNotificationDB(
                project_id=project_id,
                event_type=notification.event.event_type.value,
                priority=notification.priority.value,
                title=self._extract_notification_title(notification.event),
                message=self._extract_notification_message(notification.event),
                event_data=notification.event.data,
                expires_at=notification.expires_at,
                delivery_attempts=0
            )

            db.add(db_notification)
            db.commit()
            db.refresh(db_notification)

            logger.debug("Notification persisted to database",
                        notification_id=notification_id,
                        db_id=str(db_notification.id))

        finally:
            db.close()

    def _extract_notification_title(self, event: WebSocketEvent) -> str:
        """Extract a human-readable title from the event."""
        event_type = event.event_type

        if event_type == EventType.HITL_REQUEST_CREATED:
            return "HITL Approval Required"
        elif event_type == EventType.ERROR:
            return "System Error"
        else:
            return f"System Notification: {event_type.value}"

    def _extract_notification_message(self, event: WebSocketEvent) -> str:
        """Extract a human-readable message from the event."""
        if event.data:
            if "approval_id" in event.data:
                return f"Approval request {event.data['approval_id']} requires your attention"
            elif "emergency_stop" in event.data:
                return f"Emergency stop activated: {event.data.get('reason', 'Unknown reason')}"
            elif "recovery_event" in event.data:
                return f"Recovery session {event.data.get('event_type', 'Unknown')} for {event.data.get('agent_type', 'Unknown agent')}"

        return f"System event: {event.event_type.value}"

    async def _mark_notification_delivered(self, notification_id: str):
        """Mark notification as delivered in database."""

        db = next(get_session())
        try:
            # Find notification by event data (since we don't store the ID)
            # This is a simplified approach - in production, you'd store the notification ID
            notifications = db.query(WebSocketNotificationDB).filter(
                WebSocketNotificationDB.delivered == False
            ).order_by(WebSocketNotificationDB.created_at.desc()).limit(10).all()

            for notification in notifications:
                if notification.event_data and "notification_id" in notification.event_data:
                    if notification.event_data["notification_id"] == notification_id:
                        notification.delivered = True
                        notification.delivered_at = datetime.now(timezone.utc)
                        db.commit()
                        break

        finally:
            db.close()

    async def _mark_notification_expired(self, notification_id: str):
        """Mark notification as expired."""

        db = next(get_session())
        try:
            notifications = db.query(WebSocketNotificationDB).filter(
                WebSocketNotificationDB.expired == False
            ).order_by(WebSocketNotificationDB.created_at.desc()).limit(10).all()

            for notification in notifications:
                if notification.event_data and "notification_id" in notification.event_data:
                    if notification.event_data["notification_id"] == notification_id:
                        notification.expired = True
                        db.commit()
                        break

        finally:
            db.close()

    async def _mark_notification_failed(self, notification_id: str):
        """Mark notification as failed after max retries."""

        db = next(get_session())
        try:
            notifications = db.query(WebSocketNotificationDB).filter(
                WebSocketNotificationDB.delivered == False
            ).order_by(WebSocketNotificationDB.created_at.desc()).limit(10).all()

            for notification in notifications:
                if notification.event_data and "notification_id" in notification.event_data:
                    if notification.event_data["notification_id"] == notification_id:
                        notification.delivery_attempts = 999  # Mark as failed
                        db.commit()
                        break

        finally:
            db.close()

    async def get_pending_notifications(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending notifications for a project."""

        db = next(get_session())
        try:
            query = db.query(WebSocketNotificationDB).filter(
                WebSocketNotificationDB.delivered == False,
                WebSocketNotificationDB.expired == False
            )

            if project_id:
                query = query.filter(WebSocketNotificationDB.project_id == project_id)

            notifications = query.order_by(
                WebSocketNotificationDB.priority.desc(),
                WebSocketNotificationDB.created_at.asc()
            ).all()

            return [
                {
                    "id": str(notification.id),
                    "event_type": notification.event_type,
                    "priority": notification.priority,
                    "title": notification.title,
                    "message": notification.message,
                    "created_at": notification.created_at.isoformat(),
                    "expires_at": notification.expires_at.isoformat() if notification.expires_at else None,
                    "delivery_attempts": notification.delivery_attempts
                }
                for notification in notifications
            ]

        finally:
            db.close()

    async def cleanup_expired_notifications(self):
        """Clean up expired notifications from database."""

        db = next(get_session())
        try:
            now = datetime.now(timezone.utc)

            expired_count = db.query(WebSocketNotificationDB).filter(
                WebSocketNotificationDB.expires_at < now,
                WebSocketNotificationDB.expired == False
            ).update({"expired": True})

            logger.info("Cleaned up expired notifications",
                       expired_count=expired_count)

        finally:
            db.close()

    async def broadcast_advanced_event(
        self,
        event_type: EventType,
        project_id: Optional[str],
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        event_data: Optional[Dict[str, Any]] = None,
        expires_in_minutes: Optional[int] = None
    ):
        """Broadcast an advanced event with priority and persistence."""

        # Create WebSocket event
        event = WebSocketEvent(
            event_type=event_type,
            project_id=project_id,
            data={
                "title": title,
                "message": message,
                "priority": priority.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **(event_data or {})
            }
        )

        # Calculate expiration
        expires_at = None
        if expires_in_minutes:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        # Send as priority notification
        notification_id = await self.send_priority_notification(
            event=event,
            priority=priority,
            project_id=project_id,
            expires_at=expires_at
        )

        # Add notification ID to event data for tracking
        event.data["notification_id"] = notification_id

        logger.info("Advanced event broadcasted",
                   event_type=event_type.value,
                   priority=priority.value,
                   project_id=project_id,
                   notification_id=notification_id)

        return notification_id


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
