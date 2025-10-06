"""Tests for HITL Safety Architecture.

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies (WebSocket, Celery, notifications) remain appropriately mocked.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.services.hitl_safety_service import (
    HITLSafetyService,
    ApprovalTimeoutError,
    AgentExecutionDenied,
    BudgetLimitExceeded,
    EmergencyStopActivated,
    ApprovalResult,
    BudgetCheckResult
)
from app.database.models import (
    HitlAgentApprovalDB,
    AgentBudgetControlDB,
    EmergencyStopDB,
    ResponseApprovalDB,
    RecoverySessionDB,
    WebSocketNotificationDB
)
from app.models.agent import AgentStatus
from app.agents.base_agent import BaseAgent
from app.models.agent import AgentType
from app.services.response_safety_analyzer import ResponseSafetyAnalyzer, SafetyAnalysisResult
# RecoveryManager import removed - not used in tests
from app.websocket.manager import NotificationPriority
from tests.utils.database_test_utils import DatabaseTestManager

class TestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""

    def _create_system_message(self, task, context):
        return "Test system message"

    def create_handoff(self, task, context):
        return None

    def execute_task(self, task, context):
        return {"status": "completed", "result": "test"}

class TestHITLSafetyService:
    """Test cases for HITL Safety Service."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for HITL safety tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    def test_approval_result_creation(self):
        """Test ApprovalResult creation."""
        result = ApprovalResult(approved=True, response="approved", comment="Good to go")
        assert result.approved is True
        assert result.response == "approved"
        assert result.comment == "Good to go"

    @pytest.mark.real_data
    def test_budget_check_result_creation(self):
        """Test BudgetCheckResult creation."""
        result = BudgetCheckResult(approved=False, reason="Budget exceeded")
        assert result.approved is False
        assert result.reason == "Budget exceeded"

    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_create_approval_request_success(self, db_manager):
        """Test successful approval request creation with real database."""
        # Create real project and task
        project = db_manager.create_test_project(name="HITL Safety Test Project")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")

        with db_manager.get_session() as session:
            hitl_service = HITLSafetyService(session)
            
            # Mock external dependencies only (WebSocket notifications)
            with patch('app.websocket.manager.WebSocketManager') as mock_ws, \
                 patch.object(hitl_service, '_send_hitl_notification', new_callable=AsyncMock) as mock_send, \
                 patch.object(hitl_service, 'calculate_cost', new_callable=AsyncMock) as mock_calc:

                mock_calc.return_value = Decimal('0.002')

                approval_id = await hitl_service.create_approval_request(
                    project_id=project.id,
                    task_id=task.id,
                    agent_type="analyst",
                    request_type="PRE_EXECUTION",
                    request_data={"test": "data"},
                    estimated_tokens=100
                )

                assert approval_id is not None
                mock_send.assert_called_once()
                
                # Verify real database persistence
                db_checks = [
                    {
                        'table': 'hitl_agent_approvals',
                        'conditions': {'project_id': project.id, 'task_id': task.id},
                        'count': 1
                    }
                ]
                assert db_manager.verify_database_state(db_checks)

    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_budget_limit_check_success(self, db_manager):
        """Test successful budget limit check with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Budget Test Project")

        # Create real budget control record
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="analyst",
                daily_token_limit=10000,
                session_token_limit=2000,
                tokens_used_today=500,
                tokens_used_session=100,
                budget_reset_at=datetime.now(timezone.utc)
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

            hitl_service = HITLSafetyService(session)
            
            result = await hitl_service.check_budget_limits(project.id, "analyst", 1000)

            assert result.approved is True

    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_budget_limit_check_exceeded(self, db_manager):
        """Test budget limit exceeded with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Budget Exceeded Test")

        # Create real budget control record with exceeded limits
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="analyst",
                daily_token_limit=10000,
                session_token_limit=2000,
                tokens_used_today=9500,  # Near daily limit
                tokens_used_session=100,
                budget_reset_at=datetime.now(timezone.utc)
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

            hitl_service = HITLSafetyService(session)
            
            result = await hitl_service.check_budget_limits(project.id, "analyst", 1000)

            assert result.approved is False
            assert "daily limit" in result.reason

    @pytest.mark.asyncio
    @pytest.mark.external_service

    async def test_emergency_stop_trigger(self, db_manager):
        """Test emergency stop triggering with real database."""
        # Create real project
        project = db_manager.create_test_project(name="Emergency Stop Test")

        with db_manager.get_session() as session:
            hitl_service = HITLSafetyService(session)
            
            # Mock external dependencies only (WebSocket broadcast)
            with patch.object(hitl_service, '_broadcast_emergency_stop', new_callable=AsyncMock) as mock_broadcast:

                await hitl_service.trigger_emergency_stop(
                    project_id=project.id,
                    agent_type="analyst",
                    reason="Test emergency",
                    triggered_by="USER"
                )

                # Verify real database persistence
                db_checks = [
                    {
                        'table': 'emergency_stops',
                        'conditions': {'project_id': project.id, 'agent_type': 'analyst'},
                        'count': 1
                    }
                ]
                assert db_manager.verify_database_state(db_checks)
                mock_broadcast.assert_called_once()



    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_wait_for_approval_timeout(self, db_manager):
        """Test approval timeout handling with real database."""
        # Create real project and approval request
        project = db_manager.create_test_project(name="Timeout Test Project")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")

        with db_manager.get_session() as session:
            # Create real pending approval
            approval = HitlAgentApprovalDB(
                project_id=project.id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="PENDING",
                request_data={"test": "data"}
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)
            
            db_manager.track_test_record('hitl_agent_approvals', str(approval.id))

            hitl_service = HITLSafetyService(session)
            
            # Mock external sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(ApprovalTimeoutError):
                    await hitl_service.wait_for_approval(approval.id, timeout_minutes=0.001)

    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_wait_for_approval_approved(self, db_manager):
        """Test successful approval with real database."""
        # Create real project and approval request
        project = db_manager.create_test_project(name="Approval Test Project")
        task = db_manager.create_test_task(project_id=project.id, agent_type="analyst")

        with db_manager.get_session() as session:
            # Create real approved approval
            approval = HitlAgentApprovalDB(
                project_id=project.id,
                task_id=task.id,
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="APPROVED",
                user_response="approved",
                user_comment="Looks good",
                request_data={"test": "data"}
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)
            
            db_manager.track_test_record('hitl_agent_approvals', str(approval.id))

            hitl_service = HITLSafetyService(session)
            
            result = await hitl_service.wait_for_approval(approval.id)

            assert result.approved is True
            assert result.response == "approved"
            assert result.comment == "Looks good"





class TestBaseAgentHITLControls:
    """Test cases for BaseAgent HITL controls."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for agent HITL tests."""
        manager = DatabaseTestManager(use_memory_db=True)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()


