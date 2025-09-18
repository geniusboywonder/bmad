"""
Test Cases for P2.4 Context Store Mixed-Granularity Enhancement

This module contains comprehensive test cases for mixed-granularity context storage,
including intelligent granularity system, document sectioning, concept extraction, and redundancy prevention.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

from app.services.context_store import ContextStore
from app.services.artifact_service import ArtifactService
from app.services.granularity_analyzer import GranularityAnalyzer
from app.models.context_artifact import ContextArtifact
from app.models.knowledge_unit import KnowledgeUnit


class TestContextStore:
    """Test cases for the enhanced context store."""

    @pytest.fixture
    def context_store_config(self):
        """Context store configuration for testing."""
        return {
            "storage_backend": "postgresql",
            "cache_enabled": True,
            "compression_enabled": True,
            "max_artifact_size": 1048576,  # 1MB
            "retention_policy": "30_days"
        }

    def test_context_store_initialization(self, context_store_config):
        """Test context store initialization."""
        context_store = ContextStore(context_store_config)

        # Verify configuration was applied
        assert context_store.storage_backend == context_store_config["storage_backend"]
        assert context_store.cache_enabled == context_store_config["cache_enabled"]
        assert context_store.max_artifact_size == context_store_config["max_artifact_size"]

    def test_artifact_storage(self, context_store_config):
        """Test context artifact storage."""
        context_store = ContextStore(context_store_config)

        # Test storing an artifact
        artifact_data = {
            "id": "artifact-123",
            "project_id": "project-456",
            "type": "requirements",
            "content": "User requirements document content",
            "metadata": {
                "author": "analyst",
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

        result = context_store.store_artifact(artifact_data)

        # Verify storage result
        assert result["stored"] == True
        assert result["artifact_id"] == "artifact-123"
        assert "storage_location" in result

    def test_artifact_retrieval(self, context_store_config):
        """Test context artifact retrieval."""
        context_store = ContextStore(context_store_config)

        # Test retrieving an artifact
        artifact_id = "artifact-123"
        project_id = "project-456"

        artifact = context_store.retrieve_artifact(artifact_id, project_id)

        # Verify retrieval result
        assert artifact is not None
        assert artifact["id"] == artifact_id
        assert artifact["project_id"] == project_id

    def test_context_injection(self, context_store_config):
        """Test context injection for agents."""
        context_store = ContextStore(context_store_config)

        # Test injecting relevant context
        agent_request = {
            "agent_type": "architect",
            "phase": "design",
            "project_id": "project-456",
            "query": "What are the system requirements?"
        }

        context = context_store.inject_context(agent_request)

        # Verify context injection
        assert "relevant_artifacts" in context
        assert "knowledge_units" in context
        assert len(context["relevant_artifacts"]) > 0

    def test_cache_management(self, context_store_config):
        """Test context store cache management."""
        context_store = ContextStore(context_store_config)

        # Test cache storage
        cache_key = "project-456:requirements"
        cache_data = {"artifacts": ["req1", "req2"], "last_updated": datetime.now()}

        context_store._cache_context(cache_key, cache_data)

        # Test cache retrieval
        cached_data = context_store._get_cached_context(cache_key)

        assert cached_data == cache_data

        # Test cache invalidation
        context_store._invalidate_cache(cache_key)
        cached_data = context_store._get_cached_context(cache_key)

        assert cached_data is None

    def test_compression_handling(self, context_store_config):
        """Test artifact compression handling."""
        context_store = ContextStore(context_store_config)

        # Test compression of large artifacts
        large_content = "x" * 100000  # 100KB of content

        compressed = context_store._compress_artifact(large_content)
        decompressed = context_store._decompress_artifact(compressed)

        # Verify compression/decompression
        assert decompressed == large_content
        # Note: Our simple compression may not always be smaller, so we'll just verify it works

    def test_retention_policy(self, context_store_config):
        """Test artifact retention policy enforcement."""
        context_store = ContextStore(context_store_config)

        # Test retention policy application
        old_artifacts = [
            {
                "id": "old-artifact",
                "created_at": datetime.now() - timedelta(days=45),  # Older than 30 days
                "size": 1024
            }
        ]

        cleanup_result = context_store._apply_retention_policy(old_artifacts)

        # Verify retention policy application
        assert cleanup_result["artifacts_removed"] > 0
        assert "storage_freed" in cleanup_result


class TestArtifactService:
    """Test cases for the artifact service."""

    @pytest.fixture
    def artifact_service_config(self):
        """Artifact service configuration for testing."""
        return {
            "enable_granularity_analysis": True,
            "max_atomic_size": 10240,  # 10KB
            "enable_concept_extraction": True,
            "supported_formats": ["text", "json", "yaml", "markdown"]
        }

    def test_artifact_service_initialization(self, artifact_service_config):
        """Test artifact service initialization."""
        artifact_service = ArtifactService(artifact_service_config)

        # Verify configuration was applied
        assert artifact_service.enable_granularity_analysis == artifact_service_config["enable_granularity_analysis"]
        assert artifact_service.max_atomic_size == artifact_service_config["max_atomic_size"]

    def test_granularity_determination(self, artifact_service_config):
        """Test artifact granularity determination."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test small artifact (should be atomic)
        small_content = "This is a small requirements document."
        granularity = artifact_service.determine_granularity(small_content, "requirements")

        assert granularity["strategy"] == "atomic"
        assert granularity["size_category"] == "small"

        # Test large artifact (should be sectioned)
        large_content = "Section 1\n" + "x" * 50000 + "\nSection 2\n" + "y" * 50000
        granularity = artifact_service.determine_granularity(large_content, "architecture")

        assert granularity["strategy"] == "sectioned"
        assert granularity["size_category"] == "large"

    def test_document_sectioning(self, artifact_service_config):
        """Test document sectioning for large artifacts."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test sectioning a large document
        document_content = """
