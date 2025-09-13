"""Unit tests for audit service."""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

from app.services.audit_service import AuditService
from app.models.event_log import EventType, EventSource, EventLogCreate, EventLogFilter
from app.database.models import EventLogDB


class TestAuditService:
    """Test cases for AuditService."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.execute = Mock()
        session.rollback = Mock()
        session.add = Mock()
        return session
    
    @pytest.fixture
    def audit_service(self, mock_db_session):
        """Audit service instance with mocked database session."""
        return AuditService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_log_event_success(self, audit_service, mock_db_session):
        """Test successful event logging."""
        # Arrange
        project_id = uuid4()
        task_id = uuid4()
        event_data = {"action": "test_action", "details": "test details"}
        metadata = {"source": "test"}
        
        # Mock the EventLogDB object and EventLogResponse.model_validate
        with patch('app.services.audit_service.EventLogDB') as mock_event_db_class, \
             patch('app.services.audit_service.EventLogResponse') as mock_response_class:
            
            mock_event = Mock()
            mock_event.id = uuid4()
            mock_event.project_id = project_id
            mock_event.task_id = task_id
            mock_event.hitl_request_id = None
            mock_event.event_type = EventType.TASK_CREATED.value
            mock_event.event_source = EventSource.SYSTEM.value
            mock_event.event_data = event_data
            mock_event.event_metadata = {"logged_at": datetime.utcnow().isoformat(), "service_version": "1.0.0"}
            mock_event.created_at = datetime.utcnow()
            
            mock_event_db_class.return_value = mock_event
            
            # Mock the response object
            mock_response = Mock()
            mock_response.id = mock_event.id
            mock_response.project_id = project_id
            mock_response.task_id = task_id
            mock_response.event_type = EventType.TASK_CREATED
            mock_response.event_source = EventSource.SYSTEM
            mock_response_class.model_validate.return_value = mock_response
            
            # Act
            result = await audit_service.log_event(
                event_type=EventType.TASK_CREATED,
                event_source=EventSource.SYSTEM,
                event_data=event_data,
                project_id=project_id,
                task_id=task_id,
                metadata=metadata
            )
            
            # Assert
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            mock_response_class.model_validate.assert_called_once_with(mock_event)
            
            # Verify the result
            assert result == mock_response
            assert result.id == mock_event.id
            assert result.project_id == project_id
            assert result.task_id == task_id
    
    @pytest.mark.asyncio
    async def test_log_event_database_error(self, audit_service, mock_db_session):
        """Test event logging with database error."""
        # Arrange
        mock_db_session.commit.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await audit_service.log_event(
                event_type=EventType.TASK_FAILED,
                event_source=EventSource.SYSTEM,
                event_data={"error": "test error"}
            )
        
        mock_db_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_log_task_event(self, audit_service, mock_db_session):
        """Test task event logging convenience method."""
        # Arrange
        task_id = uuid4()
        project_id = uuid4()
        event_data = {"status": "completed"}
        
        # Mock the EventLogDB object and EventLogResponse.model_validate
        with patch('app.services.audit_service.EventLogDB') as mock_event_db_class, \
             patch('app.services.audit_service.EventLogResponse') as mock_response_class:
            
            mock_event = Mock()
            mock_event.id = uuid4()
            mock_event.project_id = project_id
            mock_event.task_id = task_id
            mock_event.hitl_request_id = None
            mock_event.event_type = EventType.TASK_COMPLETED.value
            mock_event.event_source = EventSource.SYSTEM.value
            mock_event.event_data = event_data
            mock_event.event_metadata = {"logged_at": datetime.utcnow().isoformat(), "service_version": "1.0.0"}
            mock_event.created_at = datetime.utcnow()
            
            mock_event_db_class.return_value = mock_event
            
            # Mock the response object
            mock_response = Mock()
            mock_response.task_id = task_id
            mock_response.project_id = project_id
            mock_response.event_type = EventType.TASK_COMPLETED
            mock_response.event_source = EventSource.SYSTEM
            mock_response_class.model_validate.return_value = mock_response
            
            # Act
            result = await audit_service.log_task_event(
                task_id=task_id,
                event_type=EventType.TASK_COMPLETED,
                event_data=event_data,
                project_id=project_id
            )
            
            # Assert
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            
            # Verify the database object was created correctly
            added_event = mock_db_session.add.call_args[0][0]
            assert added_event == mock_event
            assert mock_event.task_id == task_id
            assert mock_event.project_id == project_id
            assert mock_event.event_type == EventType.TASK_COMPLETED.value
            assert mock_event.event_source == EventSource.SYSTEM.value
    
    @pytest.mark.asyncio
    async def test_log_hitl_event(self, audit_service, mock_db_session):
        """Test HITL event logging convenience method."""
        # Arrange
        hitl_request_id = uuid4()
        project_id = uuid4()
        event_data = {"action": "approve", "comment": "Looks good"}
        
        # Mock the EventLogDB object and EventLogResponse.model_validate
        with patch('app.services.audit_service.EventLogDB') as mock_event_db_class, \
             patch('app.services.audit_service.EventLogResponse') as mock_response_class:
            
            mock_event = Mock()
            mock_event.id = uuid4()
            mock_event.project_id = project_id
            mock_event.task_id = None
            mock_event.hitl_request_id = hitl_request_id
            mock_event.event_type = EventType.HITL_RESPONSE.value
            mock_event.event_source = EventSource.USER.value
            mock_event.event_data = event_data
            mock_event.event_metadata = {"logged_at": datetime.utcnow().isoformat(), "service_version": "1.0.0"}
            mock_event.created_at = datetime.utcnow()
            
            mock_event_db_class.return_value = mock_event
            
            # Mock the response object
            mock_response = Mock()
            mock_response.hitl_request_id = hitl_request_id
            mock_response.project_id = project_id
            mock_response.event_type = EventType.HITL_RESPONSE
            mock_response.event_source = EventSource.USER
            mock_response_class.model_validate.return_value = mock_response
            
            # Act
            result = await audit_service.log_hitl_event(
                hitl_request_id=hitl_request_id,
                event_type=EventType.HITL_RESPONSE,
                event_data=event_data,
                event_source=EventSource.USER,
                project_id=project_id
            )
            
            # Assert
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()
            
            # Verify the database object was created correctly
            added_event = mock_db_session.add.call_args[0][0]
            assert added_event == mock_event
            assert mock_event.hitl_request_id == hitl_request_id
            assert mock_event.project_id == project_id
            assert mock_event.event_type == EventType.HITL_RESPONSE.value
            assert mock_event.event_source == EventSource.USER.value
    
    @pytest.mark.asyncio
    async def test_get_events_with_filters(self, audit_service, mock_db_session):
        """Test retrieving events with filters."""
        # Arrange
        project_id = uuid4()
        filter_params = EventLogFilter(
            project_id=project_id,
            event_type=EventType.TASK_CREATED,
            limit=50,
            offset=0
        )
        
        # Mock database query result
        mock_events = [
            Mock(
                id=uuid4(),
                project_id=project_id,
                task_id=uuid4(),
                hitl_request_id=None,
                event_type=EventType.TASK_CREATED.value,
                event_source=EventSource.SYSTEM.value,
                event_data={"test": "data"},
                event_metadata={"test": "metadata"},
                created_at=datetime.utcnow()
            )
        ]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_events
        mock_db_session.execute.return_value = mock_result
        
        # Mock EventLogResponse.model_validate
        with patch('app.services.audit_service.EventLogResponse') as mock_response_class:
            mock_response_class.model_validate.return_value = Mock(
                id=mock_events[0].id,
                project_id=project_id,
                event_type=EventType.TASK_CREATED
            )
            
            # Act
            events = await audit_service.get_events(filter_params)
            
            # Assert
            assert len(events) == 1
            mock_db_session.execute.assert_called_once()
            mock_response_class.model_validate.assert_called_once_with(mock_events[0])
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_found(self, audit_service, mock_db_session):
        """Test retrieving specific event by ID when found."""
        # Arrange
        event_id = uuid4()
        mock_event = Mock(
            id=event_id,
            project_id=uuid4(),
            task_id=None,
            hitl_request_id=None,
            event_type=EventType.TASK_CREATED.value,
            event_source=EventSource.SYSTEM.value,
            event_data={"test": "data"},
            event_metadata={"test": "metadata"},
            created_at=datetime.utcnow()
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_event
        mock_db_session.execute.return_value = mock_result
        
        # Mock EventLogResponse.model_validate
        with patch('app.services.audit_service.EventLogResponse') as mock_response_class:
            mock_response = Mock(id=event_id, event_type=EventType.TASK_CREATED)
            mock_response_class.model_validate.return_value = mock_response
            
            # Act
            event = await audit_service.get_event_by_id(event_id)
            
            # Assert
            assert event is not None
            assert event == mock_response
            mock_db_session.execute.assert_called_once()
            mock_response_class.model_validate.assert_called_once_with(mock_event)
    
    @pytest.mark.asyncio
    async def test_get_event_by_id_not_found(self, audit_service, mock_db_session):
        """Test retrieving specific event by ID when not found."""
        # Arrange
        event_id = uuid4()
        
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Act
        event = await audit_service.get_event_by_id(event_id)
        
        # Assert
        assert event is None
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_events_database_error(self, audit_service, mock_db_session):
        """Test handling database error when retrieving events."""
        # Arrange
        filter_params = EventLogFilter(limit=10, offset=0)
        mock_db_session.execute.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await audit_service.get_events(filter_params)


class TestAuditEventTypes:
    """Test event type and source enums."""
    
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
    
    def test_event_sources_complete(self):
        """Test that all required event sources are defined."""
        required_sources = ["AGENT", "USER", "SYSTEM", "WEBHOOK", "SCHEDULER"]
        
        for event_source in required_sources:
            assert hasattr(EventSource, event_source)


class TestEventLogModels:
    """Test event log Pydantic models."""
    
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
    
    def test_event_log_filter_defaults(self):
        """Test EventLogFilter default values."""
        # Arrange & Act
        filter_params = EventLogFilter()
        
        # Assert
        assert filter_params.limit == 100
        assert filter_params.offset == 0
        assert filter_params.project_id is None
        assert filter_params.event_type is None
    
    def test_event_log_filter_validation(self):
        """Test EventLogFilter validation."""
        # Test limit validation
        with pytest.raises(ValueError):
            EventLogFilter(limit=2000)  # Exceeds maximum
        
        # Test offset validation
        with pytest.raises(ValueError):
            EventLogFilter(offset=-1)  # Below minimum