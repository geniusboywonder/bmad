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
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open

from app.services.artifact_service import ArtifactService, ProjectArtifact, artifact_service
from app.models.context import ArtifactType
from tests.utils.database_test_utils import DatabaseTestManager


class TestProjectArtifactModel:
    """Test ProjectArtifact model - S3-UNIT-015."""
    
    def test_project_artifact_creation(self):
        """Test ProjectArtifact model creation."""
        name = "test_file.py"
        content = "print('Hello World')"
        file_type = "py"
        
        artifact = ProjectArtifact(name, content, file_type)
        
        assert artifact.name == name
        assert artifact.content == content
        assert artifact.file_type == file_type
        assert isinstance(artifact.created_at, datetime)
    
    def test_project_artifact_default_file_type(self):
        """Test ProjectArtifact with default file type."""
        artifact = ProjectArtifact("test.txt", "content")
        assert artifact.file_type == "txt"


class TestArtifactServiceInitialization:
    """Test ArtifactService initialization."""
    
    def test_service_initializes_with_artifacts_directory(self):
        """Test that service creates artifacts directory."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            service = ArtifactService()
            
            assert service.artifacts_dir == Path("/tmp/bmad_artifacts")
            mock_mkdir.assert_called_once_with(exist_ok=True)


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
                artifact_type=ArtifactType.CODE,
                content={"code": "import fastapi\nimport pydantic\ndef hello(): print('Hello')", "filename": "hello.py"}
            )
            
            doc_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="analyst",
                artifact_type=ArtifactType.DOCUMENTATION,
                content={"content": "# Project Documentation\n\nThis is a test project.", "filename": "docs.md"}
            )
            
            req_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="architect",
                artifact_type=ArtifactType.REQUIREMENTS,
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
                artifact_type=ArtifactType.CODE,
                content={"code": "def hello(): return 'Hello World'", "language": "python", "filename": "hello.py"}
            )
            doc_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="architect",
                artifact_type=ArtifactType.DOCUMENTATION,
                content={"documentation": "This is project documentation", "filename": "docs.md"}
            )
            req_artifact = ContextArtifactDB(
                project_id=project.id,
                source_agent="analyst",
                artifact_type=ArtifactType.REQUIREMENTS,
                content={"requirements": "User should be able to say hello"}
            )
            
            session.add_all([code_artifact, doc_artifact, req_artifact])
            session.commit()
            
            artifacts = await service.generate_project_artifacts(project.id, session)
            
            # Should generate multiple artifacts
            assert len(artifacts) >= 4  # code, docs, requirements.txt, README.md, summary
            
            # Check for expected artifacts
            artifact_names = [a.name for a in artifacts]
            assert "hello.py" in artifact_names
            assert "docs.md" in artifact_names  
            assert "requirements.txt" in artifact_names
            assert "README.md" in artifact_names
            assert "project_summary.md" in artifact_names
    
    @pytest.mark.asyncio 
    @pytest.mark.real_data
    async def test_generate_project_artifacts_project_not_found(self, service, db_manager):
        """Test artifact generation with non-existent project using real database."""
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            with pytest.raises(ValueError, match=f"Project {project_id} not found"):
                await service.generate_project_artifacts(project_id, session)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_generate_project_artifacts_empty_context(self, service, db_manager):
        """Test artifact generation with no context artifacts using real database."""
        # Create real project with no context artifacts
        project = db_manager.create_test_project(name="Empty Project", description="No artifacts")
        
        with db_manager.get_session() as session:
            artifacts = await service.generate_project_artifacts(project.id, session)
            
            # Should still generate basic artifacts
            assert len(artifacts) >= 2  # README.md and project_summary
            artifact_names = [a.name for a in artifacts]
            assert "README.md" in artifact_names
            # Check for project summary (could be .md or .txt)
            assert any("project_summary" in name for name in artifact_names)


class TestZipFileCreation:
    """Test ZIP file creation - S3-UNIT-011."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    @pytest.fixture
    def sample_artifacts(self):
        """Sample artifacts for testing."""
        return [
            ProjectArtifact("main.py", "print('Hello World')", "py"),
            ProjectArtifact("README.md", "# Test Project", "md"),
            ProjectArtifact("requirements.txt", "fastapi>=0.68.0", "txt")
        ]
    
    @pytest.mark.asyncio
    async def test_create_project_zip_creates_file(self, service, sample_artifacts):
        """Test that ZIP creation creates a valid ZIP file."""
        project_id = uuid4()
        
        with patch('zipfile.ZipFile') as mock_zipfile, \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            mock_stat.return_value.st_size = 1024
            
            zip_path = await service.create_project_zip(project_id, sample_artifacts)
            
            # Verify ZIP file operations
            expected_path = str(service.artifacts_dir / f"project_{project_id}.zip")
            assert zip_path == expected_path
            
            # Verify all artifacts were added to ZIP
            assert mock_zip_instance.writestr.call_count == len(sample_artifacts)
            
            # Verify file contents
            calls = mock_zip_instance.writestr.call_args_list
            for i, artifact in enumerate(sample_artifacts):
                assert calls[i][0][0] == artifact.name
                assert calls[i][0][1] == artifact.content
    
    @pytest.mark.asyncio
    async def test_create_project_zip_handles_large_content(self, service):
        """Test ZIP creation with large artifact content."""
        project_id = uuid4()
        large_content = "x" * 10000  # 10KB content
        large_artifacts = [ProjectArtifact("large_file.txt", large_content, "txt")]
        
        with patch('zipfile.ZipFile') as mock_zipfile, \
             patch('pathlib.Path.stat') as mock_stat:
            
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            mock_stat.return_value.st_size = 8192  # Compressed size
            
            zip_path = await service.create_project_zip(project_id, large_artifacts)
            
            assert zip_path is not None
            mock_zip_instance.writestr.assert_called_once_with("large_file.txt", large_content)


