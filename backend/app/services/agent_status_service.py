"""Agent status service for managing real-time agent status updates."""

from typing import Dict, List, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
import structlog

from app.models.agent import AgentType, AgentStatus, AgentStatusModel
from app.database.models import AgentStatusDB
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class AgentStatusService:
    """Service for managing agent status and broadcasting updates."""
    
    def __init__(self):
        """Initialize the agent status service."""
        self._status_cache: Dict[AgentType, AgentStatusModel] = {}
        self._initialize_default_statuses()
    
    def _initialize_default_statuses(self):
        """Initialize all agents with idle status."""
        for agent_type in AgentType:
            self._status_cache[agent_type] = AgentStatusModel(
                agent_type=agent_type,
                status=AgentStatus.IDLE,
                last_activity=datetime.utcnow()
            )
    
    async def update_agent_status(
        self,
        agent_type: AgentType,
        status: AgentStatus,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        error_message: Optional[str] = None,
        db: Optional[Session] = None
    ) -> AgentStatusModel:
        """Update agent status and broadcast to WebSocket clients."""
        
        logger.info("Updating agent status",
                   agent_type=agent_type,
                   status=status,
                   task_id=task_id,
                   project_id=project_id)
        
        # Create updated status model
        agent_status = AgentStatusModel(
            agent_type=agent_type,
            status=status,
            current_task_id=task_id,
            last_activity=datetime.utcnow(),
            error_message=error_message
        )
        
        # Update cache
        self._status_cache[agent_type] = agent_status
        
        # Persist to database if session provided
        if db:
            await self._persist_status(agent_status, project_id, db)
        
        # Broadcast status change via WebSocket
        await self._broadcast_status_change(agent_status, project_id)
        
        return agent_status
    
    async def _persist_status(
        self,
        agent_status: AgentStatusModel,
        project_id: Optional[UUID],
        db: Session
    ):
        """Persist agent status to database."""
        
        try:
            # Find or create agent status record
            db_status = db.query(AgentStatusDB).filter(
                AgentStatusDB.agent_type == agent_status.agent_type
            ).first()
            
            if not db_status:
                db_status = AgentStatusDB(
                    agent_type=agent_status.agent_type,
                    status=agent_status.status,
                    current_task_id=agent_status.current_task_id,
                    last_activity=agent_status.last_activity,
                    error_message=agent_status.error_message
                )
                db.add(db_status)
            else:
                db_status.status = agent_status.status
                db_status.current_task_id = agent_status.current_task_id
                db_status.last_activity = agent_status.last_activity
                db_status.error_message = agent_status.error_message
            
            db.commit()
            
        except Exception as e:
            logger.error("Failed to persist agent status",
                        agent_type=agent_status.agent_type,
                        error=str(e),
                        exc_info=True)
            db.rollback()
    
    async def _broadcast_status_change(
        self,
        agent_status: AgentStatusModel,
        project_id: Optional[UUID]
    ):
        """Broadcast agent status change via WebSocket."""
        
        event_data = {
            "agent_type": agent_status.agent_type,
            "status": agent_status.status,
            "current_task_id": str(agent_status.current_task_id) if agent_status.current_task_id else None,
            "last_activity": agent_status.last_activity.isoformat(),
            "error_message": agent_status.error_message
        }
        
        event = WebSocketEvent(
            event_type=EventType.AGENT_STATUS_CHANGE,
            project_id=project_id,
            agent_type=agent_status.agent_type,
            data=event_data
        )
        
        try:
            if project_id:
                await websocket_manager.broadcast_to_project(event, str(project_id))
            else:
                await websocket_manager.broadcast_global(event)
                
            logger.info("Agent status broadcast sent",
                       agent_type=agent_status.agent_type,
                       status=agent_status.status,
                       project_id=project_id)
                       
        except Exception as e:
            logger.error("Failed to broadcast agent status",
                        agent_type=agent_status.agent_type,
                        error=str(e),
                        exc_info=True)
    
    def get_agent_status(self, agent_type: AgentType) -> Optional[AgentStatusModel]:
        """Get current status of a specific agent."""
        return self._status_cache.get(agent_type)
    
    def get_all_agent_statuses(self) -> Dict[AgentType, AgentStatusModel]:
        """Get current status of all agents."""
        return self._status_cache.copy()
    
    async def set_agent_working(
        self,
        agent_type: AgentType,
        task_id: UUID,
        project_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> AgentStatusModel:
        """Set agent status to working on a specific task."""
        return await self.update_agent_status(
            agent_type=agent_type,
            status=AgentStatus.WORKING,
            project_id=project_id,
            task_id=task_id,
            db=db
        )
    
    async def set_agent_idle(
        self,
        agent_type: AgentType,
        project_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> AgentStatusModel:
        """Set agent status to idle."""
        return await self.update_agent_status(
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            project_id=project_id,
            task_id=None,
            db=db
        )
    
    async def set_agent_waiting_for_hitl(
        self,
        agent_type: AgentType,
        task_id: UUID,
        project_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> AgentStatusModel:
        """Set agent status to waiting for human-in-the-loop."""
        return await self.update_agent_status(
            agent_type=agent_type,
            status=AgentStatus.WAITING_FOR_HITL,
            project_id=project_id,
            task_id=task_id,
            db=db
        )
    
    async def set_agent_error(
        self,
        agent_type: AgentType,
        error_message: str,
        task_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        db: Optional[Session] = None
    ) -> AgentStatusModel:
        """Set agent status to error with error message."""
        return await self.update_agent_status(
            agent_type=agent_type,
            status=AgentStatus.ERROR,
            project_id=project_id,
            task_id=task_id,
            error_message=error_message,
            db=db
        )


# Global agent status service instance
agent_status_service = AgentStatusService()