"""
Real Database Tests for Agent Task Processing

This module replaces mock-heavy agent task tests with real database
operations to validate actual business logic and database constraints.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

from app.tasks.agent_tasks import process_agent_task, validate_task_data
from app.models.task import TaskStatus
from app.models.agent import AgentType
from app.database.models import TaskDB, ProjectDB, ContextArtifactDB

from tests.utils.database_test_utils import DatabaseTestManager

class TestAgentTaskProcessingReal:
    """Test agent task processing with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for agent task tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def sample_task_data(self, db_manager):
        """Sample task data using real project ID."""
        project = db_manager.create_test_project(name="Agent Task Test Project")
        return {
            "task_id": str(uuid4()),
            "project_id": str(project.id),
            "agent_type": "analyst",
            "instructions": "Analyze the user requirements and create a project plan",
            "context_ids": []
        }

    @pytest.mark.real_data
    def test_validate_task_data_uuid_conversion(self, sample_task_data):
        """Test that UUID strings are properly converted to UUID objects."""
        result = validate_task_data(sample_task_data)

        # Verify UUID conversion
        assert isinstance(result["task_id"], UUID)
        assert isinstance(result["project_id"], UUID)
        assert str(result["task_id"]) == sample_task_data["task_id"]
        assert str(result["project_id"]) == sample_task_data["project_id"]

        # Verify defaults are applied correctly
        assert result["from_agent"] == "orchestrator"
        assert result["expected_outputs"] == ["task_result"]
        assert result["priority"] == 1

    @pytest.mark.real_data
    def test_validate_task_data_with_context_ids_real_db(self, db_manager):
        """Test UUID conversion with real context artifacts in database."""
        project = db_manager.create_test_project(name="Context Test Project")

        # Create real context artifact
        context_artifact = db_manager.create_test_context_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            content={"test": "context data"}
        )

        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(project.id),
            "agent_type": "analyst",
            "instructions": "Test instructions with context",
            "from_agent": "custom_agent",
            "expected_outputs": ["custom_output"],
            "priority": 5,
            "context_ids": [str(context_artifact.id)]
        }

        result = validate_task_data(task_data)

        # Verify UUID conversion for all IDs
        assert isinstance(result["task_id"], UUID)
        assert isinstance(result["project_id"], UUID)
        assert isinstance(result["context_ids"][0], UUID)
        assert str(result["context_ids"][0]) == str(context_artifact.id)

        # Verify custom values are preserved
        assert result["from_agent"] == "custom_agent"
        assert result["expected_outputs"] == ["custom_output"]
        assert result["priority"] == 5

    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_process_agent_task_database_persistence_real_db(self, db_manager, sample_task_data):
        """Test agent task processing with real database persistence."""
        # Create task in database first
        project_id = UUID(sample_task_data["project_id"])
        task_id = UUID(sample_task_data["task_id"])

        task = db_manager.create_test_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST,
            instructions=sample_task_data["instructions"],
            status=TaskStatus.PENDING
        )

        # Update task_id in sample data to match created task
        sample_task_data["task_id"] = str(task.id)

        # Mock external services (AutoGen, WebSocket, Context Store)
        with patch('app.tasks.agent_tasks.websocket_manager') as mock_websocket, \
             patch('app.tasks.agent_tasks.AutoGenService') as mock_autogen_service, \
             patch('app.tasks.agent_tasks.ContextStoreService') as mock_context_store:

            # Setup external service mocks
            mock_websocket.broadcast_event = AsyncMock()

            mock_autogen_instance = Mock()
            mock_autogen_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "agent_type": "analyst",
                "task_id": str(task.id),
                "result": "Analysis completed successfully",
                "context_used": []
            })
            mock_autogen_service.return_value = mock_autogen_instance

            mock_context_store_instance = Mock()
            mock_context_store_instance.get_artifacts_by_ids.return_value = []
            mock_context_store.return_value = mock_context_store_instance

            # Execute the task with real database session
            with db_manager.get_session() as session:
                with patch('app.database.connection.get_session', return_value=iter([session])):
                    await process_agent_task(sample_task_data)

            # Verify task status was updated in real database
            with db_manager.get_session() as verify_session:
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert updated_task is not None
                assert updated_task.status == TaskStatus.COMPLETED
                assert updated_task.started_at is not None
                assert updated_task.completed_at is not None
                assert "Analysis completed successfully" in updated_task.output

            # Verify WebSocket events were sent
            assert mock_websocket.broadcast_event.call_count >= 2  # Started + completed

    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_process_agent_task_failure_real_db(self, db_manager, sample_task_data):
        """Test agent task failure handling with real database updates."""
        # Create task in database
        project_id = UUID(sample_task_data["project_id"])
        task = db_manager.create_test_task(
            project_id=project_id,
            agent_type=AgentType.ANALYST,
            instructions=sample_task_data["instructions"],
            status=TaskStatus.PENDING
        )

        sample_task_data["task_id"] = str(task.id)

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
                "task_id": str(task.id),
                "error": "LLM service unavailable",
                "context_used": []
            })
            mock_autogen_service.return_value = mock_autogen_instance

            mock_context_store_instance = Mock()
            mock_context_store_instance.get_artifacts_by_ids.return_value = []
            mock_context_store.return_value = mock_context_store_instance

            # Execute task and expect failure
            # Note: We don't mock get_session - let the task use real database operations
            # The DatabaseTestManager ensures we use test database
            with pytest.raises(Exception) as exc_info:
                await process_agent_task(sample_task_data)

            # Verify the exception message
            assert "Task execution failed" in str(exc_info.value)
            assert "LLM service unavailable" in str(exc_info.value)

            # Verify task status was updated to FAILED in real database
            with db_manager.get_session() as verify_session:
                failed_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert failed_task is not None
                assert failed_task.status == TaskStatus.FAILED
                assert failed_task.error_message is not None
                assert "LLM service unavailable" in failed_task.error_message

    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_process_agent_task_with_context_real_db(self, db_manager):
        """Test agent task processing with real context artifacts."""
        project = db_manager.create_test_project(name="Context Integration Test")

        # Create real context artifact
        context_artifact = db_manager.create_test_context_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            content={"requirements": "User wants a web application", "priority": "high"}
        )

        # Create task with context
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ARCHITECT,
            instructions="Design architecture based on requirements",
            status=TaskStatus.PENDING
        )

        task_data = {
            "task_id": str(task.id),
            "project_id": str(project.id),
            "agent_type": "architect",
            "instructions": "Design architecture based on requirements",
            "context_ids": [str(context_artifact.id)]
        }

        # Mock external services
        with patch('app.tasks.agent_tasks.websocket_manager') as mock_websocket, \
             patch('app.tasks.agent_tasks.AutoGenService') as mock_autogen_service, \
             patch('app.tasks.agent_tasks.ContextStoreService') as mock_context_store:

            mock_websocket.broadcast_event = AsyncMock()

            mock_autogen_instance = Mock()
            mock_autogen_instance.execute_task = AsyncMock(return_value={
                "success": True,
                "agent_type": "architect",
                "task_id": str(task.id),
                "result": "Architecture designed with microservices approach",
                "context_used": [str(context_artifact.id)]
            })
            mock_autogen_service.return_value = mock_autogen_instance

            # Mock context store to return real artifact data
            mock_context_store_instance = Mock()
            mock_context_store_instance.get_artifacts_by_ids.return_value = [
                {
                    "id": str(context_artifact.id),
                    "content": context_artifact.content,
                    "source_agent": context_artifact.source_agent
                }
            ]
            mock_context_store.return_value = mock_context_store_instance

            # Execute task
            with db_manager.get_session() as session:
                with patch('app.database.connection.get_session', return_value=iter([session])):
                    await process_agent_task(task_data)

            # Verify task completion and context usage
            with db_manager.get_session() as verify_session:
                completed_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert completed_task is not None
                assert completed_task.status == TaskStatus.COMPLETED
                assert "Architecture designed" in completed_task.output

                # Verify context artifact still exists
                context_check = verify_session.query(ContextArtifactDB).filter_by(
                    id=context_artifact.id
                ).first()

                assert context_check is not None
                assert context_check.content == {"requirements": "User wants a web application", "priority": "high"}

    @pytest.mark.real_data
    def test_task_database_constraints_real_db(self, db_manager):
        """Test task creation with database constraints validation."""
        project = db_manager.create_test_project(name="Constraints Test Project")

        # Test creating task with valid data
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST,
            instructions="Valid task instructions",
            status=TaskStatus.PENDING
        )

        with db_manager.get_session() as session:
            # Verify task was created
            created_task = session.query(TaskDB).filter_by(id=task.id).first()
            assert created_task is not None
            assert created_task.project_id == project.id
            assert created_task.agent_type == AgentType.ANALYST

        # Test foreign key constraint with invalid project
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            with db_manager.get_session() as session:
                invalid_task = TaskDB(
                    id=uuid4(),
                    project_id=uuid4(),  # Non-existent project
                    agent_type=AgentType.ANALYST,
                    instructions="Invalid project reference",
                    status=TaskStatus.PENDING,
                    context_ids=[],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                session.add(invalid_task)
                session.commit()

    @pytest.mark.real_data
    def test_task_status_transitions_real_db(self, db_manager):
        """Test task status transitions with real database persistence."""
        project = db_manager.create_test_project(name="Status Transition Test")

        # Create task in PENDING status
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.CODER,
            status=TaskStatus.PENDING
        )

        with db_manager.get_session() as session:
            # Test status transitions
            db_task = session.query(TaskDB).filter_by(id=task.id).first()

            # PENDING -> WORKING
            db_task.status = TaskStatus.WORKING
            db_task.started_at = datetime.now(timezone.utc)
            session.commit()

            # Verify transition
            assert db_task.status == TaskStatus.WORKING
            assert db_task.started_at is not None

            # WORKING -> COMPLETED
            db_task.status = TaskStatus.COMPLETED
            db_task.completed_at = datetime.now(timezone.utc)
            db_task.output = "Task completed successfully"
            session.commit()

            # Verify final state
            assert db_task.status == TaskStatus.COMPLETED
            assert db_task.completed_at is not None
            assert db_task.output == "Task completed successfully"

    @pytest.mark.real_data
    def test_multiple_tasks_same_project_real_db(self, db_manager):
        """Test creating multiple tasks for the same project."""
        project = db_manager.create_test_project(name="Multi-Task Project")

        # Create multiple tasks
        task_types = [AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER]
        tasks = []

        for agent_type in task_types:
            task = db_manager.create_test_task(
                project_id=project.id,
                agent_type=agent_type,
                instructions=f"Task for {agent_type.value}",
                status=TaskStatus.PENDING
            )
            tasks.append(task)

        # Verify all tasks exist in database
        with db_manager.get_session() as session:
            project_tasks = session.query(TaskDB).filter_by(
                project_id=project.id
            ).all()

            assert len(project_tasks) == 3

            # Verify each task has correct agent type
            found_types = {task.agent_type for task in project_tasks}
            expected_types = {AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER}
            assert found_types == expected_types

