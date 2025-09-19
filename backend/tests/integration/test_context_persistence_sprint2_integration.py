"""
Integration tests for Story 2.2: Context Persistence (Sprint 2)

Test scenarios:
- 2.2-INT-001: Context artifact CRUD operations (P0)
- 2.2-INT-002: Agent context retrieval by IDs (P0) 
- 2.2-INT-003: Project-scoped artifact queries (P1)
- 2.2-INT-004: Artifact relationship maintenance (P1)
- 2.2-INT-005: Context store performance with volume (P2)
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.database.models import ContextArtifactDB, ProjectDB
from app.models.context import ArtifactType
from app.models.agent import AgentType
from app.services.context_store import ContextStoreService
from tests.conftest import assert_performance_threshold

class TestContextArtifactCRUDOperations:
    """Test scenario 2.2-INT-001: Context artifact CRUD operations (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_create_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService, 
        project_factory, sample_context_artifact_data
    ):
        """Test creation of context artifacts through service."""
        project = project_factory.create(db_session)
        artifact_data = sample_context_artifact_data
        
        # Create artifact
        artifact = context_store_service.create_artifact(
            project_id=project.id,
            source_agent=artifact_data["source_agent"],
            artifact_type=artifact_data["artifact_type"],
            content=artifact_data["content"],
            artifact_metadata=artifact_data.get("artifact_metadata")
        )
        
        # Verify artifact created
        assert artifact is not None
        assert artifact.project_id == project.id
        assert artifact.source_agent == artifact_data["source_agent"]
        assert artifact.artifact_type == artifact_data["artifact_type"]
        assert artifact.content == artifact_data["content"]
        
        # Verify database persistence
        db_artifact = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact.context_id
        ).first()
        assert db_artifact is not None
        assert db_artifact.project_id == project.id
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_read_context_artifact_by_id(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test reading context artifacts by ID."""
        project = project_factory.create(db_session)
        
        # Create artifact using factory
        db_artifact = context_artifact_factory.create(
            db_session, 
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"plan": "Test project plan"}
        )
        
        # Read artifact through service
        retrieved_artifact = context_store_service.get_artifact_by_id(db_artifact.id)
        
        # Verify retrieval
        assert retrieved_artifact is not None
        assert retrieved_artifact.context_id == db_artifact.id
        assert retrieved_artifact.project_id == project.id
        assert retrieved_artifact.artifact_type == ArtifactType.PROJECT_PLAN
        assert retrieved_artifact.content["plan"] == "Test project plan"
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_update_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test updating context artifacts."""
        project = project_factory.create(db_session)
        
        # Create initial artifact
        db_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            content={"version": "1.0", "status": "draft"}
        )
        
        # Update artifact
        updated_content = {"version": "2.0", "status": "reviewed", "changes": ["added section 3"]}
        updated_metadata = {"reviewed_by": "senior_analyst", "review_date": "2024-01-15"}
        
        updated_artifact = context_store_service.update_artifact(
            artifact_id=db_artifact.id,
            content=updated_content,
            artifact_metadata=updated_metadata
        )
        
        # Verify update
        assert updated_artifact.content["version"] == "2.0"
        assert updated_artifact.content["status"] == "reviewed"
        assert updated_artifact.artifact_metadata["reviewed_by"] == "senior_analyst"
        
        # Verify database persistence
        db_session.refresh(db_artifact)
        assert db_artifact.content["version"] == "2.0"
        assert db_artifact.artifact_metadata["reviewed_by"] == "senior_analyst"
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_delete_context_artifact(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test deletion of context artifacts."""
        project = project_factory.create(db_session)
        
        # Create artifact
        db_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            content={"to_be_deleted": True}
        )
        artifact_id = db_artifact.id
        
        # Delete artifact
        deletion_result = context_store_service.delete_artifact(artifact_id)
        assert deletion_result is True
        
        # Verify deletion
        deleted_artifact = context_store_service.get_artifact_by_id(artifact_id)
        assert deleted_artifact is None
        
        # Verify database deletion
        db_artifact = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.id == artifact_id
        ).first()
        assert db_artifact is None
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_crud_transaction_integrity(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory
    ):
        """Test transaction integrity during CRUD operations."""
        project = project_factory.create(db_session)
        initial_count = db_session.query(ContextArtifactDB).count()
        
        # Create multiple artifacts in sequence
        artifacts = []
        for i in range(3):
            artifact = context_store_service.create_artifact(
                project_id=project.id,
                source_agent=AgentType.ANALYST,  # Use enum directly
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"sequence": i, "batch": "transaction_test"}
            )
            artifacts.append(artifact)
        
        # Verify all created
        final_count = db_session.query(ContextArtifactDB).count()
        assert final_count == initial_count + 3
        
        # Update one, delete one, keep one
        context_store_service.update_artifact(
            artifacts[0].context_id,
            content={"sequence": 0, "status": "updated"}
        )
        
        context_store_service.delete_artifact(artifacts[1].context_id)
        
        # Verify final state
        remaining_count = db_session.query(ContextArtifactDB).count()
        assert remaining_count == initial_count + 2
        
        # Verify updated artifact
        updated = context_store_service.get_artifact_by_id(artifacts[0].context_id)
        assert updated.content["status"] == "updated"

class TestAgentContextRetrievalByIDs:
    """Test scenario 2.2-INT-002: Agent context retrieval by IDs (P0)"""
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_retrieve_multiple_artifacts_by_ids(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test retrieving multiple context artifacts by their IDs."""
        project = project_factory.create(db_session)
        
        # Create multiple artifacts
        artifacts = []
        for i, artifact_type in enumerate([
            ArtifactType.PROJECT_PLAN,
            ArtifactType.SYSTEM_ARCHITECTURE, 
            ArtifactType.SOURCE_CODE
        ]):
            artifact = context_artifact_factory.create(
                db_session,
                project_id=project.id,
                artifact_type=artifact_type,
                content={"phase": f"phase_{i+1}", "data": f"test_data_{i+1}"}
            )
            artifacts.append(artifact)
        
        # Retrieve by IDs
        artifact_ids = [artifact.id for artifact in artifacts]
        retrieved_artifacts = context_store_service.get_artifacts_by_ids(artifact_ids)
        
        # Verify retrieval
        assert len(retrieved_artifacts) == 3
        
        # Verify all artifacts retrieved correctly
        retrieved_ids = [artifact.context_id for artifact in retrieved_artifacts]
        for original_id in artifact_ids:
            assert original_id in retrieved_ids
        
        # Verify content preserved
        for retrieved in retrieved_artifacts:
            assert "phase" in retrieved.content
            assert "data" in retrieved.content
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_retrieve_artifacts_with_missing_ids(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test retrieving artifacts when some IDs don't exist."""
        project = project_factory.create(db_session)
        
        # Create one real artifact
        real_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            content={"real": "artifact"}
        )
        
        # Mix real and fake IDs
        mixed_ids = [
            real_artifact.id,
            uuid4(),  # Non-existent ID
            uuid4(),  # Another non-existent ID
        ]
        
        # Retrieve artifacts
        retrieved_artifacts = context_store_service.get_artifacts_by_ids(mixed_ids)
        
        # Should only return existing artifacts
        assert len(retrieved_artifacts) == 1
        assert retrieved_artifacts[0].context_id == real_artifact.id
        assert retrieved_artifacts[0].content["real"] == "artifact"
    
    @pytest.mark.integration
    @pytest.mark.p0
    @pytest.mark.context
    def test_retrieve_artifacts_empty_id_list(
        self, context_store_service: ContextStoreService
    ):
        """Test retrieving artifacts with empty ID list."""
        # Test empty list
        retrieved_artifacts = context_store_service.get_artifacts_by_ids([])
        assert retrieved_artifacts == []
        
        # Test None input
        retrieved_artifacts = context_store_service.get_artifacts_by_ids(None)
        assert retrieved_artifacts == []
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_retrieve_artifacts_cross_project_isolation(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test that artifact retrieval respects project isolation."""
        # Create two projects
        project1 = project_factory.create(db_session, name="Project 1")
        project2 = project_factory.create(db_session, name="Project 2")
        
        # Create artifacts in different projects
        artifact1 = context_artifact_factory.create(
            db_session,
            project_id=project1.id,
            content={"project": "1", "secret": "project1_data"}
        )
        
        artifact2 = context_artifact_factory.create(
            db_session,
            project_id=project2.id,
            content={"project": "2", "secret": "project2_data"}
        )
        
        # Try to retrieve artifacts from different projects
        all_ids = [artifact1.id, artifact2.id]
        retrieved_artifacts = context_store_service.get_artifacts_by_ids(all_ids)
        
        # Should retrieve both (no project filtering at this level)
        assert len(retrieved_artifacts) == 2
        
        # But when filtering by project, should be isolated
        project1_artifacts = context_store_service.get_artifacts_by_project(project1.id)
        project1_ids = [artifact.context_id for artifact in project1_artifacts]
        assert artifact1.id in project1_ids
        assert artifact2.id not in project1_ids
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    def test_retrieve_artifacts_performance_with_large_id_list(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, load_test_data, performance_timer
    ):
        """Test performance of retrieving large number of artifacts by IDs."""
        project = project_factory.create(db_session)
        
        # Create many artifacts
        artifact_count = 100
        artifacts = []
        
        performance_timer.start()
        
        # Create test artifacts
        for i in range(artifact_count):
            artifact_data = {
                "project_id": project.id,
                "source_agent": AgentType.ANALYST,  # Use enum directly
                "artifact_type": ArtifactType.PROJECT_PLAN,
                "content": {"index": i, "data": f"large_dataset_{i}"},
                "artifact_metadata": {"batch": "performance_test", "index": i}
            }

            artifact = context_store_service.create_artifact(**artifact_data)
            artifacts.append(artifact)
        
        creation_time = performance_timer.elapsed_ms
        performance_timer.start()
        
        # Retrieve all artifacts by ID
        artifact_ids = [artifact.context_id for artifact in artifacts]
        retrieved_artifacts = context_store_service.get_artifacts_by_ids(artifact_ids)
        
        performance_timer.stop()
        retrieval_time = performance_timer.elapsed_ms
        
        # Verify all retrieved
        assert len(retrieved_artifacts) == artifact_count
        
        # Verify performance thresholds
        assert_performance_threshold(retrieval_time, 2000, f"Retrieve {artifact_count} artifacts by IDs")
        
        # Verify data integrity
        retrieved_indices = [artifact.content["index"] for artifact in retrieved_artifacts]
        expected_indices = list(range(artifact_count))
        assert sorted(retrieved_indices) == sorted(expected_indices)

class TestProjectScopedArtifactQueries:
    """Test scenario 2.2-INT-003: Project-scoped artifact queries (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_get_all_artifacts_by_project(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test retrieving all artifacts for a specific project."""
        project = project_factory.create(db_session)
        
        # Create artifacts of different types
        artifact_types = [
            ArtifactType.USER_INPUT,
            ArtifactType.PROJECT_PLAN,
            ArtifactType.SYSTEM_ARCHITECTURE,
            ArtifactType.SOURCE_CODE
        ]

        created_artifacts = []
        for i, artifact_type in enumerate(artifact_types):
            artifact = context_artifact_factory.create(
                db_session,
                project_id=project.id,
                artifact_type=artifact_type,
                source_agent=AgentType.ANALYST if i % 2 == 0 else AgentType.ARCHITECT,  # Use enum directly
                content={"type": artifact_type.value, "index": i}
            )
            created_artifacts.append(artifact)
        
        # Retrieve all project artifacts
        project_artifacts = context_store_service.get_artifacts_by_project(project.id)
        
        # Verify all artifacts retrieved
        assert len(project_artifacts) == len(artifact_types)
        
        # Verify artifact types are correct
        retrieved_types = [artifact.artifact_type for artifact in project_artifacts]
        for artifact_type in artifact_types:
            assert artifact_type in retrieved_types
        
        # Verify project isolation
        for artifact in project_artifacts:
            assert artifact.project_id == project.id
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_filter_artifacts_by_type_within_project(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test filtering artifacts by type within a project."""
        project = project_factory.create(db_session)
        
        # Create mixed artifact types
        for i in range(2):
            context_artifact_factory.create(
                db_session,
                project_id=project.id,
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={"plan": f"plan_{i}"}
            )
        
        for i in range(3):
            context_artifact_factory.create(
                db_session,
                project_id=project.id,
                artifact_type=ArtifactType.SOURCE_CODE,
                content={"code": f"code_{i}"}
            )
        
        context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.TEST_RESULTS,
            content={"tests": "results"}
        )
        
        # Filter by specific type
        plan_artifacts = context_store_service.get_artifacts_by_project_and_type(
            project.id, 
            ArtifactType.PROJECT_PLAN
        )
        assert len(plan_artifacts) == 2
        for artifact in plan_artifacts:
            assert artifact.artifact_type == ArtifactType.PROJECT_PLAN
        
        code_artifacts = context_store_service.get_artifacts_by_project_and_type(
            project.id,
            ArtifactType.SOURCE_CODE
        )
        assert len(code_artifacts) == 3
        
        test_artifacts = context_store_service.get_artifacts_by_project_and_type(
            project.id,
            ArtifactType.TEST_RESULTS
        )
        assert len(test_artifacts) == 1
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_filter_artifacts_by_source_agent_within_project(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test filtering artifacts by source agent within a project."""
        project = project_factory.create(db_session)
        
        # Create artifacts from different agents
        agents_and_counts = [
            (AgentType.ANALYST, 3),
            (AgentType.ARCHITECT, 2),
            (AgentType.CODER, 1)
        ]

        for agent, count in agents_and_counts:
            for i in range(count):
                context_artifact_factory.create(
                    db_session,
                    project_id=project.id,
                    source_agent=agent,  # Use enum directly
                    content={"agent": agent.value, "index": i}
                )

        # Filter by source agent
        analyst_artifacts = context_store_service.get_artifacts_by_project_and_agent(
            project.id,
            AgentType.ANALYST  # Use enum directly
        )
        assert len(analyst_artifacts) == 3

        architect_artifacts = context_store_service.get_artifacts_by_project_and_agent(
            project.id,
            AgentType.ARCHITECT  # Use enum directly
        )
        assert len(architect_artifacts) == 2

        coder_artifacts = context_store_service.get_artifacts_by_project_and_agent(
            project.id,
            AgentType.CODER  # Use enum directly
        )
        assert len(coder_artifacts) == 1

        # Verify agent isolation
        for artifact in analyst_artifacts:
            assert artifact.source_agent == AgentType.ANALYST  # Use enum directly
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    def test_complex_project_artifact_queries(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test complex queries combining multiple filters."""
        project = project_factory.create(db_session)
        
        # Create artifacts with various combinations
        test_scenarios = [
            (AgentType.ANALYST, ArtifactType.PROJECT_PLAN, {"priority": "high"}),
            (AgentType.ANALYST, ArtifactType.PROJECT_PLAN, {"priority": "medium"}),
            (AgentType.ARCHITECT, ArtifactType.SYSTEM_ARCHITECTURE, {"priority": "high"}),
            (AgentType.ARCHITECT, ArtifactType.PROJECT_PLAN, {"priority": "low"}),
            (AgentType.CODER, ArtifactType.SOURCE_CODE, {"priority": "high"}),
        ]

        created_artifacts = []
        for agent, artifact_type, metadata in test_scenarios:
            artifact = context_artifact_factory.create(
                db_session,
                project_id=project.id,
                source_agent=agent,  # Use enum directly
                artifact_type=artifact_type,
                artifact_metadata=metadata,
                content={"scenario": f"{agent.value}_{artifact_type.value}"}
            )
            created_artifacts.append(artifact)

        # Test compound filtering (agent + type)
        analyst_plans = []
        all_artifacts = context_store_service.get_artifacts_by_project(project.id)
        for artifact in all_artifacts:
            if (artifact.source_agent == AgentType.ANALYST and  # Use enum directly
                artifact.artifact_type == ArtifactType.PROJECT_PLAN):
                analyst_plans.append(artifact)
        
        assert len(analyst_plans) == 2
        
        # Test filtering by metadata priority
        high_priority_artifacts = []
        for artifact in all_artifacts:
            if artifact.artifact_metadata and artifact.artifact_metadata.get("priority") == "high":
                high_priority_artifacts.append(artifact)
        
        assert len(high_priority_artifacts) == 3

class TestArtifactRelationshipMaintenance:
    """Test scenario 2.2-INT-004: Artifact relationship maintenance (P1)"""
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_artifact_dependency_tracking(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test tracking of artifact dependencies and relationships."""
        project = project_factory.create(db_session)
        
        # Create base artifact
        user_input = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.USER_INPUT,
            source_agent=AgentType.ORCHESTRATOR,
            content={"requirements": "Build task manager"}
        )
        
        # Create dependent artifact
        analysis_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
            source_agent=AgentType.ANALYST,  # Use enum directly
            content={"based_on": str(user_input.id), "analysis": "completed"},
            artifact_metadata={"dependencies": [str(user_input.id)]}
        )

        # Create architecture artifact dependent on analysis
        architecture_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.SYSTEM_ARCHITECTURE,
            source_agent=AgentType.ARCHITECT,  # Use enum directly
            content={"based_on": str(analysis_artifact.id), "architecture": "microservices"},
            artifact_metadata={"dependencies": [str(analysis_artifact.id), str(user_input.id)]}
        )
        
        # Test dependency chain retrieval
        arch_dependencies = architecture_artifact.artifact_metadata.get("dependencies", [])
        assert len(arch_dependencies) == 2
        assert str(analysis_artifact.id) in arch_dependencies
        assert str(user_input.id) in arch_dependencies
        
        # Retrieve dependency artifacts
        dependency_artifacts = context_store_service.get_artifacts_by_ids(arch_dependencies)
        assert len(dependency_artifacts) == 2
        
        dependency_types = [artifact.artifact_type for artifact in dependency_artifacts]
        assert ArtifactType.USER_INPUT in dependency_types
        assert ArtifactType.PROJECT_PLAN in dependency_types
    
    @pytest.mark.integration
    @pytest.mark.p1
    @pytest.mark.context
    def test_artifact_version_relationships(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test relationships between artifact versions."""
        project = project_factory.create(db_session)
        
        # Create initial version
        v1_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"version": "1.0", "status": "draft"},
            artifact_metadata={"version": "1.0", "is_latest": False}
        )
        
        # Create updated version
        v2_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            artifact_type=ArtifactType.PROJECT_PLAN,
            content={"version": "2.0", "status": "reviewed", "changes": ["added requirements"]},
            artifact_metadata={
                "version": "2.0", 
                "is_latest": True,
                "previous_version": str(v1_artifact.id)
            }
        )
        
        # Update v1 to point to v2
        context_store_service.update_artifact(
            v1_artifact.id,
            artifact_metadata={
                "version": "1.0",
                "is_latest": False,
                "next_version": str(v2_artifact.id)
            }
        )
        
        # Test version chain navigation
        updated_v1 = context_store_service.get_artifact_by_id(v1_artifact.id)
        latest_v2 = context_store_service.get_artifact_by_id(v2_artifact.id)
        
        # Forward navigation (v1 -> v2)
        next_version_id = updated_v1.artifact_metadata.get("next_version")
        assert next_version_id == str(v2_artifact.id)
        
        # Backward navigation (v2 -> v1)
        prev_version_id = latest_v2.artifact_metadata.get("previous_version") 
        assert prev_version_id == str(v1_artifact.id)
        
        # Find latest version
        project_plans = context_store_service.get_artifacts_by_project_and_type(
            project.id,
            ArtifactType.PROJECT_PLAN
        )
        
        latest_plans = [
            artifact for artifact in project_plans 
            if artifact.artifact_metadata and artifact.artifact_metadata.get("is_latest", False)
        ]
        assert len(latest_plans) == 1
        assert latest_plans[0].context_id == v2_artifact.id
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    def test_artifact_reference_integrity(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory
    ):
        """Test maintenance of reference integrity when artifacts are deleted."""
        project = project_factory.create(db_session)
        
        # Create artifact chain
        base_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            content={"type": "base"}
        )
        
        dependent_artifact = context_artifact_factory.create(
            db_session,
            project_id=project.id,
            content={"depends_on": str(base_artifact.id)},
            artifact_metadata={"references": [str(base_artifact.id)]}
        )
        
        # Verify reference exists
        dependent = context_store_service.get_artifact_by_id(dependent_artifact.id)
        references = dependent.artifact_metadata.get("references", [])
        assert str(base_artifact.id) in references
        
        # Delete base artifact
        context_store_service.delete_artifact(base_artifact.id)
        
        # Verify dependent still exists but reference is broken
        dependent_after_delete = context_store_service.get_artifact_by_id(dependent_artifact.id)
        assert dependent_after_delete is not None
        
        # In a real implementation, there might be cleanup of broken references
        # or warnings about orphaned references
        
        # Verify referenced artifact is gone
        deleted_base = context_store_service.get_artifact_by_id(base_artifact.id)
        assert deleted_base is None

class TestContextStorePerformanceWithVolume:
    """Test scenario 2.2-INT-005: Context store performance with volume (P2)"""
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    @pytest.mark.performance
    def test_large_volume_artifact_creation(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, performance_timer
    ):
        """Test performance of creating large volumes of artifacts."""
        project = project_factory.create(db_session)
        artifact_count = 500
        
        performance_timer.start()
        
        created_artifacts = []
        for i in range(artifact_count):
            artifact = context_store_service.create_artifact(
                project_id=project.id,
                source_agent=AgentType.ANALYST.value,
                artifact_type=ArtifactType.PROJECT_PLAN,
                content={
                    "index": i,
                    "data": f"performance_test_data_{i}",
                    "large_field": "x" * 1000  # 1KB per artifact
                },
                artifact_metadata={"batch": "performance_test", "index": i}
            )
            created_artifacts.append(artifact)
        
        performance_timer.stop()
        
        # Verify all created
        assert len(created_artifacts) == artifact_count
        
        # Verify performance threshold
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            10000,  # 10 seconds for 500 artifacts
            f"Create {artifact_count} artifacts"
        )
        
        # Verify database consistency
        db_count = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.project_id == project.id
        ).count()
        assert db_count == artifact_count
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    @pytest.mark.performance
    def test_large_volume_artifact_queries(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, context_artifact_factory, performance_timer
    ):
        """Test performance of querying large volumes of artifacts."""
        project = project_factory.create(db_session)
        
        # Create large dataset
        artifact_count = 1000
        for i in range(artifact_count):
            context_artifact_factory.create(
                db_session,
                project_id=project.id,
                artifact_type=ArtifactType.PROJECT_PLAN if i % 2 == 0 else ArtifactType.SOURCE_CODE,
                source_agent=AgentType.ANALYST if i % 3 == 0 else AgentType.ARCHITECT,  # Use enum directly
                content={"index": i, "batch": "query_performance_test"},
                artifact_metadata={"priority": "high" if i % 5 == 0 else "normal"}
            )
        
        # Test query performance
        performance_timer.start()
        
        # Query all project artifacts
        all_artifacts = context_store_service.get_artifacts_by_project(project.id)
        
        performance_timer.stop()
        query_all_time = performance_timer.elapsed_ms
        
        # Verify results
        assert len(all_artifacts) == artifact_count
        assert_performance_threshold(query_all_time, 2000, f"Query all {artifact_count} artifacts")
        
        # Test filtered query performance
        performance_timer.start()
        
        plan_artifacts = context_store_service.get_artifacts_by_project_and_type(
            project.id,
            ArtifactType.PROJECT_PLAN
        )
        
        performance_timer.stop()
        filtered_query_time = performance_timer.elapsed_ms
        
        # Verify filtered results
        assert len(plan_artifacts) == artifact_count // 2
        assert_performance_threshold(
            filtered_query_time,
            1500,
            f"Filtered query on {artifact_count} artifacts"
        )
    
    @pytest.mark.integration
    @pytest.mark.p2
    @pytest.mark.context
    @pytest.mark.performance
    def test_concurrent_artifact_operations(
        self, db_session: Session, context_store_service: ContextStoreService,
        project_factory, performance_timer
    ):
        """Test performance of concurrent artifact operations."""
        import threading
        import time
        
        project = project_factory.create(db_session)
        results = {"created": [], "errors": []}
        
        def create_artifacts_batch(batch_id, count):
            """Create a batch of artifacts in a separate thread."""
            try:
                for i in range(count):
                    artifact = context_store_service.create_artifact(
                        project_id=project.id,
                        source_agent=AgentType.ANALYST,  # Use enum directly
                        artifact_type=ArtifactType.PROJECT_PLAN,
                        content={"batch": batch_id, "index": i}
                    )
                    results["created"].append(artifact)
            except Exception as e:
                results["errors"].append(str(e))
        
        performance_timer.start()
        
        # Create multiple threads
        threads = []
        batch_count = 5
        artifacts_per_batch = 20
        
        for batch_id in range(batch_count):
            thread = threading.Thread(
                target=create_artifacts_batch,
                args=(batch_id, artifacts_per_batch)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        performance_timer.stop()
        
        # Verify results
        expected_total = batch_count * artifacts_per_batch
        assert len(results["created"]) == expected_total
        assert len(results["errors"]) == 0
        
        # Verify performance
        assert_performance_threshold(
            performance_timer.elapsed_ms,
            5000,
            f"Concurrent creation of {expected_total} artifacts"
        )
        
        # Verify database consistency
        final_count = db_session.query(ContextArtifactDB).filter(
            ContextArtifactDB.project_id == project.id
        ).count()
        assert final_count == expected_total
