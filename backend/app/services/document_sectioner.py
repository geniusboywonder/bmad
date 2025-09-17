"""
Document Sectioner Service for BMAD Core Template System

This module implements intelligent document sectioning for large artifacts,
including automatic section detection, content segmentation, and hierarchical
organization of document components.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import structlog
import json
import re
from collections import defaultdict

logger = structlog.get_logger(__name__)


class DocumentSectioner:
    """
    Service for intelligent document sectioning and content segmentation.

    This service provides automatic detection of document structure,
    section boundary identification, and hierarchical content organization
    for optimal storage and retrieval of large documents.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the document sectioner.

        Args:
            config: Configuration dictionary with sectioning parameters
        """
        self.max_section_size = config.get("max_section_size", 8192)  # 8KB
        self.min_section_size = config.get("min_section_size", 512)   # 512B
        self.enable_semantic_sectioning = config.get("enable_semantic_sectioning", True)
        self.preserve_hierarchy = config.get("preserve_hierarchy", True)
        self.supported_formats = config.get("supported_formats", [
            "markdown", "text", "json", "yaml", "html"
        ])

        logger.info("Document sectioner initialized",
                   max_section_size=self.max_section_size,
                   semantic_sectioning=self.enable_semantic_sectioning)

    def section_document(self, content: str, format_type: str = "markdown") -> List[Dict[str, Any]]:
        """
        Section a document into logical components.

        Args:
            content: Document content to section
            format_type: Format of the document (markdown, text, etc.)

        Returns:
            List of document sections
        """
        if not content:
            return []

        if format_type == "markdown":
            sections = self._section_markdown_document(content)
        elif format_type == "text":
            sections = self._section_text_document(content)
        elif format_type == "json":
            sections = self._section_json_document(content)
        else:
            sections = self._section_generic_document(content)

        # Validate and optimize sections
        sections = self._validate_sections(sections)
        sections = self._optimize_section_sizes(sections)

        logger.info("Document sectioned",
                   original_length=len(content),
                   sections_created=len(sections),
                   format_type=format_type)

        return sections

    def _section_markdown_document(self, content: str) -> List[Dict[str, Any]]:
        """Section a markdown document."""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        current_position = 0

        for i, line in enumerate(lines):
            line_start = current_position
            line_end = current_position + len(line) + 1

            # Check if this is a header
            if self._is_markdown_header(line):
                # Save previous section if it exists
                if current_section:
                    current_section["content"] = '\n'.join(current_content).strip()
                    current_section["end_position"] = line_start
                    current_section["content_length"] = line_start - current_section["start_position"]
                    sections.append(current_section)

                # Start new section
                header_level = self._get_markdown_header_level(line)
                header_text = self._extract_markdown_header_text(line)

                current_section = {
                    "title": header_text,
                    "level": header_level,
                    "start_position": line_start,
                    "content": "",
                    "metadata": {
                        "format": "markdown",
                        "header_marker": "#" * header_level,
                        "line_number": i + 1
                    }
                }
                current_content = []

            elif current_section:
                current_content.append(line)

            current_position = line_end

        # Add final section
        if current_section:
            current_section["content"] = '\n'.join(current_content).strip()
            current_section["end_position"] = current_position
            current_section["content_length"] = current_position - current_section["start_position"]
            sections.append(current_section)

        return sections

    def _section_text_document(self, content: str) -> List[Dict[str, Any]]:
        """Section a plain text document."""
        sections = []

        # Split by common section delimiters
        section_delimiters = [
            r'^={3,}$',  # === separators
            r'^-{3,}$',  # --- separators
            r'^\*{3,}$', # *** separators
        ]

        parts = []
        current_part = []
        lines = content.split('\n')

        for line in lines:
            is_delimiter = False
            for pattern in section_delimiters:
                if re.match(pattern, line.strip()):
                    is_delimiter = True
                    break

            if is_delimiter and current_part:
                parts.append('\n'.join(current_part))
                current_part = []
            else:
                current_part.append(line)

        if current_part:
            parts.append('\n'.join(current_part))

        # Create sections from parts
        for i, part in enumerate(parts):
            if part.strip():  # Skip empty parts
                sections.append({
                    "title": f"Section {i + 1}",
                    "level": 1,
                    "start_position": sum(len(p) + 1 for p in parts[:i]),  # +1 for newlines
                    "end_position": sum(len(p) + 1 for p in parts[:i+1]),
                    "content": part.strip(),
                    "content_length": len(part),
                    "metadata": {
                        "format": "text",
                        "section_type": "auto_detected"
                    }
                })

        return sections

    def _section_json_document(self, content: str) -> List[Dict[str, Any]]:
        """Section a JSON document."""
        try:
            data = json.loads(content)
            sections = []

            def traverse_json(obj, path="", level=1):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if isinstance(value, (dict, list)):
                            # Create section for nested object/array
                            section_content = json.dumps(value, indent=2)
                            sections.append({
                                "title": key,
                                "level": level,
                                "start_position": 0,  # JSON sections don't have linear positions
                                "end_position": len(section_content),
                                "content": section_content,
                                "content_length": len(section_content),
                                "metadata": {
                                    "format": "json",
                                    "json_path": current_path,
                                    "data_type": type(value).__name__
                                }
                            })
                            traverse_json(value, current_path, level + 1)
                elif isinstance(obj, list) and len(obj) > 0:
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]"
                        if isinstance(item, (dict, list)):
                            section_content = json.dumps(item, indent=2)
                            sections.append({
                                "title": f"Item {i}",
                                "level": level,
                                "start_position": 0,
                                "end_position": len(section_content),
                                "content": section_content,
                                "content_length": len(section_content),
                                "metadata": {
                                    "format": "json",
                                    "json_path": current_path,
                                    "data_type": type(item).__name__
                                }
                            })

            traverse_json(data)
            return sections

        except json.JSONDecodeError:
            # Fall back to generic sectioning
            return self._section_generic_document(content)

    def _section_generic_document(self, content: str) -> List[Dict[str, Any]]:
        """Generic document sectioning for unsupported formats."""
        # Simple paragraph-based sectioning
        paragraphs = re.split(r'\n\s*\n', content)
        sections = []

        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                sections.append({
                    "title": f"Paragraph {i + 1}",
                    "level": 1,
                    "start_position": sum(len(p) + 2 for p in paragraphs[:i]),  # +2 for paragraph breaks
                    "end_position": sum(len(p) + 2 for p in paragraphs[:i+1]),
                    "content": paragraph.strip(),
                    "content_length": len(paragraph),
                    "metadata": {
                        "format": "generic",
                        "section_type": "paragraph"
                    }
                })

        return sections

    def _validate_sections(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean up sections."""
        validated_sections = []

        for section in sections:
            # Skip empty sections
            if not section.get("content", "").strip():
                continue

            # Ensure required fields
            validated_section = {
                "title": section.get("title", "Untitled Section"),
                "level": section.get("level", 1),
                "start_position": section.get("start_position", 0),
                "end_position": section.get("end_position", 0),
                "content": section.get("content", ""),
                "content_length": section.get("content_length", 0),
                "metadata": section.get("metadata", {})
            }

            # Validate position data
            if validated_section["start_position"] > validated_section["end_position"]:
                validated_section["end_position"] = validated_section["start_position"] + validated_section["content_length"]

            validated_sections.append(validated_section)

        return validated_sections

    def _optimize_section_sizes(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize section sizes for better granularity."""
        optimized_sections = []

        for section in sections:
            content_length = section["content_length"]

            # If section is too large, try to split it
            if content_length > self.max_section_size:
                split_sections = self._split_large_section(section)
                optimized_sections.extend(split_sections)
            # If section is too small, try to merge with adjacent sections
            elif content_length < self.min_section_size and optimized_sections:
                # Merge with previous section
                prev_section = optimized_sections[-1]
                merged_content = prev_section["content"] + "\n\n" + section["content"]
                prev_section["content"] = merged_content
                prev_section["content_length"] = len(merged_content)
                prev_section["end_position"] = section["end_position"]
            else:
                optimized_sections.append(section)

        return optimized_sections

    def _split_large_section(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a large section into smaller sections."""
        content = section["content"]
        content_length = len(content)

        if content_length <= self.max_section_size:
            return [section]

        # Try to split at natural boundaries
        split_sections = []
        remaining_content = content
        section_index = 1
        base_position = section["start_position"]

        while len(remaining_content) > self.max_section_size:
            # Find a good split point
            split_point = self._find_split_point(remaining_content, self.max_section_size)

            if split_point == 0:
                # Can't find a good split point, force split
                split_point = self.max_section_size

            section_content = remaining_content[:split_point].strip()
            split_sections.append({
                "title": f"{section['title']} (Part {section_index})",
                "level": section["level"],
                "start_position": base_position,
                "end_position": base_position + len(section_content),
                "content": section_content,
                "content_length": len(section_content),
                "metadata": {
                    **section.get("metadata", {}),
                    "split": True,
                    "part": section_index,
                    "original_title": section["title"]
                }
            })

            remaining_content = remaining_content[split_point:].strip()
            base_position += len(section_content) + 2  # +2 for \n\n
            section_index += 1

        # Add remaining content as final section
        if remaining_content:
            split_sections.append({
                "title": f"{section['title']} (Part {section_index})",
                "level": section["level"],
                "start_position": base_position,
                "end_position": base_position + len(remaining_content),
                "content": remaining_content,
                "content_length": len(remaining_content),
                "metadata": {
                    **section.get("metadata", {}),
                    "split": True,
                    "part": section_index,
                    "original_title": section["title"]
                }
            })

        return split_sections

    def _find_split_point(self, content: str, max_length: int) -> int:
        """Find the best point to split content."""
        if len(content) <= max_length:
            return len(content)

        # Look for paragraph breaks
        paragraphs = content[:max_length].split('\n\n')
        if len(paragraphs) > 1:
            # Use the end of the last complete paragraph
            split_content = '\n\n'.join(paragraphs[:-1])
            return len(split_content)

        # Look for sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', content[:max_length])
        if len(sentences) > 1:
            # Use the end of the last complete sentence
            split_content = ' '.join(sentences[:-1])
            return len(split_content)

        # Look for line breaks
        lines = content[:max_length].split('\n')
        if len(lines) > 1:
            # Use the end of the last complete line
            split_content = '\n'.join(lines[:-1])
            return len(split_content)

        # No good split point found
        return 0

    def _is_markdown_header(self, line: str) -> bool:
        """Check if a line is a markdown header."""
        return bool(re.match(r'^#{1,6}\s+', line.strip()))

    def _get_markdown_header_level(self, line: str) -> int:
        """Get the level of a markdown header."""
        match = re.match(r'^(#{1,6})', line.strip())
        return len(match.group(1)) if match else 1

    def _extract_markdown_header_text(self, line: str) -> str:
        """Extract the text from a markdown header."""
        match = re.match(r'^#{1,6}\s+(.+)', line.strip())
        return match.group(1).strip() if match else line.strip()

    def create_section_hierarchy(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a hierarchical representation of sections.

        Args:
            sections: List of sections to organize hierarchically

        Returns:
            Hierarchical section structure
        """
        if not sections:
            return {"root": [], "hierarchy": {}}

        # Sort sections by level and position
        sorted_sections = sorted(sections, key=lambda x: (x["level"], x["start_position"]))

        # Build hierarchy
        hierarchy = {"root": []}
        level_stacks = {1: hierarchy["root"]}

        for section in sorted_sections:
            level = section["level"]
            section_node = {
                "section": section,
                "children": []
            }

            # Ensure we have a stack for this level
            if level not in level_stacks:
                level_stacks[level] = []

            # Find parent level
            parent_level = level - 1
            if parent_level in level_stacks and level_stacks[parent_level]:
                # Add to parent's children
                level_stacks[parent_level][-1]["children"].append(section_node)
            else:
                # Add to root if no parent
                hierarchy["root"].append(section_node)

            # Update stack for this level
            level_stacks[level].append(section_node)

        return {
            "root": hierarchy["root"],
            "hierarchy": level_stacks,
            "total_sections": len(sections),
            "max_depth": max((s["level"] for s in sections), default=1)
        }

    def extract_section_metadata(self, section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a section.

        Args:
            section: Section to analyze

        Returns:
            Extracted metadata
        """
        content = section.get("content", "")
        metadata = section.get("metadata", {})

        # Extract basic statistics
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        char_count = len(content)

        # Extract keywords (simple frequency-based)
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] += 1

        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Detect content type
        content_type = "text"
        if re.search(r'```[\s\S]*?```', content):
            content_type = "code"
        elif re.search(r'^\s*[-*+]\s+', content, re.MULTILINE):
            content_type = "list"
        elif re.search(r'^\s*\d+\.?\s+', content, re.MULTILINE):
            content_type = "numbered_list"
        elif re.search(r'^\s*\|\s*.*\s*\|\s*$', content, re.MULTILINE):
            content_type = "table"

        extracted_metadata = {
            "word_count": word_count,
            "line_count": line_count,
            "char_count": char_count,
            "content_type": content_type,
            "top_keywords": top_keywords,
            "has_code": bool(re.search(r'```', content)),
            "has_links": bool(re.search(r'\[.*?\]\(.*?\)', content)),
            "has_images": bool(re.search(r'!\[.*?\]\(.*?\)', content)),
            "reading_time_minutes": max(1, word_count // 200)  # Rough estimate
        }

        # Merge with existing metadata
        metadata.update(extracted_metadata)

        return metadata

    def merge_similar_sections(self, sections: List[Dict[str, Any]], similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Merge sections that are very similar.

        Args:
            sections: List of sections to analyze
            similarity_threshold: Threshold for considering sections similar

        Returns:
            List of sections with similar ones merged
        """
        if len(sections) <= 1:
            return sections

        merged_sections = []

        for section in sections:
            merged = False

            # Check against existing merged sections
            for merged_section in merged_sections:
                similarity = self._calculate_section_similarity(section, merged_section)

                if similarity >= similarity_threshold:
                    # Merge sections
                    merged_content = merged_section["content"] + "\n\n" + section["content"]
                    merged_section["content"] = merged_content
                    merged_section["content_length"] = len(merged_content)
                    merged_section["end_position"] = section["end_position"]
                    merged_section["title"] = f"{merged_section['title']} + {section['title']}"

                    # Update metadata
                    merged_section["metadata"]["merged_sections"] = merged_section["metadata"].get("merged_sections", [])
                    merged_section["metadata"]["merged_sections"].append(section["title"])

                    merged = True
                    break

            if not merged:
                merged_sections.append(section.copy())

        logger.info("Similar sections merged",
                   original_count=len(sections),
                   merged_count=len(merged_sections),
                   similarity_threshold=similarity_threshold)

        return merged_sections

    def _calculate_section_similarity(self, section1: Dict[str, Any], section2: Dict[str, Any]) -> float:
        """Calculate similarity between two sections."""
        content1 = section1.get("content", "").lower()
        content2 = section2.get("content", "").lower()

        if not content1 or not content2:
            return 0.0

        # Simple Jaccard similarity based on words
        words1 = set(re.findall(r'\b\w+\b', content1))
        words2 = set(re.findall(r'\b\w+\b', content2))

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)