class TestAgentTaskValidationReal:
    """Test agent task validation with real data constraints."""

    @pytest.mark.real_data
    def test_validate_required_fields(self):
        """Test validation of required task data fields."""
        # Test missing required fields
        incomplete_data = {
            "task_id": str(uuid4()),
            # Missing project_id, agent_type, instructions
        }

        with pytest.raises(KeyError):
            validate_task_data(incomplete_data)

    @pytest.mark.real_data
    def test_validate_agent_type_enum(self):
        """Test validation of agent type enum values."""
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "invalid_agent_type",  # Invalid enum value
            "instructions": "Test instructions",
            "context_ids": []
        }

        # Should handle invalid agent type gracefully
        result = validate_task_data(task_data)
        assert result["agent_type"] == "invalid_agent_type"  # Passes through for now

    @pytest.mark.real_data
    def test_validate_context_ids_list(self):
        """Test validation of context_ids as list of UUIDs."""
        context_ids = [str(uuid4()), str(uuid4())]

        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions",
            "context_ids": context_ids
        }

        result = validate_task_data(task_data)

        # Verify all context_ids are converted to UUID objects
        assert len(result["context_ids"]) == 2
        for context_id in result["context_ids"]:
            assert isinstance(context_id, UUID)

    @pytest.mark.real_data
    def test_validate_priority_bounds(self):
        """Test validation of priority value bounds."""
        task_data = {
            "task_id": str(uuid4()),
            "project_id": str(uuid4()),
            "agent_type": "analyst",
            "instructions": "Test instructions",
            "priority": 10,  # High priority value
            "context_ids": []
        }

        result = validate_task_data(task_data)
        assert result["priority"] == 10  # Should accept any integer priority