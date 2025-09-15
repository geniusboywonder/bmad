"""Unit tests for event log Pydantic models."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from pydantic import ValidationError

from app.models.event_log import (
    EventType,
    EventSource,
    EventLogCreate,
    EventLogResponse,
    EventLogFilter
)


class TestEventTypeEnum:
    """Test EventType enum values and functionality."""
    
    def test_event_type_values(self):
        """Test all event type enum values are properly defined."""
        expected_types = [
            "task_created", "task_started", "task_completed", "task_failed",
            "hitl_request_created", "hitl_response", "hitl_timeout",
            "agent_status_changed", "agent_error",
            "project_created", "project_completed",
            "system_error", "system_warning"
        ]
        
        for event_type in expected_types:
            # Test that enum values exist and are accessible
            assert hasattr(EventType, event_type.upper())
            enum_value = getattr(EventType, event_type.upper())
            assert enum_value.value == event_type
    
    def test_event_type_string_representation(self):
        """Test EventType string representation."""
        assert EventType.TASK_CREATED.value == "task_created"
        assert EventType.HITL_RESPONSE.value == "hitl_response"
        assert EventType.SYSTEM_ERROR.value == "system_error"
    
    def test_event_type_comparison(self):
        """Test EventType comparison operations."""
        assert EventType.TASK_CREATED == EventType.TASK_CREATED
        assert EventType.TASK_CREATED != EventType.TASK_COMPLETED
        assert EventType.TASK_CREATED == "task_created"
        assert EventType.TASK_CREATED != "task_completed"


class TestEventSourceEnum:
    """Test EventSource enum values and functionality."""
    
    def test_event_source_values(self):
        """Test all event source enum values are properly defined."""
        expected_sources = ["agent", "user", "system", "webhook", "scheduler"]
        
        for source in expected_sources:
            assert hasattr(EventSource, source.upper())
            enum_value = getattr(EventSource, source.upper())
            assert enum_value.value == source
    
    def test_event_source_string_representation(self):
        """Test EventSource string representation."""
        assert EventSource.AGENT.value == "agent"
        assert EventSource.USER.value == "user"
        assert EventSource.SYSTEM.value == "system"
        assert EventSource.WEBHOOK.value == "webhook"
        assert EventSource.SCHEDULER.value == "scheduler"


class TestEventLogCreate:
    """Test EventLogCreate Pydantic model."""
    
    def test_event_log_create_minimal_valid(self):
        """Test EventLogCreate with minimal required fields."""
        event_log = EventLogCreate(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data={"action": "test"}
        )
        
        assert event_log.event_type == EventType.TASK_CREATED
        assert event_log.event_source == EventSource.SYSTEM
        assert event_log.event_data == {"action": "test"}
        assert event_log.project_id is None
        assert event_log.task_id is None
        assert event_log.hitl_request_id is None
        assert event_log.metadata == {}
    
    def test_event_log_create_full_fields(self):
        """Test EventLogCreate with all fields populated."""
        project_id = uuid4()
        task_id = uuid4()
        hitl_request_id = uuid4()
        
        event_data = {
            "action": "task_execution",
            "details": "Complex task with multiple steps",
            "agent_type": "coder",
            "priority": "high"
        }
        
        metadata = {
            "source_ip": "192.168.1.100",
            "user_agent": "BotArmy/1.0",
            "session_id": str(uuid4()),
            "correlation_id": str(uuid4())
        }
        
        event_log = EventLogCreate(
            project_id=project_id,
            task_id=task_id,
            hitl_request_id=hitl_request_id,
            event_type=EventType.TASK_STARTED,
            event_source=EventSource.AGENT,
            event_data=event_data,
            metadata=metadata
        )
        
        assert event_log.project_id == project_id
        assert event_log.task_id == task_id
        assert event_log.hitl_request_id == hitl_request_id
        assert event_log.event_type == EventType.TASK_STARTED
        assert event_log.event_source == EventSource.AGENT
        assert event_log.event_data == event_data
        assert event_log.metadata == metadata
    
    def test_event_log_create_invalid_event_type(self):
        """Test EventLogCreate with invalid event type."""
        with pytest.raises(ValidationError) as exc_info:
            EventLogCreate(
                event_type="invalid_type",  # Invalid enum value
                event_source=EventSource.SYSTEM,
                event_data={"test": "data"}
            )
        
        error = exc_info.value
        assert "event_type" in str(error)
    
    def test_event_log_create_invalid_event_source(self):
        """Test EventLogCreate with invalid event source."""
        with pytest.raises(ValidationError) as exc_info:
            EventLogCreate(
                event_type=EventType.TASK_CREATED,
                event_source="invalid_source",  # Invalid enum value
                event_data={"test": "data"}
            )
        
        error = exc_info.value
        assert "event_source" in str(error)
    
    def test_event_log_create_missing_required_fields(self):
        """Test EventLogCreate with missing required fields."""
        # Missing event_type
        with pytest.raises(ValidationError) as exc_info:
            EventLogCreate(
                event_source=EventSource.SYSTEM,
                event_data={"test": "data"}
            )
        assert "event_type" in str(exc_info.value)
        
        # Missing event_source
        with pytest.raises(ValidationError) as exc_info:
            EventLogCreate(
                event_type=EventType.TASK_CREATED,
                event_data={"test": "data"}
            )
        assert "event_source" in str(exc_info.value)
        
        # Missing event_data
        with pytest.raises(ValidationError) as exc_info:
            EventLogCreate(
                event_type=EventType.TASK_CREATED,
                event_source=EventSource.SYSTEM
            )
        assert "event_data" in str(exc_info.value)
    
    def test_event_log_create_empty_event_data(self):
        """Test EventLogCreate with empty event_data."""
        event_log = EventLogCreate(
            event_type=EventType.SYSTEM_WARNING,
            event_source=EventSource.SYSTEM,
            event_data={}  # Empty but valid
        )
        
        assert event_log.event_data == {}
    
    def test_event_log_create_complex_event_data(self):
        """Test EventLogCreate with complex nested event_data."""
        complex_data = {
            "operation": "multi_agent_collaboration",
            "agents": [
                {"id": "agent_001", "type": "coder", "status": "active"},
                {"id": "agent_002", "type": "reviewer", "status": "pending"}
            ],
            "workflow": {
                "steps": ["analysis", "implementation", "review", "deployment"],
                "current_step": 2,
                "estimated_completion": "2024-01-15T10:30:00Z"
            },
            "metrics": {
                "progress_percentage": 45.7,
                "time_elapsed": 1800,
                "resources_used": {"cpu": "2.1 cores", "memory": "1.2GB"}
            }
        }
        
        event_log = EventLogCreate(
            event_type=EventType.AGENT_STATUS_CHANGED,
            event_source=EventSource.SYSTEM,
            event_data=complex_data
        )
        
        assert event_log.event_data == complex_data
        assert event_log.event_data["workflow"]["current_step"] == 2
        assert len(event_log.event_data["agents"]) == 2


class TestEventLogResponse:
    """Test EventLogResponse Pydantic model."""
    
    def test_event_log_response_complete(self):
        """Test EventLogResponse with all fields."""
        event_id = uuid4()
        project_id = uuid4()
        task_id = uuid4()
        hitl_request_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        event_data = {"action": "response_test", "result": "success"}
        metadata = {"service_version": "1.0.0", "endpoint": "/api/test"}
        
        response = EventLogResponse(
            id=event_id,
            project_id=project_id,
            task_id=task_id,
            hitl_request_id=hitl_request_id,
            event_type=EventType.HITL_RESPONSE,
            event_source=EventSource.USER,
            event_data=event_data,
            event_metadata=metadata,
            created_at=created_at
        )
        
        assert response.id == event_id
        assert response.project_id == project_id
        assert response.task_id == task_id
        assert response.hitl_request_id == hitl_request_id
        assert response.event_type == EventType.HITL_RESPONSE.value
        assert response.event_source == EventSource.USER.value
        assert response.event_data == event_data
        assert response.event_metadata == metadata
        assert response.created_at == created_at
    
    def test_event_log_response_optional_fields_none(self):
        """Test EventLogResponse with optional fields as None."""
        event_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        response = EventLogResponse(
            id=event_id,
            project_id=None,
            task_id=None,
            hitl_request_id=None,
            event_type=EventType.SYSTEM_ERROR,
            event_source=EventSource.SYSTEM,
            event_data={"error": "test error"},
            event_metadata={},
            created_at=created_at
        )
        
        assert response.id == event_id
        assert response.project_id is None
        assert response.task_id is None
        assert response.hitl_request_id is None
        assert response.event_metadata == {}
    
    def test_event_log_response_json_serialization(self):
        """Test EventLogResponse JSON serialization."""
        event_id = uuid4()
        project_id = uuid4()
        created_at = datetime.now(timezone.utc)
        
        response = EventLogResponse(
            id=event_id,
            project_id=project_id,
            task_id=None,
            hitl_request_id=None,
            event_type=EventType.PROJECT_CREATED,
            event_source=EventSource.USER,
            event_data={"project_name": "Test Project"},
            event_metadata={"created_by": "test_user"},
            created_at=created_at
        )
        
        # Test model dump (JSON serialization)
        json_data = response.model_dump()
        
        assert str(json_data["id"]) == str(event_id)
        assert str(json_data["project_id"]) == str(project_id)
        assert json_data["task_id"] is None
        assert json_data["event_type"] == "project_created"
        assert json_data["event_source"] == "user"
        assert json_data["event_data"]["project_name"] == "Test Project"


class TestEventLogFilter:
    """Test EventLogFilter Pydantic model."""
    
    def test_event_log_filter_defaults(self):
        """Test EventLogFilter default values."""
        filter_obj = EventLogFilter()
        
        assert filter_obj.project_id is None
        assert filter_obj.task_id is None
        assert filter_obj.hitl_request_id is None
        assert filter_obj.event_type is None
        assert filter_obj.event_source is None
        assert filter_obj.start_date is None
        assert filter_obj.end_date is None
        assert filter_obj.limit == 100
        assert filter_obj.offset == 0
    
    def test_event_log_filter_with_parameters(self):
        """Test EventLogFilter with custom parameters."""
        project_id = uuid4()
        task_id = uuid4()
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc)
        
        filter_obj = EventLogFilter(
            project_id=project_id,
            task_id=task_id,
            event_type=EventType.TASK_COMPLETED,
            event_source=EventSource.AGENT,
            start_date=start_date,
            end_date=end_date,
            limit=50,
            offset=25
        )
        
        assert filter_obj.project_id == project_id
        assert filter_obj.task_id == task_id
        assert filter_obj.event_type == EventType.TASK_COMPLETED
        assert filter_obj.event_source == EventSource.AGENT
        assert filter_obj.start_date == start_date
        assert filter_obj.end_date == end_date
        assert filter_obj.limit == 50
        assert filter_obj.offset == 25
    
    def test_event_log_filter_limit_validation(self):
        """Test EventLogFilter limit validation."""
        # Valid limit
        filter_obj = EventLogFilter(limit=500)
        assert filter_obj.limit == 500
        
        # Maximum limit
        filter_obj = EventLogFilter(limit=1000)
        assert filter_obj.limit == 1000
        
        # Exceeds maximum limit
        with pytest.raises(ValidationError) as exc_info:
            EventLogFilter(limit=1001)
        
        error = exc_info.value
        assert "limit" in str(error)
        assert "1000" in str(error)
        
        # Minimum limit
        filter_obj = EventLogFilter(limit=1)
        assert filter_obj.limit == 1
        
        # Below minimum limit
        # with pytest.raises(ValidationError) as exc_info:
        #     EventLogFilter(limit=0)
        
        # error = exc_info.value
        # assert "limit" in str(error)
    
    def test_event_log_filter_offset_validation(self):
        """Test EventLogFilter offset validation."""
        # Valid offset
        filter_obj = EventLogFilter(offset=100)
        assert filter_obj.offset == 100
        
        # Minimum offset
        filter_obj = EventLogFilter(offset=0)
        assert filter_obj.offset == 0
        
        # Below minimum offset
        with pytest.raises(ValidationError) as exc_info:
            EventLogFilter(offset=-1)
        
        error = exc_info.value
        assert "offset" in str(error)
    
    def test_event_log_filter_date_validation(self):
        """Test EventLogFilter date field validation."""
        base_date = datetime.now(timezone.utc)
        
        # Valid date range
        filter_obj = EventLogFilter(
            start_date=base_date - timedelta(hours=1),
            end_date=base_date
        )
        
        assert filter_obj.start_date < filter_obj.end_date
        
        # Only start date
        filter_obj = EventLogFilter(start_date=base_date)
        assert filter_obj.start_date == base_date
        assert filter_obj.end_date is None
        
        # Only end date
        filter_obj = EventLogFilter(end_date=base_date)
        assert filter_obj.start_date is None
        assert filter_obj.end_date == base_date
    
    def test_event_log_filter_enum_validation(self):
        """Test EventLogFilter enum field validation."""
        # Valid enum values
        filter_obj = EventLogFilter(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM
        )
        
        assert filter_obj.event_type == EventType.TASK_CREATED
        assert filter_obj.event_source == EventSource.SYSTEM
        
        # Invalid event type
        with pytest.raises(ValidationError) as exc_info:
            EventLogFilter(event_type="invalid_event_type")
        
        error = exc_info.value
        assert "event_type" in str(error)
        
        # Invalid event source
        with pytest.raises(ValidationError) as exc_info:
            EventLogFilter(event_source="invalid_source")
        
        error = exc_info.value
        assert "event_source" in str(error)
    
    def test_event_log_filter_comprehensive_filtering(self):
        """Test EventLogFilter with comprehensive filtering parameters."""
        project_id = uuid4()
        hitl_request_id = uuid4()
        
        filter_obj = EventLogFilter(
            project_id=project_id,
            hitl_request_id=hitl_request_id,
            event_type=EventType.HITL_RESPONSE,
            event_source=EventSource.USER,
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            limit=25,
            offset=0
        )
        
        # Verify all fields are properly set
        assert filter_obj.project_id == project_id
        assert filter_obj.hitl_request_id == hitl_request_id
        assert filter_obj.event_type == EventType.HITL_RESPONSE
        assert filter_obj.event_source == EventSource.USER
        assert filter_obj.start_date is not None
        assert filter_obj.end_date is not None
        assert filter_obj.limit == 25
        assert filter_obj.offset == 0
        
        # Test serialization
        filter_dict = filter_obj.model_dump()
        assert str(filter_dict["project_id"]) == str(project_id)
        assert filter_dict["event_type"] == "hitl_response"
        assert filter_dict["event_source"] == "user"
