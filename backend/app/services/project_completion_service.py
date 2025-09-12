"""Project completion detection and management service."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.task import TaskStatus
from app.database.models import ProjectDB, TaskDB, ContextArtifactDB
from app.services.artifact_service import artifact_service
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class ProjectCompletionService:
    """Service for detecting project completion and managing final artifacts."""
    
    def __init__(self):
        """Initialize the project completion service."""
        pass
    
    async def check_project_completion(
        self,
        project_id: UUID,
        db: Session
    ) -> bool:
        """Check if a project has completed all required tasks."""
        
        logger.info("Checking project completion", project_id=project_id)
        
        try:
            # Get project
            project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
            if not project:
                logger.warning("Project not found", project_id=project_id)
                return False
            
            # Get all tasks for the project
            tasks = db.query(TaskDB).filter(TaskDB.project_id == project_id).all()
            
            if not tasks:
                logger.info("No tasks found for project", project_id=project_id)
                return False
            
            # Check if all tasks are completed
            total_tasks = len(tasks)
            completed_tasks = len([task for task in tasks if task.status == TaskStatus.COMPLETED])
            failed_tasks = len([task for task in tasks if task.status == TaskStatus.FAILED])
            
            logger.info("Task completion status",
                       project_id=project_id,
                       total_tasks=total_tasks,
                       completed_tasks=completed_tasks,
                       failed_tasks=failed_tasks)
            
            # Project is complete if all tasks are done (completed or failed with no recovery)
            is_complete = completed_tasks == total_tasks
            
            # Additional check: Look for specific completion indicators
            if is_complete or self._has_completion_indicators(tasks):
                await self._handle_project_completion(project_id, db)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to check project completion",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            return False
    
    def _has_completion_indicators(self, tasks: List[TaskDB]) -> bool:
        """Check for specific indicators that the project is complete."""
        
        # Look for deployment or final check tasks
        completion_keywords = [
            "deployment", "final check", "project completed",
            "launch", "publish", "finalize"
        ]
        
        for task in tasks:
            if task.status == TaskStatus.COMPLETED:
                instructions_lower = task.instructions.lower()
                for keyword in completion_keywords:
                    if keyword in instructions_lower:
                        return True
        
        return False
    
    async def _handle_project_completion(
        self,
        project_id: UUID,
        db: Session
    ):
        """Handle project completion by updating status and generating artifacts."""
        
        logger.info("Handling project completion", project_id=project_id)
        
        try:
            # Update project status
            project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
            if project:
                project.status = "completed"
                project.updated_at = datetime.utcnow()
                db.commit()
            
            # Emit completion event
            await self._emit_project_completion_event(project_id)
            
            # Generate artifacts automatically
            await self._auto_generate_artifacts(project_id, db)
            
        except Exception as e:
            logger.error("Failed to handle project completion",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            db.rollback()
    
    async def _emit_project_completion_event(self, project_id: UUID):
        """Emit project completion event to WebSocket clients."""
        
        event = WebSocketEvent(
            event_type=EventType.WORKFLOW_EVENT,
            project_id=project_id,
            data={
                "event": "project_completed",
                "message": "Project has completed successfully",
                "completed_at": datetime.utcnow().isoformat(),
                "artifacts_generating": True
            }
        )
        
        try:
            await websocket_manager.broadcast_to_project(event, str(project_id))
            logger.info("Project completion event emitted", project_id=project_id)
        except Exception as e:
            logger.error("Failed to emit project completion event",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
    
    async def _auto_generate_artifacts(
        self,
        project_id: UUID,
        db: Session
    ):
        """Automatically generate artifacts for a completed project."""
        
        logger.info("Auto-generating artifacts for completed project", project_id=project_id)
        
        try:
            # Generate artifacts
            artifacts = await artifact_service.generate_project_artifacts(project_id, db)
            
            if artifacts:
                # Create ZIP file
                await artifact_service.create_project_zip(project_id, artifacts)
                
                # Notify clients that artifacts are ready
                await artifact_service.notify_artifacts_ready(project_id)
                
                logger.info("Auto-generated artifacts successfully",
                           project_id=project_id,
                           artifact_count=len(artifacts))
            else:
                logger.warning("No artifacts generated for completed project",
                              project_id=project_id)
            
        except Exception as e:
            logger.error("Failed to auto-generate artifacts",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
    
    async def force_project_completion(
        self,
        project_id: UUID,
        db: Session
    ) -> bool:
        """Force a project to be marked as completed (admin function)."""
        
        logger.info("Force completing project", project_id=project_id)
        
        try:
            # Verify project exists
            project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
            if not project:
                logger.warning("Project not found for force completion", project_id=project_id)
                return False
            
            # Handle completion
            await self._handle_project_completion(project_id, db)
            
            logger.info("Force completed project successfully", project_id=project_id)
            return True
            
        except Exception as e:
            logger.error("Failed to force complete project",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            return False
    
    async def get_project_completion_status(
        self,
        project_id: UUID,
        db: Session
    ) -> dict:
        """Get detailed completion status for a project."""
        
        try:
            # Get project
            project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
            if not project:
                return {"error": "Project not found"}
            
            # Get tasks
            tasks = db.query(TaskDB).filter(TaskDB.project_id == project_id).all()
            
            # Get artifacts
            artifacts = db.query(ContextArtifactDB).filter(
                ContextArtifactDB.project_id == project_id
            ).count()
            
            # Calculate completion metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
            pending_tasks = len([t for t in tasks if t.status == TaskStatus.PENDING])
            running_tasks = len([t for t in tasks if t.status == TaskStatus.RUNNING])
            
            completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Check if artifacts are available
            artifact_zip = artifact_service.artifacts_dir / f"project_{project_id}.zip"
            artifacts_available = artifact_zip.exists()
            
            return {
                "project_id": str(project_id),
                "project_name": project.name,
                "project_status": project.status,
                "completion_percentage": round(completion_percentage, 2),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "artifacts_count": artifacts,
                "artifacts_available": artifacts_available,
                "last_updated": project.updated_at.isoformat(),
                "is_complete": project.status == "completed"
            }
            
        except Exception as e:
            logger.error("Failed to get project completion status",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            return {"error": f"Failed to get completion status: {str(e)}"}


# Global project completion service instance
project_completion_service = ProjectCompletionService()