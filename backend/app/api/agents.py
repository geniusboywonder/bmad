"""Agent status API endpoints."""

from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import structlog

from app.models.agent import AgentType, AgentStatusModel
from app.services.agent_status_service import agent_status_service
from app.database.connection import get_session
from app.database.models import AgentStatusDB

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/status", response_model=Dict[str, AgentStatusModel])
async def get_all_agent_statuses():
    """Get current status of all agents."""
    
    logger.info("Fetching all agent statuses")
    
    statuses = agent_status_service.get_all_agent_statuses()
    
    # Convert AgentType enum keys to strings for JSON serialization
    return {agent_type.value: status for agent_type, status in statuses.items()}


@router.get("/status/{agent_type}", response_model=AgentStatusModel)
async def get_agent_status(agent_type: AgentType):
    """Get current status of a specific agent."""
    
    logger.info("Fetching agent status", agent_type=agent_type)
    
    status = agent_status_service.get_agent_status(agent_type)
    
    if not status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_type} not found"
        )
    
    return status


@router.get("/status-history/{agent_type}")
async def get_agent_status_history(
    agent_type: AgentType,
    db: Session = Depends(get_session)
):
    """Get status history for a specific agent from database."""
    
    logger.info("Fetching agent status history", agent_type=agent_type)
    
    try:
        # Query database for historical agent status
        agent_status_records = db.query(AgentStatusDB).filter(
            AgentStatusDB.agent_type == agent_type
        ).order_by(AgentStatusDB.updated_at.desc()).limit(10).all()
        
        if not agent_status_records:
            return []
        
        return [
            {
                "agent_type": record.agent_type,
                "status": record.status,
                "current_task_id": str(record.current_task_id) if record.current_task_id else None,
                "last_activity": record.last_activity.isoformat(),
                "error_message": record.error_message,
                "updated_at": record.updated_at.isoformat()
            }
            for record in agent_status_records
        ]
        
    except Exception as e:
        logger.error("Failed to fetch agent status history",
                    agent_type=agent_type,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch agent status history"
        )


@router.post("/status/{agent_type}/reset")
async def reset_agent_status(
    agent_type: AgentType,
    db: Session = Depends(get_session)
):
    """Reset agent status to idle (admin function)."""
    
    logger.info("Resetting agent status", agent_type=agent_type)
    
    try:
        await agent_status_service.set_agent_idle(
            agent_type=agent_type,
            db=db
        )
        
        return {
            "message": f"Agent {agent_type} status reset to idle",
            "agent_type": agent_type,
            "status": "idle"
        }
        
    except Exception as e:
        logger.error("Failed to reset agent status",
                    agent_type=agent_type,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset agent {agent_type} status"
        )