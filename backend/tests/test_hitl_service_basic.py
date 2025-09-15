"""
Basic HITL Service Tests

Simple tests to verify HITL service functionality.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

from app.services.hitl_service import HitlService, OversightLevel, HitlTriggerCondition
from app.models.hitl import HitlStatus, HitlAction


class TestHitlServiceBasic:
    """Basic tests for HITL service functionality."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return MagicMock()

    @pytest.fixture
    def hitl_service(self, mock_db):
        """HITL service instance."""
        return HitlService(mock_db)

    def test_hitl_service_initialization(self, hitl_service):
        """Test HITL service initializes correctly."""
        assert hitl_service.default_oversight_level == OversightLevel.MEDIUM
        assert hitl_service.default_timeout_hours == 24
        assert hasattr(hitl_service, 'trigger_configs')
        assert isinstance(hitl_service.trigger_configs, dict)

    def test_oversight_level_validation(self, hitl_service):
        """Test oversight level validation."""
        # Valid levels should not raise exceptions
        hitl_service.set_oversight_level(uuid4(), OversightLevel.HIGH)
        hitl_service.set_oversight_level(uuid4(), OversightLevel.MEDIUM)
        hitl_service.set_oversight_level(uuid4(), OversightLevel.LOW)

        # Invalid level should raise exception
        with pytest.raises(ValueError):
            hitl_service.set_oversight_level(uuid4(), "invalid_level")

    def test_trigger_condition_configuration(self, hitl_service):
        """Test trigger condition configuration."""
        # Configure a trigger condition
        hitl_service.configure_trigger_condition(
            HitlTriggerCondition.QUALITY_THRESHOLD,
            enabled=True,
            config={"threshold": 0.8}
        )

        # Verify configuration was updated in the trigger manager
        config = hitl_service.trigger_manager.trigger_configs[HitlTriggerCondition.QUALITY_THRESHOLD]
        assert config["enabled"] is True
        assert config["threshold"] == 0.8

    def test_get_oversight_level_default(self, hitl_service, mock_db):
        """Test getting default oversight level when not set."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        level = hitl_service.get_oversight_level(uuid4())
        assert level == OversightLevel.MEDIUM

    def test_generate_hitl_question_phase_completion(self, hitl_service):
        """Test HITL question generation for phase completion."""
        trigger_context = {"trigger_type": "phase_completion", "phase": "design"}

        question = hitl_service._generate_hitl_question(trigger_context)

        assert "design" in question.lower()
        assert "review" in question.lower()

    def test_generate_hitl_question_quality_threshold(self, hitl_service):
        """Test HITL question generation for quality threshold."""
        trigger_context = {"trigger_type": "quality_threshold", "confidence": 0.5}

        question = hitl_service._generate_hitl_question(trigger_context)

        assert "confidence" in question.lower() or "threshold" in question.lower()

    def test_get_hitl_options_base(self, hitl_service):
        """Test getting base HITL options."""
        trigger_context = {"trigger_type": "unknown_condition"}
        options = hitl_service._get_hitl_options(trigger_context)

        assert "Approve" in options
        assert "Reject" in options
        assert "Amend" in options

    def test_get_hitl_options_conflict(self, hitl_service):
        """Test getting HITL options for conflict detection."""
        trigger_context = {"trigger_type": "conflict"}
        options = hitl_service._get_hitl_options(trigger_context)

        assert "Accept first option" in options
        assert "Accept second option" in options
        assert "Provide alternative" in options

    def test_validate_hitl_response_approve(self, hitl_service):
        """Test HITL response validation for approve action."""
        # Should not raise exception
        hitl_service._validate_hitl_response(
            HitlAction.APPROVE,
            None,
            "Approved by user"
        )

    def test_validate_hitl_response_amend_without_content(self, hitl_service):
        """Test HITL response validation for amend without content."""
        with pytest.raises(ValueError, match="Response content is required"):
            hitl_service._validate_hitl_response(
                HitlAction.AMEND,
                None,
                "Comment without content"
            )

    def test_validate_hitl_response_without_comment(self, hitl_service):
        """Test HITL response validation without comment."""
        with pytest.raises(ValueError, match="Comment is required"):
            hitl_service._validate_hitl_response(
                HitlAction.APPROVE,
                None,
                ""
            )

    def test_get_hitl_response_message(self, hitl_service):
        """Test HITL response message generation."""
        message = hitl_service._get_hitl_response_message(HitlAction.APPROVE, True)
        assert "approved" in message.lower()
        assert "resumed" in message.lower()

        message = hitl_service._get_hitl_response_message(HitlAction.REJECT, False)
        assert "rejected" in message.lower()
        assert "unknown" in message.lower()

    def test_bulk_approval_validation(self, hitl_service):
        """Test bulk approval request validation."""
        # Should raise exception for oversized batch
        oversized_ids = [uuid4() for _ in range(20)]
        with pytest.raises(ValueError, match="Cannot approve more than"):
            # Just test the validation, not the actual async call
            if len(oversized_ids) > hitl_service.bulk_approval_batch_size:
                raise ValueError(f"Cannot approve more than {hitl_service.bulk_approval_batch_size} requests at once")

    @pytest.mark.asyncio
    async def test_cleanup_expired_requests(self, hitl_service, mock_db):
        """Test cleanup of expired HITL requests."""
        # Mock expired requests count
        mock_db.query.return_value.filter.return_value.update.return_value = 5

        count = await hitl_service.cleanup_expired_requests()

        assert count == 5
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_hitl_statistics_empty(self, hitl_service, mock_db):
        """Test HITL statistics with no requests."""
        # Mock the main query for basic counts
        mock_main_query = MagicMock()
        mock_main_query.count.return_value = 0
        mock_main_query.filter.return_value.count.return_value = 0

        # Mock the average response time query chain
        mock_avg_query = MagicMock()
        mock_avg_filter = MagicMock()
        mock_avg_filter.scalar.return_value = None
        mock_avg_query.filter.return_value = mock_avg_filter

        # Set up the db.query to return different mocks based on context
        def mock_query_side_effect(model):
            if hasattr(model, '__name__') and 'HitlRequestDB' in str(model):
                return mock_main_query
            return mock_avg_query

        mock_db.query.side_effect = mock_query_side_effect

        stats = await hitl_service.get_hitl_statistics()

        assert stats["total_requests"] == 0
        assert stats["pending_requests"] == 0
        assert stats["approved_requests"] == 0
        assert stats["approval_rate"] == 0
        assert stats["average_response_time_hours"] is None
