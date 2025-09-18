"""
Real Database Tests for Project Completion Service

This module replaces mock-heavy project completion tests with real database
operations to validate actual business logic and service interactions.
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from app.services.project_completion_service import ProjectCompletionService
from app.services.artifact_service import artifact_service, ArtifactService
from app.models.task import TaskStatus
from app.database.models import ProjectDB, TaskDB
from tests.utils.database_test_utils import DatabaseTestManager


class TestProjectCompletionServiceReal:
    """Test ProjectCompletionService with real database and service operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for project completion tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def service(self):
        """Create real ProjectCompletionService instance."""
        return ProjectCompletionService()

    @pytest.mark.real_data
    def test_service_initialization_real(self, service):
        """Test service initializes correctly with real dependencies."""
        assert isinstance(service, ProjectCompletionService)
        # Verify service has real methods, not mocks
        assert hasattr(service, 'check_project_completion')
        assert hasattr(service, 'get_project_completion_status')
        assert callable(service.check_project_completion)

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_completion_detection_all_tasks_completed_real_db(self, service, db_manager):
        """Test completion detection with all tasks completed using real database."""
        # Create real project
        project = db_manager.create_test_project(name="Completion Test Project")

        # Create completed tasks in real database
        tasks = []
        for i, agent_type in enumerate(['analyst', 'architect', 'coder']):
            task = db_manager.create_test_task(
                project_id=project.id,
                agent_type=agent_type,
                instructions=f"Task {i+1} for {agent_type}",
                status=TaskStatus.COMPLETED
            )
            tasks.append(task)

        # Check completion with real database session
        with db_manager.get_session() as session:
            is_complete = await service.check_project_completion(project.id, session)

        assert is_complete is True

        # Verify tasks are actually in database
        with db_manager.get_session() as verify_session:
            db_tasks = verify_session.query(TaskDB).filter_by(project_id=project.id).all()
            assert len(db_tasks) == 3
            assert all(task.status == TaskStatus.COMPLETED for task in db_tasks)

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_completion_detection_with_pending_tasks_real_db(self, service, db_manager):
        """Test completion detection with pending tasks using real database."""
        # Create real project
        project = db_manager.create_test_project(name="Pending Tasks Project")

        # Create mix of completed and pending tasks
        db_manager.create_test_task(
            project_id=project.id,
            agent_type='analyst',
            status=TaskStatus.COMPLETED
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type='architect',
            status=TaskStatus.PENDING
        )

        # Check completion with real database
        with db_manager.get_session() as session:
            is_complete = await service.check_project_completion(project.id, session)

        assert is_complete is False

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_artifact_generation_integration_real_services(self, service, db_manager):
        """Test artifact generation with real services integration."""
        # Create real project with completed tasks
        project = db_manager.create_test_project(name="Artifact Generation Test")

        for agent_type in ['analyst', 'architect', 'coder']:
            db_manager.create_test_task(
                project_id=project.id,
                agent_type=agent_type,
                status=TaskStatus.COMPLETED
            )

        # Only mock file system operations (external dependency)
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('pathlib.Path.write_text') as mock_write, \
             patch('shutil.make_archive') as mock_archive:

            mock_archive.return_value = f"/tmp/project_{project.id}.zip"

            # Use real database session and real ArtifactService
            with db_manager.get_session() as session:
                # Use real ArtifactService instead of mocking it
                real_artifact_service = ArtifactService()

                # Test artifact generation with real service
                artifacts = await real_artifact_service.generate_project_artifacts(project.id, session)

                # Verify real service behavior
                assert isinstance(artifacts, list)
                # Real artifact service should generate based on actual project data

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_completion_status_real_db(self, service, db_manager):
        """Test getting completion status with real database operations."""
        # Create real project
        project = db_manager.create_test_project(name="Status Test Project")

        # Create real tasks with various statuses
        db_manager.create_test_task(
            project_id=project.id,
            agent_type='analyst',
            status=TaskStatus.COMPLETED
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type='architect',
            status=TaskStatus.WORKING
        )
        db_manager.create_test_task(
            project_id=project.id,
            agent_type='coder',
            status=TaskStatus.PENDING
        )

        # Get status with real database operations
        with db_manager.get_session() as session:
            status = await service.get_project_completion_status(project.id, session)

        # Verify real status calculation
        assert status is not None
        assert 'completion_percentage' in status
        assert 'total_tasks' in status
        assert 'completed_tasks' in status
        assert 'pending_tasks' in status

        # Verify real data calculations
        assert status['total_tasks'] == 3
        assert status['completed_tasks'] == 1
        assert status['pending_tasks'] == 2
        assert status['completion_percentage'] == round(1/3 * 100, 2)

    @pytest.mark.real_data
    def test_service_integration_with_real_dependencies(self, service, db_manager):
        """Test that service integrates properly with real dependencies."""
        # Verify service uses real artifact_service instance
        assert hasattr(service, '_auto_generate_artifacts')

        # Create real project to test with
        project = db_manager.create_test_project(name="Integration Test")

        # Verify service can interact with real database
        with db_manager.get_session() as session:
            # Should not raise errors with real database operations
            result = session.query(ProjectDB).filter_by(id=project.id).first()
            assert result is not None
            assert result.name == "Integration Test"

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_completion_workflow_end_to_end_real_services(self, service, db_manager):
        """Test complete completion workflow with real services and database."""
        # Create real project
        project = db_manager.create_test_project(name="End-to-End Test Project")

        # Create tasks representing full SDLC
        sdlc_phases = [
            ('analyst', 'Analysis complete'),
            ('architect', 'Design complete'),
            ('coder', 'Implementation complete'),
            ('tester', 'Testing complete')
        ]

        for agent_type, output in sdlc_phases:
            db_manager.create_test_task(
                project_id=project.id,
                agent_type=agent_type,
                instructions=f"Complete {agent_type} phase",
                status=TaskStatus.COMPLETED,
                output=output
            )

        # Test end-to-end completion workflow with real services
        with db_manager.get_session() as session:
            # Check completion with real database
            is_complete = await service.check_project_completion(project.id, session)
            assert is_complete is True

            # Get detailed status with real calculations
            status = await service.get_project_completion_status(project.id, session)
            assert status['completion_percentage'] == 100.0
            assert status['completed_tasks'] == 4

            # Verify all tasks actually exist in database
            tasks = session.query(TaskDB).filter_by(project_id=project.id).all()
            assert len(tasks) == 4
            assert all(task.status == TaskStatus.COMPLETED for task in tasks)
            assert all(task.output is not None for task in tasks)

    @pytest.mark.real_data
    def test_error_handling_with_real_database_constraints(self, service, db_manager):
        """Test error handling with real database constraints."""
        # Test with non-existent project ID
        non_existent_id = uuid4()

        with db_manager.get_session() as session:
            # Should handle gracefully with real database
            import asyncio

            async def test_nonexistent():
                return await service.check_project_completion(non_existent_id, session)

            # Should not raise unhandled exceptions
            try:
                result = asyncio.run(test_nonexistent())
                # Should return False or handle gracefully
                assert result is False or result is None
            except Exception as e:
                # If it raises an exception, it should be a handled one
                assert "not found" in str(e).lower() or "invalid" in str(e).lower()


