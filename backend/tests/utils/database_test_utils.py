"""
Database Testing Utilities

Provides utilities for testing with real database connections while maintaining
test isolation and performance.
"""

import pytest
import asyncio
from contextlib import contextmanager
from typing import Generator, Any, Dict, List
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import get_engine, Base
from app.database.models import *


class DatabaseTestManager:
    """Manages database test setup with real connections and proper cleanup."""

    def __init__(self, use_memory_db: bool = False):
        self.use_memory_db = use_memory_db
        self.engine = None
        self.session_factory = None
        self.test_data = {}

    def setup_test_database(self):
        """Set up test database with proper isolation."""
        if self.use_memory_db:
            # Use in-memory SQLite for unit tests
            self.engine = create_engine(
                "sqlite:///:memory:",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
        else:
            # Use real PostgreSQL for integration tests
            self.engine = get_engine()

        self.session_factory = sessionmaker(bind=self.engine)

        # Create all tables
        Base.metadata.create_all(self.engine)

    def cleanup_test_database(self):
        """Clean up test database."""
        if self.engine:
            if self.use_memory_db:
                # Drop all tables for in-memory DB
                Base.metadata.drop_all(self.engine)
            else:
                # Clean up specific test data for PostgreSQL
                self._cleanup_test_data()

    def _cleanup_test_data(self):
        """Clean up test data from PostgreSQL database."""
        with self.get_session() as session:
            try:
                # Delete test data based on tracked IDs
                for table_name, ids in self.test_data.items():
                    if ids:
                        table = Base.metadata.tables.get(table_name)
                        if table is not None:
                            session.execute(
                                table.delete().where(table.c.id.in_(ids))
                            )
                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Warning: Failed to cleanup test data: {e}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with proper cleanup."""
        session = self.session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def track_test_record(self, table_name: str, record_id: str):
        """Track a test record for cleanup."""
        if table_name not in self.test_data:
            self.test_data[table_name] = []
        self.test_data[table_name].append(record_id)

    def create_test_project(self, **kwargs) -> ProjectDB:
        """Create a test project with proper tracking."""
        defaults = {
            'name': f'Test Project {uuid4().hex[:8]}',
            'description': 'Test project for database testing',
            'status': 'active'
        }
        defaults.update(kwargs)

        with self.get_session() as session:
            project = ProjectDB(**defaults)
            session.add(project)
            session.commit()
            session.refresh(project)

            self.track_test_record('projects', str(project.id))
            return project

    def create_test_task(self, project_id: str = None, **kwargs) -> TaskDB:
        """Create a test task with proper tracking."""
        if not project_id:
            project = self.create_test_project()
            project_id = project.id

        defaults = {
            'project_id': project_id,
            'agent_type': 'test_agent',
            'status': 'PENDING',
            'instructions': 'Test task instructions'
        }
        defaults.update(kwargs)

        with self.get_session() as session:
            task = TaskDB(**defaults)
            session.add(task)
            session.commit()
            session.refresh(task)

            self.track_test_record('tasks', str(task.id))
            return task

    def verify_database_state(self, checks: List[Dict[str, Any]]) -> bool:
        """Verify specific database state conditions."""
        with self.get_session() as session:
            for check in checks:
                table_name = check['table']
                conditions = check.get('conditions', {})
                expected_count = check.get('count')

                # Get the model class
                model_class = self._get_model_class(table_name)
                if not model_class:
                    raise ValueError(f"Unknown table: {table_name}")

                query = session.query(model_class)

                # Apply conditions
                for field, value in conditions.items():
                    query = query.filter(getattr(model_class, field) == value)

                # Check count if specified
                if expected_count is not None:
                    actual_count = query.count()
                    if actual_count != expected_count:
                        return False

        return True

    def _get_model_class(self, table_name: str):
        """Get model class by table name."""
        model_mapping = {
            'projects': ProjectDB,
            'tasks': TaskDB,
            'context_artifacts': ContextArtifactDB,
            'hitl_requests': HitlRequestDB,
            'agent_budget_controls': AgentBudgetControlDB,
            'emergency_stops': EmergencyStopDB,
            'response_approvals': ResponseApprovalDB,
            'websocket_notifications': WebSocketNotificationDB,
            'recovery_sessions': RecoverySessionDB,
            'event_log': EventLogDB,
        }
        return model_mapping.get(table_name)


@pytest.fixture
def db_test_manager():
    """Pytest fixture for database test manager."""
    manager = DatabaseTestManager(use_memory_db=False)  # Use real PostgreSQL
    manager.setup_test_database()
    yield manager
    manager.cleanup_test_database()


@pytest.fixture
def memory_db_test_manager():
    """Pytest fixture for in-memory database testing."""
    manager = DatabaseTestManager(use_memory_db=True)
    manager.setup_test_database()
    yield manager
    manager.cleanup_test_database()


class APITestClient:
    """Test client that verifies API → Database flow."""

    def __init__(self, app, db_manager: DatabaseTestManager):
        from fastapi.testclient import TestClient
        self.client = TestClient(app)
        self.db_manager = db_manager

    def post_and_verify_db(self, endpoint: str, data: Dict,
                          db_checks: List[Dict[str, Any]], **kwargs):
        """Make POST request and verify database state."""
        response = self.client.post(endpoint, json=data, **kwargs)

        # Verify database state
        db_state_valid = self.db_manager.verify_database_state(db_checks)

        return {
            'response': response,
            'db_state_valid': db_state_valid,
            'status_code': response.status_code,
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }

    def get_and_verify_consistency(self, endpoint: str, expected_db_state: List[Dict[str, Any]], **kwargs):
        """Make GET request and verify it matches database state."""
        response = self.client.get(endpoint, **kwargs)

        # Verify database consistency
        db_state_valid = self.db_manager.verify_database_state(expected_db_state)

        return {
            'response': response,
            'db_state_valid': db_state_valid,
            'status_code': response.status_code,
            'json': response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        }


def assert_no_mocks_in_call_stack():
    """Assert that no mocks are present in the current call stack."""
    import inspect
    from unittest.mock import Mock, MagicMock

    for frame_info in inspect.stack():
        frame = frame_info.frame
        for var_name, var_value in frame.f_locals.items():
            if isinstance(var_value, (Mock, MagicMock)):
                raise AssertionError(f"Mock object found in call stack: {var_name} = {var_value}")


def verify_celery_task_in_database(task_id: str, db_manager: DatabaseTestManager) -> bool:
    """Verify that a Celery task was properly persisted to the database."""
    with db_manager.get_session() as session:
        # Check if task exists in tasks table
        task = session.query(TaskDB).filter(TaskDB.id == task_id).first()
        return task is not None


def create_full_stack_test_scenario(db_manager: DatabaseTestManager) -> Dict[str, Any]:
    """Create a complete test scenario with project, tasks, and HITL setup."""
    # Create project
    project = db_manager.create_test_project(
        name="Full Stack Test Project"
    )

    # Create budget controls
    with db_manager.get_session() as session:
        budget = AgentBudgetControlDB(
            project_id=project.id,
            agent_type='analyst',
            daily_token_limit=1000,
            session_token_limit=500,
            emergency_stop_enabled=False
        )
        session.add(budget)
        session.commit()
        session.refresh(budget)
        db_manager.track_test_record('agent_budget_controls', str(budget.id))

    # Create task
    task = db_manager.create_test_task(
        project_id=project.id,
        agent_type='analyst',
        status='PENDING'
    )

    return {
        'project': project,
        'task': task,
        'budget': budget,
        'project_id': str(project.id),
        'task_id': str(task.id)
    }