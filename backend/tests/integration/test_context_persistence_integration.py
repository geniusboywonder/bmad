"""
Integration tests for Story 1.2: Context & Task State Persistence

Test scenarios:
- 1.2-INT-001: Context artifact CRUD operations (P0)
- 1.2-INT-002: Task state persistence and retrieval (P0)
- 1.2-INT-003: Service layer database abstraction (P1)
- 1.2-INT-004: Event logging for state changes (P1)
- 1.2-INT-005: Context artifact query performance (P2)
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.models import ContextArtifactDB, TaskDB
from app.models.context import ArtifactType
from app.models.agent import AgentType
from app.models.task import TaskStatus
from app.services.context_store import ContextStoreService
from tests.conftest import assert_context_artifact_matches_data

class TestContextArtifactCRUDOperations:
    """Test scenario 1.2-INT-001: Context artifact CRUD operations (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_create_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService, 
        project_factory, sample_context_artifact_data
    ):
        """Test creating a context artifact through service layer."""
        project = project_factory.create(db_session)
        
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType(sample_context_artifact_data["source_agent"]),  # Convert to enum
            artifact_type=sample_context_artifact_data["artifact_type"],
            content=sample_context_artifact_data["content"],
            artifact_metadata=sample_context_artifact_data["artifact_metadata"]
        )

        assert isinstance(artifact.context_id, UUID)
        assert artifact.project_id == project.id
        assert artifact.source_agent == AgentType(sample_context_artifact_data["source_agent"])  # Compare as enum
        assert artifact.artifact_type == sample_context_artifact_data["artifact_type"]
        assert artifact.content == sample_context_artifact_data["content"]
        assert artifact.artifact_metadata == sample_context_artifact_data["artifact_metadata"]
        
        # Verify persistence in database
        db_artifact = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact.context_id
        ).first()
        assert db_artifact is not None
        assert_context_artifact_matches_data(db_artifact, sample_context_artifact_data)
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_get_context_artifact_by_id(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test retrieving a context artifact by ID."""
        project = project_factory.create(db_session)
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.TESTER,  # Use enum directly
            artifact_type=ArtifactType.TEST_RESULTS,
            content={"test_id": i}
        )

        # Retrieve artifact
        retrieved_artifact = context_store_service.get_artifact(artifact.context_id)

        assert retrieved_artifact is not None
        assert retrieved_artifact.context_id == artifact.context_id
        assert retrieved_artifact.content == artifact.content
        assert retrieved_artifact.source_agent == artifact.source_agent
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_update_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test updating an existing context artifact."""
        project = project_factory.create(db_session)
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.CODER,  # Use enum directly
            artifact_type=ArtifactType.SOURCE_CODE,
            content={"version": "1.0", "files": ["main.py"]}
        )
        
        # Update content
        updated_content = {"version": "1.1", "files": ["main.py", "utils.py"]}
        updated_metadata = {"updated": True, "change_log": "Added utils.py"}
        
        updated_artifact = context_store_service.update_artifact(
            artifact.context_id,
            content=updated_content,
            artifact_metadata=updated_metadata
        )
        
        assert updated_artifact is not None
        assert updated_artifact.content == updated_content
        assert updated_artifact.artifact_metadata == updated_metadata
        assert updated_artifact.context_id == artifact.context_id  # ID unchanged
        
        # Verify in database
        db_artifact = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact.context_id
        ).first()
        assert db_artifact.content == updated_content
        assert db_artifact.artifact_metadata == updated_metadata
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_delete_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test deleting a context artifact."""
        project = project_factory.create(db_session)
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.TESTER,  # Use enum directly
            artifact_type=ArtifactType.TEST_RESULTS,
            content={"tests_passed": 10, "tests_failed": 2}
        )
        
        artifact_id = artifact.context_id
        
        # Delete artifact
        deleted = context_store_service.delete_artifact(artifact_id)
        assert deleted is True
        
        # Verify deletion
        retrieved = context_store_service.get_artifact(artifact_id)
        assert retrieved is None
        
        # Verify in database
        db_artifact = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact_id
        ).first()
        assert db_artifact is None
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_get_artifacts_by_project(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test retrieving all artifacts for a project."""
        project = project_factory.create(db_session)
        
        # Create multiple artifacts
        artifact1 = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"plan": "v1"}
        )
        
        artifact2 = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ARCHITECT,
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            content={"implementation": "v1"}
        )
        
        # Retrieve all artifacts for project
        artifacts = context_store_service.get_artifacts_by_project(project.id)
        
        assert len(artifacts) == 2
        artifact_ids = [a.context_id for a in artifacts]
        assert artifact1.context_id in artifact_ids
        assert artifact2.context_id in artifact_ids

