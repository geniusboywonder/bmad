"""
Integration Tests for Database Schema Validation

These tests ensure that SQLAlchemy models match the actual database schema
and that enum vs boolean type mismatches are caught early.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import DataError, ProgrammingError
import uuid
from datetime import datetime, timezone

from app.database.connection import get_engine, get_session
from app.database.models import (
    ProjectDB, TaskDB, ContextArtifactDB, HitlRequestDB,
    AgentBudgetControlDB, EmergencyStopDB, ResponseApprovalDB,
    WebSocketNotificationDB, RecoverySessionDB
)


class TestDatabaseSchemaValidation:
    """Test that database schema matches model definitions."""

    def test_database_is_postgresql(self):
        """Ensure tests run against PostgreSQL, not SQLite."""
        engine = get_engine()
        assert 'postgresql' in str(engine.url), "Tests must run against PostgreSQL"

    def test_enum_vs_boolean_consistency(self):
        """Test that boolean fields in models match boolean columns in database."""
        engine = get_engine()
        inspector = inspect(engine)

        # Define expected boolean fields from models
        expected_boolean_fields = {
            'agent_budget_controls': ['emergency_stop_enabled'],
            'emergency_stops': ['active'],
            'websocket_notifications': ['delivered', 'expired'],
            'response_approvals': ['auto_approved']
        }

        for table_name, boolean_fields in expected_boolean_fields.items():
            columns = inspector.get_columns(table_name)
            column_types = {col['name']: str(col['type']) for col in columns}

            for field_name in boolean_fields:
                assert field_name in column_types, f"Field {field_name} missing from {table_name}"
                column_type = column_types[field_name].upper()
                assert 'BOOLEAN' in column_type, (
                    f"{table_name}.{field_name} should be BOOLEAN, got {column_type}"
                )

    def test_enum_fields_are_actually_enums(self):
        """Test that enum fields in models match enum columns in database."""
        engine = get_engine()
        inspector = inspect(engine)

        # Define expected enum fields from models
        expected_enum_fields = {
            'tasks': [('status', 'TASKSTATUS')],  # Should be taskstatus enum
        }

        for table_name, enum_field_specs in expected_enum_fields.items():
            columns = inspector.get_columns(table_name)
            column_types = {col['name']: str(col['type']) for col in columns}

            for field_name, expected_enum_name in enum_field_specs:
                assert field_name in column_types, f"Field {field_name} missing from {table_name}"
                column_type = column_types[field_name].upper()
                # For PostgreSQL enums, we expect to see the enum name
                assert (expected_enum_name in column_type or 'ENUM' in column_type), (
                    f"{table_name}.{field_name} should be {expected_enum_name} enum, got {column_type}"
                )


class TestModelDatabaseOperations:
    """Test that models work correctly with real database operations."""

    def test_websocket_notification_boolean_operations(self):
        """Test WebSocketNotificationDB with boolean fields."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # Create notification with boolean values
            notification = WebSocketNotificationDB(
                event_type='test_schema_validation',
                title='Schema Test',
                message='Testing boolean fields',
                delivered=True,
                expired=False
            )
            session.add(notification)
            session.commit()

            # Verify the record was saved and can be retrieved
            retrieved = session.query(WebSocketNotificationDB).filter_by(
                event_type='test_schema_validation'
            ).first()

            assert retrieved is not None
            assert retrieved.delivered is True
            assert retrieved.expired is False
            assert isinstance(retrieved.delivered, bool)
            assert isinstance(retrieved.expired, bool)

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass

    def test_emergency_stop_boolean_operations(self):
        """Test EmergencyStopDB with boolean active field."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # Create emergency stop with boolean active
            stop = EmergencyStopDB(
                agent_type='test_agent',
                stop_reason='Schema validation test',
                triggered_by='TEST',
                active=True
            )
            session.add(stop)
            session.commit()

            # Verify the record was saved with correct boolean type
            retrieved = session.query(EmergencyStopDB).filter_by(
                stop_reason='Schema validation test'
            ).first()

            assert retrieved is not None
            assert retrieved.active is True
            assert isinstance(retrieved.active, bool)

            # Test updating the boolean field
            retrieved.active = False
            session.commit()

            # Verify the update worked
            session.refresh(retrieved)
            assert retrieved.active is False

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass

    def test_agent_budget_control_boolean_operations(self):
        """Test AgentBudgetControlDB with boolean emergency_stop_enabled."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # First create a project to satisfy foreign key
            project = ProjectDB(
                name='Schema Test Project',
                description='For testing schema validation',
                status='active'
            )
            session.add(project)
            session.commit()

            # Create budget control with boolean emergency_stop_enabled
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type='test_agent',
                daily_token_limit=1000,
                session_token_limit=500,
                emergency_stop_enabled=True
            )
            session.add(budget)
            session.commit()

            # Verify the record was saved with correct boolean type
            retrieved = session.query(AgentBudgetControlDB).filter_by(
                project_id=project.id,
                agent_type='test_agent'
            ).first()

            assert retrieved is not None
            assert retrieved.emergency_stop_enabled is True
            assert isinstance(retrieved.emergency_stop_enabled, bool)

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass

    def test_task_enum_operations(self):
        """Test TaskDB with enum status field."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # First create a project to satisfy foreign key
            project = ProjectDB(
                name='Task Schema Test Project',
                description='For testing task schema validation',
                status='active'
            )
            session.add(project)
            session.commit()

            # Create task with enum status
            task = TaskDB(
                project_id=project.id,
                name='Schema validation task',
                description='Testing enum status field',
                agent_type='test_agent',
                status='IDLE'  # This should be from agentstatus enum
            )
            session.add(task)
            session.commit()

            # Verify the record was saved with correct enum value
            retrieved = session.query(TaskDB).filter_by(
                name='Schema validation task'
            ).first()

            assert retrieved is not None
            assert retrieved.status == 'IDLE'

            # Test updating with other valid enum values
            for status in ['WORKING', 'WAITING_FOR_HITL', 'ERROR']:
                retrieved.status = status
                session.commit()
                session.refresh(retrieved)
                assert retrieved.status == status

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass

    def test_invalid_enum_values_fail(self):
        """Test that invalid enum values are rejected by database."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # First create a project to satisfy foreign key
            project = ProjectDB(
                name='Invalid Enum Test Project',
                description='For testing invalid enum rejection',
                status='active'
            )
            session.add(project)
            session.commit()

            # Try to create task with invalid enum status
            task = TaskDB(
                project_id=project.id,
                name='Invalid enum test task',
                description='Testing invalid enum rejection',
                agent_type='test_agent',
                status='INVALID_STATUS'  # This should fail
            )
            session.add(task)

            # This should raise an exception
            with pytest.raises((DataError, ProgrammingError)):
                session.commit()

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass


