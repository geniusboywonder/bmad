"""Tests for HITL Safety Architecture with Real Database."""

import pytest
import asyncio
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
from app.services.recovery_procedure_manager import RecoveryProcedureManager, RecoveryStrategy
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


class TestHITLSafetyServiceRealDB:
    """Test cases for HITL Safety Service with real database."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for HITL tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.fixture
    def hitl_service(self):
        """Create HITL safety service instance."""
        return HITLSafetyService()



    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_create_approval_request_success_real_db(self, hitl_service, db_manager):
        """Test successful approval request creation with real database."""
        # Create test scenario
        project = db_manager.create_test_project()
        task = db_manager.create_test_task(project_id=project.id)

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            approval_id = await hitl_service.create_approval_request(
                project_id=project.id,
                task_id=task.id,
                agent_type="TEST_AGENT",
                request_type="PRE_EXECUTION",
                request_data={"test": "data"},
                estimated_tokens=100
            )

            assert approval_id is not None

            # Verify approval was created in database
            with db_manager.get_session() as session:
                approval = session.query(HitlAgentApprovalDB).filter_by(id=approval_id).first()
                assert approval is not None
                assert approval.agent_type == "TEST_AGENT"
                assert approval.request_type == "PRE_EXECUTION"
                assert approval.estimated_tokens == 100

            db_manager.track_test_record('hitl_agent_approvals', str(approval_id))

        finally:
            hitl_service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_budget_limit_check_success_real_db(self, hitl_service, db_manager):
        """Test successful budget limit check with real database."""
        # Create test scenario
        project = db_manager.create_test_project()

        # Create budget control
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                tokens_used_today=500,
                tokens_used_session=100,
                daily_token_limit=10000,
                session_token_limit=2000,
                budget_reset_at=datetime.now(timezone.utc),
                emergency_stop_enabled=False
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            result = await hitl_service.check_budget_limits(project.id, "TEST_AGENT", 1000)

            assert result.approved is True

            # Verify budget calculations are correct
            with db_manager.get_session() as session:
                updated_budget = session.query(AgentBudgetControlDB).filter_by(
                    project_id=project.id,
                    agent_type="TEST_AGENT"
                ).first()
                assert updated_budget.tokens_used_today == 500  # Should not be updated yet
                assert updated_budget.tokens_used_session == 100

        finally:
            hitl_service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_budget_limit_check_exceeded_real_db(self, hitl_service, db_manager):
        """Test budget limit exceeded with real database."""
        # Create test scenario
        project = db_manager.create_test_project()

        # Create budget control with exceeded limits
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                tokens_used_today=9500,  # Very close to limit
                tokens_used_session=100,
                daily_token_limit=10000,
                session_token_limit=2000,
                budget_reset_at=datetime.now(timezone.utc),
                emergency_stop_enabled=False
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            result = await hitl_service.check_budget_limits(project.id, "TEST_AGENT", 1000)

            assert result.approved is False
            assert "daily limit" in result.reason

        finally:
            hitl_service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_emergency_stop_trigger_real_db(self, hitl_service, db_manager):
        """Test emergency stop triggering with real database."""
        # Create test scenario
        project = db_manager.create_test_project()

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            stop_id = await hitl_service.trigger_emergency_stop(
                project_id=project.id,
                agent_type="TEST_AGENT",
                reason="Test emergency",
                triggered_by="USER"
            )

            assert stop_id is not None

            # Verify emergency stop was created in database
            with db_manager.get_session() as session:
                stop = session.query(EmergencyStopDB).filter_by(id=stop_id).first()
                assert stop is not None
                assert stop.agent_type == "TEST_AGENT"
                assert stop.stop_reason == "Test emergency"
                assert stop.triggered_by == "USER"
                assert stop.active is True  # Real boolean field!

            db_manager.track_test_record('emergency_stops', str(stop_id))

            # Verify emergency stop was added to active stops
            assert str(stop_id) in hitl_service.emergency_stops

        finally:
            hitl_service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_emergency_stop_deactivation_real_db(self, hitl_service, db_manager):
        """Test emergency stop deactivation with real database."""
        # Create test scenario
        project = db_manager.create_test_project()

        # Create emergency stop
        with db_manager.get_session() as session:
            stop = EmergencyStopDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                stop_reason="Test stop",
                triggered_by="USER",
                active=True
            )
            session.add(stop)
            session.commit()
            session.refresh(stop)
            db_manager.track_test_record('emergency_stops', str(stop.id))
            stop_id = stop.id

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            await hitl_service.deactivate_emergency_stop(stop_id)

            # Verify deactivation in database
            with db_manager.get_session() as session:
                updated_stop = session.query(EmergencyStopDB).filter_by(id=stop_id).first()
                assert updated_stop.active is False  # Real boolean field!
                assert updated_stop.deactivated_at is not None

        finally:
            hitl_service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.asyncio
    async def test_budget_usage_update_real_db(self, hitl_service, db_manager):
        """Test budget usage update with real database."""
        # Create test scenario
        project = db_manager.create_test_project()

        # Create budget control
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                tokens_used_today=500,
                tokens_used_session=100,
                daily_token_limit=10000,
                session_token_limit=2000,
                budget_reset_at=datetime.now(timezone.utc),
                emergency_stop_enabled=False
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

        # Override get_session to use our test database
        original_get_session = hitl_service._get_session
        hitl_service._get_session = lambda: db_manager.get_session()

        try:
            await hitl_service.update_budget_usage(project.id, "TEST_AGENT", 200)

            # Verify budget was updated in database
            with db_manager.get_session() as session:
                updated_budget = session.query(AgentBudgetControlDB).filter_by(
                    project_id=project.id,
                    agent_type="TEST_AGENT"
                ).first()
                assert updated_budget.tokens_used_today == 700
                assert updated_budget.tokens_used_session == 300

        finally:
            hitl_service._get_session = original_get_session


class TestHITLIntegrationRealDB:
    """Integration tests for HITL Safety system with real database."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for integration tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_full_hitl_workflow_real_db(self, db_manager):
        """Test complete HITL workflow from request to approval with real database."""
        service = HITLSafetyService()

        # Create test scenario
        project = db_manager.create_test_project()
        task = db_manager.create_test_task(project_id=project.id)

        # Override get_session to use our test database
        original_get_session = service._get_session
        service._get_session = lambda: db_manager.get_session()

        try:
            # Step 1: Create approval request
            approval_id = await service.create_approval_request(
                project_id=project.id,
                task_id=task.id,
                agent_type="TEST_AGENT",
                request_type="PRE_EXECUTION",
                request_data={"test": "workflow"}
            )

            assert approval_id is not None
            db_manager.track_test_record('hitl_agent_approvals', str(approval_id))

            # Verify approval was created in database
            with db_manager.get_session() as session:
                approval = session.query(HitlAgentApprovalDB).filter_by(id=approval_id).first()
                assert approval is not None
                assert approval.status == "PENDING"

            # Step 2: Simulate approval by updating database directly
            with db_manager.get_session() as session:
                approval = session.query(HitlAgentApprovalDB).filter_by(id=approval_id).first()
                approval.status = "APPROVED"
                approval.user_response = "approved"
                approval.user_comment = "Proceed"
                approval.approved_at = datetime.now(timezone.utc)
                session.commit()

            # Step 3: Wait for approval (should return immediately since approved)
            result = await service.wait_for_approval(approval_id, timeout_minutes=0.001)

            assert result.approved is True
            assert result.response == "approved"
            assert result.comment == "Proceed"

        finally:
            service._get_session = original_get_session

    @pytest.mark.real_data
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_budget_limit_workflow_real_db(self, db_manager):
        """Test budget limit enforcement workflow with real database."""
        service = HITLSafetyService()

        # Create test scenario
        project = db_manager.create_test_project()

        # Create budget control
        with db_manager.get_session() as session:
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                tokens_used_today=1000,
                tokens_used_session=500,
                daily_token_limit=10000,
                session_token_limit=2000,
                budget_reset_at=datetime.now(timezone.utc).date(),
                emergency_stop_enabled=False
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            db_manager.track_test_record('agent_budget_controls', str(budget.id))

        # Override get_session to use our test database
        original_get_session = service._get_session
        service._get_session = lambda: db_manager.get_session()

        try:
            # Test budget checking
            result = await service.check_budget_limits(project.id, "TEST_AGENT", 500)
            assert result.approved is True

            # Test budget update
            await service.update_budget_usage(project.id, "TEST_AGENT", 200)

            # Verify update in database
            with db_manager.get_session() as session:
                updated_budget = session.query(AgentBudgetControlDB).filter_by(
                    project_id=project.id,
                    agent_type="TEST_AGENT"
                ).first()
                assert updated_budget.tokens_used_today == 1200
                assert updated_budget.tokens_used_session == 700

        finally:
            service._get_session = original_get_session