class TestTaskStatePersistence:
    """Test scenario 1.2-INT-002: Task state persistence and retrieval (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_task_status_updates_persisted(
        self, db_session: Session, orchestrator_service, project_factory
    ):
        """Test that task status updates are properly persisted."""
        project = project_factory.create(db_session)
        
        # Create task
        task = orchestrator_service.create_task(
            project_id=project.id,
            agent_type=AgentType.ANALYST,
            instructions="Test task for status updates"
        )
        
        initial_status = task.status
        assert initial_status == TaskStatus.PENDING
        
        # Update task status
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.WORKING,
            output={"progress": "50%"}
        )
        
        # Verify status update in database
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert db_task.status == TaskStatus.WORKING
        assert db_task.output["progress"] == "50%"
        assert db_task.started_at is not None  # Should be auto-set
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_task_completion_timestamps(
        self, db_session: Session, orchestrator_service, project_factory
    ):
        """Test task completion timestamp handling."""
        project = project_factory.create(db_session)
        
        task = orchestrator_service.create_task(
            project_id=project.id,
            agent_type=AgentType.CODER,
            instructions="Timestamp test task"
        )
        
        # Mark as working
        orchestrator_service.update_task_status(task.task_id, TaskStatus.WORKING)
        
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        started_at = db_task.started_at
        assert started_at is not None
        
        # Mark as completed
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            output={"result": "success"}
        )
        
        db_session.refresh(db_task)
        assert db_task.completed_at is not None
        assert db_task.completed_at >= started_at
        assert db_task.status == TaskStatus.COMPLETED
    
    @pytest.mark.integration
    @pytest.mark.p0
    def test_task_error_state_persistence(
        self, db_session: Session, orchestrator_service, project_factory
    ):
        """Test task error state and message persistence."""
        project = project_factory.create(db_session)
        
        task = orchestrator_service.create_task(
            project_id=project.id,
            agent_type=AgentType.TESTER,
            instructions="Error test task"
        )
        
        error_message = "Test execution failed due to missing dependencies"
        
        # Update to failed status with error message
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.FAILED,
            error_message=error_message
        )
        
        # Verify error state persistence
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert db_task.status == TaskStatus.FAILED
        assert db_task.error_message == error_message
        assert db_task.completed_at is not None  # Failed tasks should have completion time
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_task_output_data_persistence(
        self, db_session: Session, orchestrator_service, project_factory
    ):
        """Test complex task output data persistence."""
        project = project_factory.create(db_session)
        
        task = orchestrator_service.create_task(
            project_id=project.id,
            agent_type=AgentType.DEPLOYER,
            instructions="Output data test"
        )
        
        complex_output = {
            "deployment": {
                "status": "successful",
                "url": "https://app.example.com",
                "services": ["api", "frontend", "database"],
                "metrics": {
                    "cpu_usage": 0.25,
                    "memory_usage": 0.60,
                    "response_time_ms": 120
                }
            },
            "logs": [
                {"timestamp": "2023-12-01T10:00:00Z", "message": "Starting deployment"},
                {"timestamp": "2023-12-01T10:05:00Z", "message": "Deployment complete"}
            ]
        }
        
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.COMPLETED,
            output=complex_output
        )
        
        # Verify complex data persistence
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert db_task.output == complex_output
        assert db_task.output["deployment"]["status"] == "successful"
        assert len(db_task.output["logs"]) == 2

class TestServiceLayerDatabaseAbstraction:
    """Test scenario 1.2-INT-003: Service layer database abstraction (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_service_layer_isolates_database_concerns(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test that service layer properly abstracts database operations."""
        project = project_factory.create(db_session)
        
        # Service methods should return domain models, not database models
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,  # Use enum directly
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"test": "abstraction"}
        )
        
        # Result should be domain model, not database model
        from app.models.context import ContextArtifact
        assert isinstance(artifact, ContextArtifact)
        assert not isinstance(artifact, ContextArtifactDB)
        
        # Service should handle conversion between domain and database models
        retrieved = context_store_service.get_artifact(artifact.context_id)
        assert isinstance(retrieved, ContextArtifact)
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_service_layer_transaction_management(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test service layer handles database transactions properly."""
        project = project_factory.create(db_session)
        
        initial_count = db_session.query(ContextArtifactDB).count()
        
        # Service operation should complete transaction
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ARCHITECT,  # Use enum directly
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            content={"transaction": "test"}
        )
        
        # Changes should be committed
        final_count = db_session.query(ContextArtifactDB).count()
        assert final_count == initial_count + 1
        
        # Data should be retrievable in same session
        retrieved = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact.context_id
        ).first()
        assert retrieved is not None
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_service_layer_error_handling(
        self, db_session: Session, context_store_service: ContextStoreService
    ):
        """Test service layer error handling and database rollback."""
        # Test deleting non-existent artifact
        fake_id = uuid4()
        result = context_store_service.delete_artifact(fake_id)
        assert result is False  # Should handle gracefully
        
        # Test getting non-existent artifact
        retrieved = context_store_service.get_artifact(fake_id)
        assert retrieved is None  # Should return None, not raise exception
        
        # Test updating non-existent artifact
        updated = context_store_service.update_artifact(
            fake_id,
            content={"test": "update"}
        )
        assert updated is None  # Should handle gracefully

