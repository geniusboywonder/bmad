"""Project artifact API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import structlog

from app.services.artifact_service import artifact_service, ProjectArtifact
from app.database.connection import get_session
from app.database.models import ProjectDB

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


class ArtifactSummaryResponse(BaseModel):
    """Response model for artifact summary."""
    project_id: UUID
    project_name: str
    artifact_count: int
    generated_at: str
    download_available: bool
    artifacts: List[dict]


class ArtifactGenerationResponse(BaseModel):
    """Response model for artifact generation."""
    project_id: UUID
    status: str
    message: str
    artifact_count: int


@router.post("/{project_id}/generate", response_model=ArtifactGenerationResponse)
async def generate_project_artifacts(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Generate downloadable artifacts for a completed project."""
    
    logger.info("Generating artifacts for project", project_id=project_id)
    
    try:
        # Verify project exists
        project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Generate artifacts
        artifacts = await artifact_service.generate_project_artifacts(project_id, db)
        
        # Create ZIP file
        zip_path = await artifact_service.create_project_zip(project_id, artifacts)
        
        # Notify clients
        await artifact_service.notify_artifacts_ready(project_id)
        
        logger.info("Artifacts generated successfully",
                   project_id=project_id,
                   artifact_count=len(artifacts))
        
        return ArtifactGenerationResponse(
            project_id=project_id,
            status="success",
            message=f"Generated {len(artifacts)} artifacts successfully",
            artifact_count=len(artifacts)
        )
        
    except ValueError as e:
        logger.error("Invalid project for artifact generation",
                    project_id=project_id,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to generate artifacts",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate project artifacts"
        )


@router.get("/{project_id}/summary", response_model=ArtifactSummaryResponse)
async def get_project_artifact_summary(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Get summary of available artifacts for a project."""
    
    logger.info("Getting artifact summary", project_id=project_id)
    
    try:
        # Verify project exists
        project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Generate artifacts to get summary
        artifacts = await artifact_service.generate_project_artifacts(project_id, db)
        
        # Check if ZIP file exists
        zip_path = artifact_service.artifacts_dir / f"project_{project_id}.zip"
        download_available = zip_path.exists()
        
        artifact_list = [
            {
                "name": artifact.name,
                "file_type": artifact.file_type,
                "created_at": artifact.created_at.isoformat()
            }
            for artifact in artifacts
        ]
        
        return ArtifactSummaryResponse(
            project_id=project_id,
            project_name=project.name,
            artifact_count=len(artifacts),
            generated_at=artifacts[0].created_at.isoformat() if artifacts else None,
            download_available=download_available,
            artifacts=artifact_list
        )
        
    except Exception as e:
        logger.error("Failed to get artifact summary",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project artifact summary"
        )


@router.get("/{project_id}/download")
async def download_project_artifacts(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Download project artifacts as a ZIP file."""
    
    logger.info("Downloading artifacts", project_id=project_id)
    
    try:
        # Verify project exists
        project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Check if ZIP file exists
        zip_path = artifact_service.artifacts_dir / f"project_{project_id}.zip"
        
        if not zip_path.exists():
            # Generate artifacts if they don't exist
            logger.info("ZIP file not found, generating artifacts", project_id=project_id)
            artifacts = await artifact_service.generate_project_artifacts(project_id, db)
            zip_path = await artifact_service.create_project_zip(project_id, artifacts)
        
        # Return file download
        filename = f"{project.name.replace(' ', '_')}_artifacts.zip"
        
        logger.info("Serving artifact download",
                   project_id=project_id,
                   filename=filename,
                   file_path=str(zip_path))
        
        return FileResponse(
            path=str(zip_path),
            filename=filename,
            media_type="application/zip"
        )
        
    except Exception as e:
        logger.error("Failed to download artifacts",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download project artifacts"
        )


@router.delete("/{project_id}/artifacts")
async def cleanup_project_artifacts(
    project_id: UUID,
    db: Session = Depends(get_session)
):
    """Clean up generated artifacts for a project."""
    
    logger.info("Cleaning up project artifacts", project_id=project_id)
    
    try:
        # Verify project exists
        project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Remove ZIP file if exists
        zip_path = artifact_service.artifacts_dir / f"project_{project_id}.zip"
        if zip_path.exists():
            zip_path.unlink()
            logger.info("Cleaned up project artifacts", project_id=project_id)
        
        return {"message": f"Artifacts cleaned up for project {project_id}"}
        
    except Exception as e:
        logger.error("Failed to cleanup artifacts",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup project artifacts"
        )


@router.post("/cleanup-old")
async def cleanup_old_artifacts(max_age_hours: int = 24):
    """Clean up old artifact files (admin endpoint)."""
    
    logger.info("Cleaning up old artifacts", max_age_hours=max_age_hours)
    
    try:
        artifact_service.cleanup_old_artifacts(max_age_hours)
        return {"message": f"Cleaned up artifacts older than {max_age_hours} hours"}
        
    except Exception as e:
        logger.error("Failed to cleanup old artifacts",
                    error=str(e),
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup old artifacts"
        )