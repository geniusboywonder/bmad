"""Unit tests for Project Completion Service - Sprint 3."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from app.services.project_completion_service import ProjectCompletionService, project_completion_service
from app.models.task import TaskStatus


class TestProjectCompletionServiceInitialization:
    """Test ProjectCompletionService initialization."""
    
    def test_service_initializes_correctly(self):
        """Test that service initializes correctly."""
        service = ProjectCompletionService()
        assert isinstance(service, ProjectCompletionService)
    
    def test_global_service_exists(self):
        """Test that global service instance exists."""
        assert project_completion_service is not None
        assert isinstance(project_completion_service, ProjectCompletionService)


class TestCompletionDetectionLogic:
    """Test completion detection algorithm - S3-UNIT-007."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.fixture
    def mock_project(self):
        """Mock project for testing."""
        mock_project = Mock()
        mock_project.id = uuid4()
        mock_project.name = "Test Project"
        mock_project.status = "active"
        return mock_project
    
    @pytest.mark.asyncio
    async def test_completion_detection_all_tasks_completed(self, service, mock_project):
        """Test completion detection when all tasks are completed."""
        mock_db = Mock()
        project_id = mock_project.id
        
        # Mock project exists
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock completed tasks
        completed_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = completed_tasks
        
        with patch.object(service, '_handle_project_completion') as mock_handle:
            mock_handle.return_value = None
            
            result = await service.check_project_completion(project_id, mock_db)
            
            assert result is True
            mock_handle.assert_called_once_with(project_id, mock_db)
    
    @pytest.mark.asyncio
    async def test_completion_detection_mixed_task_states(self, service, mock_project):
        """Test completion detection with mixed task states."""
        mock_db = Mock()
        project_id = mock_project.id
        
        # Mock project exists
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock mixed task states
        mixed_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.RUNNING),
            Mock(status=TaskStatus.PENDING)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mixed_tasks
        
        result = await service.check_project_completion(project_id, mock_db)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_completion_detection_no_tasks(self, service, mock_project):
        """Test completion detection with no tasks."""
        mock_db = Mock()
        project_id = mock_project.id
        
        # Mock project exists
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock no tasks
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await service.check_project_completion(project_id, mock_db)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_completion_detection_project_not_found(self, service):
        """Test completion detection with non-existent project."""
        mock_db = Mock()
        project_id = uuid4()
        
        # Mock project not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service.check_project_completion(project_id, mock_db)
        
        assert result is False