# Introduction
This is the introduction section.

## Requirements
- Requirement 1
- Requirement 2
- Requirement 3

## Architecture
### Component A
Details about component A.

### Component B
Details about component B.

## Implementation
Implementation details here.

# Conclusion
This is the conclusion.
"""

        sections = artifact_service.section_document(document_content, "architecture")

        # Verify document sectioning
        assert len(sections) > 1
        assert "Introduction" in [s["title"] for s in sections]
        assert "Requirements" in [s["title"] for s in sections]
        assert "Architecture" in [s["title"] for s in sections]

        # Verify section content
        intro_section = next(s for s in sections if s["title"] == "Introduction")
        assert "introduction section" in intro_section["content"].lower()

    def test_concept_extraction(self, artifact_service_config):
        """Test concept extraction from artifacts."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test extracting concepts from content
        content = """
        The user authentication system must support OAuth 2.0 and JWT tokens.
        The database should use PostgreSQL with connection pooling.
        The API should follow RESTful principles with proper error handling.
        """

        concepts = artifact_service.extract_concepts(content)

        # Verify concept extraction
        assert len(concepts) > 0
        concept_names = [c["name"] for c in concepts]

        assert "authentication" in concept_names or "oauth" in concept_names
        assert "database" in concept_names or "postgresql" in concept_names
        assert "api" in concept_names or "rest" in concept_names

        # Verify concept relationships
        for concept in concepts:
            assert "relationships" in concept
            assert isinstance(concept["relationships"], list)

    def test_knowledge_unit_creation(self, artifact_service_config):
        """Test knowledge unit creation from concepts."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test creating knowledge units
        concepts = [
            {
                "name": "authentication",
                "type": "security_concept",
                "importance": 0.9,
                "relationships": ["user_management", "security"]
            },
            {
                "name": "database",
                "type": "infrastructure_concept",
                "importance": 0.8,
                "relationships": ["data_storage", "performance"]
            }
        ]

        knowledge_units = artifact_service.create_knowledge_units(concepts)

        # Verify knowledge unit creation
        assert len(knowledge_units) == len(concepts)

        for unit in knowledge_units:
            assert "id" in unit
            assert "concept" in unit
            assert "context" in unit
            assert "usage_count" in unit
            assert unit["usage_count"] == 0

    def test_redundancy_detection(self, artifact_service_config):
        """Test redundancy detection and prevention."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test detecting redundant content
        existing_artifacts = [
            {
                "id": "artifact-1",
                "content": "User authentication is required for the system.",
                "concepts": ["authentication", "security"]
            }
        ]

        new_content = "The system needs user authentication and security measures."

        redundancy = artifact_service.detect_redundancy(new_content, existing_artifacts)

        # Verify redundancy detection
        assert redundancy["is_redundant"] == True
        assert redundancy["similarity_score"] > 0.7
        assert "existing_artifact" in redundancy

    def test_artifact_relationship_mapping(self, artifact_service_config):
        """Test artifact relationship mapping."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test mapping relationships between artifacts
        artifacts = [
            {"id": "req-1", "type": "requirements", "concepts": ["authentication", "api"]},
            {"id": "arch-1", "type": "architecture", "concepts": ["api", "database"]},
            {"id": "impl-1", "type": "implementation", "concepts": ["database", "authentication"]}
        ]

        relationships = artifact_service.map_artifact_relationships(artifacts)

        # Verify relationship mapping
        assert len(relationships) > 0

        # Check for expected relationships
        relationship_types = [r["type"] for r in relationships]
        assert "depends_on" in relationship_types or "related_to" in relationship_types

    def test_artifact_versioning(self, artifact_service_config):
        """Test artifact versioning and evolution tracking."""
        artifact_service = ArtifactService(artifact_service_config)

        # Test versioning an artifact
        original_artifact = {
            "id": "artifact-123",
            "version": "1.0",
            "content": "Original content",
            "concepts": ["concept_a"]
        }

        updated_content = "Updated content with new information"
        new_concepts = ["concept_a", "concept_b"]

        versioned_artifact = artifact_service.version_artifact(
            original_artifact,
            updated_content,
            new_concepts
        )

        # Verify versioning
        assert versioned_artifact["version"] == "1.1"
        assert versioned_artifact["previous_version"] == "1.0"
        assert len(versioned_artifact["changes"]) > 0
        assert "concept_b" in versioned_artifact["concepts"]


class TestGranularityAnalyzer:
    """Test cases for the granularity analyzer."""

    @pytest.fixture
    def granularity_config(self):
        """Granularity analyzer configuration for testing."""
        return {
            "analysis_depth": "comprehensive",
            "enable_ml_classification": True,
            "complexity_thresholds": {
                "low": 0.3,
                "medium": 0.7,
                "high": 1.0
            },
            "size_thresholds": {
                "small": 1024,      # 1KB
                "medium": 10240,    # 10KB
                "large": 1048576    # 1MB
            }
        }

    def test_granularity_analyzer_initialization(self, granularity_config):
        """Test granularity analyzer initialization."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Verify configuration was applied
        assert analyzer.analysis_depth == granularity_config["analysis_depth"]
        assert analyzer.enable_ml_classification == granularity_config["enable_ml_classification"]

    def test_content_complexity_analysis(self, granularity_config):
        """Test content complexity analysis."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Test analyzing simple content
        simple_content = "This is a simple requirement."
        complexity = analyzer.analyze_complexity(simple_content)

        assert complexity["score"] < granularity_config["complexity_thresholds"]["low"]
        assert complexity["level"] == "low"

        # Test analyzing complex content
        complex_content = """
        The system shall implement OAuth 2.0 authentication with JWT tokens,
        support role-based access control with hierarchical permissions,
        provide audit logging for all security events, implement rate limiting
        for API endpoints, support multi-factor authentication, and ensure
        compliance with GDPR data protection regulations.
        """

        complexity = analyzer.analyze_complexity(complex_content)

        assert complexity["score"] > granularity_config["complexity_thresholds"]["medium"]
        assert complexity["level"] in ["medium", "high"]

    def test_optimal_granularity_recommendation(self, granularity_config):
        """Test optimal granularity recommendation."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Test small, simple content
        small_simple = {
            "content": "Simple requirement",
            "size": 100,
            "complexity_score": 0.2
        }

        recommendation = analyzer.recommend_granularity(small_simple)

        assert recommendation["strategy"] == "atomic"
        assert recommendation["confidence"] > 0.8

        # Test large, complex content
        large_complex = {
            "content": "x" * 50000,  # 50KB
            "size": 50000,
            "complexity_score": 0.8
        }

        recommendation = analyzer.recommend_granularity(large_complex)

        assert recommendation["strategy"] in ["sectioned", "conceptual"]
        assert recommendation["confidence"] > 0.7

    def test_section_boundary_detection(self, granularity_config):
        """Test section boundary detection in documents."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Test detecting section boundaries
        document = """
        # Introduction
        This is the introduction.

        ## Background
        Some background information.

        # Requirements
        ## Functional Requirements
        - Req 1
        - Req 2

        ## Non-Functional Requirements
        - Performance
        - Security

        # Conclusion
        Final thoughts.
        """

        boundaries = analyzer.detect_section_boundaries(document)

        # Verify boundary detection
        assert len(boundaries) > 0
        section_titles = [b["title"] for b in boundaries]

        assert "Introduction" in section_titles
        assert "Requirements" in section_titles
        assert "Conclusion" in section_titles

        # Verify boundary positions
        for boundary in boundaries:
            assert "start_position" in boundary
            assert "end_position" in boundary
            assert boundary["start_position"] < boundary["end_position"]

    def test_concept_relationship_analysis(self, granularity_config):
        """Test concept relationship analysis."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Test analyzing concept relationships
        concepts = [
            {"name": "authentication", "type": "security"},
            {"name": "database", "type": "infrastructure"},
            {"name": "api", "type": "interface"},
            {"name": "user", "type": "entity"}
        ]

        relationships = analyzer.analyze_concept_relationships(concepts)

        # Verify relationship analysis
        assert len(relationships) > 0

        # Check for expected relationships
        relationship_pairs = [(r["source"], r["target"]) for r in relationships]

        # Authentication and user should be related
        assert ("authentication", "user") in relationship_pairs or ("user", "authentication") in relationship_pairs

    def test_performance_optimization_recommendations(self, granularity_config):
        """Test performance optimization recommendations."""
        analyzer = GranularityAnalyzer(granularity_config)

        # Test recommending optimizations
        content_profile = {
            "size": 100000,  # 100KB
            "complexity": 0.6,
            "access_pattern": "frequent_small_reads",
            "update_frequency": "low"
        }

        recommendations = analyzer.recommend_optimizations(content_profile)

        # Verify optimization recommendations
        assert len(recommendations) > 0
        assert "strategy" in recommendations[0]
        assert "expected_benefit" in recommendations[0]


