"""Integration tests for the audit trail system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.models import Base, EventLogDB
from app.services.audit_service import AuditService
from app.models.event_log import EventType, EventSource, EventLogFilter


class TestAuditTrailIntegration:
    """Integration tests for audit trail with database operations."""
    
    @pytest.fixture
    def test_engine(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        return engine
    
    @pytest.fixture
    def test_session(self, test_engine):
        """Create test database session."""
        TestingSessionLocal = sessionmaker(bind=test_engine)
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    @pytest.fixture
    def audit_service(self, test_session):
        """Create audit service with test database session."""
        return AuditService(test_session)
    
    @pytest.mark.asyncio
    async def test_complete_audit_workflow_integration(self, audit_service):
        """Test complete audit trail workflow with database persistence."""
        # Setup test data
        project_id = uuid4()
        task_id = uuid4()
        hitl_request_id = uuid4()
        
        # Phase 1: Log task creation event
        task_created_event = await audit_service.log_event(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data={
                "agent_type": "coder",
                "instructions": "Create a Python function",
                "priority": "high"
            },
            project_id=project_id,
            task_id=task_id,
            metadata={"endpoint": "/api/v1/tasks", "user_agent": "test-client"}
        )
        
        assert task_created_event.id is not None
        assert task_created_event.project_id == project_id
        assert task_created_event.task_id == task_id
        assert task_created_event.event_type == EventType.TASK_CREATED
        assert task_created_event.event_source == EventSource.SYSTEM
        
        # Phase 2: Log task start event
        task_started_event = await audit_service.log_task_event(
            task_id=task_id,
            event_type=EventType.TASK_STARTED,
            event_data={
                "started_by": "agent_orchestrator",
                "assigned_agent": "coder_001",
                "estimated_duration": "10m"
            },
            project_id=project_id,
            metadata={"workflow_step": 1}
        )
        
        assert task_started_event.task_id == task_id
        assert task_started_event.project_id == project_id
        assert task_started_event.event_type == EventType.TASK_STARTED
        
        # Phase 3: Log HITL request
        hitl_request_event = await audit_service.log_hitl_event(
            hitl_request_id=hitl_request_id,
            event_type=EventType.HITL_REQUEST_CREATED,
            event_data={
                "question": "Please review the generated code",
                "options": ["approve", "reject", "modify"],
                "timeout": "30m",
                "requested_by": "coder_001"
            },
            project_id=project_id,
            metadata={"review_type": "code_review"}
        )
        
        assert hitl_request_event.hitl_request_id == hitl_request_id
        assert hitl_request_event.event_type == EventType.HITL_REQUEST_CREATED
        
        # Phase 4: Log HITL response
        hitl_response_event = await audit_service.log_hitl_event(
            hitl_request_id=hitl_request_id,
            event_type=EventType.HITL_RESPONSE,
            event_data={
                "action": "approve",
                "comment": "Code looks good, well structured",
                "reviewed_by": "human_reviewer_001",
                "review_duration": "5m"
            },
            event_source=EventSource.USER,
            project_id=project_id,
            metadata={"confidence_score": 0.95}
        )
        
        assert hitl_response_event.event_source == EventSource.USER
        assert hitl_response_event.hitl_request_id == hitl_request_id
        
        # Phase 5: Log task completion
        task_completed_event = await audit_service.log_task_event(
            task_id=task_id,
            event_type=EventType.TASK_COMPLETED,
            event_data={
                "status": "success",
                "output": "Function created successfully",
                "execution_time": "8m",
                "artifacts_generated": 3
            },
            project_id=project_id,
            metadata={"performance_metrics": {"cpu_time": "2.1s", "memory_peak": "45MB"}}
        )
        
        assert task_completed_event.event_type == EventType.TASK_COMPLETED
        
        # Phase 6: Query and verify complete audit trail
        filter_params = EventLogFilter(
            project_id=project_id,
            limit=100,
            offset=0
        )
        
        all_events = await audit_service.get_events(filter_params)
        
        # Verify all events are present and ordered correctly
        assert len(all_events) == 5
        
        event_types = [event.event_type for event in all_events]
        expected_types = [
            EventType.TASK_COMPLETED,  # Most recent first
            EventType.HITL_RESPONSE,
            EventType.HITL_REQUEST_CREATED,
            EventType.TASK_STARTED,
            EventType.TASK_CREATED
        ]
        
        assert event_types == expected_types
        
        # Verify data integrity across all events
        project_events = [e for e in all_events if e.project_id == project_id]
        assert len(project_events) == 5
        
        task_events = [e for e in all_events if e.task_id == task_id]
        assert len(task_events) == 3  # Created, Started, Completed
        
        hitl_events = [e for e in all_events if e.hitl_request_id == hitl_request_id]
        assert len(hitl_events) == 2  # Request, Response
    
    @pytest.mark.asyncio
    async def test_audit_trail_filtering_integration(self, audit_service):
        """Test comprehensive filtering capabilities."""
        # Setup test data with multiple projects and event types
        project_1 = uuid4()
        project_2 = uuid4()
        task_1 = uuid4()
        task_2 = uuid4()
        
        # Create events for project 1
        await audit_service.log_event(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data={"test": "project1_task1"},
            project_id=project_1,
            task_id=task_1
        )
        
        await audit_service.log_event(
            event_type=EventType.TASK_COMPLETED,
            event_source=EventSource.SYSTEM,
            event_data={"test": "project1_task1_completed"},
            project_id=project_1,
            task_id=task_1
        )
        
        # Create events for project 2
        await audit_service.log_event(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data={"test": "project2_task2"},
            project_id=project_2,
            task_id=task_2
        )
        
        await audit_service.log_event(
            event_type=EventType.PROJECT_CREATED,
            event_source=EventSource.USER,
            event_data={"test": "project2_created"},
            project_id=project_2
        )
        
        # Test project-specific filtering
        project_1_filter = EventLogFilter(project_id=project_1)
        project_1_events = await audit_service.get_events(project_1_filter)
        
        assert len(project_1_events) == 2
        assert all(event.project_id == project_1 for event in project_1_events)
        
        # Test event type filtering
        task_created_filter = EventLogFilter(event_type=EventType.TASK_CREATED)
        task_created_events = await audit_service.get_events(task_created_filter)
        
        assert len(task_created_events) == 2
        assert all(event.event_type == EventType.TASK_CREATED for event in task_created_events)
        
        # Test event source filtering
        user_events_filter = EventLogFilter(event_source=EventSource.USER)
        user_events = await audit_service.get_events(user_events_filter)
        
        assert len(user_events) == 1
        assert user_events[0].event_source == EventSource.USER
        assert user_events[0].event_type == EventType.PROJECT_CREATED
        
        # Test combined filtering
        combined_filter = EventLogFilter(
            project_id=project_1,
            event_type=EventType.TASK_COMPLETED
        )
        combined_events = await audit_service.get_events(combined_filter)
        
        assert len(combined_events) == 1
        assert combined_events[0].project_id == project_1
        assert combined_events[0].event_type == EventType.TASK_COMPLETED
        
        # Test task-specific filtering
        task_1_filter = EventLogFilter(task_id=task_1)
        task_1_events = await audit_service.get_events(task_1_filter)
        
        assert len(task_1_events) == 2
        assert all(event.task_id == task_1 for event in task_1_events)
    
    @pytest.mark.asyncio 
    async def test_audit_trail_pagination_integration(self, audit_service):
        """Test pagination functionality with database."""
        project_id = uuid4()
        
        # Create multiple events
        for i in range(15):
            await audit_service.log_event(
                event_type=EventType.TASK_CREATED if i % 2 == 0 else EventType.TASK_COMPLETED,
                event_source=EventSource.SYSTEM,
                event_data={"sequence": i, "test": f"event_{i}"},
                project_id=project_id
            )
        
        # Test first page
        page_1_filter = EventLogFilter(project_id=project_id, limit=5, offset=0)
        page_1_events = await audit_service.get_events(page_1_filter)
        
        assert len(page_1_events) == 5
        
        # Test second page
        page_2_filter = EventLogFilter(project_id=project_id, limit=5, offset=5)
        page_2_events = await audit_service.get_events(page_2_filter)
        
        assert len(page_2_events) == 5
        
        # Test third page
        page_3_filter = EventLogFilter(project_id=project_id, limit=5, offset=10)
        page_3_events = await audit_service.get_events(page_3_filter)
        
        assert len(page_3_events) == 5
        
        # Test fourth page (partial)
        page_4_filter = EventLogFilter(project_id=project_id, limit=5, offset=15)
        page_4_events = await audit_service.get_events(page_4_filter)
        
        assert len(page_4_events) == 0  # No more events
        
        # Verify no duplicate events across pages
        all_event_ids = set()
        for events in [page_1_events, page_2_events, page_3_events]:
            for event in events:
                assert event.id not in all_event_ids, "Duplicate event found across pages"
                all_event_ids.add(event.id)
        
        assert len(all_event_ids) == 15
    
    @pytest.mark.asyncio
    async def test_audit_trail_date_range_filtering_integration(self, audit_service):
        """Test date range filtering with real database operations."""
        project_id = uuid4()
        base_time = datetime.utcnow()
        
        # Create events with different timestamps by patching datetime
        events_data = [
            (base_time - timedelta(hours=2), "old_event_1"),
            (base_time - timedelta(hours=1), "recent_event_1"),
            (base_time, "current_event"),
            (base_time + timedelta(minutes=30), "future_event_1")  # Simulating clock skew
        ]
        
        created_events = []
        for event_time, event_name in events_data:
            # Mock the datetime for each event creation
            with patch('app.services.audit_service.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = event_time
                
                event = await audit_service.log_event(
                    event_type=EventType.SYSTEM_WARNING,
                    event_source=EventSource.SYSTEM,
                    event_data={"event_name": event_name, "timestamp": event_time.isoformat()},
                    project_id=project_id,
                    metadata={"test_timestamp": event_time.isoformat()}
                )
                created_events.append(event)
        
        # Test date range filtering (last hour)
        recent_filter = EventLogFilter(
            project_id=project_id,
            start_date=base_time - timedelta(hours=1, minutes=30),
            end_date=base_time + timedelta(hours=1)
        )
        
        recent_events = await audit_service.get_events(recent_filter)
        
        # Should include: recent_event_1, current_event, future_event_1
        assert len(recent_events) == 3
        
        event_names = [event.event_data["event_name"] for event in recent_events]
        expected_names = ["future_event_1", "current_event", "recent_event_1"]  # Newest first
        assert event_names == expected_names
        
        # Test filtering for very recent events only
        very_recent_filter = EventLogFilter(
            project_id=project_id,
            start_date=base_time - timedelta(minutes=30),
            end_date=base_time + timedelta(hours=1)
        )
        
        very_recent_events = await audit_service.get_events(very_recent_filter)
        
        # Should include: current_event, future_event_1
        assert len(very_recent_events) == 2
        
        very_recent_names = [event.event_data["event_name"] for event in very_recent_events]
        assert "current_event" in very_recent_names
        assert "future_event_1" in very_recent_names
    
    @pytest.mark.asyncio
    async def test_audit_trail_error_recovery_integration(self, audit_service):
        """Test audit trail behavior during error conditions."""
        project_id = uuid4()
        
        # Test successful event logging
        success_event = await audit_service.log_event(
            event_type=EventType.TASK_CREATED,
            event_source=EventSource.SYSTEM,
            event_data={"status": "success"},
            project_id=project_id
        )
        
        assert success_event.id is not None
        
        # Test logging system error event
        error_event = await audit_service.log_event(
            event_type=EventType.SYSTEM_ERROR,
            event_source=EventSource.SYSTEM,
            event_data={
                "error_type": "database_connection_failed",
                "error_message": "Unable to connect to primary database",
                "error_code": "DB_CONN_FAIL",
                "recovery_action": "switched_to_replica",
                "affected_services": ["task_processor", "audit_logger"]
            },
            project_id=project_id,
            metadata={
                "severity": "high",
                "requires_immediate_attention": True,
                "incident_id": str(uuid4())
            }
        )
        
        assert error_event.event_type == EventType.SYSTEM_ERROR
        assert error_event.event_data["error_code"] == "DB_CONN_FAIL"
        assert error_event.event_metadata["severity"] == "high"
        
        # Test recovery event logging
        recovery_event = await audit_service.log_event(
            event_type=EventType.SYSTEM_WARNING,
            event_source=EventSource.SYSTEM,
            event_data={
                "recovery_status": "services_restored",
                "downtime_duration": "5m 32s",
                "affected_requests": 23,
                "recovery_method": "automatic_failover"
            },
            project_id=project_id,
            metadata={
                "incident_resolved": True,
                "post_mortem_required": True
            }
        )
        
        # Query all error-related events
        error_filter = EventLogFilter(
            project_id=project_id,
            event_type=EventType.SYSTEM_ERROR
        )
        error_events = await audit_service.get_events(error_filter)
        
        assert len(error_events) == 1
        assert error_events[0].event_data["error_code"] == "DB_CONN_FAIL"
        
        # Verify complete incident trail
        incident_filter = EventLogFilter(project_id=project_id)
        all_events = await audit_service.get_events(incident_filter)
        
        assert len(all_events) == 3  # success, error, recovery
        
        # Verify chronological order (newest first)
        event_types = [event.event_type for event in all_events]
        expected_order = [EventType.SYSTEM_WARNING, EventType.SYSTEM_ERROR, EventType.TASK_CREATED]
        assert event_types == expected_order
    
    @pytest.mark.asyncio
    async def test_audit_trail_high_volume_integration(self, audit_service):
        """Test audit trail performance with high volume of events."""
        import time
        
        project_id = uuid4()
        num_events = 100
        
        # Measure bulk event creation performance
        start_time = time.time()
        
        created_events = []
        for i in range(num_events):
            event = await audit_service.log_event(
                event_type=EventType.AGENT_STATUS_CHANGED if i % 3 == 0 else EventType.TASK_CREATED,
                event_source=EventSource.SYSTEM,
                event_data={
                    "sequence_number": i,
                    "batch_id": "high_volume_test",
                    "agent_id": f"agent_{i % 10}",
                    "operation": f"bulk_operation_{i}"
                },
                project_id=project_id,
                metadata={
                    "batch_sequence": i,
                    "performance_test": True
                }
            )
            created_events.append(event)
        
        creation_time = time.time() - start_time
        
        # Performance validation: should handle 100 events in reasonable time
        assert creation_time < 10.0, f"Bulk creation took {creation_time}s, too slow"
        
        # Verify all events were created
        assert len(created_events) == num_events
        assert all(event.id is not None for event in created_events)
        
        # Test bulk retrieval performance
        start_time = time.time()
        
        bulk_filter = EventLogFilter(project_id=project_id, limit=num_events)
        retrieved_events = await audit_service.get_events(bulk_filter)
        
        retrieval_time = time.time() - start_time
        
        # Performance validation: retrieval should be fast
        assert retrieval_time < 2.0, f"Bulk retrieval took {retrieval_time}s, too slow"
        
        # Verify data integrity
        assert len(retrieved_events) == num_events
        
        # Verify sequence integrity (newest first)
        sequences = [event.event_data["sequence_number"] for event in retrieved_events]
        expected_sequences = list(range(num_events - 1, -1, -1))  # Reverse order
        assert sequences == expected_sequences
        
        # Test filtered high-volume query performance
        start_time = time.time()
        
        status_change_filter = EventLogFilter(
            project_id=project_id,
            event_type=EventType.AGENT_STATUS_CHANGED
        )
        status_events = await audit_service.get_events(status_change_filter)
        
        filtered_query_time = time.time() - start_time
        
        # Should be fast even with filtering
        assert filtered_query_time < 1.0, f"Filtered query took {filtered_query_time}s"
        
        # Verify filtering worked correctly
        expected_status_events = len([i for i in range(num_events) if i % 3 == 0])
        assert len(status_events) == expected_status_events
        assert all(event.event_type == EventType.AGENT_STATUS_CHANGED for event in status_events)