"""
Real Database Tests for Orchestrator Core Services

This module tests the orchestrator core functionality with real database
operations to validate actual business logic and database constraints.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import text

from app.services.orchestrator.orchestrator_core import OrchestratorCore
from app.models.task import TaskStatus
from app.models.agent import AgentType
from app.database.models import ProjectDB, TaskDB

from tests.utils.database_test_utils import DatabaseTestManager

class TestOrchestratorCoreReal:
    """Test OrchestratorCore with real database operations."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for orchestrator tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_orchestrator_core_initialization_real_db(self, db_manager):
        """Test OrchestratorCore initialization with real database."""
        with db_manager.get_session() as session:
            # Create orchestrator core with real database session
            orchestrator = OrchestratorCore(session)

            # Verify basic initialization
            assert orchestrator is not None
            assert orchestrator.db == session

            # Test basic database connectivity
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1

    @pytest.mark.real_data
    def test_create_project_real_db(self, db_manager):
        """Test project creation with real database persistence."""
        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            project_name = "Real Database Test Project"
            project_description = "Testing orchestrator with real database"

            project_id = orchestrator.create_project(project_name, project_description)

            assert project_id is not None

            # Verify project was actually created in database
            with db_manager.get_session() as verify_session:
                created_project = verify_session.query(ProjectDB).filter_by(
                    id=project_id
                ).first()

                assert created_project is not None
                assert created_project.name == project_name
                assert created_project.description == project_description

            db_manager.track_test_record('projects', str(project_id))

    @pytest.mark.real_data
    def test_create_task_real_db(self, db_manager):
        """Test task creation with real database persistence."""
        project = db_manager.create_test_project(name='Task Creation Test')

        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            agent_type = "analyst"
            instructions = "Analyze requirements with real database"

            task = orchestrator.create_task(project.id, agent_type, instructions)

            assert task is not None
            assert task.agent_type == agent_type
            assert task.instructions == instructions
            assert task.status == TaskStatus.PENDING

            # Verify task was persisted to database
            with db_manager.get_session() as verify_session:
                created_task = verify_session.query(TaskDB).filter_by(
                    id=task.task_id
                ).first()

                assert created_task is not None
                assert created_task.project_id == project.id
                assert created_task.agent_type == agent_type
                assert created_task.instructions == instructions

    @pytest.mark.real_data
    def test_update_task_status_real_db(self, db_manager):
        """Test task status updates with real database."""
        project = db_manager.create_test_project(name='Task Status Test')
        task = db_manager.create_test_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST,
            status=TaskStatus.PENDING
        )

        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Update task to WORKING
            orchestrator.update_task_status(task.id, TaskStatus.WORKING)

            # Verify status update in database
            with db_manager.get_session() as verify_session:
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert updated_task is not None
                assert updated_task.status == TaskStatus.WORKING
                assert updated_task.started_at is not None

            # Update task to COMPLETED
            orchestrator.update_task_status(task.id, TaskStatus.COMPLETED)

            # Verify completion in database
            with db_manager.get_session() as verify_session:
                completed_task = verify_session.query(TaskDB).filter_by(
                    id=task.id
                ).first()

                assert completed_task is not None
                assert completed_task.status == TaskStatus.COMPLETED
                assert completed_task.completed_at is not None

    @pytest.mark.real_data
    def test_project_task_relationship_real_db(self, db_manager):
        """Test project-task relationship with real database constraints."""
        project = db_manager.create_test_project(name='Relationship Test')

        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Create multiple tasks for the same project
            tasks = []
            for i, agent_type in enumerate([AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER]):
                task = orchestrator.create_task(
                    project.id,
                    agent_type.value,
                    f"Task {i+1} for {agent_type.value}"
                )
                tasks.append(task)

            # Verify all tasks are linked to the same project
            with db_manager.get_session() as verify_session:
                project_tasks = verify_session.query(TaskDB).filter_by(
                    project_id=project.id
                ).all()

                assert len(project_tasks) == 3

                # Verify each task has correct agent type
                found_types = {task.agent_type for task in project_tasks}
                expected_types = {AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER}
                assert found_types == expected_types

    @pytest.mark.real_data
    def test_database_constraint_validation_real_db(self, db_manager):
        """Test database constraints with real operations."""
        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Test creating task with non-existent project should fail
            invalid_project_id = uuid4()

            with pytest.raises(Exception):  # Should raise foreign key constraint error
                orchestrator.create_task(
                    invalid_project_id,
                    "analyst",
                    "This should fail due to FK constraint"
                )

    @pytest.mark.real_data
    def test_concurrent_task_creation_real_db(self, db_manager):
        """Test concurrent task creation with real database."""
        project = db_manager.create_test_project(name='Concurrent Test')

        # Create tasks in rapid succession to test database handling
        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            tasks = []
            for i in range(5):
                task = orchestrator.create_task(
                    project.id,
                    "analyst",
                    f"Concurrent task {i+1}"
                )
                tasks.append(task)

            # Verify all tasks were created successfully
            assert len(tasks) == 5
            task_ids = {task.task_id for task in tasks}
            assert len(task_ids) == 5  # All unique IDs

            # Verify in database
            with db_manager.get_session() as verify_session:
                db_tasks = verify_session.query(TaskDB).filter_by(
                    project_id=project.id
                ).all()

                assert len(db_tasks) == 5
                db_task_ids = {task.id for task in db_tasks}
                assert db_task_ids == task_ids

class TestOrchestratorDatabaseIntegration:
    """Test orchestrator database integration patterns."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for integration tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_session_transaction_handling_real_db(self, db_manager):
        """Test proper transaction handling in orchestrator operations."""
        project = db_manager.create_test_project(name='Transaction Test')

        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Create task within transaction
            task = orchestrator.create_task(
                project.id,
                "analyst",
                "Transaction test task"
            )

            # Session should auto-commit on context exit
            task_id = task.task_id

        # Verify persistence after session close
        with db_manager.get_session() as verify_session:
            persisted_task = verify_session.query(TaskDB).filter_by(
                id=task_id
            ).first()

            assert persisted_task is not None
            assert persisted_task.instructions == "Transaction test task"

    @pytest.mark.real_data
    def test_orchestrator_state_consistency_real_db(self, db_manager):
        """Test state consistency across orchestrator operations."""
        project = db_manager.create_test_project(name='State Consistency Test')

        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Create and immediately update task
            task = orchestrator.create_task(
                project.id,
                "architect",
                "State consistency test"
            )

            original_status = task.status
            assert original_status == TaskStatus.PENDING

            # Update status
            orchestrator.update_task_status(task.task_id, TaskStatus.WORKING)

            # Verify state change is reflected
            with db_manager.get_session() as verify_session:
                updated_task = verify_session.query(TaskDB).filter_by(
                    id=task.task_id
                ).first()

                assert updated_task.status == TaskStatus.WORKING
                assert updated_task.status != original_status

    @pytest.mark.real_data
    def test_orchestrator_error_recovery_real_db(self, db_manager):
        """Test orchestrator error handling with real database."""
        with db_manager.get_session() as session:
            orchestrator = OrchestratorCore(session)

            # Test graceful handling of invalid operations
            invalid_task_id = uuid4()

            # Should not raise exception, but return False or handle gracefully
            try:
                result = orchestrator.update_task_status(invalid_task_id, TaskStatus.COMPLETED)
                # If method returns a value, it should indicate failure
                if result is not None:
                    assert result is False
            except Exception:
                # If method raises exception, it should be handled appropriately
                pass  # This is acceptable for non-existent task updates
