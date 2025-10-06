"""
Test suite for consolidated DocumentService.
Covers document assembly, sectioning, and granularity analysis.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from app.services.document_service import DocumentService
from tests.utils.database_test_utils import DatabaseTestManager


class TestDocumentService:
    """Test consolidated document processing service."""
    
    @pytest.fixture
    def document_config(self):
        """Standard document service configuration."""
        return {
            "enable_deduplication": True,
            "enable_conflict_resolution": True,
            "max_section_size": 8192,
            "min_section_size": 512,
            "enable_semantic_sectioning": True,
            "preserve_hierarchy": True,
            "supported_formats": ["markdown", "text", "json", "yaml", "html"],
            "analysis_depth": "comprehensive",
            "enable_ml_classification": True,
            "complexity_thresholds": {
                "low": 0.3,
                "medium": 0.7,
                "high": 1.0
            },
            "size_thresholds": {
                "small": 1024,
                "medium": 10240,
                "large": 1048576
            }
        }
    
    @pytest.fixture
    def document_service(self, document_config):
        """Create DocumentService instance with test configuration."""
        return DocumentService(document_config)
    
    @pytest.fixture
    def sample_artifacts(self):
        """Sample artifacts for testing document assembly."""
        return [
            {
                "id": "artifact_1",
                "content": "# Introduction\nThis is the introduction section.",
                "metadata": {"type": "introduction", "priority": 1}
            },
            {
                "id": "artifact_2", 
                "content": "## Requirements\n- Requirement 1\n- Requirement 2",
                "metadata": {"type": "requirements", "priority": 2}
            },
            {
                "id": "artifact_3",
                "content": "### Implementation\nImplementation details here.",
                "metadata": {"type": "implementation", "priority": 3}
            }
        ]

    # Document Assembly Tests
    
    @pytest.mark.real_data
    async def test_assemble_document_multiple_artifacts(self, document_service, sample_artifacts):
        """Test document assembly from multiple artifacts."""
        project_id = "test_project_123"
        
        result = await document_service.assemble_document(
            artifacts=sample_artifacts,
            project_id=project_id
        )
        
        # Verify assembly result structure
        assert isinstance(result, dict)
        assert "content" in result
        assert "metadata" in result
        assert "assembly_info" in result
        
        # Verify content contains all artifacts
        content = result["content"]
        assert "Introduction" in content
        assert "Requirements" in content
        assert "Implementation" in content
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["project_id"] == project_id
        assert metadata["artifact_count"] == 3
        assert "assembled_at" in metadata
    
    @pytest.mark.real_data  
    async def test_assemble_document_deduplication(self, document_service):
        """Test content deduplication during assembly."""
        duplicate_artifacts = [
            {
                "id": "artifact_1",
                "content": "# Duplicate Section\nThis content appears twice.",
                "metadata": {"type": "section"}
            },
            {
                "id": "artifact_2",
                "content": "# Duplicate Section\nThis content appears twice.",
                "metadata": {"type": "section"}
            },
            {
                "id": "artifact_3",
                "content": "# Unique Section\nThis is unique content.",
                "metadata": {"type": "section"}
            }
        ]
        
        result = await document_service.assemble_document(
            artifacts=duplicate_artifacts,
            project_id="test_project"
        )
        
        content = result["content"]
        # Should only contain one instance of duplicate content
        duplicate_count = content.count("This content appears twice.")
        assert duplicate_count == 1
        
        # Should contain unique content
        assert "This is unique content." in content
        
        # Verify deduplication was applied
        assembly_info = result["assembly_info"]
        assert assembly_info["deduplication_applied"] is True
        assert assembly_info["duplicates_removed"] > 0

    @pytest.mark.real_data
    async def test_assemble_document_empty_artifacts(self, document_service):
        """Test document assembly with empty artifacts list."""
        result = await document_service.assemble_document(
            artifacts=[],
            project_id="test_project"
        )
        
        assert result["content"] == ""
        assert result["metadata"]["artifact_count"] == 0
        assert result["assembly_info"]["total_size"] == 0

    @pytest.mark.real_data
    async def test_assemble_document_with_config_override(self, document_service, sample_artifacts):
        """Test document assembly with configuration overrides."""
        assembly_config = {
            "enable_deduplication": False,
            "generate_toc": True
        }
        
        result = await document_service.assemble_document(
            artifacts=sample_artifacts,
            project_id="test_project",
            assembly_config=assembly_config
        )
        
        # Should have table of contents when enabled
        assert "table_of_contents" in result
        
        # Verify config was applied
        assembly_info = result["assembly_info"]
        assert assembly_info["deduplication_applied"] is False

    # Document Sectioning Tests
    
    @pytest.mark.mock_data
    def test_section_document_markdown(self, document_service):
        """Test sectioning of markdown content."""
        markdown_content = """
# Main Title

## Section 1
Content for section 1 with some text that makes it substantial.

## Section 2  
Content for section 2 with more text to meet minimum size requirements.

### Subsection 2.1
Subsection content here.

