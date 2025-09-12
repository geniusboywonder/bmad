"""Context Store service for persistent memory management."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
import structlog

from app.models.context import ContextArtifact, ArtifactType
from app.database.models import ContextArtifactDB

logger = structlog.get_logger(__name__)


class ContextStoreService:
    """Service for managing the Context Store pattern."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_artifact(
        self,
        project_id: UUID,
        source_agent: str,
        artifact_type: ArtifactType,
        content: Dict[str, Any],
        artifact_metadata: Optional[Dict[str, Any]] = None
    ) -> ContextArtifact:
        """Create a new context artifact."""
        
        db_artifact = ContextArtifactDB(
            project_id=project_id,
            source_agent=source_agent,
            artifact_type=artifact_type,
            content=content,
            artifact_metadata=artifact_metadata
        )
        
        self.db.add(db_artifact)
        self.db.commit()
        self.db.refresh(db_artifact)
        
        # Convert to Pydantic model
        artifact = ContextArtifact(
            context_id=db_artifact.id,
            project_id=db_artifact.project_id,
            source_agent=db_artifact.source_agent,
            artifact_type=db_artifact.artifact_type,
            content=db_artifact.content,
            artifact_metadata=db_artifact.artifact_metadata,
            created_at=db_artifact.created_at,
            updated_at=db_artifact.updated_at
        )
        
        logger.info("Context artifact created", 
                   artifact_id=artifact.context_id,
                   artifact_type=artifact_type,
                   source_agent=source_agent)
        
        return artifact
    
    def get_artifact(self, context_id: UUID) -> Optional[ContextArtifact]:
        """Get a context artifact by ID."""
        
        db_artifact = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == context_id
        ).first()
        
        if not db_artifact:
            return None
        
        return ContextArtifact(
            context_id=db_artifact.id,
            project_id=db_artifact.project_id,
            source_agent=db_artifact.source_agent,
            artifact_type=db_artifact.artifact_type,
            content=db_artifact.content,
            artifact_metadata=db_artifact.artifact_metadata,
            created_at=db_artifact.created_at,
            updated_at=db_artifact.updated_at
        )
    
    def get_artifact_by_id(self, artifact_id: UUID) -> Optional[ContextArtifact]:
        """Get a context artifact by ID (alias for get_artifact)."""
        return self.get_artifact(artifact_id)
    
    def get_artifacts_by_project(
        self, 
        project_id: UUID,
        artifact_type: Optional[ArtifactType] = None
    ) -> List[ContextArtifact]:
        """Get all context artifacts for a project."""
        
        query = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.project_id == project_id
        )
        
        if artifact_type:
            query = query.filter(ContextArtifactDB.artifact_type == artifact_type)
        
        db_artifacts = query.all()
        
        artifacts = []
        for db_artifact in db_artifacts:
            artifact = ContextArtifact(
                context_id=db_artifact.id,
                project_id=db_artifact.project_id,
                source_agent=db_artifact.source_agent,
                artifact_type=db_artifact.artifact_type,
                content=db_artifact.content,
                artifact_metadata=db_artifact.artifact_metadata,
                created_at=db_artifact.created_at,
                updated_at=db_artifact.updated_at
            )
            artifacts.append(artifact)
        
        return artifacts
    
    def get_artifacts_by_ids(self, context_ids: List[UUID]) -> List[ContextArtifact]:
        """Get multiple context artifacts by their IDs."""
        
        # Handle empty or None input
        if not context_ids:
            return []
        
        db_artifacts = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.id.in_(context_ids)
        ).all()
        
        artifacts = []
        for db_artifact in db_artifacts:
            artifact = ContextArtifact(
                context_id=db_artifact.id,
                project_id=db_artifact.project_id,
                source_agent=db_artifact.source_agent,
                artifact_type=db_artifact.artifact_type,
                content=db_artifact.content,
                artifact_metadata=db_artifact.artifact_metadata,
                created_at=db_artifact.created_at,
                updated_at=db_artifact.updated_at
            )
            artifacts.append(artifact)
        
        return artifacts
    
    def update_artifact(
        self,
        context_id: UUID = None,
        artifact_id: UUID = None,
        content: Optional[Dict[str, Any]] = None,
        artifact_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ContextArtifact]:
        """Update an existing context artifact."""
        
        # Support both context_id and artifact_id parameter names
        target_id = context_id or artifact_id
        if target_id is None:
            raise ValueError("Either context_id or artifact_id must be provided")
        
        db_artifact = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == target_id
        ).first()
        
        if not db_artifact:
            return None
        
        if content is not None:
            db_artifact.content = content
        
        if artifact_metadata is not None:
            db_artifact.artifact_metadata = artifact_metadata
        
        self.db.commit()
        self.db.refresh(db_artifact)
        
        artifact = ContextArtifact(
            context_id=db_artifact.id,
            project_id=db_artifact.project_id,
            source_agent=db_artifact.source_agent,
            artifact_type=db_artifact.artifact_type,
            content=db_artifact.content,
            artifact_metadata=db_artifact.artifact_metadata,
            created_at=db_artifact.created_at,
            updated_at=db_artifact.updated_at
        )
        
        logger.info("Context artifact updated", artifact_id=target_id)
        
        return artifact
    
    def delete_artifact(self, context_id: UUID) -> bool:
        """Delete a context artifact."""
        
        db_artifact = self.db.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == context_id
        ).first()
        
        if not db_artifact:
            return False
        
        self.db.delete(db_artifact)
        self.db.commit()
        
        logger.info("Context artifact deleted", artifact_id=context_id)
        
        return True
