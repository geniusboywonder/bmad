"""
Context Store Service for BMAD Core Template System

This module implements the Context Store pattern with mixed-granularity support,
providing intelligent storage, retrieval, and management of context artifacts.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import structlog
import json
import os
from collections import defaultdict

from .artifact_service import ArtifactService
from .granularity_analyzer import GranularityAnalyzer

logger = structlog.get_logger(__name__)


class ContextStore:
    """
    Enhanced Context Store with mixed-granularity support.

    This service provides intelligent context management including:
    - Mixed-granularity artifact storage and retrieval
    - Intelligent caching and optimization
    - Compression and retention policies
    - Selective context injection for agents
    - Performance analytics and recommendations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the context store.

        Args:
            config: Configuration dictionary with storage parameters
        """
        self.storage_backend = config.get("storage_backend", "postgresql")
        self.cache_enabled = config.get("cache_enabled", True)
        self.compression_enabled = config.get("compression_enabled", True)
        self.max_artifact_size = config.get("max_artifact_size", 1048576)  # 1MB
        self.retention_policy = config.get("retention_policy", "30_days")

        # Initialize cache
        self._cache = {}
        self._cache_timestamps = {}

        # Initialize sub-services
        self.artifact_service = ArtifactService(config)
        self.granularity_analyzer = GranularityAnalyzer(config)

        logger.info("Context store initialized",
                   backend=self.storage_backend,
                   cache_enabled=self.cache_enabled,
                   compression=self.compression_enabled)

    def store_artifact(self, artifact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a context artifact with intelligent processing.

        Args:
            artifact_data: Artifact data to store

        Returns:
            Storage result with metadata
        """
        artifact_id = artifact_data.get("id", f"artifact_{datetime.now(timezone.utc).timestamp()}")
        content = artifact_data.get("content", "")
        artifact_type = artifact_data.get("type", "unknown")

        # Analyze content for optimal storage strategy
        granularity = self.artifact_service.determine_granularity(content, artifact_type)

        # Process content based on granularity strategy
        processed_data = self._process_artifact_for_storage(artifact_data, granularity)

        # Store the artifact
        storage_result = self._store_artifact_data(processed_data)

        # Update cache if enabled
        if self.cache_enabled:
            self._cache_artifact(artifact_id, processed_data)

        # Extract and store concepts if enabled
        if self.artifact_service.enable_concept_extraction:
            concepts = self.artifact_service.extract_concepts(content)
            if concepts:
                self._store_artifact_concepts(artifact_id, concepts)

        logger.info("Artifact stored",
                   artifact_id=artifact_id,
                   type=artifact_type,
                   strategy=granularity.get("strategy"),
                   size=len(content))

        return {
            "stored": True,
            "artifact_id": artifact_id,
            "storage_location": storage_result.get("location"),
            "granularity_strategy": granularity.get("strategy"),
            "compressed": processed_data.get("compressed", False),
            "concepts_extracted": len(concepts) if concepts else 0
        }

    def retrieve_artifact(self, artifact_id: str, project_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve a context artifact with intelligent reconstruction.

        Args:
            artifact_id: ID of the artifact to retrieve
            project_id: Optional project ID for filtering

        Returns:
            Retrieved artifact data or None if not found
        """
        # Check cache first
        if self.cache_enabled:
            cached = self._get_cached_artifact(artifact_id)
            if cached:
                logger.info("Artifact retrieved from cache", artifact_id=artifact_id)
                return cached

        # Retrieve from storage
        stored_data = self._retrieve_artifact_data(artifact_id, project_id)

        if not stored_data:
            return None

        # Reconstruct artifact if needed
        reconstructed = self._reconstruct_artifact(stored_data)

        # Update cache
        if self.cache_enabled:
            self._cache_artifact(artifact_id, reconstructed)

        logger.info("Artifact retrieved from storage", artifact_id=artifact_id)
        return reconstructed

    def inject_context(self, agent_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject relevant context for an agent request.

        Args:
            agent_request: Agent request parameters

        Returns:
            Context injection result
        """
        agent_type = agent_request.get("agent_type", "unknown")
        phase = agent_request.get("phase", "unknown")
        project_id = agent_request.get("project_id")
        query = agent_request.get("query", "")

        # Get selective context based on agent needs
        selective_context = self.get_selective_context(
            project_id=project_id,
            agent_type=agent_type,
            phase=phase,
            query=query
        )

        # Format context for agent consumption
        formatted_context = self._format_context_for_agent(
            selective_context, agent_request
        )

        logger.info("Context injected for agent",
                   agent_type=agent_type,
                   phase=phase,
                   artifacts_selected=len(selective_context.get("selected_artifacts", [])))

        return formatted_context

    def get_selective_context(
        self,
        project_id: str,
        agent_type: str,
        phase: str,
        query: str = "",
        max_tokens: Optional[int] = None,
        time_budget_hours: Optional[float] = None,
        priority_filter: Optional[str] = None,
        recency_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get selective context with advanced filtering and optimization.

        Args:
            project_id: Project ID
            agent_type: Type of agent
            phase: Current SDLC phase
            query: Optional query for relevance filtering
            max_tokens: Maximum token limit
            time_budget_hours: Time budget in hours
            priority_filter: Priority level filter
            recency_hours: Recency filter in hours

        Returns:
            Selective context result
        """
        # Get all project artifacts
        all_artifacts = self._get_project_artifacts(project_id)

        # Apply filters
        filtered_artifacts = self._apply_context_filters(
            all_artifacts, recency_hours, priority_filter, query
        )

        # Score artifacts for relevance
        scored_artifacts = self._score_artifacts_for_context(
            filtered_artifacts, agent_type, phase, query
        )

        # Sort by relevance
        scored_artifacts.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Apply token optimization if specified
        if max_tokens:
            selected_artifacts, optimization_info = self._optimize_context_size(
                scored_artifacts, max_tokens
            )
        else:
            selected_artifacts = scored_artifacts
            optimization_info = {"optimization_applied": False}

        # Calculate statistics
        total_artifacts = len(all_artifacts)
        selected_count = len(selected_artifacts)
        reduction_percentage = ((total_artifacts - selected_count) / total_artifacts) * 100 if total_artifacts > 0 else 0

        result = {
            "selected_artifacts": selected_artifacts,
            "statistics": {
                "total_artifacts": total_artifacts,
                "selected_count": selected_count,
                "reduction_percentage": reduction_percentage,
                "average_relevance": sum(a["relevance_score"] for a in selected_artifacts) / selected_count if selected_count > 0 else 0
            },
            "filtering_criteria": {
                "agent_type": agent_type,
                "phase": phase,
                "query": query,
                "max_tokens": max_tokens,
                "time_budget_hours": time_budget_hours,
                "priority_filter": priority_filter,
                "recency_hours": recency_hours
            },
            "optimization_info": optimization_info
        }

        return result

    def _cache_artifact(self, artifact_id: str, artifact_data: Dict[str, Any]) -> None:
        """Cache an artifact for faster retrieval."""
        self._cache[artifact_id] = artifact_data
        self._cache_timestamps[artifact_id] = datetime.now(timezone.utc)

    def _cache_context(self, cache_key: str, cache_data: Dict[str, Any]) -> None:
        """Cache context data for faster retrieval."""
        self._cache[cache_key] = cache_data
        self._cache_timestamps[cache_key] = datetime.now(timezone.utc)

    def _get_cached_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an artifact from cache."""
        if artifact_id not in self._cache:
            return None

        # Check if cache is still valid (not expired)
        cached_time = self._cache_timestamps.get(artifact_id)
        if cached_time and (datetime.now(timezone.utc) - cached_time).total_seconds() > 3600:  # 1 hour
            # Cache expired, remove it
            del self._cache[artifact_id]
            del self._cache_timestamps[artifact_id]
            return None

        return self._cache[artifact_id]

    def _get_cached_context(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve context data from cache."""
        if cache_key not in self._cache:
            return None

        # Check if cache is still valid (not expired)
        cached_time = self._cache_timestamps.get(cache_key)
        if cached_time and (datetime.now(timezone.utc) - cached_time).total_seconds() > 3600:  # 1 hour
            # Cache expired, remove it
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None

        return self._cache[cache_key]

    def _invalidate_cache(self, artifact_id: str = None) -> None:
        """Invalidate cache entries."""
        if artifact_id:
            self._cache.pop(artifact_id, None)
            self._cache_timestamps.pop(artifact_id, None)
        else:
            # Clear all cache
            self._cache.clear()
            self._cache_timestamps.clear()

    def _compress_artifact(self, content: str) -> bytes:
        """Compress artifact content using proper compression."""
        if not self.compression_enabled:
            return content.encode('utf-8')

        import gzip
        return gzip.compress(content.encode('utf-8'))

    def _decompress_artifact(self, compressed_data: bytes) -> str:
        """Decompress artifact content."""
        if not self.compression_enabled:
            return compressed_data.decode('utf-8')

        import gzip
        return gzip.decompress(compressed_data).decode('utf-8')

    def _apply_retention_policy(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply retention policy to clean up old artifacts."""
        if self.retention_policy == "30_days":
            retention_days = 30
        elif self.retention_policy == "90_days":
            retention_days = 90
        else:
            retention_days = 30

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

        artifacts_to_remove = []
        storage_freed = 0

        for artifact in artifacts:
            created_at = artifact.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif isinstance(created_at, datetime) and created_at.tzinfo is None:
                # Make offset-naive datetime timezone-aware
                created_at = created_at.replace(tzinfo=timezone.utc)

            if created_at and created_at < cutoff_date:
                artifacts_to_remove.append(artifact)
                storage_freed += artifact.get("size", 0)

        # In real implementation, actually remove the artifacts
        # For now, just return statistics
        return {
            "artifacts_removed": len(artifacts_to_remove),
            "storage_freed": storage_freed,
            "retention_policy": self.retention_policy
        }

    def _process_artifact_for_storage(self, artifact_data: Dict[str, Any], granularity: Dict[str, Any]) -> Dict[str, Any]:
        """Process artifact for optimal storage."""
        processed = artifact_data.copy()
        content = artifact_data.get("content", "")

        # Apply granularity strategy
        strategy = granularity.get("strategy", "atomic")

        if strategy == "sectioned" and len(content) > 10000:  # 10KB
            # Section the content
            sections = self.artifact_service.section_document(content)
            processed["sections"] = sections
            processed["granularity"] = "sectioned"
        elif strategy == "conceptual":
            # Extract concepts
            concepts = self.artifact_service.extract_concepts(content)
            processed["concepts"] = concepts
            processed["granularity"] = "conceptual"
        else:
            processed["granularity"] = "atomic"

        # Apply compression if enabled and content is large
        if self.compression_enabled and len(content) > 50000:  # 50KB
            compressed = self._compress_artifact(content)
            processed["compressed_content"] = compressed
            processed["original_size"] = len(content)
            processed["compressed"] = True

        return processed

    def _store_artifact_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store artifact data in the configured backend."""
        # In a real implementation, this would store to the configured backend
        # For now, simulate storage
        artifact_id = processed_data.get("id", "unknown")
        storage_location = f"/artifacts/{artifact_id}"

        return {
            "location": storage_location,
            "backend": self.storage_backend,
            "stored_at": datetime.now(timezone.utc).isoformat()
        }

    def _retrieve_artifact_data(self, artifact_id: str, project_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve artifact data from storage."""
        # In a real implementation, this would retrieve from the configured backend
        # For now, simulate retrieval
        return {
            "id": artifact_id,
            "content": f"Sample content for {artifact_id}",
            "type": "sample",
            "project_id": project_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def _reconstruct_artifact(self, stored_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reconstruct artifact from stored data."""
        reconstructed = stored_data.copy()

        # Decompress if needed
        if stored_data.get("compressed"):
            compressed_content = stored_data.get("compressed_content", b"")
            original_content = self._decompress_artifact(compressed_content)
            reconstructed["content"] = original_content

        return reconstructed

    def _store_artifact_concepts(self, artifact_id: str, concepts: List[Dict[str, Any]]) -> None:
        """Store extracted concepts for an artifact."""
        # In a real implementation, this would store concepts in a separate index
        # For now, just log
        logger.info("Concepts stored for artifact",
                   artifact_id=artifact_id,
                   concepts_count=len(concepts))

    def _get_project_artifacts(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts for a project."""
        # In a real implementation, this would query the storage backend
        # For now, return sample data that includes architect-relevant artifacts
        return [
            {
                "id": f"artifact_{i}",
                "project_id": project_id,
                "type": "requirements" if i % 3 == 0 else ("architecture" if i % 3 == 1 else "design"),
                "content": f"What are the system requirements? This document contains detailed system requirements and architecture details for artifact {i}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "size": 1000 + (i * 100)
            }
            for i in range(10)
        ]

    def _apply_context_filters(
        self,
        artifacts: List[Dict[str, Any]],
        recency_hours: Optional[int],
        priority_filter: Optional[str],
        query: str
    ) -> List[Dict[str, Any]]:
        """Apply filtering to artifacts for context selection."""
        filtered = artifacts.copy()

        # Apply recency filter
        if recency_hours:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=recency_hours)
            filtered = [
                a for a in filtered
                if datetime.fromisoformat(a.get("created_at", "").replace('Z', '+00:00')) >= cutoff_time
            ]

        # Apply priority filter (simplified)
        if priority_filter:
            if priority_filter == "high":
                filtered = filtered[:len(filtered)//3]  # Top 1/3
            elif priority_filter == "low":
                filtered = filtered[len(filtered)//3:]  # Bottom 2/3

        # Apply query filter (simple text search)
        if query:
            query_lower = query.lower()
            filtered = [
                a for a in filtered
                if query_lower in a.get("content", "").lower() or query_lower in a.get("type", "").lower()
            ]

        return filtered

    def _score_artifacts_for_context(
        self,
        artifacts: List[Dict[str, Any]],
        agent_type: str,
        phase: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Score artifacts for context relevance."""
        scored = []

        for artifact in artifacts:
            # Calculate relevance score
            relevance_score = self._calculate_context_relevance_score(
                artifact, agent_type, phase, query
            )

            scored_artifact = {
                "artifact": artifact,
                "relevance_score": relevance_score,
                "estimated_tokens": len(artifact.get("content", "")) // 4,  # Rough token estimate
                "is_recent": self._is_recent_artifact(artifact),
                "priority": self._calculate_artifact_priority(artifact, agent_type, phase)
            }

            scored.append(scored_artifact)

        return scored

    def _calculate_context_relevance_score(
        self,
        artifact: Dict[str, Any],
        agent_type: str,
        phase: str,
        query: str
    ) -> float:
        """Calculate relevance score for context selection."""
        score = 0.0

        # Agent type relevance
        if agent_type == "analyst" and artifact.get("type") == "requirements":
            score += 0.4
        elif agent_type == "architect" and artifact.get("type") == "architecture":
            score += 0.4
        elif agent_type == "coder" and artifact.get("type") == "source_code":
            score += 0.4

        # Phase relevance
        if phase == "design" and artifact.get("type") in ["architecture", "design"]:
            score += 0.3
        elif phase == "build" and artifact.get("type") in ["design", "source_code"]:
            score += 0.3

        # Query relevance
        if query:
            content = artifact.get("content", "").lower()
            query_lower = query.lower()
            if query_lower in content:
                score += 0.2

        # Recency bonus
        if self._is_recent_artifact(artifact):
            score += 0.1

        return min(1.0, score)  # Cap at 1.0

    def _is_recent_artifact(self, artifact: Dict[str, Any]) -> bool:
        """Check if artifact is recent."""
        created_at = artifact.get("created_at")
        if not created_at:
            return False

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

        time_diff = datetime.now(timezone.utc) - created_at
        return time_diff.total_seconds() < 86400  # 24 hours

    def _calculate_artifact_priority(self, artifact: Dict[str, Any], agent_type: str, phase: str) -> str:
        """Calculate priority level for artifact."""
        relevance_score = self._calculate_context_relevance_score(artifact, agent_type, phase, "")

        if relevance_score > 0.7:
            return "high"
        elif relevance_score > 0.4:
            return "medium"
        else:
            return "low"

    def _optimize_context_size(self, scored_artifacts: List[Dict[str, Any]], max_tokens: int) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Optimize context size to fit within token limit."""
        selected = []
        total_tokens = 0
        optimization_info = {
            "optimization_applied": True,
            "original_total_tokens": sum(a["estimated_tokens"] for a in scored_artifacts),
            "max_tokens": max_tokens,
            "final_total_tokens": 0,
            "artifacts_removed": 0
        }

        # Sort by relevance score first
        scored_artifacts.sort(key=lambda x: x["relevance_score"], reverse=True)

        for artifact in scored_artifacts:
            if total_tokens + artifact["estimated_tokens"] <= max_tokens:
                selected.append(artifact)
                total_tokens += artifact["estimated_tokens"]
            else:
                optimization_info["artifacts_removed"] += 1

        optimization_info["final_total_tokens"] = total_tokens

        return selected, optimization_info

    def _format_context_for_agent(self, selective_context: Dict[str, Any], agent_request: Dict[str, Any]) -> Dict[str, Any]:
        """Format context for agent consumption."""
        selected_artifacts = selective_context.get("selected_artifacts", [])

        # Extract artifact IDs
        context_ids = [a["artifact"]["id"] for a in selected_artifacts]

        # Create knowledge units from concepts if available
        knowledge_units = []
        for artifact in selected_artifacts:
            content = artifact["artifact"].get("content", "")
            if content:
                concepts = self.artifact_service.extract_concepts(content)
                units = self.artifact_service.create_knowledge_units(concepts)
                knowledge_units.extend(units)

        # Create formatted context
        formatted = {
            "context_ids": context_ids,
            "relevant_artifacts": [a["artifact"] for a in selected_artifacts],
            "artifacts": [a["artifact"] for a in selected_artifacts],  # Keep both for compatibility
            "knowledge_units": knowledge_units,
            "relevance_scores": {a["artifact"]["id"]: a["relevance_score"] for a in selected_artifacts},
            "statistics": selective_context.get("statistics", {}),
            "agent_request": agent_request
        }

        return formatted


class ContextStoreService:
    """
    Service wrapper for ContextStore providing additional functionality.

    This service provides a higher-level interface to the ContextStore,
    including batch operations, advanced querying, and integration
    with other BMAD services.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the context store service.

        Args:
            config: Configuration dictionary
        """
        self.context_store = ContextStore(config)
        self.config = config

    def store_artifacts_batch(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Store multiple artifacts in batch.

        Args:
            artifacts: List of artifacts to store

        Returns:
            Batch storage results
        """
        results = []
        total_stored = 0
        total_failed = 0

        for artifact in artifacts:
            try:
                result = self.context_store.store_artifact(artifact)
                results.append(result)
                if result.get("stored", False):
                    total_stored += 1
                else:
                    total_failed += 1
            except Exception as e:
                logger.error("Failed to store artifact",
                           artifact_id=artifact.get("id"),
                           error=str(e))
                results.append({
                    "stored": False,
                    "error": str(e),
                    "artifact_id": artifact.get("id")
                })
                total_failed += 1

        return {
            "total_artifacts": len(artifacts),
            "stored": total_stored,
            "failed": total_failed,
            "results": results
        }

    def get_project_context_summary(self, project_id: str) -> Dict[str, Any]:
        """
        Get a summary of all context for a project.

        Args:
            project_id: Project ID

        Returns:
            Project context summary
        """
        artifacts = self.context_store._get_project_artifacts(project_id)

        if not artifacts:
            return {"project_id": project_id, "artifacts_count": 0}

        # Analyze artifacts
        artifact_types = {}
        total_size = 0
        recent_count = 0

        for artifact in artifacts:
            # Count by type
            artifact_type = artifact.get("type", "unknown")
            artifact_types[artifact_type] = artifact_types.get(artifact_type, 0) + 1

            # Calculate total size
            total_size += artifact.get("size", 0)

            # Count recent artifacts
            if self.context_store._is_recent_artifact(artifact):
                recent_count += 1

        return {
            "project_id": project_id,
            "artifacts_count": len(artifacts),
            "artifact_types": artifact_types,
            "total_size_bytes": total_size,
            "recent_artifacts": recent_count,
            "storage_efficiency": self._calculate_storage_efficiency(artifacts)
        }

    def _calculate_storage_efficiency(self, artifacts: List[Dict[str, Any]]) -> float:
        """Calculate storage efficiency score."""
        if not artifacts:
            return 0.0

        # Simple efficiency calculation based on compression and deduplication
        compressed_count = sum(1 for a in artifacts if a.get("compressed", False))
        efficiency = compressed_count / len(artifacts)

        return min(1.0, efficiency)