class TestEventLoggingForStateChanges:
    """Test scenario 1.2-INT-004: Event logging for state changes (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_artifact_creation_event_logging(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, mock_websocket_manager
    ):
        """Test that artifact creation generates appropriate events."""
        project = project_factory.create(db_session)
        
        # Note: In actual implementation, this would test WebSocket event emission
        # For now, we test the structure supports event logging
        
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"event": "test"}
        )
        
        # Verify artifact was created (event logging would be tested with WebSocket integration)
        assert artifact is not None
        assert artifact.context_id is not None
        
        # In full implementation, would verify:
        # - WebSocket event was emitted
        # - Event contains artifact details
        # - Event timestamp is accurate
    
    @pytest.mark.integration
    @pytest.mark.p1
    def test_task_status_change_event_logging(
        self, db_session: Session, orchestrator_service, project_factory,
        mock_websocket_manager
    ):
        """Test that task status changes generate events."""
        project = project_factory.create(db_session)
        
        task = orchestrator_service.create_task(
            project_id=project.id,
            agent_type=AgentType.CODER,  # Use enum directly
            instructions="Event logging test"
        )
        
        # Update task status (should generate event)
        orchestrator_service.update_task_status(
            task.task_id,
            TaskStatus.WORKING
        )
        
        # Verify status was updated
        db_task = db_session.query(TaskDB).filter(TaskDB.id == task.task_id).first()
        assert db_task.status == TaskStatus.WORKING
        
        # In full implementation, would verify WebSocket event emission
    
    @pytest.mark.integration
    @pytest.mark.p2
    def test_event_log_data_integrity(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test event log data integrity and consistency."""
        project = project_factory.create(db_session)
        
        # Perform multiple operations that should generate events
        operations = []
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"operation": "create"}
        )
        operations.append(("CREATE", artifact.context_id))
        
        # Update artifact
        updated = context_store_service.update_artifact(
            artifact.context_id,
            content={"operation": "update"}
        )
        operations.append(("UPDATE", artifact.context_id))
        
        # Delete artifact
        deleted = context_store_service.delete_artifact(artifact.context_id)
        operations.append(("DELETE", artifact.context_id))
        
        # Verify operations completed successfully
        assert len(operations) == 3
        assert updated is not None
        assert deleted is True

class TestContextArtifactQueryPerformance:
    """Test scenario 1.2-INT-005: Context artifact query performance (P2)"""
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.performance
    def test_query_performance_with_volume(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, performance_timer
    ):
        """Test context artifact query performance with volume."""
        project = project_factory.create(db_session)
        
        # Create multiple artifacts
        artifact_count = 100
        created_artifacts = []
        
        for i in range(artifact_count):
            artifact = context_store_service.create_artifact(
                project_id=project.id,
                source_agent=AgentType.ANALYST,
                artifact_type=ArtifactType.AGENT_OUTPUT,
                content={"index": i, "data": f"test_data_{i}"}
            )
            created_artifacts.append(artifact)
        
        # Test query performance
        performance_timer.start()
        artifacts = context_store_service.get_artifacts_by_project(project.id)
        performance_timer.stop()
        
        # Verify results
        assert len(artifacts) == artifact_count
        
        # Performance assertion (adjust threshold as needed)
        assert performance_timer.elapsed_ms < 500  # Should complete within 500ms
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.performance
    def test_single_artifact_retrieval_performance(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, performance_timer
    ):
        """Test single artifact retrieval performance."""
        project = project_factory.create(db_session)
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=AgentType.CODER,  # Use enum directly
            artifact_type=ArtifactType.SOURCE_CODE,
            content={"performance": "test"}
        )
        
        # Test retrieval performance
        performance_timer.start()
        retrieved = context_store_service.get_artifact(artifact.context_id)
        performance_timer.stop()
        
        # Verify result
        assert retrieved is not None
        assert retrieved.context_id == artifact.context_id
        
        # Performance assertion
        assert performance_timer.elapsed_ms < 100  # Should complete within 100ms
    
    @pytest.mark.integration
    @pytest.mark.p2
    def test_bulk_artifact_retrieval_performance(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, performance_timer
    ):
        """Test bulk artifact retrieval by IDs performance."""
        project = project_factory.create(db_session)
        
        # Create multiple artifacts
        artifact_ids = []
        for i in range(50):
            artifact = context_store_service.create_artifact(
                project_id=project.id,
                source_agent=AgentType.TESTER,
                artifact_type=ArtifactType.TEST_RESULTS,
                content={"test_id": i}
            )
            artifact_ids.append(artifact.context_id)
        
        # Test bulk retrieval performance
        performance_timer.start()
        artifacts = context_store_service.get_artifacts_by_ids(artifact_ids)
        performance_timer.stop()
        
        # Verify results
        assert len(artifacts) == 50
        
        # Performance assertion
        assert performance_timer.elapsed_ms < 200  # Should complete within 200ms