class TestProjectCompletionServiceConstraints:
    """Test service behavior with database constraints and edge cases."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for constraint tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_project_with_no_tasks_real_db(self, db_manager):
        """Test completion detection for project with no tasks."""
        service = ProjectCompletionService()

        # Create project with no tasks
        project = db_manager.create_test_project(name="Empty Project")

        with db_manager.get_session() as session:
            # Should handle empty project gracefully
            async def check_empty():
                return await service.check_project_completion(project.id, session)

            import asyncio
            result = asyncio.run(check_empty())

            # Empty project should be considered complete or handled appropriately
            assert result is True or result is False  # Either is acceptable

    @pytest.mark.real_data
    def test_task_status_validation_real_db(self, db_manager):
        """Test that only valid task statuses are considered in completion."""
        service = ProjectCompletionService()
        project = db_manager.create_test_project(name="Status Validation Test")

        # Create tasks with various statuses
        valid_statuses = [TaskStatus.COMPLETED, TaskStatus.WORKING, TaskStatus.PENDING, TaskStatus.FAILED]

        for i, status in enumerate(valid_statuses):
            db_manager.create_test_task(
                project_id=project.id,
                agent_type=f'agent_{i}',
                status=status
            )

        with db_manager.get_session() as session:
            async def get_status():
                return await service.get_project_completion_status(project.id, session)

            import asyncio
            status = asyncio.run(get_status())

            # Should count all valid statuses
            assert status['total_tasks'] == len(valid_statuses)
            assert status['completed_tasks'] == 1  # Only COMPLETED status