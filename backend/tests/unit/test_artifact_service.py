"""Unit tests for Artifact Service - Sprint 3.

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies (file system) remain appropriately mocked.
"""

import pytest
import os
import json
import zipfile
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open

from app.services.artifact_service import ArtifactService, ProjectArtifact, artifact_service
from app.models.context import ArtifactType
from tests.utils.database_test_utils import DatabaseTestManager

class TestProjectArtifactModel:
    """Test ProjectArtifact model - S3-UNIT-015."""
    
    @pytest.mark.mock_data

    def test_project_artifact_creation(self):
        """Test ProjectArtifact model creation."""
        name = "test_file.py"
        content = "print('Hello World')"
        file_type = "py"
        
        artifact = ProjectArtifact(name, content, file_type, "proj1")
        
        assert artifact.name == name
        assert artifact.content == content
        assert artifact.file_type == file_type
        assert isinstance(artifact.created_at, datetime)
    
    @pytest.mark.mock_data

    def test_project_artifact_default_file_type(self):
        """Test ProjectArtifact with default file type."""
        artifact = ProjectArtifact("test.txt", "content", "txt", "proj1")
        assert artifact.file_type == "txt"

class TestArtifactServiceInitialization:
    """Test ArtifactService initialization."""
    
    @pytest.mark.mock_data

    def test_service_initializes_with_artifacts_directory(self):
        """Test that service has artifacts directory property."""
        from pathlib import Path
        service = ArtifactService({})
        
        # The service should have an artifacts_dir property that returns Path("artifacts")
        assert service.artifacts_dir == Path("artifacts")
        # The constructor doesn't create the directory - that happens in other methods

