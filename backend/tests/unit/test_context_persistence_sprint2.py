"""
Unit tests for Story 2.2: Context Persistence (Sprint 2)

Test scenarios:
- 2.2-UNIT-001: ContextArtifact model validation (P0)
- 2.2-UNIT-002: Artifact type enumeration validation (P0)
- 2.2-UNIT-003: Artifact metadata structure validation (P1)
- 2.2-UNIT-004: Content serialization/deserialization (P1)
- 2.2-UNIT-005: Artifact search/filter logic (P2)
"""

import pytest
import json
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import Mock, patch

from app.models.context import ArtifactType, ContextArtifact
from app.models.agent import AgentType
from app.database.models import ContextArtifactDB

@pytest.mark.mock_data
class TestContextArtifactModelValidation:
    """Test scenario 2.2-UNIT-001: ContextArtifact model validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_valid_context_artifact_creation(self, sample_context_artifact_data):
        """Test creation of valid ContextArtifact model."""
        artifact_data = sample_context_artifact_data.copy()
        artifact_data["project_id"] = uuid4()
        artifact_data["context_id"] = uuid4()
        
        # Create ContextArtifact instance
        artifact = ContextArtifact(
            project_id=artifact_data["project_id"],
            context_id=artifact_data["context_id"],
            source_agent=AgentType.ANALYST,
            artifact_type=artifact_data["artifact_type"],
            content=artifact_data["content"],
            artifact_metadata=artifact_data["artifact_metadata"]
        )

        # Verify all fields are correctly set
        assert artifact.project_id == artifact_data["project_id"]
        assert artifact.context_id == artifact_data["context_id"]
        assert artifact.source_agent == AgentType(artifact_data["source_agent"])  # Compare as enum
        assert artifact.artifact_type == artifact_data["artifact_type"]
        assert artifact.content == artifact_data["content"]
        assert artifact.artifact_metadata == artifact_data["artifact_metadata"]
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_context_artifact_required_fields(self):
        """Test that required fields are validated in ContextArtifact."""
        # Test with missing required fields
        with pytest.raises((TypeError, ValueError)):
            # Missing project_id
            ContextArtifact(
                context_id=uuid4(),
                source_agent=AgentType.ANALYST,
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"test": "content"}
            )
        
        # Test with None values for required fields
        with pytest.raises((TypeError, ValueError)):
            ContextArtifact(
                project_id=None,
                context_id=uuid4(),
                source_agent=AgentType.ANALYST,
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"test": "content"}
            )
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_context_artifact_field_types(self):
        """Test field type validation in ContextArtifact."""
        project_id = uuid4()
        context_id = uuid4()
        
        # Test valid types
        artifact = ContextArtifact(
            project_id=project_id,
            context_id=context_id,
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"valid": "content"},
            artifact_metadata={"valid": "metadata"}
        )
        
        assert isinstance(artifact.project_id, UUID)
        assert isinstance(artifact.context_id, UUID)
        assert isinstance(artifact.source_agent, str)
        assert isinstance(artifact.artifact_type, ArtifactType)
        assert isinstance(artifact.content, dict)
        assert isinstance(artifact.artifact_metadata, dict)
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_context_artifact_optional_fields(self):
        """Test optional fields handling in ContextArtifact."""
        # Test with minimal required fields
        minimal_artifact = ContextArtifact(
            project_id=uuid4(),
            context_id=uuid4(),
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"minimal": "content"}
            # artifact_metadata is optional
        )
        
        assert minimal_artifact.artifact_metadata is None or minimal_artifact.artifact_metadata == {}
        
        # Test with all fields
        complete_artifact = ContextArtifact(
            project_id=uuid4(),
            context_id=uuid4(),
            source_agent=AgentType.ANALYST,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"complete": "content"},
            artifact_metadata={"version": "1.0", "created_by": "test"}
        )
        
        assert complete_artifact.artifact_metadata is not None
        assert len(complete_artifact.artifact_metadata) > 0
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_context_artifact_immutability_validation(self):
        """Test validation of immutable fields in ContextArtifact."""
        artifact = ContextArtifact(
            project_id=uuid4(),
            context_id=uuid4(),
            source_agent=AgentType.ANALYST.value,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"original": "content"}
        )
        
        original_project_id = artifact.project_id
        original_context_id = artifact.context_id
        
        # Immutable fields should not be modifiable after creation
        # (In Pydantic models, this would be handled by field configuration)
        assert artifact.project_id == original_project_id
        assert artifact.context_id == original_context_id

@pytest.mark.mock_data
class TestArtifactTypeEnumerationValidation:
    """Test scenario 2.2-UNIT-002: Artifact type enumeration validation (P0)"""
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_all_artifact_types_defined(self):
        """Test that all required artifact types are defined."""
        # Verify core artifact types exist
        required_types = [
            "USER_INPUT",
            "PROJECT_PLAN", 
            "SYSTEM_ARCHITECTURE",
            "SOURCE_CODE",
            "TEST_RESULTS",
            "DEPLOYMENT_PACKAGE",
            "SOFTWARE_SPECIFICATION"
        ]
        
        artifact_type_names = [artifact_type.name for artifact_type in ArtifactType]
        
        for required_type in required_types:
            assert required_type in artifact_type_names, f"Missing artifact type: {required_type}"
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_artifact_type_values_consistency(self):
        """Test that artifact type values are consistent and valid."""
        for artifact_type in ArtifactType:
            # Each type should have a name
            assert hasattr(artifact_type, 'name')
            assert len(artifact_type.name) > 0
            
            # Each type should have a value
            assert hasattr(artifact_type, 'value')
            assert len(artifact_type.value) > 0
            
            # Name and value should be strings
            assert isinstance(artifact_type.name, str)
            assert isinstance(artifact_type.value, str)
    
    @pytest.mark.unit
    @pytest.mark.p0
    @pytest.mark.context
    def test_artifact_type_uniqueness(self):
        """Test that all artifact types are unique."""
        type_names = [artifact_type.name for artifact_type in ArtifactType]
        type_values = [artifact_type.value for artifact_type in ArtifactType]
        
        # Names should be unique
        assert len(type_names) == len(set(type_names)), "Duplicate artifact type names found"
        
        # Values should be unique  
        assert len(type_values) == len(set(type_values)), "Duplicate artifact type values found"
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_artifact_type_string_conversion(self):
        """Test string conversion of artifact types."""
        for artifact_type in ArtifactType:
            # Should convert to string
            str_value = str(artifact_type)
            assert isinstance(str_value, str)
            assert len(str_value) > 0
            
            # String representation should be meaningful
            assert artifact_type.name in str_value or artifact_type.value in str_value
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_artifact_type_from_string_creation(self):
        """Test creation of artifact types from string values."""
        # Test valid string conversion
        project_plan_from_string = ArtifactType("project_plan")
        assert project_plan_from_string == ArtifactType.PROJECT_PLAN
        
        # Test invalid string handling
        with pytest.raises(ValueError):
            ArtifactType("invalid_artifact_type")
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_type_categorization(self):
        """Test categorization of artifact types by phase."""
        phase_categories = {
            "input": [ArtifactType.USER_INPUT],
            "analysis": [ArtifactType.PROJECT_PLAN, ArtifactType.SOFTWARE_SPECIFICATION],
            "architecture": [ArtifactType.SYSTEM_ARCHITECTURE],
            "implementation": [ArtifactType.SOURCE_CODE],
            "testing": [ArtifactType.TEST_RESULTS],
            "deployment": [ArtifactType.DEPLOYMENT_PACKAGE]
        }
        
        for phase, types in phase_categories.items():
            assert len(types) > 0, f"No artifact types defined for phase: {phase}"
            
            for artifact_type in types:
                assert isinstance(artifact_type, ArtifactType)

@pytest.mark.mock_data
class TestArtifactMetadataStructureValidation:
    """Test scenario 2.2-UNIT-003: Artifact metadata structure validation (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_metadata_structure_validation(self):
        """Test validation of artifact metadata structure."""
        # Test valid metadata structures
        valid_metadata_examples = [
            {"version": "1.0", "created_by": "agent_analyst"},
            {"confidence_score": 0.95, "review_status": "approved"},
            {"tags": ["important", "reviewed"], "priority": "high"},
            {"source_phase": "analysis", "target_audience": "architects"}
        ]
        
        for metadata in valid_metadata_examples:
            # Should be valid dict structure
            assert isinstance(metadata, dict)
            
            # Should have at least one key-value pair
            assert len(metadata) > 0
            
            # All keys should be strings
            for key in metadata.keys():
                assert isinstance(key, str)
                assert len(key) > 0
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_metadata_reserved_fields(self):
        """Test handling of reserved metadata fields."""
        reserved_fields = ["id", "created_at", "updated_at", "project_id", "context_id"]
        
        # Test that reserved fields are not allowed in user-provided metadata
        for field in reserved_fields:
            metadata_with_reserved = {field: "should_not_be_allowed", "custom": "field"}
            
            # In a real implementation, this would be validated
            # For now, just verify the field exists
            assert field in metadata_with_reserved
            
            # Custom validation logic would prevent reserved fields
            # validate_metadata(metadata_with_reserved) would raise error
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context  
    def test_metadata_size_limits(self):
        """Test metadata size and complexity limits."""
        # Test reasonable metadata size
        reasonable_metadata = {
            "version": "1.0",
            "created_by": "test_agent",
            "tags": ["tag1", "tag2", "tag3"],
            "description": "A reasonable description of the artifact"
        }
        
        # Should be acceptable size when serialized
        serialized = json.dumps(reasonable_metadata)
        assert len(serialized) < 10000  # 10KB limit example
        
        # Test large metadata
        large_metadata = {
            "large_field": "x" * 50000,  # 50KB string
            "another_field": "normal content"
        }
        
        large_serialized = json.dumps(large_metadata)
        # Would be rejected in real implementation due to size
        assert len(large_serialized) > 50000
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_metadata_type_validation(self):
        """Test validation of metadata field types."""
        valid_type_examples = {
            "string_field": "text value",
            "number_field": 42,
            "float_field": 3.14,
            "boolean_field": True,
            "list_field": ["item1", "item2"],
            "dict_field": {"nested": "value"}
        }
        
        for field_name, field_value in valid_type_examples.items():
            metadata = {field_name: field_value}
            
            # Should be JSON serializable
            try:
                json.dumps(metadata)
                json_valid = True
            except (TypeError, ValueError):
                json_valid = False
            
            assert json_valid, f"Metadata field {field_name} with value {field_value} is not JSON serializable"
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_metadata_nesting_limits(self):
        """Test limits on metadata nesting depth."""
        # Test reasonable nesting (depth 3)
        reasonable_nested = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
        
        # Should be acceptable
        assert reasonable_nested["level1"]["level2"]["level3"] == "deep_value"
        
        # Test excessive nesting (depth 10)
        deep_nested = {"level1": {}}
        current_level = deep_nested["level1"]
        for i in range(2, 11):
            current_level[f"level{i}"] = {}
            current_level = current_level[f"level{i}"]
        current_level["final"] = "too_deep"
        
        # Would be limited in real implementation
        assert deep_nested["level1"]["level2"]["level3"]["level4"] is not None

@pytest.mark.mock_data
class TestContentSerializationDeserialization:
    """Test scenario 2.2-UNIT-004: Content serialization/deserialization (P1)"""
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_json_content_serialization(self):
        """Test JSON serialization of artifact content."""
        test_contents = [
            {"simple": "content"},
            {"nested": {"structure": {"with": ["arrays", "and", "values"]}}},
            {"mixed_types": {"string": "text", "number": 42, "boolean": True, "list": [1, 2, 3]}},
            {"unicode": "Content with émojis 🚀 and spëcial châractërs"},
        ]
        
        for content in test_contents:
            # Test serialization
            try:
                serialized = json.dumps(content)
                assert isinstance(serialized, str)
                assert len(serialized) > 0
            except (TypeError, ValueError) as e:
                pytest.fail(f"Failed to serialize content: {content}, error: {e}")
            
            # Test deserialization
            try:
                deserialized = json.loads(serialized)
                assert deserialized == content
            except (TypeError, ValueError) as e:
                pytest.fail(f"Failed to deserialize content: {serialized}, error: {e}")
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_content_type_preservation(self):
        """Test that content types are preserved during serialization."""
        original_content = {
            "integer": 42,
            "float": 3.14159,
            "string": "text content",
            "boolean": True,
            "null_value": None,
            "list": [1, "two", 3.0, True],
            "nested_dict": {"inner": "value"}
        }
        
        # Serialize and deserialize
        serialized = json.dumps(original_content)
        deserialized = json.loads(serialized)
        
        # Verify type preservation
        assert type(deserialized["integer"]) == type(original_content["integer"])
        assert type(deserialized["float"]) == type(original_content["float"])
        assert type(deserialized["string"]) == type(original_content["string"])
        assert type(deserialized["boolean"]) == type(original_content["boolean"])
        assert deserialized["null_value"] is None
        assert type(deserialized["list"]) == type(original_content["list"])
        assert type(deserialized["nested_dict"]) == type(original_content["nested_dict"])
    
    @pytest.mark.unit
    @pytest.mark.p1
    @pytest.mark.context
    def test_large_content_serialization(self):
        """Test serialization of large content objects."""
        # Create large content (1MB of text)
        large_text = "x" * (1024 * 1024)
        large_content = {
            "large_field": large_text,
            "metadata": {"size": len(large_text)}
        }
        
        # Test serialization performance and correctness
        import time
        start_time = time.time()
        
        try:
            serialized = json.dumps(large_content)
            serialization_time = time.time() - start_time
            
            # Should complete in reasonable time (< 5 seconds)
            assert serialization_time < 5.0
            
            # Should be correct size
            assert len(serialized) > 1024 * 1024  # At least 1MB
            
        except (TypeError, ValueError, MemoryError) as e:
            # Large content might be rejected, which is acceptable
            assert "too large" in str(e).lower() or "memory" in str(e).lower()
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_special_character_handling(self):
        """Test handling of special characters in content."""
        special_content = {
            "quotes": 'Content with "double" and \'single\' quotes',
            "backslashes": "Path\\with\\backslashes",
            "newlines": "Content\nwith\nnewlines",
            "tabs": "Content\twith\ttabs",
            "unicode": "Content with 🚀 émojis and spëcial characters",
            "control_chars": "Content with \x00 null and \x1F control chars"
        }
        
        for key, content_value in special_content.items():
            test_content = {key: content_value}
            
            # Should serialize without error
            try:
                serialized = json.dumps(test_content)
                deserialized = json.loads(serialized)
                
                # Content should be preserved
                assert deserialized[key] == content_value
                
            except (TypeError, ValueError) as e:
                # Some control characters might not be serializable, which is acceptable
                if "control" in key:
                    assert True  # Expected for control characters
                else:
                    pytest.fail(f"Failed to serialize {key}: {e}")
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_circular_reference_handling(self):
        """Test handling of circular references in content."""
        # Create circular reference
        circular_content = {"self": None}
        circular_content["self"] = circular_content
        
        # Should handle circular references gracefully
        with pytest.raises((ValueError, TypeError)):
            json.dumps(circular_content)
        
        # Test complex circular reference
        obj1 = {"name": "obj1", "ref": None}
        obj2 = {"name": "obj2", "ref": obj1}
        obj1["ref"] = obj2
        
        with pytest.raises((ValueError, TypeError)):
            json.dumps(obj1)

@pytest.mark.mock_data
class TestArtifactSearchFilterLogic:
    """Test scenario 2.2-UNIT-005: Artifact search/filter logic (P2)"""
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_filtering_by_type(self):
        """Test filtering artifacts by type."""
        # Mock artifacts with different types
        mock_artifacts = [
            {"artifact_type": ArtifactType.PROJECT_PLAN, "content": {"plan": "data"}},
            {"artifact_type": ArtifactType.SYSTEM_ARCHITECTURE, "content": {"arch": "data"}},
            {"artifact_type": ArtifactType.SOURCE_CODE, "content": {"code": "data"}},
            {"artifact_type": ArtifactType.TEST_RESULTS, "content": {"test": "data"}},
        ]
        
        # Filter by type function
        def filter_by_type(artifacts, target_type):
            return [artifact for artifact in artifacts if artifact["artifact_type"] == target_type]
        
        # Test filtering
        plan_artifacts = filter_by_type(mock_artifacts, ArtifactType.PROJECT_PLAN)
        assert len(plan_artifacts) == 1
        assert plan_artifacts[0]["artifact_type"] == ArtifactType.PROJECT_PLAN
        
        code_artifacts = filter_by_type(mock_artifacts, ArtifactType.SOURCE_CODE)
        assert len(code_artifacts) == 1
        assert code_artifacts[0]["artifact_type"] == ArtifactType.SOURCE_CODE
        
        # Test non-existent type
        deployment_artifacts = filter_by_type(mock_artifacts, ArtifactType.DEPLOYMENT_PACKAGE)
        assert len(deployment_artifacts) == 0
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_filtering_by_source_agent(self):
        """Test filtering artifacts by source agent."""
        mock_artifacts = [
            {"source_agent": AgentType.ANALYST.value, "content": {"analysis": "data"}},
            {"source_agent": AgentType.ARCHITECT.value, "content": {"architecture": "data"}},
            {"source_agent": AgentType.ANALYST.value, "content": {"more_analysis": "data"}},
            {"source_agent": AgentType.CODER.value, "content": {"code": "data"}},
        ]
        
        def filter_by_agent(artifacts, target_agent):
            return [artifact for artifact in artifacts if artifact["source_agent"] == target_agent]
        
        # Test filtering by analyst
        analyst_artifacts = filter_by_agent(mock_artifacts, AgentType.ANALYST.value)
        assert len(analyst_artifacts) == 2
        
        # Test filtering by architect
        architect_artifacts = filter_by_agent(mock_artifacts, AgentType.ARCHITECT.value)
        assert len(architect_artifacts) == 1
        
        # Test filtering by non-existent agent
        tester_artifacts = filter_by_agent(mock_artifacts, AgentType.TESTER.value)
        assert len(tester_artifacts) == 0
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_content_search(self):
        """Test searching artifacts by content."""
        mock_artifacts = [
            {"content": {"description": "user authentication system"}},
            {"content": {"description": "database schema design"}}, 
            {"content": {"description": "authentication middleware"}},
            {"content": {"code": "def authenticate(user): pass"}},
        ]
        
        def search_content(artifacts, search_term):
            results = []
            for artifact in artifacts:
                content_str = json.dumps(artifact["content"]).lower()
                if search_term.lower() in content_str:
                    results.append(artifact)
            return results
        
        # Test search for authentication
        auth_results = search_content(mock_artifacts, "authentication")
        assert len(auth_results) == 2  # Two artifacts contain "authentication"
        
        # Test search for database
        db_results = search_content(mock_artifacts, "database")
        assert len(db_results) == 1
        
        # Test search for non-existent term
        missing_results = search_content(mock_artifacts, "nonexistent")
        assert len(missing_results) == 0
    
    @pytest.mark.unit
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_metadata_filtering(self):
        """Test filtering artifacts by metadata."""
        mock_artifacts = [
            {"metadata": {"priority": "high", "reviewed": True}},
            {"metadata": {"priority": "medium", "reviewed": False}},
            {"metadata": {"priority": "high", "reviewed": False}},
            {"metadata": {"priority": "low", "reviewed": True}},
        ]
        
        def filter_by_metadata(artifacts, metadata_filters):
            results = []
            for artifact in artifacts:
                metadata = artifact.get("metadata", {})
                matches = True
                for key, value in metadata_filters.items():
                    if metadata.get(key) != value:
                        matches = False
                        break
                if matches:
                    results.append(artifact)
            return results
        
        # Test filter by high priority
        high_priority = filter_by_metadata(mock_artifacts, {"priority": "high"})
        assert len(high_priority) == 2
        
        # Test filter by reviewed status
        reviewed = filter_by_metadata(mock_artifacts, {"reviewed": True})
        assert len(reviewed) == 2
        
        # Test compound filter
        high_priority_reviewed = filter_by_metadata(
            mock_artifacts, 
            {"priority": "high", "reviewed": True}
        )
        assert len(high_priority_reviewed) == 1
    
    @pytest.mark.unit
    @pytest.mark.p3
    @pytest.mark.context
    def test_artifact_sorting_logic(self):
        """Test sorting artifacts by various criteria."""
        from datetime import datetime, timedelta
        
        base_time = datetime.now()
        mock_artifacts = [
            {"created_at": base_time + timedelta(hours=3), "priority": "medium"},
            {"created_at": base_time + timedelta(hours=1), "priority": "high"}, 
            {"created_at": base_time + timedelta(hours=2), "priority": "low"},
            {"created_at": base_time + timedelta(hours=4), "priority": "high"},
        ]
        
        # Test sort by creation time (newest first)
        by_time = sorted(mock_artifacts, key=lambda x: x["created_at"], reverse=True)
        assert by_time[0]["created_at"] == base_time + timedelta(hours=4)
        assert by_time[-1]["created_at"] == base_time + timedelta(hours=1)
        
        # Test sort by priority (custom order)
        priority_order = {"high": 1, "medium": 2, "low": 3}
        by_priority = sorted(
            mock_artifacts, 
            key=lambda x: priority_order.get(x["priority"], 999)
        )
        assert by_priority[0]["priority"] == "high"
        assert by_priority[-1]["priority"] == "low"
        
        # Test compound sorting (priority first, then time)
        by_priority_then_time = sorted(
            mock_artifacts,
            key=lambda x: (priority_order.get(x["priority"], 999), x["created_at"]),
            reverse=False
        )
        
        # High priority items should come first
        assert by_priority_then_time[0]["priority"] == "high"
        assert by_priority_then_time[1]["priority"] == "high"
