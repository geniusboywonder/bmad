"""Tests for ADK Handoff Service."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from uuid import UUID

from app.services.adk_handoff_service import ADKHandoffService
from app.agents.bmad_adk_wrapper import BMADADKWrapper
from app.models.handoff import HandoffSchema

@pytest.fixture
def handoff_service(db_session):
    """Create a fresh ADK Handoff Service for testing."""
    return ADKHandoffService(db_session)

@pytest.fixture
def mock_adk_wrapper():
    """Create a mock BMADADKWrapper for testing."""
    wrapper = Mock(spec=BMADADKWrapper)
    wrapper.agent_name = "test_agent_from"
    wrapper.agent_type = "analyst"
    wrapper.is_initialized = True
    wrapper.adk_agent = Mock()
    return wrapper

@pytest.fixture
def mock_adk_wrapper_to():
    """Create a mock BMADADKWrapper for the receiving agent."""
    wrapper = Mock(spec=BMADADKWrapper)
    wrapper.agent_name = "test_agent_to"
    wrapper.agent_type = "architect"
    wrapper.is_initialized = True
    wrapper.adk_agent = Mock()
    return wrapper

class TestADKHandoffService:
    """Test ADK Handoff Service functionality."""

    @pytest.mark.mock_data

    def test_service_initialization(self, handoff_service):
        """Test that handoff service initializes correctly."""
        assert isinstance(handoff_service.active_handoffs, dict)
        assert handoff_service.handoff_count == 0

    @patch('app.services.adk_handoff_service.datetime')
    @pytest.mark.mock_data

    async def test_create_structured_handoff(self, mock_datetime, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test creating a structured handoff."""
        mock_datetime.now.return_value = datetime(2025, 9, 15, 15, 0, 0)

        handoff_data = {
            "phase": "requirements_analysis",
            "instructions": "Review the PRD and provide technical feedback",
            "expected_outputs": ["technical_feedback", "feasibility_assessment"],
            "priority": "high",
            "context_ids": ["artifact_123", "artifact_456"]
        }

        # Mock persistence
        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project"
            )

            # Check handoff_id is a valid UUID string
            UUID(handoff_id)  # This will raise ValueError if not a valid UUID
            assert handoff_id in handoff_service.active_handoffs

            # Verify handoff info
            handoff_info = handoff_service.active_handoffs[handoff_id]
            assert handoff_info["from_agent"] == mock_adk_wrapper
            assert handoff_info["to_agent"] == mock_adk_wrapper_to
            assert handoff_info["status"] == "pending"

            # Verify handoff schema
            schema = handoff_info["schema"]
            assert isinstance(schema, HandoffSchema)
            assert schema.from_agent == "analyst"
            assert schema.to_agent == "architect"
            assert schema.phase == "requirements_analysis"
            assert "Review the PRD" in schema.instructions
            assert schema.expected_outputs == ["technical_feedback", "feasibility_assessment"]
            assert schema.priority == 1  # "high" priority maps to 1

    @pytest.mark.mock_data

    async def test_create_handoff_with_invalid_data_fails(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test that creating handoff with invalid data fails."""
        invalid_handoff_data = {
            "phase": "test_phase"
            # Missing required "instructions" field
        }

        with pytest.raises(ValueError, match="Missing required handoff field"):
            await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=invalid_handoff_data,
                project_id="test_project"
            )

    @pytest.mark.mock_data

    async def test_create_handoff_with_empty_instructions_fails(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test that creating handoff with empty instructions fails."""
        invalid_handoff_data = {
            "phase": "test_phase",
            "instructions": ""  # Empty instructions
        }

        with pytest.raises(ValueError, match="Handoff instructions cannot be empty"):
            await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=invalid_handoff_data,
                project_id="test_project"
            )

    @pytest.mark.mock_data

    async def test_create_handoff_with_invalid_priority_fails(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test that creating handoff with invalid priority fails."""
        invalid_handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions",
            "priority": "invalid_priority"
        }

        with pytest.raises(ValueError, match="Invalid priority"):
            await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=invalid_handoff_data,
                project_id="test_project"
            )

    @pytest.mark.mock_data

    async def test_get_handoff_status_for_active_handoff(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test getting status for an active handoff."""
        # Create a handoff first
        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions"
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project"
            )

        # Get status
        status = await handoff_service.get_handoff_status(handoff_id)

        assert status is not None
        assert status["handoff_id"] == handoff_id
        assert status["status"] == "pending"
        assert status["from_agent"] == "analyst"
        assert status["to_agent"] == "architect"
        assert status["phase"] == "test_phase"
        assert status["priority"] == 2  # "medium" priority maps to 2
        assert "created_at" in status
        assert status["expected_outputs"] == []

    @pytest.mark.mock_data

    async def test_get_handoff_status_for_unknown_handoff(self, handoff_service):
        """Test getting status for unknown handoff returns None."""
        status = await handoff_service.get_handoff_status("unknown_handoff")
        assert status is None

    @pytest.mark.mock_data

    async def test_list_active_handoffs(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test listing active handoffs."""
        # Initially empty
        assert handoff_service.list_active_handoffs() == []

        # Create a handoff
        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions"
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project_1"
            )

        # Should now have one active handoff
        active_handoffs = handoff_service.list_active_handoffs()
        assert len(active_handoffs) == 1
        assert handoff_id in active_handoffs

    @pytest.mark.mock_data

    async def test_list_active_handoffs_with_project_filter(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test listing active handoffs with project filter."""
        from uuid import uuid4

        # Create handoffs for different projects using real UUIDs
        project_uuid_1 = uuid4()
        project_uuid_2 = uuid4()

        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions"
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id_1 = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id=project_uuid_1
            )

            handoff_id_2 = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id=project_uuid_2
            )

        # Filter by project_uuid_1
        project_1_handoffs = handoff_service.list_active_handoffs(project_uuid_1)
        assert len(project_1_handoffs) == 1
        assert handoff_id_1 in project_1_handoffs
        assert handoff_id_2 not in project_1_handoffs

        # Filter by project_uuid_2
        project_2_handoffs = handoff_service.list_active_handoffs(project_uuid_2)
        assert len(project_2_handoffs) == 1
        assert handoff_id_2 in project_2_handoffs
        assert handoff_id_1 not in project_2_handoffs

    @pytest.mark.mock_data

    async def test_cancel_handoff(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test cancelling an active handoff."""
        # Create a handoff
        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions"
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project"
            )

        # Mock update status
        with patch.object(handoff_service, '_update_handoff_status'):
            # Cancel the handoff
            result = await handoff_service.cancel_handoff(handoff_id)

            assert result is True
            assert handoff_id not in handoff_service.active_handoffs

    @pytest.mark.mock_data

    async def test_cancel_unknown_handoff(self, handoff_service):
        """Test cancelling unknown handoff returns False."""
        result = await handoff_service.cancel_handoff("unknown_handoff")
        assert result is False

    @pytest.mark.mock_data

    def test_build_handoff_instructions(self, handoff_service):
        """Test building comprehensive handoff instructions."""
        handoff_data = {
            "instructions": "Basic instructions",
            "expected_outputs": ["output1", "output2"],
            "priority": "high",
            "additional_context": "Extra context information"
        }

        instructions = handoff_service._build_handoff_instructions(handoff_data)

        assert "Basic instructions" in instructions
        assert "output1" in instructions
        assert "output2" in instructions
        assert "HIGH" in instructions
        assert "Extra context information" in instructions

    @pytest.mark.mock_data

    def test_build_handoff_instructions_minimal(self, handoff_service):
        """Test building handoff instructions with minimal data."""
        handoff_data = {
            "instructions": "Minimal instructions"
        }

        instructions = handoff_service._build_handoff_instructions(handoff_data)

        assert "Minimal instructions" in instructions
        assert "⚠️" not in instructions  # No high priority warning

    @pytest.mark.mock_data

    def test_create_handoff_prompt(self, handoff_service):
        """Test creating handoff execution prompt."""
        from uuid import uuid4
        schema = HandoffSchema(
            handoff_id=uuid4(),
            project_id=uuid4(),
            from_agent="analyst",
            to_agent="architect",
            phase="requirements_review",
            instructions="Review these requirements",
            context_ids=[uuid4()],
            expected_outputs=["review_feedback"],
            priority=2  # medium priority
        )

        context_data = {
            "project_context": "Test project context",
            "previous_work": "Previous analysis work",
            "artifacts": ["PRD document", "Requirements spec"]
        }

        prompt = handoff_service._create_handoff_prompt(schema, context_data)

        assert "🤝 AGENT HANDOFF: analyst → architect" in prompt
        assert "requirements_review" in prompt
        assert "Review these requirements" in prompt
        assert "Test project context" in prompt
        assert "Previous analysis work" in prompt
        assert "PRD document" in prompt
        assert "Requirements spec" in prompt

    @pytest.mark.mock_data

    def test_create_handoff_prompt_minimal_context(self, handoff_service):
        """Test creating handoff prompt with minimal context."""
        from uuid import uuid4
        schema = HandoffSchema(
            handoff_id=uuid4(),
            project_id=uuid4(),
            from_agent="analyst",
            to_agent="architect",
            phase="test_phase",
            instructions="Test instructions",
            context_ids=[],
            expected_outputs=[],
            priority=4  # low priority
        )

        prompt = handoff_service._create_handoff_prompt(schema, {})

        assert "🤝 AGENT HANDOFF: analyst → architect" in prompt
        assert "test_phase" in prompt
        assert "Test instructions" in prompt
        assert "PROJECT CONTEXT:" not in prompt  # No project context provided

    @pytest.mark.mock_data

    def test_validate_handoff_data_success(self, handoff_service):
        """Test successful handoff data validation."""
        valid_data = {
            "phase": "test_phase",
            "instructions": "Test instructions",
            "priority": "medium"
        }

        # Should not raise any exception
        handoff_service._validate_handoff_data(valid_data)

    @pytest.mark.mock_data

    def test_validate_handoff_data_missing_fields(self, handoff_service):
        """Test handoff data validation with missing required fields."""
        invalid_data = {
            "phase": "test_phase"
            # Missing "instructions"
        }

        with pytest.raises(ValueError, match="Missing required handoff field: instructions"):
            handoff_service._validate_handoff_data(invalid_data)

    @pytest.mark.mock_data

    def test_validate_handoff_data_invalid_priority(self, handoff_service):
        """Test handoff data validation with invalid priority."""
        invalid_data = {
            "phase": "test_phase",
            "instructions": "Test instructions",
            "priority": "invalid"
        }

        with pytest.raises(ValueError, match="Invalid priority"):
            handoff_service._validate_handoff_data(invalid_data)

    @pytest.mark.mock_data

    async def test_cleanup_completed_handoffs(self, handoff_service):
        """Test cleanup of completed handoffs."""
        # This test would need timestamp mocking for proper testing
        result = await handoff_service.cleanup_completed_handoffs()
        assert isinstance(result, int)
        assert result >= 0

class TestADKHandoffExecution:
    """Test handoff execution functionality."""

    @pytest.mark.mock_data

    def test_execute_handoff_unknown_workflow(self, handoff_service):
        """Test executing handoff for unknown workflow."""
        async def run_test():
            results = []
            async for result in handoff_service.execute_handoff("unknown_handoff"):
                results.append(result)

            assert len(results) == 1
            assert results[0]["error"] == "Handoff unknown_handoff not found"

        import asyncio
        asyncio.run(run_test())

    @pytest.mark.mock_data

    def test_execute_handoff_with_orchestration_error(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test handoff execution with orchestration service error."""
        # Create a handoff first
        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions"
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project"
            )

        async def run_test():
            # Mock orchestration service to raise an error
            with patch.object(handoff_service.orchestration_service, 'create_multi_agent_workflow', side_effect=Exception("Orchestration failed")):
                with patch.object(handoff_service, '_update_handoff_status'):
                    results = []
                    async for result in handoff_service.execute_handoff(handoff_id):
                        results.append(result)

                    assert len(results) >= 1
                    assert "error" in results[-1]  # Last result should contain error

        import asyncio
        asyncio.run(run_test())

