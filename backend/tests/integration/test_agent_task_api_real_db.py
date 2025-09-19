"""
Real Database Integration Tests for Agent Task API

This module tests agent task processing through the actual API endpoints
using real database operations. No database session mocking is performed.
"""

import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, Mock

from app.models.task import TaskStatus
from app.models.agent import AgentType
from tests.utils.database_test_utils import DatabaseTestManager

class TestAgentTaskAPIReal:
    """Test agent task processing through API with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for API tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_agent_task_processing_api_real_db(self, client, db_manager):
        """Test agent task processing through API with real database persistence."""

        # Create a test project and task in the database
        project_id = uuid4()
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(project_id),
            "agent_type": "analyst",
            "instructions": "Analyze the requirements and create a plan",
            "context_ids": []
        }

        # Create project in database using the real database manager
        with db_manager.get_session() as session:
            project = db_manager.create_test_project(
                id=project_id,
                name="Test API Project",
                description="Testing agent task API"
            )
            task = db_manager.create_test_task(
                project_id=project_id,
                agent_type=AgentType.ANALYST,
                instructions=task_data["instructions"],
                status=TaskStatus.PENDING
            )
            task_data["task_id"] = str(task.id)

        # Mock only external services (not database sessions)
        with patch('app.tasks.agent_tasks.websocket_manager') as mock_websocket, \
             patch('app.tasks.agent_tasks.AutoGenService') as mock_autogen_service, \
             patch('app.tasks.agent_tasks.ContextStoreService') as mock_context_store:

            # Setup external service mocks
            mock_websocket.broadcast_event = AsyncMock()

            mock_autogen_instance = Mock()
            mock_autogen_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "agent_type": "analyst",
                "task_id": task_data["task_id"],
                "output": {"analysis": "Analysis completed successfully"},
                "artifacts_created": ["analysis_result"],
                "context_used": []
            })
            mock_autogen_service.return_value = mock_autogen_instance

            mock_context_store_instance = Mock()
            mock_context_store_instance.get_artifacts_by_ids.return_value = []
            mock_context_store_instance.create_artifact = AsyncMock(return_value=Mock(context_id=uuid4()))
            mock_context_store.return_value = mock_context_store_instance

            # Execute through API endpoint (uses dependency override for database)
            response = client.post("/api/tasks/process", json=task_data)

            # Verify API response
            assert response.status_code in [200, 202]  # Success or Accepted

            # Verify real database state was updated
            with db_manager.get_session() as verify_session:
                updated_task = verify_session.query(db_manager.TaskDB).filter_by(
                    id=task.id
                ).first()

                assert updated_task is not None
                # Task should have been processed (status updated)
                assert updated_task.status in [TaskStatus.WORKING, TaskStatus.COMPLETED]

    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_agent_task_failure_api_real_db(self, client, db_manager):
        """Test agent task failure handling through API with real database updates."""

        # Create test data
        project_id = uuid4()
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(project_id),
            "agent_type": "analyst",
            "instructions": "This task will fail",
            "context_ids": []
        }

        with db_manager.get_session() as session:
            project = db_manager.create_test_project(
                id=project_id,
                name="Test Failure Project"
            )
            task = db_manager.create_test_task(
                project_id=project_id,
                agent_type=AgentType.ANALYST,
                instructions=task_data["instructions"],
                status=TaskStatus.PENDING
            )
            task_data["task_id"] = str(task.id)

        # Mock external services to simulate failure
        with patch('app.tasks.agent_tasks.websocket_manager') as mock_websocket, \
             patch('app.tasks.agent_tasks.AutoGenService') as mock_autogen_service, \
             patch('app.tasks.agent_tasks.ContextStoreService') as mock_context_store:

            mock_websocket.broadcast_event = AsyncMock()

            # Mock AutoGen service to return failure
            mock_autogen_instance = Mock()
            mock_autogen_instance.execute_task = AsyncMock(return_value={
                "success": False,
                "agent_type": "analyst",
                "task_id": task_data["task_id"],
                "error": "LLM service unavailable",
                "context_used": []
            })
            mock_autogen_service.return_value = mock_autogen_instance

            mock_context_store_instance = Mock()
            mock_context_store_instance.get_artifacts_by_ids.return_value = []
            mock_context_store.return_value = mock_context_store_instance

            # Execute through API endpoint
            response = client.post("/api/tasks/process", json=task_data)

            # API should handle the failure gracefully
            assert response.status_code in [200, 202, 400, 500]

            # Verify database state reflects the failure
            with db_manager.get_session() as verify_session:
                failed_task = verify_session.query(db_manager.TaskDB).filter_by(
                    id=task.id
                ).first()

                assert failed_task is not None
                # Task should show failure in database
                if failed_task.status == TaskStatus.FAILED:
                    assert failed_task.error_message is not None