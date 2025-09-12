"""
Unit tests for Story 1.2: Context & Task State Persistence

Test scenarios:
- 1.2-UNIT-001: ContextArtifact model validation (P0)
- 1.2-UNIT-002: ArtifactType enumeration validation (P0) 
- 1.2-UNIT-003: Event log model validation (P1)
- 1.2-UNIT-004: Service layer interface compliance (P1)
- 1.2-UNIT-005: Context metadata serialization (P2)
"""

import pytest
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import ValidationError

from app.models.context import ContextArtifact, ArtifactType
from app.database.models import ContextArtifactDB
from app.models.agent import AgentType
from app.services.context_store import ContextStoreService


class TestContextArtifactModelValidation:
    """Test scenario 1.2-UNIT-001: ContextArtifact model validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_valid_context_artifact_creation(self):
        """Test creating a valid ContextArtifact model."""
        artifact_data = {
            "context_id": uuid4(),
            "project_id": uuid4(),
            "source_agent": AgentType.ANALYST.value,
            "artifact_type": ArtifactType.PROJECT_PLAN,
            "content": {
                "plan_title": "Test Plan",
                "objectives": ["Objective 1", "Objective 2"],
                "timeline": "2 weeks"
            },
            "artifact_metadata": {
                "version": "1.0",
                "confidence": 0.95
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        artifact = ContextArtifact(**artifact_data)
        
        assert isinstance(artifact.context_id, UUID)
        assert isinstance(artifact.project_id, UUID)
        assert artifact.source_agent == AgentType.ANALYST.value
        assert artifact.artifact_type == ArtifactType.PROJECT_PLAN
        assert artifact.content["plan_title"] == "Test Plan"
        assert len(artifact.content["objectives"]) == 2
        assert artifact.artifact_metadata["confidence"] == 0.95
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_context_artifact_minimal_fields(self):
        """Test ContextArtifact with minimal required fields."""
        minimal_artifact = ContextArtifact(
            project_id=uuid4(),
            source_agent=AgentType.ARCHITECT.value,
            artifact_type=ArtifactType.IMPLEMENTATION_PLAN,
            content={"basic": "content"}
        )
        
        assert isinstance(minimal_artifact.context_id, UUID)  # Auto-generated
        assert minimal_artifact.artifact_metadata is None  # Optional
        assert minimal_artifact.content == {"basic": "content"}
        assert isinstance(minimal_artifact.created_at, datetime)
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_context_artifact_database_model(self):
        """Test ContextArtifactDB SQLAlchemy model."""
        db_artifact_data = {
            "id": uuid4(),
            "project_id": uuid4(),
            "source_agent": AgentType.CODER.value,
            "artifact_type": ArtifactType.SOURCE_CODE,
            "content": {
                "files": ["main.py", "utils.py"],
                "language": "python"
            },
            "artifact_metadata": {
                "lines_of_code": 150,
                "test_coverage": 0.85
            }
        }
        
        db_artifact = ContextArtifactDB(**db_artifact_data)
        
        assert db_artifact.source_agent == AgentType.CODER.value
        assert db_artifact.artifact_type == ArtifactType.SOURCE_CODE
        assert db_artifact.content["language"] == "python"
        assert db_artifact.artifact_metadata["test_coverage"] == 0.85
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_context_artifact_content_validation(self):
        """Test ContextArtifact content field validation."""
        # Test with various content types
        content_types = [
            {"string": "value"},
            {"number": 42},
            {"boolean": True},
            {"list": [1, 2, 3]},
            {"nested": {"deep": {"value": "nested content"}}},
            {"mixed": {"str": "text", "num": 123, "list": ["a", "b"]}}
        ]
        
        for content in content_types:
            artifact = ContextArtifact(
                project_id=uuid4(),
                source_agent=AgentType.ANALYST.value,
                artifact_type=ArtifactType.USER_INPUT,
                content=content
            )
            assert artifact.content == content
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_context_artifact_invalid_fields(self):
        """Test ContextArtifact validation with invalid fields."""
        # Test invalid agent type
        with pytest.raises(ValidationError):
            ContextArtifact(
                project_id=uuid4(),
                source_agent="invalid_agent",
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"test": "content"}
            )
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            ContextArtifact(
                project_id=uuid4(),
                # Missing source_agent
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"test": "content"}
            )


class TestArtifactTypeEnumValidation:
    """Test scenario 1.2-UNIT-002: ArtifactType enumeration validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_artifact_type_enum_values(self):
        """Test all ArtifactType enumeration values."""
        expected_types = [
            "project_plan",
            "software_specification", 
            "implementation_plan",
            "source_code",
            "test_results",
            "deployment_log",
            "user_input",
            "agent_output",
            "hitl_response"
        ]
        
        actual_types = [artifact_type.value for artifact_type in ArtifactType]
        
        assert len(actual_types) >= len(expected_types)
        for expected in expected_types:
            assert expected in actual_types
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_artifact_type_usage_in_context(self):
        """Test ArtifactType enum usage in ContextArtifact."""
        for artifact_type in ArtifactType:
            artifact = ContextArtifact(
                project_id=uuid4(),
                source_agent=AgentType.ANALYST.value,
                artifact_type=artifact_type,
                content={"type_test": artifact_type.value}
            )
            assert artifact.artifact_type == artifact_type
    
    @pytest.mark.unit
    @pytest.mark.p0
    def test_artifact_type_string_values(self):
        """Test ArtifactType enum string values."""
        assert ArtifactType.PROJECT_PLAN.value == "project_plan"
        assert ArtifactType.SOFTWARE_SPECIFICATION.value == "software_specification"
        assert ArtifactType.IMPLEMENTATION_PLAN.value == "implementation_plan"
        assert ArtifactType.SOURCE_CODE.value == "source_code"
        assert ArtifactType.TEST_RESULTS.value == "test_results"
        assert ArtifactType.DEPLOYMENT_LOG.value == "deployment_log"
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_artifact_type_comparison(self):
        """Test ArtifactType enum comparison operations."""
        assert ArtifactType.PROJECT_PLAN == ArtifactType.PROJECT_PLAN
        assert ArtifactType.PROJECT_PLAN != ArtifactType.SOURCE_CODE
        
        # String comparison
        assert ArtifactType.PROJECT_PLAN.value == "project_plan"
        assert ArtifactType.SOURCE_CODE.value == "source_code"
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_artifact_type_categorization(self):
        """Test logical categorization of artifact types."""
        planning_types = [ArtifactType.PROJECT_PLAN, ArtifactType.SOFTWARE_SPECIFICATION]
        implementation_types = [ArtifactType.IMPLEMENTATION_PLAN, ArtifactType.SOURCE_CODE]
        validation_types = [ArtifactType.TEST_RESULTS, ArtifactType.DEPLOYMENT_LOG]
        interaction_types = [ArtifactType.USER_INPUT, ArtifactType.HITL_RESPONSE]
        
        all_categorized = planning_types + implementation_types + validation_types + interaction_types
        
        # Verify all main types are categorized
        for artifact_type in [ArtifactType.PROJECT_PLAN, ArtifactType.SOURCE_CODE, 
                             ArtifactType.TEST_RESULTS, ArtifactType.USER_INPUT]:
            assert artifact_type in all_categorized