class TestCompletionIndicators:
    """Test completion indicators evaluation - S3-UNIT-008."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    def test_completion_indicators_deployment_task(self, service):
        """Test completion indicators detect deployment completion."""
        tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Execute deployment to production environment"
            ),
            Mock(
                status=TaskStatus.COMPLETED, 
                instructions="Run unit tests"
            )
        ]
        
        result = service._has_completion_indicators(tasks)
        assert result is True
    
    def test_completion_indicators_final_check_task(self, service):
        """Test completion indicators detect final check completion."""
        tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Perform final check of all components"
            ),
            Mock(
                status=TaskStatus.RUNNING,
                instructions="Code review in progress" 
            )
        ]
        
        result = service._has_completion_indicators(tasks)
        assert result is True
    
    def test_completion_indicators_project_completed_keyword(self, service):
        """Test completion indicators detect 'project completed' keyword."""
        tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Mark project completed and generate final artifacts"
            )
        ]
        
        result = service._has_completion_indicators(tasks)
        assert result is True
    
    def test_completion_indicators_no_completion_keywords(self, service):
        """Test completion indicators when no completion keywords present."""
        tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Write unit tests for user service"
            ),
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Implement user authentication"
            )
        ]
        
        result = service._has_completion_indicators(tasks)
        assert result is False
    
    def test_completion_indicators_case_insensitive(self, service):
        """Test completion indicators are case insensitive."""
        tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="DEPLOYMENT completed successfully"
            )
        ]
        
        result = service._has_completion_indicators(tasks)
        assert result is True


class TestEdgeCaseHandling:
    """Test edge case handling - S3-UNIT-009."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_completion_with_failed_tasks(self, service):
        """Test completion detection with failed tasks."""
        mock_db = Mock()
        project_id = uuid4()
        
        mock_project = Mock()
        mock_project.id = project_id
        mock_project.status = "active"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock tasks with failures
        mixed_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.FAILED),
            Mock(status=TaskStatus.COMPLETED)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mixed_tasks
        
        result = await service.check_project_completion(project_id, mock_db)
        
        # Should not be complete with failed tasks
        assert result is False
    
    @pytest.mark.asyncio
    async def test_completion_detection_database_error(self, service):
        """Test graceful handling of database errors."""
        mock_db = Mock()
        project_id = uuid4()
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection failed")
        
        result = await service.check_project_completion(project_id, mock_db)
        
        # Should return False on error, not raise exception
        assert result is False
    
    @pytest.mark.asyncio
    async def test_completion_with_completion_indicators_overrides_incomplete_tasks(self, service):
        """Test that completion indicators can override incomplete task status."""
        mock_db = Mock()
        project_id = uuid4()
        
        mock_project = Mock()
        mock_project.id = project_id
        mock_project.status = "active"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock tasks - not all completed but has completion indicator
        mixed_tasks = [
            Mock(
                status=TaskStatus.COMPLETED,
                instructions="Final deployment completed successfully"
            ),
            Mock(
                status=TaskStatus.RUNNING,
                instructions="Optional cleanup in progress"
            )
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mixed_tasks
        
        with patch.object(service, '_handle_project_completion') as mock_handle:
            mock_handle.return_value = None
            
            result = await service.check_project_completion(project_id, mock_db)
            
            # Should be complete due to completion indicator
            assert result is True
            mock_handle.assert_called_once_with(project_id, mock_db)


class TestProjectCompletionHandling:
    """Test project completion handling logic."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_handle_project_completion_updates_status(self, service):
        """Test that completion handling updates project status."""
        mock_db = Mock()
        project_id = uuid4()
        
        mock_project = Mock()
        mock_project.status = "active"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        with patch.object(service, '_emit_project_completion_event') as mock_emit, \
             patch.object(service, '_auto_generate_artifacts') as mock_generate:
            
            mock_emit.return_value = None
            mock_generate.return_value = None
            
            await service._handle_project_completion(project_id, mock_db)
            
            # Verify project status updated
            assert mock_project.status == "completed"
            assert mock_project.updated_at is not None
            mock_db.commit.assert_called_once()
            
            # Verify completion workflow called
            mock_emit.assert_called_once_with(project_id)
            mock_generate.assert_called_once_with(project_id, mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_project_completion_database_error(self, service):
        """Test graceful handling of database errors during completion."""
        mock_db = Mock()
        project_id = uuid4()
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        with patch.object(service, '_emit_project_completion_event') as mock_emit:
            mock_emit.return_value = None
            
            # Should not raise exception
            await service._handle_project_completion(project_id, mock_db)
            
            # Database rollback should be called
            mock_db.rollback.assert_called_once()


class TestWebSocketEventEmission:
    """Test WebSocket event emission."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_emit_project_completion_event(self, service):
        """Test project completion event emission."""
        project_id = uuid4()
        
        with patch('app.services.project_completion_service.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_project = AsyncMock()
            
            await service._emit_project_completion_event(project_id)
            
            mock_ws.broadcast_to_project.assert_called_once()
            call_args = mock_ws.broadcast_to_project.call_args
            event, project_id_str = call_args[0]
            
            assert project_id_str == str(project_id)
            assert event.event_type == "workflow_event"
            assert event.data["event"] == "project_completed"
            assert "completed_at" in event.data
            assert event.data["artifacts_generating"] is True
    
    @pytest.mark.asyncio
    async def test_emit_project_completion_event_websocket_error(self, service):
        """Test graceful handling of WebSocket errors."""
        project_id = uuid4()
        
        with patch('app.services.project_completion_service.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_project = AsyncMock(side_effect=Exception("WebSocket error"))
            
            # Should not raise exception
            await service._emit_project_completion_event(project_id)
            
            # WebSocket broadcast should have been attempted
            mock_ws.broadcast_to_project.assert_called_once()


class TestAutoArtifactGeneration:
    """Test automatic artifact generation."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_auto_generate_artifacts_success(self, service):
        """Test successful automatic artifact generation."""
        project_id = uuid4()
        mock_db = Mock()
        
        with patch('app.services.project_completion_service.artifact_service') as mock_artifact_service:
            # Mock successful artifact generation
            mock_artifacts = [Mock(), Mock(), Mock()]  # 3 artifacts
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=mock_artifacts)
            mock_artifact_service.create_project_zip = AsyncMock(return_value="/tmp/project.zip")
            mock_artifact_service.notify_artifacts_ready = AsyncMock()
            
            await service._auto_generate_artifacts(project_id, mock_db)
            
            # Verify artifact generation workflow
            mock_artifact_service.generate_project_artifacts.assert_called_once_with(project_id, mock_db)
            mock_artifact_service.create_project_zip.assert_called_once_with(project_id, mock_artifacts)
            mock_artifact_service.notify_artifacts_ready.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_auto_generate_artifacts_no_artifacts(self, service):
        """Test artifact generation with no artifacts generated."""
        project_id = uuid4()
        mock_db = Mock()
        
        with patch('app.services.project_completion_service.artifact_service') as mock_artifact_service:
            # Mock no artifacts generated
            mock_artifact_service.generate_project_artifacts = AsyncMock(return_value=[])
            
            await service._auto_generate_artifacts(project_id, mock_db)
            
            # ZIP creation should not be called
            mock_artifact_service.create_project_zip.assert_not_called()
            mock_artifact_service.notify_artifacts_ready.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auto_generate_artifacts_error_handling(self, service):
        """Test error handling in artifact generation."""
        project_id = uuid4()
        mock_db = Mock()
        
        with patch('app.services.project_completion_service.artifact_service') as mock_artifact_service:
            # Mock artifact generation error
            mock_artifact_service.generate_project_artifacts = AsyncMock(
                side_effect=Exception("Artifact generation failed")
            )
            
            # Should not raise exception
            await service._auto_generate_artifacts(project_id, mock_db)
            
            # Should have attempted artifact generation
            mock_artifact_service.generate_project_artifacts.assert_called_once_with(project_id, mock_db)


class TestForceCompletion:
    """Test force completion functionality."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_force_project_completion_success(self, service):
        """Test successful force completion."""
        project_id = uuid4()
        mock_db = Mock()
        
        mock_project = Mock()
        mock_project.id = project_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        with patch.object(service, '_handle_project_completion') as mock_handle:
            mock_handle.return_value = None
            
            result = await service.force_project_completion(project_id, mock_db)
            
            assert result is True
            mock_handle.assert_called_once_with(project_id, mock_db)
    
    @pytest.mark.asyncio
    async def test_force_project_completion_project_not_found(self, service):
        """Test force completion with non-existent project."""
        project_id = uuid4()
        mock_db = Mock()
        
        # Mock project not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service.force_project_completion(project_id, mock_db)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_force_project_completion_error(self, service):
        """Test force completion with error."""
        project_id = uuid4()
        mock_db = Mock()
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.force_project_completion(project_id, mock_db)
        
        assert result is False


class TestCompletionStatusMetrics:
    """Test completion status metrics."""
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    async def test_get_project_completion_status_detailed_metrics(self, service):
        """Test detailed completion status metrics."""
        project_id = uuid4()
        mock_db = Mock()
        
        # Mock project
        mock_project = Mock()
        mock_project.id = project_id
        mock_project.name = "Test Project"
        mock_project.status = "active"
        mock_project.updated_at = datetime.now()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        
        # Mock tasks with various states
        mock_tasks = [
            Mock(status=TaskStatus.COMPLETED),
            Mock(status=TaskStatus.COMPLETED), 
            Mock(status=TaskStatus.RUNNING),
            Mock(status=TaskStatus.PENDING),
            Mock(status=TaskStatus.FAILED)
        ]
        
        # Set up query chain for tasks
        task_query = Mock()
        task_query.filter.return_value = Mock()
        task_query.filter.return_value.all.return_value = mock_tasks
        
        # Set up query chain for artifacts count
        artifact_query = Mock() 
        artifact_query.filter.return_value = Mock()
        artifact_query.filter.return_value.count.return_value = 3
        
        # Configure query method to return appropriate mocks
        def query_side_effect(model):
            if hasattr(model, '__name__') and 'Task' in model.__name__:
                return task_query
            elif hasattr(model, '__name__') and 'Artifact' in model.__name__:
                return artifact_query
            else:  # ProjectDB
                return mock_db.query.return_value
        
        mock_db.query.side_effect = query_side_effect
        
        with patch('app.services.project_completion_service.artifact_service') as mock_artifact_service:
            mock_zip_path = Mock()
            mock_zip_path.exists.return_value = True
            mock_artifact_service.artifacts_dir = Mock()
            mock_artifact_service.artifacts_dir.__truediv__ = Mock(return_value=mock_zip_path)
            
            status = await service.get_project_completion_status(project_id, mock_db)
        
        assert status["project_id"] == str(project_id)
        assert status["project_name"] == "Test Project"
        assert status["total_tasks"] == 5
        assert status["completed_tasks"] == 2
        assert status["failed_tasks"] == 1
        assert status["pending_tasks"] == 1
        assert status["running_tasks"] == 1
        assert status["completion_percentage"] == 40.0  # 2/5 * 100
        assert status["artifacts_count"] == 3
        assert status["artifacts_available"] is True
        assert status["is_complete"] is False
    
    @pytest.mark.asyncio
    async def test_get_project_completion_status_project_not_found(self, service):
        """Test completion status with non-existent project."""
        project_id = uuid4()
        mock_db = Mock()
        
        # Mock project not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        status = await service.get_project_completion_status(project_id, mock_db)
        
        assert "error" in status
        assert status["error"] == "Project not found"
    
    @pytest.mark.asyncio
    async def test_get_project_completion_status_database_error(self, service):
        """Test completion status with database error."""
        project_id = uuid4()
        mock_db = Mock()
        
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection failed")
        
        status = await service.get_project_completion_status(project_id, mock_db)
        
        assert "error" in status
        assert "Failed to get completion status" in status["error"]