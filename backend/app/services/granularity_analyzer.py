"""
Granularity Analyzer Service for BMAD Core Template System

This module implements intelligent granularity analysis for context artifacts,
including complexity assessment, optimal granularity recommendations, and
performance optimization suggestions.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import structlog
import json
import re
from collections import Counter

logger = structlog.get_logger(__name__)


class GranularityAnalyzer:
    """
    Service for analyzing and optimizing artifact granularity.

    This service provides intelligent analysis of content complexity,
    optimal granularity recommendations, and performance optimization
    for context storage and retrieval.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the granularity analyzer.

        Args:
            config: Configuration dictionary with analysis parameters
        """
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

        logger.info("Granularity analyzer initialized",
                   analysis_depth=self.analysis_depth,
                   ml_enabled=self.enable_ml_classification)

    def analyze_complexity(self, content: str) -> Dict[str, Any]:
        """
        Analyze the complexity of content for granularity decisions.

        Args:
            content: Text content to analyze

        Returns:
            Complexity analysis results
        """
        if not content:
            return {"score": 0.0, "level": "low", "factors": []}

        # Basic complexity metrics
        word_count = len(content.split())
        sentence_count = len(re.split(r'[.!?]+', content))
        avg_words_per_sentence = word_count / max(sentence_count, 1)

        # Vocabulary diversity
        words = re.findall(r'\b\w+\b', content.lower())
        unique_words = len(set(words))
        vocabulary_ratio = unique_words / max(len(words), 1)

        # Technical complexity indicators
        technical_terms = self._count_technical_terms(content)
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        structural_elements = self._count_structural_elements(content)

        # Calculate complexity score
        complexity_factors = {
            "word_count": min(word_count / 1000, 1.0),  # Normalize to 0-1
            "vocabulary_diversity": vocabulary_ratio,
            "sentence_complexity": min(avg_words_per_sentence / 20, 1.0),
            "technical_density": min(technical_terms / 50, 1.0),
            "code_density": min(code_blocks / 5, 1.0),
            "structural_complexity": min(structural_elements / 10, 1.0)
        }

        # Weighted complexity score
        weights = {
            "word_count": 0.1,
            "vocabulary_diversity": 0.2,
            "sentence_complexity": 0.15,
            "technical_density": 0.25,
            "code_density": 0.15,
            "structural_complexity": 0.15
        }

        complexity_score = sum(
            factor_value * weights[factor_name]
            for factor_name, factor_value in complexity_factors.items()
        )

        # Determine complexity level
        if complexity_score < self.complexity_thresholds["low"]:
            level = "low"
        elif complexity_score < self.complexity_thresholds["medium"]:
            level = "medium"
        else:
            level = "high"

        return {
            "score": complexity_score,
            "level": level,
            "factors": complexity_factors,
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "unique_words": unique_words,
                "technical_terms": technical_terms,
                "code_blocks": code_blocks,
                "structural_elements": structural_elements
            }
        }

    def recommend_granularity(self, content_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend optimal granularity strategy for content.

        Args:
            content_profile: Content profile with size, complexity, etc.

        Returns:
            Granularity recommendation
        """
        size = content_profile.get("size", 0)
        complexity_score = content_profile.get("complexity_score", 0.0)
        access_pattern = content_profile.get("access_pattern", "unknown")
        update_frequency = content_profile.get("update_frequency", "unknown")

        # Size-based recommendation
        if size < self.size_thresholds["small"]:
            base_strategy = "atomic"
            confidence = 0.9
        elif size < self.size_thresholds["medium"]:
            base_strategy = "sectioned" if complexity_score > 0.4 else "atomic"
            confidence = 0.8
        else:
            base_strategy = "sectioned"
            confidence = 0.95

        # Complexity adjustment
        if complexity_score > self.complexity_thresholds["high"]:
            if base_strategy == "atomic":
                base_strategy = "sectioned"
            confidence = min(confidence + 0.1, 1.0)
        elif complexity_score < self.complexity_thresholds["low"]:
            if base_strategy == "sectioned" and size < self.size_thresholds["medium"]:
                base_strategy = "atomic"
            confidence = min(confidence + 0.05, 1.0)

        # Access pattern adjustment
        if access_pattern == "frequent_small_reads":
            if base_strategy == "sectioned":
                base_strategy = "conceptual"
            confidence = min(confidence + 0.1, 1.0)
        elif access_pattern == "bulk_processing":
            confidence = min(confidence + 0.05, 1.0)

        # Update frequency adjustment
        if update_frequency == "high":
            if base_strategy == "sectioned":
                base_strategy = "atomic"
            confidence = min(confidence - 0.1, 1.0)

        return {
            "strategy": base_strategy,
            "confidence": confidence,
            "reasoning": {
                "size_factor": self._get_size_factor(size),
                "complexity_factor": self._get_complexity_factor(complexity_score),
                "access_pattern": access_pattern,
                "update_frequency": update_frequency
            }
        }

    def detect_section_boundaries(self, document: str) -> List[Dict[str, Any]]:
        """
        Detect section boundaries in a document for intelligent sectioning.

        Args:
            document: Document content to analyze

        Returns:
            List of detected section boundaries
        """
        boundaries = []

        # Split document into lines
        lines = document.split('\n')
        current_position = 0

        for i, line in enumerate(lines):
            line_start = current_position
            line_end = current_position + len(line) + 1  # +1 for newline

            # Detect section headers using various patterns
            if self._is_section_header(line.strip()):
                # Look ahead to find section end
                section_end = self._find_section_end(lines, i + 1, current_position + len(line) + 1)

                boundaries.append({
                    "title": line.strip(),
                    "start_position": line_start,
                    "end_position": section_end,
                    "level": self._get_header_level(line.strip()),
                    "content_length": section_end - line_start,
                    "line_number": i + 1
                })

            current_position = line_end

        # Sort boundaries by position
        boundaries.sort(key=lambda x: x["start_position"])

        logger.info("Section boundaries detected",
                   document_length=len(document),
                   boundaries_found=len(boundaries))

        return boundaries

    def analyze_concept_relationships(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze relationships between concepts for conceptual granularity.

        Args:
            concepts: List of concepts to analyze

        Returns:
            List of concept relationships
        """
        relationships = []

        # Create concept lookup
        concept_lookup = {concept["name"]: concept for concept in concepts}

        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts[i+1:], i+1):
                relationship = self._analyze_concept_pair(concept1, concept2)

                if relationship:
                    relationships.append({
                        "source": concept1["name"],
                        "target": concept2["name"],
                        "type": relationship["type"],
                        "strength": relationship["strength"],
                        "context": relationship.get("context", "")
                    })

        # Sort by strength
        relationships.sort(key=lambda x: x["strength"], reverse=True)

        logger.info("Concept relationships analyzed",
                   concepts_count=len(concepts),
                   relationships_found=len(relationships))

        return relationships

    def recommend_optimizations(self, content_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recommend performance optimizations based on content profile.

        Args:
            content_profile: Content profile analysis

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        size = content_profile.get("size", 0)
        complexity = content_profile.get("complexity", 0.0)
        access_pattern = content_profile.get("access_pattern", "unknown")

        # Size-based optimizations
        if size > self.size_thresholds["large"]:
            recommendations.append({
                "strategy": "compression",
                "expected_benefit": "Reduce storage by 50-70%",
                "implementation_effort": "low",
                "priority": "high"
            })

        # Complexity-based optimizations
        if complexity > self.complexity_thresholds["high"]:
            recommendations.append({
                "strategy": "sectioning",
                "expected_benefit": "Improve retrieval speed by 60-80%",
                "implementation_effort": "medium",
                "priority": "high"
            })

        # Access pattern optimizations
        if access_pattern == "frequent_small_reads":
            recommendations.append({
                "strategy": "conceptual_indexing",
                "expected_benefit": "Reduce query time by 70-90%",
                "implementation_effort": "high",
                "priority": "medium"
            })
        elif access_pattern == "bulk_processing":
            recommendations.append({
                "strategy": "batch_processing",
                "expected_benefit": "Improve throughput by 40-60%",
                "implementation_effort": "low",
                "priority": "low"
            })

        # Cache recommendations
        if content_profile.get("update_frequency") == "low":
            recommendations.append({
                "strategy": "aggressive_caching",
                "expected_benefit": "Reduce response time by 80-95%",
                "implementation_effort": "low",
                "priority": "high"
            })

        return recommendations

    def _count_technical_terms(self, content: str) -> int:
        """Count technical terms in content."""
        technical_patterns = [
            r'\b(API|REST|JSON|XML|HTTP|HTTPS|SQL|NoSQL|Docker|Kubernetes)\b',
            r'\b(algorithm|function|method|class|object|interface)\b',
            r'\b(database|server|client|endpoint|service|microservice)\b',
            r'\b(security|authentication|authorization|encryption)\b'
        ]

        count = 0
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            count += len(matches)

        return count

    def _count_structural_elements(self, content: str) -> int:
        """Count structural elements in content."""
        structural_patterns = [
            r'^#{1,6}\s+',  # Headers
            r'^\d+\.',      # Numbered lists
            r'^\s*[-*+]\s+', # Bullet lists
            r'^\s*\d+\)',   # Numbered lists alternative
            r'```',         # Code blocks
            r'\[.*?\]\(.*?\)', # Links
            r'!\[.*?\]\(.*?\)', # Images
            r'^\s*\|.*\|\s*$',  # Tables
        ]

        count = 0
        lines = content.split('\n')

        for line in lines:
            for pattern in structural_patterns:
                if re.search(pattern, line):
                    count += 1
                    break  # Count each line only once

        return count

    def _get_size_factor(self, size: int) -> str:
        """Get size factor description."""
        if size < self.size_thresholds["small"]:
            return "small"
        elif size < self.size_thresholds["medium"]:
            return "medium"
        else:
            return "large"

    def _get_complexity_factor(self, complexity: float) -> str:
        """Get complexity factor description."""
        if complexity < self.complexity_thresholds["low"]:
            return "low"
        elif complexity < self.complexity_thresholds["medium"]:
            return "medium"
        else:
            return "high"

    def _is_section_header(self, line: str) -> bool:
        """Check if a line is a section header."""
        # Markdown headers
        if re.match(r'^#{1,6}\s+', line):
            return True

        # Common section header patterns
        header_patterns = [
            r'^(Chapter|Section|Part)\s+\d+',
            r'^(Introduction|Background|Methodology|Results|Conclusion|Summary)',
            r'^(Overview|Architecture|Design|Implementation|Testing|Deployment)',
            r'^[A-Z][^.!?]*:$',  # Title case followed by colon
        ]

        for pattern in header_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        return False

    def _find_section_end(self, lines: List[str], start_index: int, start_position: int) -> int:
        """Find the end position of a section."""
        position = start_position

        for i in range(start_index, len(lines)):
            line = lines[i]

            # Check if this is the start of a new section
            if self._is_section_header(line.strip()):
                return position

            position += len(line) + 1  # +1 for newline

        return position  # End of document

    def _get_header_level(self, header: str) -> int:
        """Get the level of a header (1-6 for markdown, 1 for others)."""
        match = re.match(r'^(#{1,6})', header)
        if match:
            return len(match.group(1))
        return 1

    def _analyze_concept_pair(self, concept1: Dict[str, Any], concept2: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze relationship between two concepts."""
        name1 = concept1["name"].lower()
        name2 = concept2["name"].lower()

        # Define relationship patterns
        relationship_patterns = {
            "depends_on": [
                ("authentication", "user"),
                ("database", "application"),
                ("api", "service"),
                ("security", "authentication"),
            ],
            "related_to": [
                ("user", "interface"),
                ("data", "database"),
                ("client", "server"),
                ("frontend", "backend"),
            ],
            "contains": [
                ("application", "service"),
                ("system", "component"),
                ("database", "table"),
            ]
        }

        # Check for direct relationships
        for rel_type, pairs in relationship_patterns.items():
            if (name1, name2) in pairs or (name2, name1) in pairs:
                return {
                    "type": rel_type,
                    "strength": 0.8,
                    "context": f"Direct {rel_type} relationship"
                }

        # Check for semantic similarity
        similarity = self._calculate_semantic_similarity(concept1, concept2)
        if similarity > 0.6:
            return {
                "type": "related_to",
                "strength": similarity,
                "context": "Semantic similarity"
            }

        return None

    def _calculate_semantic_similarity(self, concept1: Dict[str, Any], concept2: Dict[str, Any]) -> float:
        """Calculate semantic similarity between concepts."""
        # Simple semantic similarity based on shared keywords
        text1 = f"{concept1['name']} {concept1.get('description', '')}".lower()
        text2 = f"{concept2['name']} {concept2.get('description', '')}".lower()

        words1 = set(re.findall(r'\b\w+\b', text1))
        words2 = set(re.findall(r'\b\w+\b', text2))

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)