class TestEventLogModelValidation:
    """Test scenario 1.2-UNIT-003: Event log model validation (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_event_log_structure_validation(self):
        """Test event log data structure validation."""
        # Note: Based on current codebase, event logging is handled by WebSocket events
        # Testing the WebSocketEvent structure as the event log mechanism
        from app.websocket.events import WebSocketEvent, EventType
        
        event = WebSocketEvent(
            event_type=EventType.ARTIFACT_CREATED,
            project_id=uuid4(),
            data={
                "artifact_id": str(uuid4()),
                "artifact_type": ArtifactType.PROJECT_PLAN.value,
                "source_agent": AgentType.ANALYST.value
            }
        )
        
        assert event.event_type == EventType.ARTIFACT_CREATED
        assert isinstance(event.project_id, UUID)
        assert "artifact_id" in event.data
        assert isinstance(event.timestamp, datetime)
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_event_log_timestamp_handling(self):
        """Test event log timestamp generation and validation."""
        from app.websocket.events import WebSocketEvent, EventType
        
        before_creation = datetime.utcnow()
        
        event = WebSocketEvent(
            event_type=EventType.TASK_COMPLETED,
            data={"test": "timestamp"}
        )
        
        after_creation = datetime.utcnow()
        
        # Timestamp should be between before and after
        assert before_creation <= event.timestamp <= after_creation
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_event_log_serialization(self):
        """Test event log JSON serialization."""
        from app.websocket.events import WebSocketEvent, EventType
        
        event = WebSocketEvent(
            event_type=EventType.WORKFLOW_EVENT,
            project_id=uuid4(),
            task_id=uuid4(),
            data={"message": "Test workflow event"}
        )
        
        # Test model can be serialized to dict
        event_dict = event.model_dump()
        
        assert "event_type" in event_dict
        assert "project_id" in event_dict
        assert "task_id" in event_dict
        assert "timestamp" in event_dict
        assert "data" in event_dict
        
        # UUIDs should be serialized as strings
        assert isinstance(event_dict["project_id"], str)
        assert isinstance(event_dict["task_id"], str)


class TestServiceLayerInterfaceCompliance:
    """Test scenario 1.2-UNIT-004: Service layer interface compliance (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_context_store_service_interface(self):
        """Test ContextStoreService interface compliance with DIP."""
        from unittest.mock import Mock
        from sqlalchemy.orm import Session
        
        # Mock database session
        mock_session = Mock(spec=Session)
        
        # ContextStoreService should accept any Session implementation
        service = ContextStoreService(mock_session)
        
        assert service.db == mock_session
        assert hasattr(service, 'create_artifact')
        assert hasattr(service, 'get_artifact')
        assert hasattr(service, 'get_artifacts_by_project')
        assert hasattr(service, 'get_artifacts_by_ids')
        assert hasattr(service, 'update_artifact')
        assert hasattr(service, 'delete_artifact')
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_service_layer_method_signatures(self):
        """Test service layer method signatures for consistency."""
        from unittest.mock import Mock
        
        mock_session = Mock()
        service = ContextStoreService(mock_session)
        
        # Test create_artifact signature
        import inspect
        create_sig = inspect.signature(service.create_artifact)
        expected_params = ['project_id', 'source_agent', 'artifact_type', 'content', 'artifact_metadata']
        actual_params = list(create_sig.parameters.keys())
        
        for param in expected_params:
            assert param in actual_params
    
    @pytest.mark.unit
    @pytest.mark.p1
    def test_service_layer_dependency_injection(self):
        """Test service layer follows dependency injection principles."""
        # Service should not create its own dependencies
        # It should accept them via constructor or method parameters
        
        from unittest.mock import Mock
        
        mock_session1 = Mock()
        mock_session2 = Mock()
        
        service1 = ContextStoreService(mock_session1)
        service2 = ContextStoreService(mock_session2)
        
        # Different instances should use different sessions
        assert service1.db is mock_session1
        assert service2.db is mock_session2
        assert service1.db is not service2.db
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_service_layer_abstraction(self):
        """Test service layer provides proper abstraction."""
        from unittest.mock import Mock
        
        # Service should hide database implementation details
        mock_session = Mock()
        service = ContextStoreService(mock_session)
        
        # Methods should return domain models, not database models
        # This would be tested more thoroughly in integration tests
        # Here we just verify the service structure supports this
        
        # Verify service has methods that return domain objects
        assert hasattr(service, 'create_artifact')  # Should return ContextArtifact
        assert hasattr(service, 'get_artifact')     # Should return ContextArtifact


class TestContextMetadataSerialization:
    """Test scenario 1.2-UNIT-005: Context metadata serialization (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_metadata_json_serialization(self):
        """Test context artifact metadata JSON serialization."""
        complex_metadata = {
            "version": "1.2.3",
            "tags": ["important", "reviewed"],
            "metrics": {
                "confidence": 0.95,
                "quality_score": 8.5
            },
            "timestamps": {
                "created": "2023-12-01T10:00:00Z",
                "reviewed": "2023-12-01T14:30:00Z"
            },
            "contributors": [
                {"agent": "analyst", "role": "creator"},
                {"agent": "architect", "role": "reviewer"}
            ]
        }
        
        artifact = ContextArtifact(
            project_id=uuid4(),
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"plan": "test"},
            artifact_metadata=complex_metadata
        )
        
        # Test serialization to dict
        artifact_dict = artifact.model_dump()
        assert artifact_dict["artifact_metadata"] == complex_metadata
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_metadata_edge_cases(self):
        """Test metadata serialization edge cases."""
        edge_case_metadata = [
            None,  # No metadata
            {},    # Empty metadata
            {"single": "value"},  # Single value
            {"nested": {"deep": {"value": True}}},  # Deep nesting
            {"unicode": "测试数据"},  # Unicode content
            {"numbers": [1, 2.5, -3]},  # Various number types
            {"mixed": {"str": "text", "num": 42, "bool": False, "null": None}}
        ]
        
        for metadata in edge_case_metadata:
            artifact = ContextArtifact(
                project_id=uuid4(),
                source_agent=AgentType.CODER.value,
                artifact_type=ArtifactType.SOURCE_CODE,
                content={"test": "content"},
                artifact_metadata=metadata
            )
            
            # Should serialize without errors
            artifact_dict = artifact.model_dump()
            assert artifact_dict["artifact_metadata"] == metadata
    
    @pytest.mark.unit
    @pytest.mark.p2
    def test_content_serialization_types(self):
        """Test various content types serialization."""
        content_examples = [
            {"text": "Simple text content"},
            {"code": {"language": "python", "content": "print('hello')"}},
            {"plan": {"phases": ["analysis", "design", "implementation"]}},
            {"results": {"passed": 15, "failed": 2, "coverage": 0.85}},
            {"log": {"level": "info", "messages": ["started", "completed"]}},
            {"binary_ref": {"type": "file", "path": "/uploads/document.pdf"}}
        ]
        
        for content in content_examples:
            artifact = ContextArtifact(
                project_id=uuid4(),
                source_agent=AgentType.TESTER.value,
                artifact_type=ArtifactType.TEST_RESULTS,
                content=content
            )
            
            artifact_dict = artifact.model_dump()
            assert artifact_dict["content"] == content
    
    @pytest.mark.unit
    @pytest.mark.p3
    def test_datetime_serialization_in_metadata(self):
        """Test datetime serialization in metadata fields."""
        now = datetime.utcnow()
        
        artifact = ContextArtifact(
            project_id=uuid4(),
            source_agent=AgentType.DEPLOYER.value,
            artifact_type=ArtifactType.DEPLOYMENT_LOG,
            content={"deployment": "successful"},
            artifact_metadata={
                "deployed_at": now,
                "duration_seconds": 45.2
            }
        )
        
        # The artifact should handle datetime serialization
        artifact_dict = artifact.model_dump(mode="json")
        
        # Datetime should be serialized as ISO string
        assert isinstance(artifact_dict["artifact_metadata"]["deployed_at"], str)
        assert "T" in artifact_dict["artifact_metadata"]["deployed_at"]  # ISO format
        assert artifact_dict["artifact_metadata"]["duration_seconds"] == 45.2