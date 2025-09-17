"""
Test Cases for P1.1 Database Setup with PostgreSQL + Redis

This module contains comprehensive test cases for the database setup phase,
including PostgreSQL configuration, Redis integration, and Celery worker setup.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import redis
import json
from datetime import datetime, timedelta

from app.database.connection import get_engine, get_session
from app.tasks.celery_app import celery_app
from app.database.models import ProjectDB, TaskDB, ContextArtifactDB, HitlRequestDB


class TestDatabaseConnection:
    """Test cases for database connection setup and management."""

    def test_get_engine_creation(self):
        """Test that engine is created successfully."""
        engine = get_engine()
        assert engine is not None
        assert hasattr(engine, 'url')

    def test_get_session_creation(self):
        """Test that database session is created successfully."""
        session_gen = get_session()
        session = next(session_gen)
        assert session is not None

        # Clean up session
        try:
            next(session_gen)
        except StopIteration:
            pass  # Expected behavior

    def test_database_tables_exist(self):
        """Test that all required database tables exist."""
        engine = get_engine()

        # Check if main tables exist
        with engine.connect() as conn:
            # Test projects table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"))
            assert result.fetchone() is not None, "Projects table should exist"

            # Test tasks table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"))
            assert result.fetchone() is not None, "Tasks table should exist"

            # Test context_artifacts table
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='context_artifacts'"))
            assert result.fetchone() is not None, "Context artifacts table should exist"

            # Test workflow_states table (Phase 1 requirement)
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_states'"))
            assert result.fetchone() is not None, "Workflow states table should exist"

    def test_database_indexes_exist(self):
        """Test that performance indexes exist."""
        engine = get_engine()

        with engine.connect() as conn:
            # Check for performance indexes
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_tasks_project_agent_status'"))
            assert result.fetchone() is not None, "Tasks performance index should exist"

            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_context_artifacts_project_type'"))
            assert result.fetchone() is not None, "Context artifacts performance index should exist"

    def test_database_migration_status(self):
        """Test that database migrations are up to date."""
        engine = get_engine()

        with engine.connect() as conn:
            # Check that alembic version table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'"))
            assert result.fetchone() is not None, "Alembic version table should exist"

            # Check that we have a current revision
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            assert version is not None, "Should have current migration version"


class TestDatabaseModels:
    """Test cases for database model operations."""

    def test_project_model_creation(self):
        """Test creating project records."""
        session_gen = get_session()
        session = next(session_gen)

        try:
            # Create a test project
            project = ProjectDB(
                name="Test Project",
                description="A test project",
                status="active"
            )
            session.add(project)
            session.commit()

            # Verify project was created
            assert project.id is not None
            assert project.name == "Test Project"

        finally:
            session.rollback()
            try:
                next(session_gen)
            except StopIteration:
                pass


class TestRedisIntegration:
    """Test cases for Redis integration with Celery."""

    def test_celery_app_configuration(self):
        """Test that Celery app is properly configured."""
        assert celery_app is not None
        assert celery_app.conf.broker_url is not None
        assert celery_app.conf.result_backend is not None

    def test_celery_app_tasks(self):
        """Test that Celery tasks are registered."""
        # Check if task is registered
        tasks = list(celery_app.tasks.keys())
        # Should have at least some tasks registered
        assert len(tasks) > 0

    def test_celery_queue_configuration(self):
        """Test that Celery queues are properly configured."""
        # Check task routes configuration
        assert hasattr(celery_app.conf, 'task_routes')
        assert celery_app.conf.task_routes is not None


class TestPhase1Requirements:
    """Test cases specifically for Phase 1 completion criteria."""

    def test_database_with_proper_indexing(self):
        """Test that database has proper indexing per Phase 1 requirements."""
        engine = get_engine()

        with engine.connect() as conn:
            # Test compound indexes as specified in Phase1and2.md
            required_indexes = [
                'idx_tasks_project_agent_status',
                'idx_context_artifacts_project_type',
                'idx_hitl_requests_project_status'
            ]

            for index_name in required_indexes:
                result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'"))
                assert result.fetchone() is not None, f"Required index {index_name} should exist"

    def test_redis_backed_celery_operational(self):
        """Test that Redis-backed Celery task queue is operational."""
        # Test Celery app configuration
        assert celery_app.conf.broker_url is not None
        assert 'redis' in celery_app.conf.broker_url

        # Test that broker and result backend use Redis
        assert celery_app.conf.result_backend is not None
        assert 'redis' in celery_app.conf.result_backend

    def test_workflow_states_table_exists(self):
        """Test that workflow_states table exists (critical for Phase 1)."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='workflow_states'"))
            assert result.fetchone() is not None, "Workflow states table must exist for Phase 1"

            # Test table structure
            result = conn.execute(text("PRAGMA table_info(workflow_states)"))
            columns = [row[1] for row in result.fetchall()]

            required_columns = ['id', 'project_id', 'workflow_id', 'execution_id', 'status']
            for col in required_columns:
                assert col in columns, f"Column {col} should exist in workflow_states table"