## Section 3
Final section content.
"""
        
        sections = document_service.section_document(markdown_content, "markdown")
        
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Verify section structure
        for section in sections:
            assert "content" in section
            assert "metadata" in section
            assert "section_id" in section
            
        # Should preserve hierarchy
        section_titles = [s["metadata"].get("title", "") for s in sections]
        assert any("Main Title" in title for title in section_titles)
        assert any("Section 1" in title for title in section_titles)

    @pytest.mark.mock_data
    def test_section_document_size_constraints(self, document_service):
        """Test sectioning respects size constraints."""
        # Create content that exceeds max section size
        large_content = "# Large Section\n" + "This is a lot of content. " * 1000
        
        sections = document_service.section_document(large_content, "markdown")
        
        # Verify no section exceeds max size
        max_size = document_service.max_section_size
        for section in sections:
            content_size = len(section["content"])
            assert content_size <= max_size, f"Section size {content_size} exceeds max {max_size}"

    @pytest.mark.mock_data
    def test_section_document_unsupported_format(self, document_service):
        """Test sectioning with unsupported format."""
        content = "Some content"
        
        with pytest.raises(ValueError, match="Unsupported format"):
            document_service.section_document(content, "unsupported_format")

    @pytest.mark.mock_data
    def test_section_document_json_format(self, document_service):
        """Test sectioning of JSON content."""
        json_content = """
{
    "section1": {
        "title": "First Section",
        "content": "Content for first section"
    },
    "section2": {
        "title": "Second Section", 
        "content": "Content for second section"
    }
}
"""
        
        sections = document_service.section_document(json_content, "json")
        
        assert isinstance(sections, list)
        assert len(sections) >= 2
        
        # Verify JSON structure is preserved
        for section in sections:
            assert "content" in section
            assert "metadata" in section

    # Granularity Analysis Tests
    
    @pytest.mark.mock_data
    async def test_analyze_granularity_simple_content(self, document_service):
        """Test granularity analysis for simple content."""
        simple_content = "This is a simple requirement with basic text."
        
        analysis = await document_service.analyze_granularity(simple_content)
        
        # Verify analysis structure
        assert isinstance(analysis, dict)
        assert "complexity_score" in analysis
        assert "size_category" in analysis
        assert "recommendations" in analysis
        assert "metrics" in analysis
        
        # Simple content should have low complexity
        assert analysis["complexity_score"] <= document_service.complexity_thresholds["medium"]
        assert analysis["size_category"] == "small"

    @pytest.mark.mock_data
    async def test_analyze_granularity_complex_content(self, document_service):
        """Test granularity analysis for complex content."""
        complex_content = """
        The system shall implement OAuth 2.0 authentication with JWT tokens,
        support role-based access control with hierarchical permissions,
        provide audit logging for all security events, implement rate limiting
        for API endpoints, support multi-factor authentication, and ensure
        compliance with GDPR data protection regulations. Additionally, the
        system must handle concurrent user sessions, provide real-time
        notifications, integrate with external identity providers, support
        API versioning, implement caching strategies, and maintain high
        availability with 99.9% uptime requirements.
        """
        
        analysis = await document_service.analyze_granularity(complex_content)
        
        # Complex content should have higher complexity
        assert analysis["complexity_score"] > document_service.complexity_thresholds["low"]
        
        # Should provide recommendations for complex content
        recommendations = analysis["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @pytest.mark.mock_data
    async def test_analyze_granularity_empty_content(self, document_service):
        """Test granularity analysis for empty content."""
        analysis = await document_service.analyze_granularity("")
        
        assert analysis["complexity_score"] == 0.0
        assert analysis["size_category"] == "small"
        assert len(analysis["recommendations"]) == 0

    @pytest.mark.mock_data
    async def test_analyze_granularity_large_content(self, document_service):
        """Test granularity analysis for large content."""
        large_content = "This is a large document. " * 10000  # ~250KB
        
        analysis = await document_service.analyze_granularity(large_content)
        
        assert analysis["size_category"] == "large"
        
        # Large content should suggest breaking down
        recommendations = analysis["recommendations"]
        assert any("break" in rec.lower() or "split" in rec.lower() for rec in recommendations)

    # Configuration and Initialization Tests
    
    @pytest.mark.mock_data
    def test_document_service_initialization(self, document_config):
        """Test DocumentService initialization with configuration."""
        service = DocumentService(document_config)
        
        # Verify configuration was applied
        assert service.enable_deduplication == document_config["enable_deduplication"]
        assert service.max_section_size == document_config["max_section_size"]
        assert service.analysis_depth == document_config["analysis_depth"]
        assert service.complexity_thresholds == document_config["complexity_thresholds"]

    @pytest.mark.mock_data
    def test_document_service_default_config(self):
        """Test DocumentService with minimal configuration."""
        minimal_config = {}
        service = DocumentService(minimal_config)
        
        # Should use sensible defaults
        assert service.enable_deduplication is True
        assert service.max_section_size == 8192
        assert service.min_section_size == 512
        assert service.analysis_depth == "comprehensive"

    # Error Handling Tests
    
    @pytest.mark.mock_data
    async def test_assemble_document_invalid_artifacts(self, document_service):
        """Test document assembly with invalid artifact data."""
        invalid_artifacts = [
            {"id": "valid", "content": "Valid content"},
            {"id": "invalid"},  # Missing content
            None  # Null artifact
        ]
        
        # Should handle invalid artifacts gracefully
        result = await document_service.assemble_document(
            artifacts=invalid_artifacts,
            project_id="test_project"
        )
        
        # Should process valid artifacts and skip invalid ones
        assert "Valid content" in result["content"]
        assert result["metadata"]["artifact_count"] == 1  # Only valid artifact counted
        
        # Should report processing issues
        assembly_info = result["assembly_info"]
        assert assembly_info["invalid_artifacts"] > 0

    @pytest.mark.mock_data
    def test_section_document_malformed_content(self, document_service):
        """Test sectioning with malformed content."""
        malformed_json = '{"incomplete": json content'
        
        # Should handle malformed content gracefully
        sections = document_service.section_document(malformed_json, "json")
        
        # Should return at least one section with the content
        assert len(sections) >= 1
        assert malformed_json in sections[0]["content"]