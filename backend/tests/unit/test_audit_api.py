"""Unit tests for audit API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.event_log import EventType, EventSource, EventLogResponse, EventLogFilter


class TestAuditAPIEndpoints:
    """Test cases for audit trail API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Test client for FastAPI application."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_audit_events(self):
        """Mock audit events for testing."""
        project_id = uuid4()
        task_id = uuid4()
        hitl_request_id = uuid4()
        
        return [
            EventLogResponse(
                id=uuid4(),
                project_id=project_id,
                task_id=task_id,
                hitl_request_id=None,
                event_type=EventType.TASK_CREATED,
                event_source=EventSource.SYSTEM,
                event_data={"action": "task_created", "agent_type": "coder"},
                event_metadata={"logged_at": datetime.now(timezone.utc).isoformat()},
                created_at=datetime.now(timezone.utc)
            ),
            EventLogResponse(
                id=uuid4(),
                project_id=project_id,
                task_id=None,
                hitl_request_id=hitl_request_id,
                event_type=EventType.HITL_RESPONSE,
                event_source=EventSource.USER,
                event_data={"action": "approve", "comment": "Looks good"},
                event_metadata={"logged_at": datetime.now(timezone.utc).isoformat()},
                created_at=datetime.now(timezone.utc)
            ),
            EventLogResponse(
                id=uuid4(),
                project_id=project_id,
                task_id=task_id,
                hitl_request_id=None,
                event_type=EventType.TASK_COMPLETED,
                event_source=EventSource.SYSTEM,
                event_data={"status": "completed", "result": "success"},
                event_metadata={"logged_at": datetime.now(timezone.utc).isoformat()},
                created_at=datetime.now(timezone.utc)
            )
        ]
    
    def test_get_audit_events_success(self, client, mock_audit_events):
        """Test successful retrieval of audit events."""
        with patch('app.api.audit.AuditService') as mock_audit_service_class:

            # Setup mocks
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = mock_audit_events
            mock_audit_service_class.return_value = mock_audit_instance
            
            # Make request
            response = client.get("/api/v1/audit/events")
            
            # Assertions
            assert response.status_code == status.HTTP_200_OK
            
            events_data = response.json()
            assert len(events_data) == 3
            
            # Verify first event structure
            first_event = events_data[0]
            assert "id" in first_event
            assert "project_id" in first_event
            assert "event_type" in first_event
            assert "event_source" in first_event
            assert "event_data" in first_event
            assert "event_metadata" in first_event
            assert "created_at" in first_event
            
            # Verify audit service was called correctly
            mock_audit_instance.get_events.assert_called_once()
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert isinstance(filter_call_args, EventLogFilter)
    
    def test_get_audit_events_with_filters(self, client, mock_audit_events):
        """Test audit events retrieval with query filters."""
        with patch('app.api.audit.get_audit_service') as mock_get_audit_service:

            # Setup mocks
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = [mock_audit_events[0]]  # Filtered result
            mock_get_audit_service.return_value = mock_audit_instance

            # Make request with filters
            project_id = mock_audit_events[0].project_id
            response = client.get(
                f"/api/v1/audit/events?project_id={project_id}&event_type=task_created&limit=50"
            )

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            events_data = response.json()
            assert len(events_data) == 1
            assert events_data[0]["event_type"] == "task_created"

            # Verify filter parameters were passed correctly
            mock_audit_instance.get_events.assert_called_once()
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert filter_call_args.project_id == project_id
            assert filter_call_args.event_type == EventType.TASK_CREATED
            assert filter_call_args.limit == 50
    
    def test_get_audit_events_invalid_limit(self, client):
        """Test audit events with invalid limit parameter."""
        response = client.get("/api/v1/audit/events?limit=2000")  # Exceeds max limit
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data
    
    def test_get_audit_events_invalid_event_type(self, client):
        """Test audit events with invalid event type."""
        response = client.get("/api/v1/audit/events?event_type=invalid_type")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_audit_event_by_id_success(self, client, mock_audit_events):
        """Test successful retrieval of specific audit event by ID."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            target_event = mock_audit_events[0]
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_event_by_id.return_value = target_event
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request
            response = client.get(f"/api/v1/audit/events/{target_event.id}")

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            event_data = response.json()
            assert event_data["id"] == str(target_event.id)
            assert event_data["event_type"] == target_event.event_type.value
            assert event_data["event_source"] == target_event.event_source.value

            # Verify audit service was called correctly
            mock_audit_instance.get_event_by_id.assert_called_once_with(target_event.id)
    
    def test_get_audit_event_by_id_not_found(self, client):
        """Test retrieval of non-existent audit event."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_event_by_id.return_value = None
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request
            non_existent_id = uuid4()
            response = client.get(f"/api/v1/audit/events/{non_existent_id}")

            # Assertions
            assert response.status_code == status.HTTP_404_NOT_FOUND

            error_data = response.json()
            assert "Event not found" in error_data["detail"]
    
    def test_get_audit_event_by_id_invalid_uuid(self, client):
        """Test retrieval with invalid UUID format."""
        response = client.get("/api/v1/audit/events/invalid-uuid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_project_audit_events_success(self, client, mock_audit_events):
        """Test successful retrieval of project-specific audit events."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            project_events = [event for event in mock_audit_events if event.project_id]
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = project_events
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request
            project_id = mock_audit_events[0].project_id
            response = client.get(f"/api/v1/audit/projects/{project_id}/events")

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            events_data = response.json()
            assert len(events_data) == len(project_events)

            # Verify all events belong to the project
            for event in events_data:
                assert event["project_id"] == str(project_id)

            # Verify filter was applied correctly
            mock_audit_instance.get_events.assert_called_once()
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert filter_call_args.project_id == project_id
    
    def test_get_task_audit_events_success(self, client, mock_audit_events):
        """Test successful retrieval of task-specific audit events."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            task_events = [event for event in mock_audit_events if event.task_id]
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = task_events
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request
            task_id = mock_audit_events[0].task_id
            response = client.get(f"/api/v1/audit/tasks/{task_id}/events")

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            events_data = response.json()
            assert len(events_data) == len(task_events)

            # Verify all events belong to the task
            for event in events_data:
                assert event["task_id"] == str(task_id)

            # Verify filter was applied correctly
            mock_audit_instance.get_events.assert_called_once()
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert filter_call_args.task_id == task_id
    
    def test_audit_endpoints_database_error(self, client):
        """Test audit endpoints handle database errors gracefully."""
        with patch('app.api.audit.get_session') as mock_get_session:
            
            # Setup failing database
            mock_db = Mock()
            mock_get_session.side_effect = Exception("Database connection failed")
            
            # Test each endpoint handles errors
            endpoints = [
                "/api/v1/audit/events",
                f"/api/v1/audit/events/{uuid4()}",
                f"/api/v1/audit/projects/{uuid4()}/events",
                f"/api/v1/audit/tasks/{uuid4()}/events"
            ]
            
            for endpoint in endpoints:
                response = client.get(endpoint)
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_audit_pagination_parameters(self, client, mock_audit_events):
        """Test audit events pagination parameters."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = mock_audit_events[1:2]  # Page 2, size 1
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request with pagination
            response = client.get("/api/v1/audit/events?limit=1&offset=1")

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            events_data = response.json()
            assert len(events_data) == 1

            # Verify pagination parameters
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert filter_call_args.limit == 1
            assert filter_call_args.offset == 1
    
    def test_audit_date_range_filtering(self, client, mock_audit_events):
        """Test audit events date range filtering."""
        with patch('app.services.audit_service.AuditService') as mock_audit_service_class:

            # Setup mocks
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = mock_audit_events
            mock_audit_service_class.return_value = mock_audit_instance

            # Make request with date range
            start_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            end_date = datetime.now(timezone.utc).isoformat()

            response = client.get(
                f"/api/v1/audit/events?start_date={start_date}&end_date={end_date}"
            )

            # Assertions
            assert response.status_code == status.HTTP_200_OK

            # Verify date range parameters
            filter_call_args = mock_audit_instance.get_events.call_args[0][0]
            assert filter_call_args.start_date is not None
            assert filter_call_args.end_date is not None


class TestAuditAPIPerformance:
    """Performance tests for audit API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_audit_query_performance_requirement(self, client):
        """Test audit queries meet NFR-01 sub-200ms requirement."""
        import time
        
        with patch('app.api.audit.get_session') as mock_get_session, \
             patch('app.services.audit_service.AuditService') as mock_audit_service:
            
            # Setup mocks
            mock_db = Mock()
            mock_get_session.return_value = mock_db
            
            # Create large mock dataset
            mock_events = []
            for i in range(100):
                mock_events.append(
                    EventLogResponse(
                        id=uuid4(),
                        project_id=uuid4(),
                        task_id=uuid4(),
                        hitl_request_id=None,
                        event_type=EventType.TASK_CREATED,
                        event_source=EventSource.SYSTEM,
                        event_data={"action": f"task_{i}"},
                        event_metadata={"logged_at": datetime.now(timezone.utc).isoformat()},
                        created_at=datetime.now(timezone.utc)
                    )
                )
            
            mock_audit_instance = AsyncMock()
            mock_audit_instance.get_events.return_value = mock_events
            mock_audit_service.return_value = mock_audit_instance
            
            # Test performance of large query
            start_time = time.time()
            
            response = client.get("/api/v1/audit/events?limit=100")
            
            query_time = (time.time() - start_time) * 1000
            
            # Verify performance requirement
            assert query_time < 200, f"Audit query took {query_time}ms, exceeds NFR-01 requirement"
            assert response.status_code == status.HTTP_200_OK
            
            events_data = response.json()
            assert len(events_data) == 100
