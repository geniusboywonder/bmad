"""Project API endpoints."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_orchestrator_service
from app.services.orchestrator import OrchestratorService
from app.services.project_completion_service import project_completion_service
from app.database.connection import get_session

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreateRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: str


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""
    agent_type: str
    instructions: str
    context_ids: List[UUID] = []
    estimated_tokens: int = 100


@router.get("/",
           response_model=List[ProjectResponse],
           summary="📋 List All Projects",
           description="**Retrieve all projects with their current status**")
async def list_projects(
    orchestrator: OrchestratorService = Depends(get_orchestrator_service)
):
    """Get all projects."""
    try:
        projects = orchestrator.list_projects()
        return [
            ProjectResponse(
                id=project.id,
                name=project.name or f"Project {project.id}",
                description=project.description,
                status=project.status or "active"
            )
            for project in projects
        ]
    except Exception as e:
        # Import logger at the top of the file if not already there
        import structlog
        logger = structlog.get_logger(__name__)
        logger.error("Failed to list projects due to an unexpected error", error=str(e), exc_info=True)
        # Return empty list if no projects or service unavailable
        return []


@router.post("/",
             response_model=ProjectResponse,
             status_code=status.HTTP_201_CREATED,
             summary="🏗️ Create New Multi-Agent Project",
             description="""
             **Initialize a new multi-agent project with SDLC orchestration**

             Creates a new project that will be managed by the multi-agent system through various SDLC phases. Each project gets its own workflow context, agent assignments, and human oversight configuration.

             **Project Lifecycle:**
             1. **Discovery** - Requirements analysis and project scoping
             2. **Planning** - Architecture design and task breakdown
             3. **Implementation** - Code development and integration
             4. **Testing** - Quality assurance and validation
             5. **Deployment** - Release preparation and deployment
             6. **Maintenance** - Ongoing support and updates

             **Automatic Setup:**
             - Project workspace initialization
             - Agent team assignment
             - HITL oversight configuration
             - Workflow template selection
             """,
             response_description="Created project with assigned ID and initial configuration")
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
    
    # Submit task to queue with estimated tokens
    task_data = {
        "task_id": str(task.task_id),
        "project_id": str(task.project_id),
        "agent_type": task.agent_type,
        "instructions": task.instructions,
        "context_ids": [str(cid) for cid in task.context_ids],
        "estimated_tokens": request.estimated_tokens
    }
    
    from app.tasks.agent_tasks import process_agent_task
    celery_task = process_agent_task.delay(task_data)
    celery_task_id = celery_task.id
    
    return {
        "task_id": task.task_id,
        "celery_task_id": celery_task_id,
        "status": "submitted",
        "hitl_required": True,
        "estimated_tokens": request.estimated_tokens,
        "message": "Task created but requires HITL approval before execution"
    }


@router.get("/{project_id}/completion")
async def get_project_completion_status(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Get detailed project completion status."""
    
    completion_status = await project_completion_service.get_project_completion_status(
        project_id, db
    )
    
    if "error" in completion_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=completion_status["error"]
        )
    
    return completion_status


@router.post("/{project_id}/check-completion")
async def check_project_completion(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Check if project is complete and trigger completion if so."""
    
    is_complete = await project_completion_service.check_project_completion(
        project_id, db
    )
    
    return {
        "project_id": project_id,
        "is_complete": is_complete,
        "message": "Project completion checked" + (" and completed" if is_complete else "")
    }


@router.post("/{project_id}/force-complete")
async def force_project_completion(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Force project completion (admin function)."""
    
    success = await project_completion_service.force_project_completion(
        project_id, db
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to force project completion"
        )
    
    return {
        "project_id": project_id,
        "message": "Project forced to completion",
        "status": "completed"
    }