class TestContentExtraction:
    """Test content extraction logic - S3-UNIT-012."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_extract_content_from_string(self, service):
        """Test content extraction from string."""
        content = "Simple string content"
        result = service._extract_content(content)
        assert result == content
    
    def test_extract_content_from_dict_with_content_key(self, service):
        """Test content extraction from dict with 'content' key."""
        content_data = {"content": "This is the content", "metadata": "extra"}
        result = service._extract_content(content_data)
        assert result == "This is the content"
    
    def test_extract_content_from_dict_with_code_key(self, service):
        """Test content extraction from dict with 'code' key."""
        content_data = {"code": "def hello(): pass", "language": "python"}
        result = service._extract_content(content_data)
        assert result == "def hello(): pass"
    
    def test_extract_content_from_dict_no_standard_keys(self, service):
        """Test content extraction from dict without standard keys."""
        content_data = {"custom_field": "value", "another_field": 123}
        result = service._extract_content(content_data)
        
        # Should return JSON representation
        parsed_result = json.loads(result)
        assert parsed_result == content_data
    
    def test_extract_content_from_other_types(self, service):
        """Test content extraction from non-string, non-dict types."""
        assert service._extract_content(123) == "123"
        assert service._extract_content(True) == "True"
        assert service._extract_content([1, 2, 3]) == "[1, 2, 3]"


class TestRequirementsExtraction:
    """Test Python requirements extraction - S3-UNIT-013."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_extract_requirements_from_code_artifacts(self, service):
        """Test requirements extraction from code artifacts."""
        mock_artifacts = [
            Mock(
                artifact_type=ArtifactType.SOURCE_CODE,
                content="import fastapi\nfrom pydantic import BaseModel\nimport requests\nfrom datetime import datetime"
            ),
            Mock(
                artifact_type=ArtifactType.SOFTWARE_SPECIFICATION,
                content="# Documentation\nNo imports here"
            )
        ]
        
        requirements = service._extract_requirements(mock_artifacts)
        
        # Should extract package names, excluding standard library
        expected = sorted(["fastapi", "pydantic", "requests"])
        assert sorted(requirements) == expected
    
    def test_extract_requirements_filters_stdlib(self, service):
        """Test that standard library modules are filtered out."""
        mock_artifacts = [
            Mock(
                artifact_type=ArtifactType.SOURCE_CODE,
                content="import os\nimport sys\nimport json\nimport requests\nfrom datetime import datetime"
            )
        ]
        
        requirements = service._extract_requirements(mock_artifacts)
        
        # Should only include non-stdlib packages
        assert requirements == ["requests"]
    
    def test_extract_requirements_handles_from_imports(self, service):
        """Test requirements extraction handles 'from X import Y' syntax."""
        mock_artifacts = [
            Mock(
                artifact_type=ArtifactType.SOURCE_CODE,
                content="from fastapi import FastAPI\nfrom sqlalchemy.orm import Session\nfrom mypackage.submodule import func"
            )
        ]
        
        requirements = service._extract_requirements(mock_artifacts)
        
        expected = sorted(["fastapi", "mypackage", "sqlalchemy"])
        assert sorted(requirements) == expected


