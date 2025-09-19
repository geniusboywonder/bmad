"""Unit tests for audit service.

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies remain appropriately mocked.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from app.services.audit_service import AuditService
from app.models.event_log import EventType, EventSource, EventLogCreate, EventLogFilter
from app.database.models import EventLogDB
from tests.utils.database_test_utils import DatabaseTestManager

class TestAuditService:
    """Test cases for AuditService."""
    
    @pytest.fixture
    def db_manager(self):
        """Real database manager for audit service tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()
    
    @pytest.fixture
    def audit_service(self, db_manager):
        """Audit service instance with real database session."""
        with db_manager.get_session() as session:
            return AuditService(session)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_log_event_success(self, db_manager):
        """Test successful event logging with real database."""
        # Create real project and task
        project = db_manager.create_test_project(name="Audit Test Project")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        event_data = {"action": "test_action", "details": "test details"}
        metadata = {"source": "test"}
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Act - log event with real database operations
            result = await audit_service.log_event(
                event_type=EventType.TASK_CREATED,
                event_source=EventSource.SYSTEM,
                event_data=event_data,
                project_id=project.id,
                task_id=task.id,
                metadata=metadata
            )
            
            # Assert - verify real database persistence
            assert result is not None
            assert result.project_id == project.id
            assert result.task_id == task.id
            assert result.event_type == EventType.TASK_CREATED
            assert result.event_source == EventSource.SYSTEM
            assert result.event_data == event_data
            
            # Verify database state
            db_checks = [
                {
                    'table': 'event_log',
                    'conditions': {'project_id': project.id, 'task_id': task.id},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)
    
    @pytest.mark.asyncio
    @pytest.mark.external_service
    @pytest.mark.real_data

    async def test_log_event_database_error(self, db_manager):
        """Test event logging with database error using real database."""
        # Create real project
        project = db_manager.create_test_project(name="Database Error Test")
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Close the session to simulate database connection failure
            session.close()
            
            # Act & Assert - should handle database error gracefully
            with pytest.raises(Exception, match="Database error|Session is closed"):
                await audit_service.log_event(
                    event_type=EventType.TASK_FAILED,
                    event_source=EventSource.SYSTEM,
                    event_data={"error": "test error"}
                )
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_log_task_event(self, db_manager):
        """Test task event logging convenience method with real database."""
        # Create real project and task
        project = db_manager.create_test_project(name="Task Event Test")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        event_data = {"status": "completed"}
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Act - log task event with real database operations
            result = await audit_service.log_task_event(
                task_id=task.id,
                event_type=EventType.TASK_COMPLETED,
                event_data=event_data,
                project_id=project.id
            )
            
            # Assert - verify real database record was created
            assert result is not None
            assert result.task_id == task.id
            assert result.project_id == project.id
            assert result.event_type == EventType.TASK_COMPLETED
            assert result.event_source == EventSource.SYSTEM
            
            # Verify database state
            db_checks = [
                {
                    'table': 'event_log',
                    'conditions': {'task_id': task.id, 'project_id': project.id},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_log_hitl_event(self, db_manager):
        """Test HITL event logging convenience method with real database."""
        # Create real project
        project = db_manager.create_test_project(name="HITL Event Test")
        hitl_request_id = uuid4()
        event_data = {"action": "approve", "comment": "Looks good"}
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Act
            result = await audit_service.log_hitl_event(
                hitl_request_id=hitl_request_id,
                event_type=EventType.HITL_RESPONSE,
                event_data=event_data,
                event_source=EventSource.USER,
                project_id=project.id
            )
            
            # Assert - verify the event was created and returned
            assert result.hitl_request_id == hitl_request_id
            assert result.project_id == project.id
            assert result.event_type == EventType.HITL_RESPONSE
            assert result.event_source == EventSource.USER
            assert result.event_data == event_data
            
            # Verify database state
            db_checks = [
                {
                    'table': 'event_log',
                    'conditions': {'hitl_request_id': hitl_request_id, 'project_id': project.id},
                    'count': 1
                }
            ]
            assert db_manager.verify_database_state(db_checks)
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_get_events_with_filters(self, db_manager):
        """Test retrieving events with filters using real database."""
        # Create real project and task
        project = db_manager.create_test_project(name="Events Filter Test")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Create a real event
            await audit_service.log_task_event(
                task_id=task.id,
                event_type=EventType.TASK_CREATED,
                event_data={"test": "data"},
                project_id=project.id
            )
            
            # Set up filter parameters
            filter_params = EventLogFilter(
                project_id=project.id,
                event_type=EventType.TASK_CREATED,
                limit=50,
                offset=0
            )
            
            # Act
            events = await audit_service.get_events(filter_params)
            
            # Assert
            assert len(events) == 1
            assert events[0].project_id == project.id
            assert events[0].event_type == EventType.TASK_CREATED
            assert events[0].task_id == task.id
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_get_event_by_id_found(self, db_manager):
        """Test retrieving specific event by ID when found using real database."""
        # Create real project and task
        project = db_manager.create_test_project(name="Event By ID Test")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Create a real event
            created_event = await audit_service.log_task_event(
                task_id=task.id,
                event_type=EventType.TASK_CREATED,
                event_data={"test": "data"},
                project_id=project.id
            )
            
            # Act
            event = await audit_service.get_event_by_id(created_event.id)
            
            # Assert
            assert event is not None
            assert event.id == created_event.id
            assert event.event_type == EventType.TASK_CREATED
            assert event.project_id == project.id
            assert event.task_id == task.id
    
    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_get_event_by_id_not_found(self, db_manager):
        """Test retrieving specific event by ID when not found using real database."""
        # Use a random UUID that doesn't exist in the database
        event_id = uuid4()
        
        with db_manager.get_session() as session:
            audit_service = AuditService(session)
            
            # Act
            event = await audit_service.get_event_by_id(event_id)
            
            # Assert
            assert event is None
    
    @pytest.mark.asyncio
    @pytest.mark.external_service
    @pytest.mark.real_data

    async def test_get_events_database_error(self, db_manager):
        """Test handling database error when retrieving events using real database."""
        filter_params = EventLogFilter(limit=10, offset=0)
        
        with db_manager.get_session() as session:
            # Close the session to simulate database connection failure
            session.close()
            audit_service = AuditService(session)
            
            # Act & Assert
            with pytest.raises(Exception):
                await audit_service.get_events(filter_params)

class TestAuditEventTypes:
    """Test event type and source enums."""
    
    @pytest.mark.mock_data

    def test_event_types_complete(self):
        """Test that all required event types are defined."""
        required_types = [
            "TASK_CREATED", "TASK_STARTED", "TASK_COMPLETED", "TASK_FAILED",
            "HITL_REQUEST_CREATED", "HITL_RESPONSE", "HITL_TIMEOUT",
            "AGENT_STATUS_CHANGED", "AGENT_ERROR",
            "PROJECT_CREATED", "PROJECT_COMPLETED",
            "SYSTEM_ERROR", "SYSTEM_WARNING"
        ]
        
        for event_type in required_types:
            assert hasattr(EventType, event_type)
    
    @pytest.mark.mock_data

    def test_event_sources_complete(self):
        """Test that all required event sources are defined."""
        required_sources = ["AGENT", "USER", "SYSTEM", "WEBHOOK", "SCHEDULER"]
        
        for event_source in required_sources:
            assert hasattr(EventSource, event_source)

class TestEventLogModels:
    """Test event log Pydantic models."""
    
    @pytest.mark.mock_data

    def test_event_log_create_valid(self):
        """Test EventLogCreate model validation."""
        # Arrange & Act
        event_data = {
            "action": "test",
            "details": "test details"
        }
        
        event_log = EventLogCreate(
            project_id=uuid4(),
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data=event_data
        )
        
        # Assert
        assert event_log.event_type == EventType.TASK_CREATED
        assert event_log.event_source == EventSource.SYSTEM
        assert event_log.event_data == event_data
        assert event_log.metadata == {}
    
    @pytest.mark.mock_data

    def test_event_log_filter_defaults(self):
        """Test EventLogFilter default values."""
        # Arrange & Act
        filter_params = EventLogFilter()
        
        # Assert
        assert filter_params.limit == 100
        assert filter_params.offset == 0
        assert filter_params.project_id is None
        assert filter_params.event_type is None
    
    @pytest.mark.mock_data

    def test_event_log_filter_validation(self):
        """Test EventLogFilter validation."""
        # Test limit validation
        with pytest.raises(ValueError):
            EventLogFilter(limit=2000)  # Exceeds maximum
        
        # Test offset validation
        with pytest.raises(ValueError):
            EventLogFilter(offset=-1)  # Below minimum
