"""Unit tests for Project Completion Service - Sprint 3.

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies remain appropriately mocked.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from app.services.project_completion_service import ProjectCompletionService, project_completion_service
from app.models.task import TaskStatus
from tests.utils.database_test_utils import DatabaseTestManager


class TestProjectCompletionServiceInitialization:
    """Test ProjectCompletionService initialization."""
    
    @pytest.mark.real_data
    def test_service_initializes_correctly(self):
        """Test that service initializes correctly."""
        service = ProjectCompletionService()
        assert isinstance(service, ProjectCompletionService)
    
    @pytest.mark.real_data
    def test_global_service_exists(self):
        """Test that global service instance exists."""
        assert project_completion_service is not None
        assert isinstance(project_completion_service, ProjectCompletionService)


class TestCompletionDetectionLogic:
    """Test completion detection algorithm - S3-UNIT-007."""
    
    @pytest.fixture
    def db_manager(self):
        """Real database manager for project completion tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_completion_detection_all_tasks_completed(self, service, db_manager):
        """Test completion detection when all tasks are completed with real database."""
        # Create real project
        project = db_manager.create_test_project(
            name="Test Project",
            status="active"
        )
        
        # Create completed tasks
        for i in range(3):
            db_manager.create_test_task(
                project_id=project.id,
                agent_type="analyst",
                status=TaskStatus.COMPLETED
            )
        
        with db_manager.get_session() as session:
            # Mock external completion handling (external dependency)
            with patch.object(service, '_handle_project_completion') as mock_handle:
                mock_handle.return_value = None
                
                result = await service.check_project_completion(project.id, session)
                
                assert result is True
                mock_handle.assert_called_once_with(project.id, session)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_completion_detection_mixed_task_states(self, service, db_manager):
        """Test completion detection with mixed task states using real database."""
        # Create real project
        project = db_manager.create_test_project(
            name="Mixed Tasks Project",
            status="active"
        )
        
        # Create tasks with mixed states
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="analyst",
            status=TaskStatus.COMPLETED
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="architect", 
            status=TaskStatus.WORKING
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="coder",
            status=TaskStatus.PENDING
        )
        
        with db_manager.get_session() as session:
            # Test completion detection with mixed states
            result = await service.check_project_completion(project.id, session)
            
            # Should not be complete with mixed task states
            assert result is False
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_completion_detection_no_tasks(self, service, db_manager):
        """Test completion detection with no tasks using real database."""
        # Create real project with no tasks
        project = db_manager.create_test_project(
            name="No Tasks Project",
            status="active"
        )
        
        with db_manager.get_session() as session:
            result = await service.check_project_completion(project.id, session)
            
            # Should not be complete with no tasks
            assert result is False
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_completion_detection_project_not_found(self, service, db_manager):
        """Test completion detection with non-existent project using real database."""
        non_existent_project_id = uuid4()
        
        with db_manager.get_session() as session:
            result = await service.check_project_completion(non_existent_project_id, session)
            
            # Should return False for non-existent project
            assert result is False


class TestCompletionIndicators:
    """Test completion indicators evaluation - S3-UNIT-008."""
    
    @pytest.fixture
    def db_manager(self):
        """Real database manager for completion indicator tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.real_data
    def test_completion_indicators_deployment_task(self, service, db_manager):
        """Test completion indicators detect deployment completion with real data."""
        # Create real project
        project = db_manager.create_test_project(name="Deployment Test Project")
        
        # Create tasks with deployment indicators
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="deployer",
            status=TaskStatus.COMPLETED,
            instructions="Execute deployment to production environment"
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type="tester",
            status=TaskStatus.COMPLETED,
            instructions="Run unit tests"
        )
        
        with db_manager.get_session() as session:
            from app.database.models import TaskDB
            tasks = session.query(TaskDB).filter(TaskDB.project_id == project.id).all()
        
        result = service._has_completion_indicators(tasks)
        assert result is True
    



class TestEdgeCaseHandling:
    """Test edge case handling - S3-UNIT-009."""
    
    @pytest.fixture
    def db_manager(self):
        """Real database manager for edge case tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()
    
    @pytest.fixture
    def service(self):
        return ProjectCompletionService()
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    async def test_completion_with_failed_tasks(self, service, db_manager):
        """Test completion detection with failed tasks using real database."""
        # Create real project and tasks
        project = db_manager.create_test_project(name="Failed Tasks Test")
        
        # Create tasks with mixed statuses including failures
        task1 = db_manager.create_test_task(project_id=project.id, agent_type="analyst", status="completed")
        task2 = db_manager.create_test_task(project_id=project.id, agent_type="architect", status="failed")
        task3 = db_manager.create_test_task(project_id=project.id, agent_type="coder", status="completed")
        
        with db_manager.get_session() as session:
            result = await service.check_project_completion(project.id, session)
            
            # Should not be complete with failed tasks
            assert result is False
            
            # Verify database state - use UUID object directly
            db_checks = [
                {
                    'table': 'tasks',
                    'conditions': {'project_id': project.id},
                    'count': 3
                }
            ]
            assert db_manager.verify_database_state(db_checks)
    
    @pytest.mark.asyncio
    @pytest.mark.external_service
    async def test_completion_detection_database_error(self, service, db_manager):
        """Test graceful handling of database errors."""
        # Create real project
        project = db_manager.create_test_project(name="Database Error Test")
        
        # Create a broken session that will cause database errors
        with db_manager.get_session() as session:
            # Close the session to simulate database connection failure
            session.close()
            
            result = await service.check_project_completion(project.id, session)
            
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
                status=TaskStatus.WORKING,
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
    @pytest.mark.external_service
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
    @pytest.mark.external_service
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
            Mock(status=TaskStatus.WORKING),
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
        assert status["working_tasks"] == 1
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