class TestFilenameGeneration:
    """Test filename generation logic - S3-UNIT-014."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_generate_filename_from_metadata(self, service):
        """Test filename generation from artifact metadata."""
        mock_artifact = Mock()
        mock_artifact.artifact_metadata = {"filename": "custom_file.py"}
        mock_artifact.source_agent = "coder"
        mock_artifact.artifact_type = ArtifactType.SOURCE_CODE
        
        filename = service._generate_filename(mock_artifact, "py")
        assert filename == "custom_file.py"
    
    def test_generate_filename_from_agent_and_type(self, service):
        """Test filename generation from agent and artifact type."""
        mock_artifact = Mock()
        mock_artifact.artifact_metadata = {}
        mock_artifact.source_agent = "analyst"
        mock_artifact.artifact_type = ArtifactType.SOFTWARE_SPECIFICATION
        
        filename = service._generate_filename(mock_artifact, "md")
        assert filename == "analyst_software_specification.md"
    
    def test_generate_filename_sanitization(self, service):
        """Test filename sanitization for invalid characters."""
        mock_artifact = Mock()
        mock_artifact.artifact_metadata = {"filename": "file with spaces & special!chars.py"}
        mock_artifact.source_agent = "coder"
        mock_artifact.artifact_type = ArtifactType.SOURCE_CODE
        
        filename = service._generate_filename(mock_artifact, "py")
        # Should sanitize invalid characters
        assert " " not in filename
        assert "&" not in filename
        assert "!" not in filename


class TestProjectSummaryGeneration:
    """Test project summary generation."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_generate_project_summary(self, service):
        """Test project summary generation."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.description = "A comprehensive test"
        mock_project.id = uuid4()
        mock_project.created_at = datetime(2025, 9, 12, 10, 0, 0)
        mock_project.updated_at = datetime(2025, 9, 12, 15, 30, 0)
        mock_project.status = "completed"
        
        mock_artifacts = [
            Mock(artifact_type=ArtifactType.SOURCE_CODE),
            Mock(artifact_type=ArtifactType.SOFTWARE_SPECIFICATION),
            Mock(artifact_type=ArtifactType.SOURCE_CODE),
        ]
        
        summary = service._generate_project_summary(mock_project, mock_artifacts)
        
        assert "Test Project" in summary
        assert "A comprehensive test" in summary
        assert str(mock_project.id) in summary
        assert "completed" in summary
        assert "Total Artifacts**: 3" in summary
        assert "Source_Code**: 2" in summary
        assert "Software_Specification**: 1" in summary


class TestREADMEGeneration:
    """Test README generation."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_generate_readme(self, service):
        """Test README.md generation."""
        mock_project = Mock()
        mock_project.name = "Awesome Project"
        mock_project.description = "An awesome test project"
        
        mock_artifacts = [
            Mock(
                artifact_type=ArtifactType.SOURCE_CODE,
                source_agent="coder",
                artifact_metadata={}
            ),
            Mock(
                artifact_type=ArtifactType.SOFTWARE_SPECIFICATION, 
                source_agent="analyst",
                artifact_metadata={}
            )
        ]
        
        readme = service._generate_readme(mock_project, mock_artifacts)
        
        assert "# Awesome Project" in readme
        assert "An awesome test project" in readme
        assert "## Project Structure" in readme
        assert "### Source_Code" in readme
        assert "### Software_Specification" in readme
        assert "Generated by coder" in readme
        assert "Generated by analyst" in readme
        assert "BotArmy" in readme


class TestArtifactCleanup:
    """Test artifact cleanup functionality."""
    
    @pytest.fixture
    def service(self):
        return ArtifactService()
    
    def test_cleanup_old_artifacts(self, service):
        """Test cleanup of old artifact files."""
        with patch('pathlib.Path.iterdir') as mock_iterdir, \
             patch('pathlib.Path.is_file') as mock_is_file, \
             patch('pathlib.Path.stat') as mock_stat, \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            # Mock old file
            old_file = Mock()
            old_file.is_file.return_value = True
            old_file.stat.return_value.st_mtime = datetime.now().timestamp() - 48*3600  # 48 hours ago
            
            # Mock new file  
            new_file = Mock()
            new_file.is_file.return_value = True
            new_file.stat.return_value.st_mtime = datetime.now().timestamp() - 1*3600   # 1 hour ago
            
            mock_iterdir.return_value = [old_file, new_file]
            
            service.cleanup_old_artifacts(max_age_hours=24)
            
            # Should only delete old file
            old_file.unlink.assert_called_once()
            new_file.unlink.assert_not_called()


class TestWebSocketNotifications:
    """Test WebSocket notification functionality."""
    
    @pytest.fixture 
    def service(self):
        return ArtifactService()
    
    @pytest.mark.asyncio
    async def test_notify_artifacts_ready(self, service):
        """Test artifacts ready notification."""
        project_id = uuid4()
        
        with patch('app.services.artifact_service.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_project = AsyncMock()
            
            await service.notify_artifacts_ready(project_id)
            
            mock_ws.broadcast_to_project.assert_called_once()
            call_args = mock_ws.broadcast_to_project.call_args
            event, project_id_str = call_args[0]
            
            assert project_id_str == str(project_id)
            assert event.event_type == "artifact_created"
            assert event.data["download_available"] is True
            assert "generated_at" in event.data
    
    @pytest.mark.asyncio
    async def test_notify_artifacts_ready_handles_websocket_errors(self, service):
        """Test graceful handling of WebSocket notification errors."""
        project_id = uuid4()
        
        with patch('app.services.artifact_service.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_project = AsyncMock(side_effect=Exception("WebSocket error"))
            
            # Should not raise exception
            await service.notify_artifacts_ready(project_id)
            
            # WebSocket broadcast should have been attempted
            mock_ws.broadcast_to_project.assert_called_once()