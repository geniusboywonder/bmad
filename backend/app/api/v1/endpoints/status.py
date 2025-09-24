
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from redis import from_url as redis_from_url

# CORRECT, VERIFIED IMPORTS
from app.database.connection import get_session
from app.services.agent_status_service import agent_status_service
from app.database.models import TaskDB
from app.tasks.celery_app import celery_app

router = APIRouter()

def get_redis_connection():
    try:
        redis_url = celery_app.conf.broker_url
        if not redis_url:
            return None
        return redis_from_url(redis_url)
    except Exception:
        return None

@router.get("/system_status", summary="Get a full system status report", tags=["health"])
def get_full_system_status(db: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Provides a comprehensive status report of the entire system.
    """
    try:
        # 1. Get Agent Statuses - convert to serializable format
        agent_statuses_raw = agent_status_service.get_all_agent_statuses()
        agent_statuses = []
        for agent_type, status_model in agent_statuses_raw.items():
            agent_statuses.append({
                "agent_type": str(agent_type),
                "status": str(status_model.status),
                "current_task_id": str(status_model.current_task_id) if status_model.current_task_id else None,
                "last_activity": status_model.last_activity.isoformat() if status_model.last_activity else None,
                "error_message": status_model.error_message
            })

        # 2. Get Task Statuses - convert to serializable format
        recent_tasks_db = db.query(TaskDB).order_by(TaskDB.created_at.desc()).limit(50).all()
        task_statuses = []
        for task_db in recent_tasks_db:
            task_statuses.append({
                "id": str(task_db.id),
                "project_id": str(task_db.project_id),
                "agent_type": str(task_db.agent_type),
                "status": str(task_db.status),
                "instructions": task_db.instructions[:100] + "..." if task_db.instructions and len(task_db.instructions) > 100 else task_db.instructions,
                "created_at": task_db.created_at.isoformat() if task_db.created_at else None,
                "updated_at": task_db.updated_at.isoformat() if task_db.updated_at else None,
                "started_at": task_db.started_at.isoformat() if task_db.started_at else None,
                "completed_at": task_db.completed_at.isoformat() if task_db.completed_at else None,
                "error_message": task_db.error_message
            })

        # 3. Get Redis Queue Status
        queue_length = -1
        redis_conn = get_redis_connection()
        if redis_conn:
            try:
                queue_length = redis_conn.llen('celery')
            except Exception:
                pass

        return {
            "agent_statuses": agent_statuses,
            "task_statuses": task_statuses,
            "queue_status": {
                "queue_length": queue_length
            },
        }

    except Exception as e:
        print(f"Error fetching system status: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching system status: {str(e)}")
