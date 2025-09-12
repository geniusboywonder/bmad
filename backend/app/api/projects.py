"""Project API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import get_orchestrator_service
from app.services.orchestrator import OrchestratorService

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    description: str = None


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: UUID
    name: str
    description: str = None
    status: str


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    agent_type: str
    instructions: str
    context_ids: List[UUID] = []


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Create a new project."""
    
    project_id = orchestrator.create_project(
        name=request.name,
        description=request.description
    )
    
    return ProjectResponse(
        id=project_id,
        name=request.name,
        description=request.description,
        status="active"
    )


@router.get("/{project_id}/status")
async def get_project_status(
    project_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Get project status and tasks."""
    
    tasks = orchestrator.get_project_tasks(project_id)
    
    return {
        "project_id": project_id,
        "tasks": [
            {
                "task_id": task.task_id,
                "agent_type": task.agent_type,
                "status": task.status,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            for task in tasks
        ]
    }


@router.post("/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    request: TaskCreateRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Create a new task for a project."""
    
    task = orchestrator.create_task(
        project_id=project_id,
        agent_type=request.agent_type,
        instructions=request.instructions,
        context_ids=request.context_ids
    )
    
    # Submit task to queue
    celery_task_id = orchestrator.submit_task(task)
    
    return {
        "task_id": task.task_id,
        "celery_task_id": celery_task_id,
        "status": "submitted"
    }