class TestSchemaMigrationValidation:
    """Test that migrations create correct schema."""

    def test_all_required_tables_exist(self):
        """Test that all model tables exist in database."""
        engine = get_engine()
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        expected_tables = [
            'projects', 'tasks', 'context_artifacts', 'hitl_requests',
            'agent_budget_controls', 'emergency_stops', 'response_approvals',
            'websocket_notifications', 'recovery_sessions', 'workflow_states'
        ]

        for table_name in expected_tables:
            assert table_name in table_names, f"Table {table_name} should exist"

    def test_foreign_key_constraints_exist(self):
        """Test that foreign key constraints are properly defined."""
        engine = get_engine()
        inspector = inspect(engine)

        # Test key foreign key relationships
        constraints_to_check = [
            ('tasks', 'project_id', 'projects'),
            ('context_artifacts', 'project_id', 'projects'),
            ('agent_budget_controls', 'project_id', 'projects'),
            ('emergency_stops', 'project_id', 'projects'),
            ('response_approvals', 'project_id', 'projects'),
        ]

        for table_name, column_name, referenced_table in constraints_to_check:
            foreign_keys = inspector.get_foreign_keys(table_name)

            # Check if the expected foreign key exists
            fk_found = False
            for fk in foreign_keys:
                if (column_name in fk['constrained_columns'] and
                    fk['referred_table'] == referenced_table):
                    fk_found = True
                    break

            assert fk_found, (
                f"Foreign key {table_name}.{column_name} -> {referenced_table} not found"
            )

    def test_indexes_exist(self):
        """Test that performance indexes exist."""
        engine = get_engine()
        inspector = inspect(engine)

        # Check for some expected indexes
        expected_indexes = [
            ('tasks', 'idx_tasks_project_agent_status'),
            ('context_artifacts', 'idx_context_artifacts_project_type'),
        ]

        for table_name, index_name in expected_indexes:
            indexes = inspector.get_indexes(table_name)
            index_names = [idx['name'] for idx in indexes]

            assert index_name in index_names, (
                f"Performance index {index_name} should exist on {table_name}"
            )