class TestADKHandoffIntegration:
    """Integration tests for ADK Handoff Service."""

    @pytest.mark.mock_data

    async def test_full_handoff_lifecycle(self, handoff_service, mock_adk_wrapper, mock_adk_wrapper_to):
        """Test complete handoff lifecycle from creation to completion."""
        # Create handoff
        handoff_data = {
            "phase": "test_phase",
            "instructions": "Test instructions",
            "expected_outputs": ["test_output"]
        }

        with patch.object(handoff_service, '_persist_handoff'):
            handoff_id = await handoff_service.create_structured_handoff(
                from_agent=mock_adk_wrapper,
                to_agent=mock_adk_wrapper_to,
                handoff_data=handoff_data,
                project_id="test_project"
            )

        # Verify creation
        assert handoff_id in handoff_service.active_handoffs
        status = await handoff_service.get_handoff_status(handoff_id)
        assert status["status"] == "pending"

        # List should include the handoff
        active_handoffs = handoff_service.list_active_handoffs()
        assert handoff_id in active_handoffs

        # Cancel handoff
        with patch.object(handoff_service, '_update_handoff_status'):
            result = await handoff_service.cancel_handoff(handoff_id)
            assert result is True

        # Verify removal
        assert handoff_id not in handoff_service.active_handoffs
        status = await handoff_service.get_handoff_status(handoff_id)
        assert status is None
