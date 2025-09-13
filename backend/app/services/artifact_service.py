"""Artifact service for managing project artifacts and downloads."""

import os
import json
import zipfile
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import structlog
from sqlalchemy.orm import Session

from app.models.context import ArtifactType
from app.database.models import ContextArtifactDB, ProjectDB
from app.websocket.manager import websocket_manager
from app.websocket.events import WebSocketEvent, EventType

logger = structlog.get_logger(__name__)


class ProjectArtifact:
    """Represents a downloadable project artifact."""
    
    def __init__(self, name: str, content: str, file_type: str = "txt"):
        self.name = name
        self.content = content
        self.file_type = file_type
        self.created_at = datetime.now(timezone.utc)


class ArtifactService:
    """Service for managing project artifacts and downloads."""
    
    def __init__(self):
        """Initialize the artifact service."""
        self.artifacts_dir = Path("/tmp/bmad_artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
    
    async def generate_project_artifacts(
        self,
        project_id: UUID,
        db: Session
    ) -> List[ProjectArtifact]:
        """Generate downloadable artifacts for a completed project."""
        
        logger.info("Generating project artifacts", project_id=project_id)
        
        try:
            # Get project details
            project = db.query(ProjectDB).filter(ProjectDB.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get all context artifacts for the project
            context_artifacts = db.query(ContextArtifactDB).filter(
                ContextArtifactDB.project_id == project_id
            ).order_by(ContextArtifactDB.created_at).all()
            
            artifacts = []
            
            # Create project summary
            summary_content = self._generate_project_summary(project, context_artifacts)
            artifacts.append(ProjectArtifact(
                name="project_summary.md",
                content=summary_content,
                file_type="md"
            ))
            
            # Process different artifact types
            code_artifacts = []
            documentation_artifacts = []
            test_artifacts = []
            
            for ctx_artifact in context_artifacts:
                if ctx_artifact.artifact_type == ArtifactType.SOURCE_CODE:
                    code_artifacts.append(ctx_artifact)
                elif ctx_artifact.artifact_type in [ArtifactType.SOFTWARE_SPECIFICATION, ArtifactType.SYSTEM_ARCHITECTURE]:
                    documentation_artifacts.append(ctx_artifact)
                elif ctx_artifact.artifact_type == ArtifactType.PROJECT_PLAN:
                    # Add project plan as documentation
                    documentation_artifacts.append(ctx_artifact)
            
            # Generate code files
            if code_artifacts:
                for artifact in code_artifacts:
                    content = self._extract_content(artifact.content)
                    filename = self._generate_filename(artifact, "py")
                    artifacts.append(ProjectArtifact(
                        name=filename,
                        content=content,
                        file_type="py"
                    ))
            
            # Generate documentation files
            if documentation_artifacts:
                for artifact in documentation_artifacts:
                    content = self._extract_content(artifact.content)
                    filename = self._generate_filename(artifact, "md")
                    artifacts.append(ProjectArtifact(
                        name=filename,
                        content=content,
                        file_type="md"
                    ))
            
            # Generate requirements.txt if we have requirements
            requirements = self._extract_requirements(context_artifacts)
            if requirements:
                artifacts.append(ProjectArtifact(
                    name="requirements.txt",
                    content="\n".join(requirements),
                    file_type="txt"
                ))
            
            # Generate README
            readme_content = self._generate_readme(project, context_artifacts)
            artifacts.append(ProjectArtifact(
                name="README.md",
                content=readme_content,
                file_type="md"
            ))
            
            logger.info("Generated project artifacts",
                       project_id=project_id,
                       artifact_count=len(artifacts))
            
            return artifacts
            
        except Exception as e:
            logger.error("Failed to generate project artifacts",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            raise
    
    def _generate_project_summary(self, project: ProjectDB, artifacts: List[ContextArtifactDB]) -> str:
        """Generate a project summary document."""
        
        summary = f"""# Project Summary: {project.name}

## Overview
{project.description or "No description provided"}

## Project Details
- **Project ID**: {project.id}
- **Created**: {project.created_at.isoformat()}
- **Last Updated**: {project.updated_at.isoformat()}
- **Status**: {project.status}

## Artifacts Generated
- **Total Artifacts**: {len(artifacts)}
- **Generation Date**: {datetime.now(timezone.utc).isoformat()}

## Artifact Breakdown
"""
        
        artifact_types = {}
        for artifact in artifacts:
            artifact_type = artifact.artifact_type.value
            if artifact_type not in artifact_types:
                artifact_types[artifact_type] = 0
            artifact_types[artifact_type] += 1
        
        for artifact_type, count in artifact_types.items():
            summary += f"- **{artifact_type.title()}**: {count} items\n"
        
        return summary
    
    def _generate_filename(self, artifact: ContextArtifactDB, extension: str) -> str:
        """Generate a filename for an artifact."""
        
        # Try to extract filename from metadata
        if artifact.artifact_metadata and "filename" in artifact.artifact_metadata:
            base_name = artifact.artifact_metadata["filename"]
            # Remove extension if present
            base_name = os.path.splitext(base_name)[0]
        else:
            # Generate filename based on artifact type and source
            base_name = f"{artifact.source_agent}_{artifact.artifact_type.value}"
        
        # Sanitize filename
        base_name = "".join(c for c in base_name if c.isalnum() or c in "._-")
        
        return f"{base_name}.{extension}"
    
    def _extract_content(self, content_data: Any) -> str:
        """Extract text content from artifact data."""
        
        if isinstance(content_data, str):
            return content_data
        elif isinstance(content_data, dict):
            # Try common content keys
            for key in ["content", "text", "code", "body"]:
                if key in content_data:
                    return str(content_data[key])
            # Return JSON representation if no content key found
            return json.dumps(content_data, indent=2)
        else:
            return str(content_data)
    
    def _extract_requirements(self, artifacts: List[ContextArtifactDB]) -> List[str]:
        """Extract Python requirements from artifacts."""
        
        requirements = set()
        
        for artifact in artifacts:
            content = self._extract_content(artifact.content)
            
            # Look for import statements in code
            if artifact.artifact_type == ArtifactType.SOURCE_CODE:
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Extract package name
                        if line.startswith('import '):
                            package = line.replace('import ', '').split('.')[0].split(' ')[0]
                        else:  # from X import Y
                            package = line.split()[1].split('.')[0]
                        
                        # Filter out standard library modules
                        if package not in ['os', 'sys', 'json', 'datetime', 'typing', 'pathlib']:
                            requirements.add(package)
        
        return sorted(list(requirements))
    
    def _generate_readme(self, project: ProjectDB, artifacts: List[ContextArtifactDB]) -> str:
        """Generate a README.md file."""
        
        readme = f"""# {project.name}

{project.description or "Project generated by BotArmy POC"}

## Project Structure

This project was automatically generated by the BotArmy system. Below is an overview of the generated files:

"""
        
        # Group artifacts by type
        artifact_groups = {}
        for artifact in artifacts:
            artifact_type = artifact.artifact_type.value
            if artifact_type not in artifact_groups:
                artifact_groups[artifact_type] = []
            artifact_groups[artifact_type].append(artifact)
        
        for artifact_type, group_artifacts in artifact_groups.items():
            readme += f"### {artifact_type.title()}\n\n"
            for artifact in group_artifacts:
                filename = self._generate_filename(artifact, "py" if artifact_type == "code" else "md")
                readme += f"- `{filename}` - Generated by {artifact.source_agent}\n"
            readme += "\n"
        
        readme += f"""## Usage

This project was generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC.

## Support

For questions about this generated project, please refer to the BotArmy documentation.
"""
        
        return readme
    
    async def create_project_zip(
        self,
        project_id: UUID,
        artifacts: List[ProjectArtifact]
    ) -> str:
        """Create a ZIP file containing all project artifacts."""
        
        logger.info("Creating project ZIP", 
                   project_id=project_id,
                   artifact_count=len(artifacts))
        
        try:
            # Create temporary ZIP file
            zip_path = self.artifacts_dir / f"project_{project_id}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for artifact in artifacts:
                    # Add file to ZIP
                    zipf.writestr(artifact.name, artifact.content)
            
            logger.info("Created project ZIP",
                       project_id=project_id,
                       zip_path=str(zip_path),
                       file_size=zip_path.stat().st_size)
            
            return str(zip_path)
            
        except Exception as e:
            logger.error("Failed to create project ZIP",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
            raise
    
    async def notify_artifacts_ready(self, project_id: UUID):
        """Notify clients that project artifacts are ready for download."""
        
        event = WebSocketEvent(
            event_type=EventType.ARTIFACT_CREATED,
            project_id=project_id,
            data={
                "message": "Project artifacts are ready for download",
                "download_available": True,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        try:
            await websocket_manager.broadcast_to_project(event, str(project_id))
            logger.info("Artifacts ready notification sent",
                       project_id=project_id)
        except Exception as e:
            logger.error("Failed to notify artifacts ready",
                        project_id=project_id,
                        error=str(e),
                        exc_info=True)
    
    def cleanup_old_artifacts(self, max_age_hours: int = 24):
        """Clean up old artifact files."""
        
        logger.info("Cleaning up old artifacts", max_age_hours=max_age_hours)
        
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
            cleaned_count = 0
            
            for file_path in self.artifacts_dir.iterdir():
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            logger.info("Cleaned up old artifacts", cleaned_count=cleaned_count)
            
        except Exception as e:
            logger.error("Failed to cleanup old artifacts",
                        error=str(e),
                        exc_info=True)


# Global artifact service instance
artifact_service = ArtifactService()