class TestHITLBooleanFieldValidation:
    """Test that boolean fields work correctly in HITL safety models."""

    @pytest.fixture
    def db_manager(self):
        """Real database manager for boolean field tests."""
        manager = DatabaseTestManager(use_memory_db=False)
        manager.setup_test_database()
        yield manager
        manager.cleanup_test_database()

    @pytest.mark.real_data
    @pytest.mark.database_schema
    def test_emergency_stop_boolean_field_real_db(self, db_manager):
        """Test EmergencyStopDB active boolean field with real database."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            # Create emergency stop with boolean field
            stop = EmergencyStopDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                stop_reason="Boolean field test",
                triggered_by="USER",
                active=True  # Boolean field!
            )
            session.add(stop)
            session.commit()
            session.refresh(stop)

            # Verify boolean type is preserved
            assert stop.active is True
            assert isinstance(stop.active, bool)

            # Test updating boolean field
            stop.active = False
            session.commit()
            session.refresh(stop)

            assert stop.active is False
            assert isinstance(stop.active, bool)

            db_manager.track_test_record('emergency_stops', str(stop.id))

    @pytest.mark.real_data
    @pytest.mark.database_schema
    def test_agent_budget_control_boolean_field_real_db(self, db_manager):
        """Test AgentBudgetControlDB emergency_stop_enabled boolean field."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            # Create budget control with boolean field
            budget = AgentBudgetControlDB(
                project_id=project.id,
                agent_type="TEST_AGENT",
                emergency_stop_enabled=True,  # Boolean field!
                daily_token_limit=10000,
                session_token_limit=2000
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)

            # Verify boolean type is preserved
            assert budget.emergency_stop_enabled is True
            assert isinstance(budget.emergency_stop_enabled, bool)

            # Test updating boolean field
            budget.emergency_stop_enabled = False
            session.commit()
            session.refresh(budget)

            assert budget.emergency_stop_enabled is False
            assert isinstance(budget.emergency_stop_enabled, bool)

            db_manager.track_test_record('agent_budget_controls', str(budget.id))

    @pytest.mark.real_data
    @pytest.mark.database_schema
    def test_response_approval_boolean_field_real_db(self, db_manager):
        """Test ResponseApprovalDB auto_approved boolean field."""
        project = db_manager.create_test_project()

        with db_manager.get_session() as session:
            # Create response approval with boolean field
            approval = ResponseApprovalDB(
                project_id=project.id,
                approval_request_id=uuid4(),
                agent_type="TEST_AGENT",
                content_safety_score=0.95,
                code_validation_score=0.90,
                auto_approved=True,  # Boolean field!
                analysis_result={"test": "data"}
            )
            session.add(approval)
            session.commit()
            session.refresh(approval)

            # Verify boolean type is preserved
            assert approval.auto_approved is True
            assert isinstance(approval.auto_approved, bool)

            # Test updating boolean field
            approval.auto_approved = False
            session.commit()
            session.refresh(approval)

            assert approval.auto_approved is False
            assert isinstance(approval.auto_approved, bool)

            db_manager.track_test_record('response_approvals', str(approval.id))

    @pytest.mark.real_data
    @pytest.mark.database_schema
    def test_websocket_notification_boolean_fields_real_db(self, db_manager):
        """Test WebSocketNotificationDB delivered and expired boolean fields."""
        with db_manager.get_session() as session:
            # Create notification with boolean fields
            notification = WebSocketNotificationDB(
                event_type="TEST_EVENT",
                title="Test Notification",
                message="Testing boolean fields",
                delivered=True,  # Boolean field!
                expired=False    # Boolean field!
            )
            session.add(notification)
            session.commit()
            session.refresh(notification)

            # Verify boolean types are preserved
            assert notification.delivered is True
            assert isinstance(notification.delivered, bool)
            assert notification.expired is False
            assert isinstance(notification.expired, bool)

            # Test updating boolean fields
            notification.delivered = False
            notification.expired = True
            session.commit()
            session.refresh(notification)

            assert notification.delivered is False
            assert isinstance(notification.delivered, bool)
            assert notification.expired is True
            assert isinstance(notification.expired, bool)

            db_manager.track_test_record('websocket_notifications', str(notification.id))