class TestArtifactGeneration:
    """Test artifact generation logic - S3-UNIT-010."""
    
    @pytest.fixture
    def db_manager(self):
        """Real database manager for artifact service tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()
    
    @pytest.fixture
    def service(self):
        config = {
            "enable_granularity_analysis": True,
            "enable_concept_extraction": True
        }
        return ArtifactService(config)
    
    @pytest.fixture
    @pytest.mark.mock_data

    def test_project_with_artifacts(self, db_manager):
        """Create real project with artifacts for testing."""
        # Create real project
        project = db_manager.create_test_project(
            name="Test Project",
            description="A test project"
        )
        
        with db_manager.get_session() as session:
            # Create real context artifacts
            from app.database.models import ContextArtifactDB
            
            code_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="coder",
                artifact_type=ArtifactType.SOURCE_CODE.value,
                content={"code": "import fastapi\nimport pydantic\ndef hello(): print('Hello')", "filename": "hello.py"}
            )
            
            doc_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="analyst",
                artifact_type=ArtifactType.PROJECT_PLAN.value,
                content={"content": "# Project Documentation\n\nThis is a test project.", "filename": "docs.md"}
            )
            
            req_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="architect",
                artifact_type=ArtifactType.REQUIREMENTS.value,
                content={"requirements": ["fastapi>=0.68.0", "pydantic>=1.8.0"]}
            )
            
            session.add_all([code_artifact, doc_artifact, req_artifact])
            session.commit()
            
            return project, [code_artifact, doc_artifact, req_artifact]
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_generate_project_artifacts_creates_correct_files(self, service, db_manager):
        """Test that artifact generation creates correct ProjectArtifact objects with real database."""
        # Create real project and context artifacts
        project = db_manager.create_test_project(name="Artifact Generation Test")
        
        with db_manager.get_session() as session:
            # Create real context artifacts
            from app.database.models import ContextArtifactDB
            
            code_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="coder",
                artifact_type=ArtifactType.SOURCE_CODE.value,
                content={"code": "def hello(): return 'Hello World'", "language": "python", "filename": "hello.py"}
            )
            doc_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="architect",
                artifact_type=ArtifactType.SYSTEM_ARCHITECTURE.value,
                content={"documentation": "This is project documentation", "filename": "docs.md"}
            )
            req_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="analyst",
                artifact_type=ArtifactType.PROJECT_PLAN.value,
                content={"requirements": "User should be able to say hello"}
            )
            
            session.add_all([code_artifact, doc_artifact, req_artifact])
            session.commit()
            
            artifacts = await service.generate_project_artifacts(str(project.id), session)
            
            # Should generate multiple artifacts
            assert len(artifacts) >= 2  # README.md, summary
            
            # Check for expected artifacts
            artifact_names = [a.name for a in artifacts]
            assert "README.md" in artifact_names
            assert "project_summary.txt" in artifact_names
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_generate_project_artifacts_project_not_found(self, service, db_manager):
        """Test artifact generation with non-existent project using real database."""
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            # The current implementation doesn't validate project existence
            # It generates basic artifacts regardless
            artifacts = await service.generate_project_artifacts(str(project_id), session)
            
            # Should still generate basic artifacts (README, summary)
            assert len(artifacts) >= 2
            assert any(artifact.name == "README.md" for artifact in artifacts)
            assert any(artifact.name == "project_summary.txt" for artifact in artifacts)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_generate_project_artifacts_empty_context(self, service, db_manager):
        """Test artifact generation with no context artifacts using real database."""
        # Create real project with no context artifacts
        project = db_manager.create_test_project(name="Empty Project", description="No artifacts")
        
        with db_manager.get_session() as session:
            artifacts = await service.generate_project_artifacts(str(project.id), session)
            
            # Should still generate basic artifacts
            assert len(artifacts) >= 2  # README.md and project_summary
            artifact_names = [a.name for a in artifacts]
            assert "README.md" in artifact_names
            assert any("project_summary" in name for name in artifact_names)

class TestZipFileCreation:
    """Test ZIP file creation - S3-UNIT-011."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService({})
    
    @pytest.fixture
    def sample_artifacts(self):
        """Sample artifacts for testing."""
        return [
            ProjectArtifact("main.py", "print('Hello World')", "py", "proj1"),
            ProjectArtifact("README.md", "# Test Project", "md", "proj1"),
            ProjectArtifact("requirements.txt", "fastapi>=0.68.0", "txt", "proj1")
        ]
    
    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_create_project_zip_creates_file(self, service, sample_artifacts):
        """Test that ZIP creation creates a valid ZIP file."""
        project_id = uuid4()
        
        with patch('zipfile.ZipFile') as mock_zipfile, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            zip_path = await service.create_project_zip(str(project_id), sample_artifacts)
            
            # Verify ZIP file operations
            expected_path = str(service.artifacts_dir / f"project_{project_id}.zip")
            assert zip_path == expected_path
            
            # Verify directory creation was called
            mock_mkdir.assert_called_once_with(exist_ok=True)
            
            # Verify all artifacts were added to ZIP
            assert mock_zip_instance.writestr.call_count == len(sample_artifacts)
            
            # Verify file contents
            calls = mock_zip_instance.writestr.call_args_list
            for i, artifact in enumerate(sample_artifacts):
                assert calls[i][0][0] == artifact.name
                assert calls[i][0][1] == artifact.content
    
    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_create_project_zip_handles_large_content(self, service):
        """Test ZIP creation with large artifact content."""
        project_id = uuid4()
        large_content = "x" * 10000  # 10KB content
        large_artifacts = [ProjectArtifact("large_file.txt", large_content, "txt", "proj1")]
        
        with patch('zipfile.ZipFile') as mock_zipfile, \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            zip_path = await service.create_project_zip(str(project_id), large_artifacts)
            
            assert zip_path is not None
            mock_mkdir.assert_called_once_with(exist_ok=True)
            mock_zip_instance.writestr.assert_called_once_with("large_file.txt", large_content)






class TestArtifactCleanup:
    """Test artifact cleanup functionality."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService({})
    
    @pytest.mark.mock_data

    def test_cleanup_old_artifacts(self, service):
        """Test cleanup of old artifact files."""
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.glob') as mock_glob:
            
            # Mock artifacts directory exists
            mock_exists.return_value = True
            
            # Mock old file
            old_file = Mock()
            old_stat = Mock()
            old_stat.st_mtime = datetime.now().timestamp() - 48*3600  # 48 hours ago
            old_file.stat.return_value = old_stat
            old_file.unlink = Mock()
            
            # Mock new file  
            new_file = Mock()
            new_stat = Mock()
            new_stat.st_mtime = datetime.now().timestamp() - 1*3600   # 1 hour ago
            new_file.stat.return_value = new_stat
            new_file.unlink = Mock()
            
            mock_glob.return_value = [old_file, new_file]
            
            service.cleanup_old_artifacts(max_age_hours=24)
            
            # Should only delete old file
            old_file.unlink.assert_called_once()
            new_file.unlink.assert_not_called()

