"""
Document Service for BMAD Core Template System

This module provides comprehensive document processing capabilities including:
- Document assembly from multiple artifacts
- Intelligent content sectioning and segmentation  
- Granularity analysis and optimization
- Content merging, deduplication, and conflict resolution
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import structlog
import json
import re
from collections import defaultdict, Counter
import difflib

# Removed ArtifactService import to avoid circular dependency

logger = structlog.get_logger(__name__)


class DocumentService:
    """
    Unified service for document processing, assembly, sectioning, and analysis.
    
    Consolidates functionality from DocumentAssembler, DocumentSectioner, 
    and GranularityAnalyzer into a single cohesive service.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the document service.

        Args:
            config: Configuration dictionary with processing parameters
        """
        # Assembly configuration
        self.enable_deduplication = config.get("enable_deduplication", True)
        self.enable_conflict_resolution = config.get("enable_conflict_resolution", True)
        self.max_merge_conflicts = config.get("max_merge_conflicts", 10)
        self.preserve_original_metadata = config.get("preserve_original_metadata", True)
        self.generate_toc = config.get("generate_toc", True)

        # Sectioning configuration
        self.max_section_size = config.get("max_section_size", 8192)  # 8KB
        self.min_section_size = config.get("min_section_size", 512)   # 512B
        self.enable_semantic_sectioning = config.get("enable_semantic_sectioning", True)
        self.preserve_hierarchy = config.get("preserve_hierarchy", True)
        self.supported_formats = config.get("supported_formats", [
            "markdown", "text", "json", "yaml", "html"
        ])

        # Granularity analysis configuration
        self.analysis_depth = config.get("analysis_depth", "comprehensive")
        self.enable_ml_classification = config.get("enable_ml_classification", True)
        self.complexity_thresholds = config.get("complexity_thresholds", {
            "low": 0.3,
            "medium": 0.7,
            "high": 1.0
        })
        self.size_thresholds = config.get("size_thresholds", {
            "small": 1024,      # 1KB
            "medium": 10240,    # 10KB
            "large": 1048576    # 1MB
        })

        # No sub-services needed - avoiding circular dependencies

        logger.info("Document service initialized",
                   deduplication=self.enable_deduplication,
                   semantic_sectioning=self.enable_semantic_sectioning,
                   analysis_depth=self.analysis_depth)

    # DOCUMENT ASSEMBLY METHODS
    
    async def assemble_document(
        self,
        artifacts: List[Dict[str, Any]],
        project_id: str,
        assembly_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assemble a document from multiple artifacts.

        Args:
            artifacts: List of artifact dictionaries to assemble
            project_id: Project identifier
            assembly_config: Optional assembly configuration overrides

        Returns:
            Assembled document with metadata
        """
        logger.info("Starting document assembly",
                   artifact_count=len(artifacts),
                   project_id=project_id)

        try:
            
            # Analyze content for optimal assembly strategy
            assembly_strategy = await self._determine_assembly_strategy(artifacts)
            
            # Perform content merging and deduplication
            merged_content = await self._merge_and_deduplicate(artifacts, assembly_strategy)
            
            # Resolve conflicts if any
            if self.enable_conflict_resolution:
                merged_content = await self._resolve_conflicts(merged_content)
            
            # Generate table of contents if requested
            if self.generate_toc:
                toc = await self._generate_table_of_contents(merged_content)
                merged_content["table_of_contents"] = toc
            
            # Add assembly metadata
            artifact_ids = [artifact.get("id", "unknown") for artifact in artifacts]
            merged_content["assembly_metadata"] = {
                "assembled_at": datetime.now(timezone.utc).isoformat(),
                "source_artifacts": artifact_ids,
                "assembly_strategy": assembly_strategy,
                "project_id": project_id
            }

            logger.info("Document assembly completed successfully",
                       final_size=len(str(merged_content)))

            return merged_content

        except Exception as e:
            logger.error("Document assembly failed", error=str(e))
            raise

    # DOCUMENT SECTIONING METHODS

    def section_document(self, content: str, format_type: str = "markdown") -> List[Dict[str, Any]]:
        """
        Section a document into logical components.

        Args:
            content: Document content to section
            format_type: Format of the content (markdown, text, json, yaml, html)

        Returns:
            List of document sections with metadata
        """
        logger.info("Starting document sectioning",
                   content_length=len(content),
                   format_type=format_type)

        if format_type not in self.supported_formats:
            logger.warning("Unsupported format, using text sectioning",
                          format_type=format_type)
            format_type = "text"

        try:
            # Detect natural section boundaries
            sections = self._detect_section_boundaries(content, format_type)
            
            # Apply size constraints
            sections = self._apply_size_constraints(sections)
            
            # Add semantic analysis if enabled
            if self.enable_semantic_sectioning:
                sections = self._enhance_with_semantic_analysis(sections)
            
            # Preserve hierarchy if requested
            if self.preserve_hierarchy:
                sections = self._preserve_document_hierarchy(sections)

            logger.info("Document sectioning completed",
                       section_count=len(sections))

            return sections

        except Exception as e:
            logger.error("Document sectioning failed", error=str(e))
            raise

    # GRANULARITY ANALYSIS METHODS

    async def analyze_granularity(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content granularity and provide optimization recommendations.

        Args:
            content: Content to analyze
            context: Optional context information

        Returns:
            Granularity analysis results with recommendations
        """
        logger.info("Starting granularity analysis",
                   content_length=len(content))

        try:
            # Calculate complexity metrics
            complexity_score = self._calculate_complexity_score(content)
            
            # Determine size category
            size_category = self._categorize_content_size(len(content))
            
            # Analyze content structure
            structure_analysis = self._analyze_content_structure(content)
            
            # Generate recommendations
            recommendations = self._generate_granularity_recommendations(
                complexity_score, size_category, structure_analysis
            )

            analysis_result = {
                "complexity_score": complexity_score,
                "size_category": size_category,
                "structure_analysis": structure_analysis,
                "recommendations": recommendations,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }

            logger.info("Granularity analysis completed",
                       complexity_score=complexity_score,
                       size_category=size_category)

            return analysis_result

        except Exception as e:
            logger.error("Granularity analysis failed", error=str(e))
            raise

    # PRIVATE HELPER METHODS

    # _retrieve_artifacts method removed to avoid circular dependency
    # Callers should pass artifacts directly instead of artifact IDs

    async def _determine_assembly_strategy(self, artifacts: List[Dict[str, Any]]) -> str:
        """Determine the optimal assembly strategy based on artifact characteristics."""
        if len(artifacts) <= 2:
            return "simple_merge"
        elif any(artifact.get("type") == "code" for artifact in artifacts):
            return "code_aware_merge"
        else:
            return "intelligent_merge"

    async def _merge_and_deduplicate(self, artifacts: List[Dict[str, Any]], strategy: str) -> Dict[str, Any]:
        """Merge artifacts and remove duplicates."""
        merged = {"content": "", "metadata": {}}
        
        for artifact in artifacts:
            content = artifact.get("content", "")
            if self.enable_deduplication:
                content = self._remove_duplicate_content(content, merged["content"])
            merged["content"] += content + "\n\n"
            
        return merged

    async def _resolve_conflicts(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve content conflicts using intelligent strategies."""
        # Simplified conflict resolution
        return content

    async def _generate_table_of_contents(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate table of contents from content."""
        toc = []
        lines = content.get("content", "").split("\n")
        
        for line in lines:
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                title = line.lstrip("# ").strip()
                toc.append({"level": level, "title": title})
                
        return toc

    def _detect_section_boundaries(self, content: str, format_type: str) -> List[Dict[str, Any]]:
        """Detect natural section boundaries in content."""
        sections = []
        
        if format_type == "markdown":
            # Split on markdown headers
            parts = re.split(r'\n(#{1,6}\s+.*)', content)
            current_section = ""
            
            for i, part in enumerate(parts):
                if re.match(r'^#{1,6}\s+', part):
                    if current_section.strip():
                        sections.append({
                            "content": current_section.strip(),
                            "type": "content",
                            "size": len(current_section)
                        })
                    sections.append({
                        "content": part,
                        "type": "header",
                        "size": len(part)
                    })
                    current_section = ""
                else:
                    current_section += part
                    
            if current_section.strip():
                sections.append({
                    "content": current_section.strip(),
                    "type": "content",
                    "size": len(current_section)
                })
        else:
            # Simple paragraph-based sectioning for other formats
            paragraphs = content.split("\n\n")
            for para in paragraphs:
                if para.strip():
                    sections.append({
                        "content": para.strip(),
                        "type": "paragraph",
                        "size": len(para)
                    })
                    
        return sections

    def _apply_size_constraints(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply size constraints to sections."""
        constrained_sections = []
        
        for section in sections:
            if section["size"] > self.max_section_size:
                # Split large sections
                content = section["content"]
                chunks = [content[i:i+self.max_section_size] 
                         for i in range(0, len(content), self.max_section_size)]
                
                for i, chunk in enumerate(chunks):
                    constrained_sections.append({
                        "content": chunk,
                        "type": f"{section['type']}_chunk_{i}",
                        "size": len(chunk)
                    })
            elif section["size"] >= self.min_section_size:
                constrained_sections.append(section)
            # Skip sections that are too small
                
        return constrained_sections

    def _enhance_with_semantic_analysis(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance sections with semantic analysis."""
        for section in sections:
            # Simple semantic classification
            content = section["content"].lower()
            if any(keyword in content for keyword in ["class", "function", "def", "import"]):
                section["semantic_type"] = "code"
            elif any(keyword in content for keyword in ["# ", "## ", "### "]):
                section["semantic_type"] = "documentation"
            else:
                section["semantic_type"] = "text"
                
        return sections

    def _preserve_document_hierarchy(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preserve document hierarchy in sections."""
        hierarchy_level = 0
        
        for section in sections:
            if section["type"] == "header":
                # Determine hierarchy level from markdown headers
                header_match = re.match(r'^(#{1,6})', section["content"])
                if header_match:
                    hierarchy_level = len(header_match.group(1))
                    
            section["hierarchy_level"] = hierarchy_level
            
        return sections

    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate content complexity score."""
        # Simple complexity metrics
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))
        avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
        
        # Normalize to 0-1 scale
        complexity = min(1.0, (unique_words / max(word_count, 1)) * (avg_word_length / 10))
        return complexity

    def _categorize_content_size(self, size: int) -> str:
        """Categorize content by size."""
        if size <= self.size_thresholds["small"]:
            return "small"
        elif size <= self.size_thresholds["medium"]:
            return "medium"
        else:
            return "large"

    def _analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure."""
        lines = content.split("\n")
        return {
            "line_count": len(lines),
            "paragraph_count": len([line for line in lines if line.strip()]),
            "has_headers": bool(re.search(r'^#{1,6}\s+', content, re.MULTILINE)),
            "has_code_blocks": bool(re.search(r'```', content)),
            "has_lists": bool(re.search(r'^\s*[-*+]\s+', content, re.MULTILINE))
        }

    def _generate_granularity_recommendations(
        self,
        complexity_score: float,
        size_category: str,
        structure_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate granularity optimization recommendations."""
        recommendations = []
        
        if complexity_score > self.complexity_thresholds["high"]:
            recommendations.append("Consider breaking down complex content into smaller sections")
            
        if size_category == "large":
            recommendations.append("Content is large - consider sectioning for better performance")
            
        if structure_analysis["has_headers"] and not structure_analysis["has_code_blocks"]:
            recommendations.append("Well-structured document - current granularity is appropriate")
            
        if not recommendations:
            recommendations.append("Content granularity is optimal")
            
        return recommendations

    def _remove_duplicate_content(self, new_content: str, existing_content: str) -> str:
        """Remove duplicate content using simple similarity check."""
        if not existing_content:
            return new_content
            
        # Simple duplicate detection - can be enhanced
        similarity = difflib.SequenceMatcher(None, new_content, existing_content).ratio()
        if similarity > 0.8:  # 80% similarity threshold
            return ""  # Skip duplicate content
            
        return new_content