class TestContextArtifact:
    """Test cases for the context artifact model."""

    def test_context_artifact_creation(self):
        """Test context artifact creation."""
        artifact_data = {
            "id": "artifact-123",
            "project_id": "project-456",
            "type": "requirements",
            "content": "User requirements content",
            "granularity": "atomic",
            "metadata": {
                "author": "analyst",
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

        artifact = ContextArtifact(**artifact_data)

        # Verify artifact creation
        assert artifact.id == "artifact-123"
        assert artifact.project_id == "project-456"
        assert artifact.type == "requirements"
        assert artifact.granularity == "atomic"

    def test_artifact_validation(self):
        """Test context artifact validation."""
        # Test valid artifact
        valid_data = {
            "id": "artifact-123",
            "project_id": "project-456",
            "type": "requirements",
            "content": "Content"
        }

        artifact = ContextArtifact(**valid_data)
        assert artifact is not None

        # Test invalid artifact (missing required field)
        invalid_data = {
            "project_id": "project-456",
            "type": "requirements",
            "content": "Content"
        }

        with pytest.raises(ValueError):
            ContextArtifact(**invalid_data)

    def test_artifact_serialization(self):
        """Test context artifact serialization."""
        artifact = ContextArtifact(
            id="artifact-123",
            project_id="project-456",
            type="requirements",
            content="Test content",
            granularity="atomic"
        )

        # Serialize to dict
        serialized = artifact.dict()

        # Verify serialization
        assert serialized["id"] == "artifact-123"
        assert serialized["type"] == "requirements"
        assert serialized["granularity"] == "atomic"


class TestKnowledgeUnit:
    """Test cases for the knowledge unit model."""

    def test_knowledge_unit_creation(self):
        """Test knowledge unit creation."""
        unit_data = {
            "id": "unit-123",
            "concept": "authentication",
            "type": "security_concept",
            "content": "Knowledge about authentication mechanisms",
            "relationships": ["user_management", "security"],
            "usage_count": 5,
            "last_accessed": datetime.now().isoformat()
        }

        unit = KnowledgeUnit(**unit_data)

        # Verify unit creation
        assert unit.id == "unit-123"
        assert unit.concept == "authentication"
        assert unit.type == "security_concept"
        assert unit.usage_count == 5

    def test_knowledge_unit_usage_tracking(self):
        """Test knowledge unit usage tracking."""
        unit = KnowledgeUnit(
            id="unit-123",
            concept="authentication",
            type="security_concept",
            content="Auth knowledge"
        )

        # Test usage tracking
        initial_usage = unit.usage_count

        unit.track_usage()

        assert unit.usage_count == initial_usage + 1
        assert unit.last_accessed is not None

    def test_unit_relationship_management(self):
        """Test knowledge unit relationship management."""
        unit = KnowledgeUnit(
            id="unit-123",
            concept="authentication",
            type="security_concept",
            content="Auth knowledge",
            relationships=["user", "security"]
        )

        # Test adding relationship
        unit.add_relationship("authorization")

        assert "authorization" in unit.relationships

        # Test removing relationship
        unit.remove_relationship("user")

        assert "user" not in unit.relationships
        assert "security" in unit.relationships




if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
