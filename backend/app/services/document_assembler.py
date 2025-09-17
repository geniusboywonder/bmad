"""
Document Assembler Service for BMAD Core Template System

This module implements intelligent document assembly from multiple artifacts,
including content merging, deduplication, and structured document generation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import structlog
import json
import re
from collections import defaultdict
import difflib

from .artifact_service import ArtifactService
from .document_sectioner import DocumentSectioner

logger = structlog.get_logger(__name__)


class DocumentAssembler:
    """
    Service for intelligent document assembly and content integration.

    This service provides comprehensive document assembly capabilities including:
    - Multi-artifact content merging and deduplication
    - Intelligent section ordering and organization
    - Cross-reference resolution and linking
    - Content conflict detection and resolution
    - Structured document generation with metadata
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the document assembler.

        Args:
            config: Configuration dictionary with assembly parameters
        """
        self.enable_deduplication = config.get("enable_deduplication", True)
        self.enable_conflict_resolution = config.get("enable_conflict_resolution", True)
        self.max_merge_conflicts = config.get("max_merge_conflicts", 10)
        self.preserve_original_metadata = config.get("preserve_original_metadata", True)
        self.generate_toc = config.get("generate_toc", True)

        # Initialize sub-services
        self.artifact_service = ArtifactService(config)
        self.document_sectioner = DocumentSectioner(config)

        logger.info("Document assembler initialized",
                   deduplication=self.enable_deduplication,
                   conflict_resolution=self.enable_conflict_resolution)

    def assemble_document(
        self,
        artifacts: List[Dict[str, Any]],
        assembly_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assemble a document from multiple artifacts.

        Args:
            artifacts: List of artifacts to assemble
            assembly_config: Configuration for assembly process

        Returns:
            Assembled document with metadata
        """
        if not artifacts:
            return self._create_empty_document()

        # Validate artifacts
        valid_artifacts = self._validate_artifacts(artifacts)
        if not valid_artifacts:
            return self._create_empty_document()

        # Extract and organize content
        content_sections = self._extract_content_sections(valid_artifacts)

        # Deduplicate content if enabled
        if self.enable_deduplication:
            content_sections = self._deduplicate_content(content_sections)

        # Resolve conflicts if enabled
        if self.enable_conflict_resolution:
            content_sections = self._resolve_content_conflicts(content_sections)

        # Organize sections
        organized_sections = self._organize_sections(content_sections, assembly_config)

        # Generate table of contents if enabled
        toc = self._generate_table_of_contents(organized_sections) if self.generate_toc else None

        # Assemble final document
        assembled_content = self._assemble_final_content(organized_sections, assembly_config)

        # Generate metadata
        metadata = self._generate_assembly_metadata(valid_artifacts, assembly_config)

        document = {
            "content": assembled_content,
            "sections": organized_sections,
            "table_of_contents": toc,
            "metadata": metadata,
            "assembly_timestamp": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(valid_artifacts),
            "total_sections": len(organized_sections)
        }

        logger.info("Document assembled",
                   artifacts_used=len(valid_artifacts),
                   sections_created=len(organized_sections),
                   content_length=len(assembled_content))

        return document

    def merge_documents(
        self,
        documents: List[Dict[str, Any]],
        merge_strategy: str = "append"
    ) -> Dict[str, Any]:
        """
        Merge multiple documents into a single document.

        Args:
            documents: List of documents to merge
            merge_strategy: Strategy for merging (append, interleave, consolidate)

        Returns:
            Merged document
        """
        if not documents:
            return self._create_empty_document()

        if len(documents) == 1:
            return documents[0]

        # Extract all sections from documents
        all_sections = []
        for doc in documents:
            sections = doc.get("sections", [])
            all_sections.extend(sections)

        # Apply merge strategy
        if merge_strategy == "append":
            merged_sections = all_sections
        elif merge_strategy == "interleave":
            merged_sections = self._interleave_sections(all_sections)
        elif merge_strategy == "consolidate":
            merged_sections = self._consolidate_sections(all_sections)
        else:
            merged_sections = all_sections

        # Deduplicate if enabled
        if self.enable_deduplication:
            merged_sections = self._deduplicate_content(merged_sections)

        # Assemble final content
        assembly_config = {"format": "markdown", "include_metadata": True}
        assembled_content = self._assemble_final_content(merged_sections, assembly_config)

        # Generate merged metadata
        merged_metadata = self._generate_merged_metadata(documents)

        merged_document = {
            "content": assembled_content,
            "sections": merged_sections,
            "table_of_contents": self._generate_table_of_contents(merged_sections) if self.generate_toc else None,
            "metadata": merged_metadata,
            "merge_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_documents": len(documents),
            "total_sections": len(merged_sections)
        }

        logger.info("Documents merged",
                   source_count=len(documents),
                   merged_sections=len(merged_sections),
                   strategy=merge_strategy)

        return merged_document

    def detect_content_conflicts(
        self,
        artifacts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between artifacts.

        Args:
            artifacts: List of artifacts to check for conflicts

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Check for duplicate sections
        section_titles = defaultdict(list)
        for artifact in artifacts:
            sections = artifact.get("sections", [])
            for section in sections:
                title = section.get("title", "").lower().strip()
                if title:
                    section_titles[title].append({
                        "artifact_id": artifact.get("id"),
                        "section": section
                    })

        # Identify conflicts
        for title, sections in section_titles.items():
            if len(sections) > 1:
                conflicts.append({
                    "type": "duplicate_section",
                    "title": title,
                    "occurrences": len(sections),
                    "affected_artifacts": [s["artifact_id"] for s in sections],
                    "severity": "medium",
                    "resolution_suggestion": "merge_similar_sections"
                })

        # Check for contradictory information
        content_conflicts = self._detect_content_contradictions(artifacts)
        conflicts.extend(content_conflicts)

        logger.info("Content conflicts detected",
                   total_conflicts=len(conflicts),
                   duplicate_sections=len([c for c in conflicts if c["type"] == "duplicate_section"]))

        return conflicts

    def generate_document_outline(
        self,
        artifacts: List[Dict[str, Any]],
        outline_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a document outline from artifacts.

        Args:
            artifacts: List of artifacts to analyze
            outline_config: Configuration for outline generation

        Returns:
            Generated document outline
        """
        # Extract all sections
        all_sections = []
        for artifact in artifacts:
            sections = artifact.get("sections", [])
            for section in sections:
                section["source_artifact"] = artifact.get("id")
                all_sections.append(section)

        # Organize by hierarchy
        hierarchy = self._build_section_hierarchy(all_sections)

        # Generate outline
        outline = self._generate_outline_from_hierarchy(hierarchy, outline_config)

        # Add metadata
        outline_metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_artifacts": len(artifacts),
            "total_sections": len(all_sections),
            "max_depth": self._calculate_max_depth(hierarchy),
            "outline_format": outline_config.get("format", "markdown")
        }

        result = {
            "outline": outline,
            "hierarchy": hierarchy,
            "metadata": outline_metadata
        }

        logger.info("Document outline generated",
                   sections_processed=len(all_sections),
                   max_depth=outline_metadata["max_depth"])

        return result

    def _validate_artifacts(self, artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate artifacts for assembly."""
        valid_artifacts = []

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                logger.warning("Invalid artifact format", artifact_type=type(artifact))
                continue

            if not artifact.get("content"):
                logger.warning("Artifact missing content", artifact_id=artifact.get("id"))
                continue

            valid_artifacts.append(artifact)

        return valid_artifacts

    def _extract_content_sections(self, artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract content sections from artifacts."""
        all_sections = []

        for artifact in artifacts:
            artifact_id = artifact.get("id", "unknown")
            content = artifact.get("content", "")
            sections = artifact.get("sections", [])

            if sections:
                # Use existing sections
                for section in sections:
                    section_copy = section.copy()
                    section_copy["source_artifact"] = artifact_id
                    all_sections.append(section_copy)
            else:
                # Section the content
                try:
                    artifact_sections = self.document_sectioner.section_document(content)
                    for section in artifact_sections:
                        section["source_artifact"] = artifact_id
                        all_sections.append(section)
                except Exception as e:
                    logger.error("Failed to section artifact content",
                               artifact_id=artifact_id,
                               error=str(e))
                    # Create a single section with the entire content
                    all_sections.append({
                        "title": f"Content from {artifact_id}",
                        "content": content,
                        "level": 1,
                        "source_artifact": artifact_id
                    })

        return all_sections

    def _deduplicate_content(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate content sections."""
        if not sections:
            return sections

        deduplicated = []
        seen_content = set()

        for section in sections:
            content = section.get("content", "").strip().lower()

            # Create a simple hash of the content for comparison
            content_hash = hash(content)

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(section)
            else:
                logger.debug("Duplicate section removed",
                           title=section.get("title"),
                           source=section.get("source_artifact"))

        logger.info("Content deduplication completed",
                   original_sections=len(sections),
                   deduplicated_sections=len(deduplicated))

        return deduplicated

    def _resolve_content_conflicts(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts between content sections."""
        if not sections:
            return sections

        resolved_sections = []
        conflict_count = 0

        # Group sections by title
        sections_by_title = defaultdict(list)
        for section in sections:
            title = section.get("title", "").lower().strip()
            if title:
                sections_by_title[title].append(section)

        for title, title_sections in sections_by_title.items():
            if len(title_sections) == 1:
                resolved_sections.extend(title_sections)
            else:
                # Resolve conflict by merging similar sections
                merged_section = self._merge_similar_sections(title_sections)
                resolved_sections.append(merged_section)
                conflict_count += 1

        if conflict_count > 0:
            logger.info("Content conflicts resolved",
                       conflicts_found=conflict_count,
                       sections_after_resolution=len(resolved_sections))

        return resolved_sections

    def _organize_sections(
        self,
        sections: List[Dict[str, Any]],
        assembly_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Organize sections according to assembly configuration."""
        if not sections:
            return sections

        organization_strategy = assembly_config.get("organization", "by_level")

        if organization_strategy == "by_level":
            # Sort by level, then by title
            organized = sorted(sections, key=lambda x: (x.get("level", 1), x.get("title", "")))
        elif organization_strategy == "alphabetical":
            # Sort alphabetically by title
            organized = sorted(sections, key=lambda x: x.get("title", "").lower())
        elif organization_strategy == "by_source":
            # Group by source artifact
            organized = sorted(sections, key=lambda x: x.get("source_artifact", ""))
        else:
            # Keep original order
            organized = sections.copy()

        return organized

    def _assemble_final_content(
        self,
        sections: List[Dict[str, Any]],
        assembly_config: Dict[str, Any]
    ) -> str:
        """Assemble final document content from sections."""
        if not sections:
            return ""

        format_type = assembly_config.get("format", "markdown")
        include_metadata = assembly_config.get("include_metadata", False)

        assembled_parts = []

        for i, section in enumerate(sections):
            section_content = []

            # Add section header
            title = section.get("title", f"Section {i + 1}")
            level = section.get("level", 1)

            if format_type == "markdown":
                header = "#" * level + " " + title
                section_content.append(header)
                section_content.append("")  # Empty line after header
            else:
                section_content.append(title.upper())
                section_content.append("-" * len(title))

            # Add section content
            content = section.get("content", "")
            if content:
                section_content.append(content)

            # Add metadata if requested
            if include_metadata:
                metadata = self._extract_section_metadata(section)
                if metadata:
                    section_content.append("")
                    section_content.append("**Metadata:**")
                    for key, value in metadata.items():
                        section_content.append(f"- {key}: {value}")

            # Join section parts
            section_text = "\n".join(section_content)
            assembled_parts.append(section_text)

            # Add separator between sections
            if i < len(sections) - 1:
                assembled_parts.append("\n---\n")

        return "\n".join(assembled_parts)

    def _generate_table_of_contents(self, sections: List[Dict[str, Any]]) -> str:
        """Generate table of contents from sections."""
        if not sections:
            return ""

        toc_lines = ["# Table of Contents\n"]

        for section in sections:
            title = section.get("title", "Untitled")
            level = section.get("level", 1)

            # Create indentation based on level
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- {title}")

        return "\n".join(toc_lines)

    def _generate_assembly_metadata(
        self,
        artifacts: List[Dict[str, Any]],
        assembly_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate metadata for the assembled document."""
        total_content_length = sum(len(str(a.get("content", ""))) for a in artifacts)
        total_sections = sum(len(a.get("sections", [])) for a in artifacts)

        return {
            "assembly_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_artifacts": len(artifacts),
            "total_content_length": total_content_length,
            "total_source_sections": total_sections,
            "assembly_config": assembly_config,
            "assembler_version": "1.0.0",
            "deduplication_applied": self.enable_deduplication,
            "conflict_resolution_applied": self.enable_conflict_resolution
        }

    def _create_empty_document(self) -> Dict[str, Any]:
        """Create an empty document structure."""
        return {
            "content": "",
            "sections": [],
            "table_of_contents": None,
            "metadata": {
                "assembly_timestamp": datetime.now(timezone.utc).isoformat(),
                "source_artifacts": 0,
                "total_content_length": 0,
                "total_source_sections": 0
            },
            "artifact_count": 0,
            "total_sections": 0
        }

    def _interleave_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interleave sections from different sources."""
        # Group by source
        sections_by_source = defaultdict(list)
        for section in sections:
            source = section.get("source_artifact", "unknown")
            sections_by_source[source].append(section)

        # Interleave sections round-robin style
        interleaved = []
        max_sections = max(len(sections) for sections in sections_by_source.values())

        for i in range(max_sections):
            for source_sections in sections_by_source.values():
                if i < len(source_sections):
                    interleaved.append(source_sections[i])

        return interleaved

    def _consolidate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate similar sections."""
        # Group by title similarity
        consolidated_groups = defaultdict(list)

        for section in sections:
            title = section.get("title", "").lower().strip()
            # Find similar titles
            found_group = False
            for group_title in consolidated_groups:
                if self._titles_similar(title, group_title):
                    consolidated_groups[group_title].append(section)
                    found_group = True
                    break

            if not found_group:
                consolidated_groups[title].append(section)

        # Merge sections in each group
        consolidated = []
        for group_sections in consolidated_groups.values():
            if len(group_sections) == 1:
                consolidated.extend(group_sections)
            else:
                merged = self._merge_similar_sections(group_sections)
                consolidated.append(merged)

        return consolidated

    def _detect_content_contradictions(self, artifacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect contradictory information between artifacts."""
        contradictions = []

        # Simple contradiction detection based on keywords
        contradiction_patterns = [
            (r'\b(required|mandatory)\b', r'\b(optional|not required)\b'),
            (r'\b(enabled|active)\b', r'\b(disabled|inactive)\b'),
            (r'\b(supported|allowed)\b', r'\b(not supported|forbidden)\b')
        ]

        for i, artifact1 in enumerate(artifacts):
            content1 = str(artifact1.get("content", "")).lower()

            for j, artifact2 in enumerate(artifacts[i+1:], i+1):
                content2 = str(artifact2.get("content", "")).lower()

                for pattern1, pattern2 in contradiction_patterns:
                    if (re.search(pattern1, content1) and re.search(pattern2, content2)) or \
                       (re.search(pattern1, content2) and re.search(pattern2, content1)):
                        contradictions.append({
                            "type": "content_contradiction",
                            "pattern": f"{pattern1} vs {pattern2}",
                            "artifact1_id": artifact1.get("id"),
                            "artifact2_id": artifact2.get("id"),
                            "severity": "high",
                            "resolution_suggestion": "manual_review_required"
                        })

        return contradictions

    def _build_section_hierarchy(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical representation of sections."""
        return self.document_sectioner.create_section_hierarchy(sections)

    def _generate_outline_from_hierarchy(
        self,
        hierarchy: Dict[str, Any],
        outline_config: Dict[str, Any]
    ) -> str:
        """Generate outline from section hierarchy."""
        format_type = outline_config.get("format", "markdown")

        def build_outline(node, level=0):
            if isinstance(node, dict) and "section" in node:
                section = node["section"]
                title = section.get("title", "Untitled")
                indent = "  " * level

                outline_parts = [f"{indent}- {title}"]

                if "children" in node and node["children"]:
                    for child in node["children"]:
                        outline_parts.extend(build_outline(child, level + 1))

                return outline_parts
            return []

        root_sections = hierarchy.get("root", [])
        outline_lines = []

        for section_node in root_sections:
            outline_lines.extend(build_outline(section_node))

        return "\n".join(outline_lines)

    def _calculate_max_depth(self, hierarchy: Dict[str, Any]) -> int:
        """Calculate maximum depth of section hierarchy."""
        def get_depth(node):
            if isinstance(node, dict) and "children" in node:
                if not node["children"]:
                    return 1
                return 1 + max(get_depth(child) for child in node["children"])
            return 1

        root_sections = hierarchy.get("root", [])
        if not root_sections:
            return 0

        return max(get_depth(section) for section in root_sections)

    def _merge_similar_sections(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge similar sections."""
        if not sections:
            return {}

        # Use the first section as base
        merged = sections[0].copy()

        # Combine content
        all_content = [s.get("content", "") for s in sections]
        merged["content"] = "\n\n".join(filter(None, all_content))

        # Update metadata
        merged["source_artifacts"] = [s.get("source_artifact") for s in sections]
        merged["merged_sections"] = len(sections)
        merged["merge_timestamp"] = datetime.now(timezone.utc).isoformat()

        return merged

    def _titles_similar(self, title1: str, title2: str) -> bool:
        """Check if two titles are similar."""
        if not title1 or not title2:
            return False

        # Simple similarity check using difflib
        similarity = difflib.SequenceMatcher(None, title1, title2).ratio()
        return similarity > 0.8

    def _extract_section_metadata(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from a section."""
        return self.document_sectioner.extract_section_metadata(section)

    def _generate_merged_metadata(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate metadata for merged documents."""
        total_artifacts = sum(doc.get("artifact_count", 0) for doc in documents)
        total_sections = sum(doc.get("total_sections", 0) for doc in documents)

        return {
            "merge_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_documents": len(documents),
            "total_source_artifacts": total_artifacts,
            "total_source_sections": total_sections,
            "merge_strategy": "consolidate",
            "assembler_version": "1.0.0"
        }
