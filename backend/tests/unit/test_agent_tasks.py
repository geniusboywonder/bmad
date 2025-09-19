"""Tests for agent task processing."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from app.tasks.agent_tasks import process_agent_task, validate_task_data
from app.models.task import TaskStatus
from app.models.agent import AgentType
from app.database.models import TaskDB
from uuid import UUID

class TestAgentTaskProcessing:
    """Test cases for agent task processing with real execution."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        task_db = Mock(spec=TaskDB)
        task_db.id = uuid4()
        task_db.status = TaskStatus.PENDING
        task_db.started_at = None
        task_db.completed_at = None
        task_db.output = None
        task_db.error_message = None

        session.query.return_value.filter.return_value.first.return_value = task_db
        session.add.return_value = None
        session.commit.return_value = None
        session.refresh.return_value = None
        return session

    @pytest.fixture
    def task_data(self):
        """Sample task data for testing."""
        return {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Analyze the user requirements and create a project plan",
            "context_ids": []
        }

    @pytest.mark.mock_data
    def test_validate_task_data_uuid_conversion(self, task_data):
        """Test that UUID strings are properly converted to UUID objects."""
        result = validate_task_data(task_data)

        # Verify UUID conversion
        assert isinstance(result["task_id"], UUID)
        assert isinstance(result["project_id"], UUID)
        assert str(result["task_id"]) == task_data["task_id"]
        assert str(result["project_id"]) == task_data["project_id"]

        # Verify defaults are applied correctly
        assert result["from_agent"] == "orchestrator"
        assert result["expected_outputs"] == ["task_result"]
        assert result["priority"] == 1

    @pytest.mark.mock_data
    def test_validate_task_data_custom_values_uuid_conversion(self):
        """Test UUID conversion with custom values."""
        context_id = str(uuid4())
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions",
            "from_agent": "custom_agent",
            "expected_outputs": ["custom_output"],
            "priority": 5,
            "context_ids": [context_id]
        }

        result = validate_task_data(task_data)

        # Verify UUID conversion for all IDs
        assert isinstance(result["task_id"], UUID)
        assert isinstance(result["project_id"], UUID)
        assert isinstance(result["context_ids"][0], UUID)
        assert str(result["context_ids"][0]) == context_id

        # Verify custom values are preserved
        assert result["from_agent"] == "custom_agent"
        assert result["expected_outputs"] == ["custom_output"]
        assert result["priority"] == 5

    # ❌ DEPRECATED: This test uses inappropriate database mocking
    # ✅ USE INSTEAD: test_process_agent_task_failure_real_db in test_agent_tasks_real_db.py
    @pytest.mark.skip(reason="DEPRECATED: Uses inappropriate database mocking. Use test_process_agent_task_failure_real_db instead.")
    @pytest.mark.mock_data
    @patch('app.database.connection.get_session')
    @patch('app.tasks.agent_tasks.websocket_manager')
    @patch('app.tasks.agent_tasks.AutoGenService')
    @patch('app.tasks.agent_tasks.ContextStoreService')
    @pytest.mark.mock_data

    def test_process_agent_task_failure(self, mock_context_store, mock_autogen_service,
                                       mock_websocket_manager, mock_get_db, mock_db_session, task_data):
        """Test agent task processing failure handling."""

        # Setup mocks
        mock_get_db.return_value = iter([mock_db_session])
        mock_websocket_manager.broadcast_event = AsyncMock()

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

        # Mock Context Store service
        mock_context_store_instance = Mock()
        mock_context_store_instance.get_artifacts_by_ids.return_value = []
        mock_context_store.return_value = mock_context_store_instance

        # Execute the task directly (not via Celery apply)
        with pytest.raises(Exception) as exc_info:
            asyncio.run(process_agent_task(task_data))

        # Verify the exception message
        assert "Task execution failed" in str(exc_info.value)
        assert "LLM service unavailable" in str(exc_info.value)

        # Verify WebSocket events were sent (started + failed)
        assert mock_websocket_manager.broadcast_event.call_count == 2

    # ❌ DEPRECATED: This test uses inappropriate database mocking
    # ✅ USE INSTEAD: test_process_agent_task_with_context_real_db in test_agent_tasks_real_db.py
    @pytest.mark.skip(reason="DEPRECATED: Uses inappropriate database mocking. Use test_process_agent_task_with_context_real_db instead.")
    @pytest.mark.mock_data
    @patch('app.database.connection.get_session')
    @patch('app.tasks.agent_tasks.websocket_manager')
    @patch('app.tasks.agent_tasks.AutoGenService')
    @patch('app.tasks.agent_tasks.ContextStoreService')
    @pytest.mark.mock_data

    def test_process_agent_task_with_context(self, mock_context_store, mock_autogen_service,
                                           mock_websocket_manager, mock_get_db, mock_db_session, task_data):
        """Test agent task processing with context artifacts."""

        # Add context IDs to task data
        context_id = str(uuid4())
        task_data["context_ids"] = [context_id]

        # Setup mocks
        mock_get_db.return_value = iter([mock_db_session])
        mock_websocket_manager.broadcast_event = AsyncMock()

        # Mock AutoGen service
        mock_autogen_instance = Mock()
        mock_autogen_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "agent_type": "analyst",
            "task_id": task_data["task_id"],
            "output": {"analysis": "Context-based analysis completed"},
            "artifacts_created": ["analysis_result"],
            "context_used": [context_id]
        })
        mock_autogen_service.return_value = mock_autogen_instance

        # Mock Context Store service
        mock_context_store_instance = Mock()
        mock_context_artifact = Mock()
        mock_context_artifact.context_id = context_id
        mock_context_store_instance.get_artifacts_by_ids.return_value = [mock_context_artifact]
        mock_context_store_instance.create_artifact.return_value = Mock(context_id=uuid4())
        mock_context_store.return_value = mock_context_store_instance

        # Execute the task directly
        result = asyncio.run(process_agent_task(task_data))

        # Verify context was retrieved - should be called with UUID objects due to validation
        from uuid import UUID
        mock_context_store_instance.get_artifacts_by_ids.assert_called_once()
        call_args = mock_context_store_instance.get_artifacts_by_ids.call_args[0][0]
        assert len(call_args) == 1
        assert isinstance(call_args[0], UUID)
        assert str(call_args[0]) == context_id

        # Verify the result
        assert result.get("success") == True
        assert context_id in result.get("context_used", [])

    # ❌ DEPRECATED: This test uses inappropriate database mocking
    # ✅ USE INSTEAD: Real database constraint testing in test_agent_tasks_real_db.py
    @pytest.mark.skip(reason="DEPRECATED: Uses inappropriate database mocking. Use real database constraint tests instead.")
    @pytest.mark.mock_data
    @patch('app.database.connection.get_session')
    @patch('app.tasks.agent_tasks.websocket_manager')
    @patch('app.tasks.agent_tasks.AutoGenService')
    @patch('app.tasks.agent_tasks.ContextStoreService')
    @pytest.mark.real_data

    def test_process_agent_task_database_error(self, mock_context_store, mock_autogen_service,
                                             mock_websocket_manager, mock_get_db, task_data):
        """Test handling of database errors during task processing."""

        # Setup mock to raise database error
        mock_db_session = Mock()
        mock_db_session.query.side_effect = Exception("Database connection failed")
        mock_get_db.return_value = iter([mock_db_session])

        mock_websocket_manager.broadcast_event = AsyncMock()

        # Mock services to prevent additional errors
        mock_autogen_instance = Mock()
        mock_autogen_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "agent_type": "analyst",
            "task_id": task_data["task_id"],
            "output": {"analysis": "Test completed"},
            "artifacts_created": [],
            "context_used": []
        })
        mock_autogen_service.return_value = mock_autogen_instance

        mock_context_store_instance = Mock()
        mock_context_store_instance.get_artifacts_by_ids.return_value = []
        mock_context_store.return_value = mock_context_store_instance

        # Execute the task directly - should handle database error gracefully
        result = asyncio.run(process_agent_task(task_data))

        # Verify the task completed despite database error
        assert result.get("success") == True

        # Verify WebSocket events were still sent
        mock_websocket_manager.broadcast_event.assert_called()

    @pytest.mark.mock_data
    def test_validate_task_data_success(self, task_data):
        """Test successful task data validation."""
        result = validate_task_data(task_data)

        assert str(result["task_id"]) == task_data["task_id"]
        assert str(result["project_id"]) == task_data["project_id"]
        assert result["agent_type"] == task_data["agent_type"]
        assert result["instructions"] == task_data["instructions"]
        assert result["context_ids"] == []
        assert result["from_agent"] == "orchestrator"
        assert result["expected_outputs"] == ["task_result"]
        assert result["priority"] == 1

    @pytest.mark.mock_data
    def test_validate_task_data_missing_required_fields(self):
        """Test validation fails with missing required fields."""
        invalid_data = {"task_id": str(uuid4())}  # Missing other required fields

        with pytest.raises(ValueError) as exc_info:
            validate_task_data(invalid_data)

        assert "Missing required field" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_validate_task_data_invalid_uuid(self):
        """Test validation fails with invalid UUID format."""
        invalid_data = {
            "task_id": "invalid-uuid",
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions"
        }

        with pytest.raises(ValueError) as exc_info:
            validate_task_data(invalid_data)

        assert "Invalid task_id format" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_validate_task_data_with_context_ids(self):
        """Test validation with context IDs."""
        context_id = str(uuid4())
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test with context",
            "context_ids": [context_id]
        }

        result = validate_task_data(task_data)
        assert len(result["context_ids"]) == 1
        assert str(result["context_ids"][0]) == context_id

    @pytest.mark.mock_data
    def test_validate_task_data_invalid_context_id(self):
        """Test validation fails with invalid context ID."""
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions",
            "context_ids": ["invalid-uuid"]
        }

        with pytest.raises(ValueError) as exc_info:
            validate_task_data(task_data)

        assert "Invalid context_id format" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_validate_task_data_custom_values(self):
        """Test validation with custom from_agent, expected_outputs, and priority."""
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions",
            "from_agent": "custom_agent",
            "expected_outputs": ["custom_output"],
            "priority": 5
        }

        result = validate_task_data(task_data)
        assert result["from_agent"] == "custom_agent"
        assert result["expected_outputs"] == ["custom_output"]
        assert result["priority"] == 5

    # ❌ DEPRECATED: This test uses inappropriate database mocking
    # ✅ USE INSTEAD: Real artifact persistence testing in test_agent_tasks_real_db.py
    @pytest.mark.skip(reason="DEPRECATED: Uses inappropriate database mocking. Use real artifact persistence tests instead.")
    @pytest.mark.mock_data
    @patch('app.database.connection.get_session')
    @patch('app.tasks.agent_tasks.websocket_manager')
    @patch('app.tasks.agent_tasks.AutoGenService')
    @patch('app.tasks.agent_tasks.ContextStoreService')
    @pytest.mark.mock_data

    def test_process_agent_task_artifact_creation(self, mock_context_store, mock_autogen_service,
                                                mock_websocket_manager, mock_get_db, mock_db_session, task_data):
        """Test that artifacts are properly created on task completion."""

        # Setup mocks
        mock_get_db.return_value = iter([mock_db_session])
        mock_websocket_manager.broadcast_event = AsyncMock()

        # Mock AutoGen service
        mock_autogen_instance = Mock()
        mock_autogen_instance.execute_task = AsyncMock(return_value={
            "success": True,
            "agent_type": "analyst",
            "task_id": task_data["task_id"],
            "output": {"analysis": "Task completed with artifact"},
            "artifacts_created": ["task_result"],
            "context_used": []
        })
        mock_autogen_service.return_value = mock_autogen_instance

        # Mock Context Store service
        mock_context_store_instance = Mock()
        mock_context_store_instance.get_artifacts_by_ids.return_value = []
        mock_artifact = Mock()
        mock_artifact.context_id = uuid4()
        mock_context_store_instance.create_artifact.return_value = mock_artifact
        mock_context_store.return_value = mock_context_store_instance

        # Execute the task directly
        result = asyncio.run(process_agent_task(task_data))

        # Verify artifact was created
        mock_context_store_instance.create_artifact.assert_called_once()
        call_args = mock_context_store_instance.create_artifact.call_args
        assert str(call_args[1]["project_id"]) == task_data["project_id"]
        assert call_args[1]["source_agent"] == "analyst"
        assert call_args[1]["artifact_type"] == "agent_output"
        assert call_args[1]["content"] == result

        # Verify the result includes artifact information
        assert "artifact_id" in result or "artifact_id" in mock_websocket_manager.broadcast_event.call_args[0][0].data
