"""
Test Cases for P2.3 Enhanced HITL Triggers

This module contains comprehensive test cases for enhanced Human-in-the-Loop (HITL) triggers,
including phase completion triggers, quality gates, and conflict resolution.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List
from uuid import uuid4

from app.services.hitl_trigger_manager import HitlTriggerManager, HitlTriggerCondition, OversightLevel
from app.services.quality_gate_service import QualityGateService, QualityGateStatus
from app.services.conflict_resolver import ConflictResolverService
from app.services.context_store import ContextStoreService
from app.services.autogen_service import AutoGenService
from app.models.hitl_request import HITLRequest
from app.models.quality_gate import QualityGate
from tests.utils.database_test_utils import DatabaseTestManager

@pytest.fixture
def db_manager():
    """Database manager fixture for tests."""
    manager = DatabaseTestManager(use_memory_db=True)
    manager.setup_test_database()
    yield manager
    manager.cleanup_test_database()

class TestHITLTriggerManager:
    """Test cases for the HITL trigger manager."""

    @pytest.fixture
    def hitl_manager(self, db_manager):
        """HITL trigger manager instance with a real database session."""
        with db_manager.get_session() as session:
            yield HitlTriggerManager(session)

    @pytest.mark.mock_data
    def test_hitl_trigger_initialization(self, hitl_manager):
        """Test HITL trigger manager initialization."""
        assert hitl_manager.db is not None
        assert hitl_manager.audit_service is not None
        assert hitl_manager.quality_threshold == 0.7

    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_phase_completion_trigger(self, hitl_manager):
        """Test phase completion HITL trigger."""
        config = hitl_manager.trigger_configs[HitlTriggerCondition.PHASE_COMPLETION]
        project_id = uuid4()
        task_id = uuid4()

        # Test high oversight triggers for a configured phase
        trigger_context = {"current_phase": "design"}
        should_trigger = await hitl_manager._check_phase_completion_trigger(
            config, project_id, task_id, trigger_context, OversightLevel.HIGH
        )
        assert should_trigger is True

        # Test low oversight does not trigger
        should_trigger = await hitl_manager._check_phase_completion_trigger(
            config, project_id, task_id, trigger_context, OversightLevel.LOW
        )
        assert should_trigger is False

    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_quality_threshold_trigger(self, hitl_manager):
        """Test quality threshold HITL trigger."""
        config = hitl_manager.trigger_configs[HitlTriggerCondition.QUALITY_THRESHOLD]
        project_id = uuid4()
        task_id = uuid4()
        agent_type = "test_agent"

        # Test low confidence triggers
        trigger_context = {"confidence_score": 0.5}
        should_trigger = await hitl_manager._check_quality_threshold_trigger(
            config, project_id, task_id, agent_type, trigger_context, OversightLevel.HIGH
        )
        assert should_trigger is True

        # Test high confidence does not trigger
        trigger_context = {"confidence_score": 0.9}
        should_trigger = await hitl_manager._check_quality_threshold_trigger(
            config, project_id, task_id, agent_type, trigger_context, OversightLevel.HIGH
        )
        assert should_trigger is False

class TestQualityGateService:
    """Test cases for the quality gate service."""

    @pytest.fixture
    def quality_service(self):
        """Quality gate service instance."""
        return QualityGateService()

    @pytest.mark.mock_data
    def test_quality_gate_initialization(self, quality_service):
        """Test quality gate service initialization."""
        assert quality_service.config == {}
        assert quality_service.quality_thresholds['minimum_score'] == 0.8

    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_gate_evaluation(self, quality_service):
        """Test quality gate evaluation."""
        # Test passing gate
        passing_metrics = {"completeness": 0.9, "accuracy": 0.95}
        result = await quality_service.evaluate_quality_gate("design", [], passing_metrics)
        assert result.status == QualityGateStatus.PASS
        assert result.score > quality_service.quality_thresholds['minimum_score']

        # Test failing gate
        failing_metrics = {"completeness": 0.6, "accuracy": 0.7}
        result = await quality_service.evaluate_quality_gate("design", [], failing_metrics)
        assert result.status == QualityGateStatus.FAIL
        assert result.score < quality_service.quality_thresholds['minimum_score']

class TestConflictResolverService:
    """Test cases for the conflict resolver service."""

    @pytest.fixture
    def conflict_resolver_service(self):
        """Conflict resolver service instance with mocked dependencies."""
        mock_context_store = Mock(spec=ContextStoreService)
        mock_autogen_service = Mock(spec=AutoGenService)
        return ConflictResolverService(mock_context_store, mock_autogen_service)

    @pytest.mark.mock_data
    def test_conflict_resolver_initialization(self, conflict_resolver_service):
        """Test conflict resolver initialization."""
        assert isinstance(conflict_resolver_service.context_store, ContextStoreService)
        assert isinstance(conflict_resolver_service.autogen_service, AutoGenService)

    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_conflict_detection(self, conflict_resolver_service):
        """Test conflict detection between agent outputs."""
        from app.models.context import ContextArtifact
        # Test conflicting artifacts
        artifacts = [
            ContextArtifact(context_id=uuid4(), project_id=uuid4(), source_agent="agent1", artifact_type="design", content={"decision": "microservices"}),
            ContextArtifact(context_id=uuid4(), project_id=uuid4(), source_agent="agent2", artifact_type="design", content={"decision": "monolith"})
        ]

        with patch.object(conflict_resolver_service, '_calculate_content_similarity', return_value=0.2):
            conflicts = await conflict_resolver_service._detect_output_contradictions(artifacts, "proj1", "wf1")
            assert len(conflicts) == 1
            assert conflicts[0].title == "Output contradiction in design"

        # Test non-conflicting artifacts
        with patch.object(conflict_resolver_service, '_calculate_content_similarity', return_value=0.9):
            conflicts = await conflict_resolver_service._detect_output_contradictions(artifacts, "proj1", "wf1")
            assert len(conflicts) == 0
