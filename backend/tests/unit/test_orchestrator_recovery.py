"""
Test suite for orchestrator recovery management.
Recovery logic is now integrated into orchestrator.py.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.orchestrator.recovery_manager import (
    RecoveryManager, 
    RecoveryStrategy, 
    RecoveryStep
)
from app.database.models import RecoverySessionDB, EmergencyStopDB
from tests.utils.database_test_utils import DatabaseTestManager


class TestOrchestratorRecovery:
    """Test orchestrator recovery integration."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create RecoveryManager instance."""
        return RecoveryManager()
    
    @pytest.fixture
    def sample_failure_context(self):
        """Sample failure context for testing."""
        return {
            "error_type": "timeout",
            "error_message": "Task execution timeout after 300 seconds",
            "agent_state": "working",
            "task_progress": 0.5,
            "retry_count": 2,
            "last_checkpoint": "analysis_phase"
        }
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager for testing."""
        mock_manager = AsyncMock()
        mock_manager.broadcast_to_project = AsyncMock()
        return mock_manager

    @pytest.mark.real_data
    async def test_recovery_manager_initialization(self, recovery_manager):
        """Test recovery manager initialization."""
        assert recovery_manager is not None
        assert isinstance(recovery_manager.active_sessions, dict)
        assert len(recovery_manager.active_sessions) == 0

    @pytest.mark.real_data
    async def test_recovery_strategy_determination(self, recovery_manager, sample_failure_context):
        """Test recovery strategy determination logic."""
        test_cases = [
            ("budget exceeded", {"budget_limit": 1000}, RecoveryStrategy.ABORT),
            ("timeout error", {"timeout": 300}, RecoveryStrategy.RETRY),
            ("emergency stop triggered", {"emergency": True}, RecoveryStrategy.ROLLBACK),
            ("validation failed", {"validation_error": "schema"}, RecoveryStrategy.CONTINUE),
            ("unknown error", {"unknown": True}, RecoveryStrategy.RETRY)
        ]
        
        for failure_reason, context, expected_strategy in test_cases:
            strategy = recovery_manager._determine_recovery_strategy(failure_reason, context)
            assert strategy == expected_strategy

    @pytest.mark.real_data
    async def test_recovery_step_creation_rollback(self, recovery_manager):
        """Test recovery step creation for rollback strategy."""
        steps = recovery_manager._create_recovery_steps(
            RecoveryStrategy.ROLLBACK, 
            {"checkpoint": "analysis_phase"}
        )
        
        assert len(steps) == 3
        assert steps[0].action_type == "rollback"
        assert steps[1].action_type == "verify"
        assert steps[2].action_type == "notify"
        
        # Verify step structure
        for step in steps:
            assert isinstance(step, RecoveryStep)
            assert step.step_id is not None
            assert step.description is not None
            assert step.status == "PENDING"

    @pytest.mark.real_data
    async def test_recovery_step_creation_retry(self, recovery_manager):
        """Test recovery step creation for retry strategy."""
        steps = recovery_manager._create_recovery_steps(
            RecoveryStrategy.RETRY,
            {"retry_count": 2}
        )
        
        assert len(steps) == 3
        assert steps[0].action_type == "analyze"
        assert steps[1].action_type == "retry"
        assert steps[2].action_type == "verify"

    @pytest.mark.real_data
    async def test_recovery_step_creation_continue(self, recovery_manager):
        """Test recovery step creation for continue strategy."""
        steps = recovery_manager._create_recovery_steps(
            RecoveryStrategy.CONTINUE,
            {"failed_step": "validation"}
        )
        
        assert len(steps) == 2
        assert steps[0].action_type == "skip"
        assert steps[1].action_type == "continue"

    @pytest.mark.real_data
    async def test_recovery_step_creation_abort(self, recovery_manager):
        """Test recovery step creation for abort strategy."""
        steps = recovery_manager._create_recovery_steps(
            RecoveryStrategy.ABORT,
            {"reason": "budget_exceeded"}
        )
        
        assert len(steps) == 3
        assert steps[0].action_type == "cleanup"
        assert steps[1].action_type == "abort"
        assert steps[2].action_type == "notify"

    @pytest.mark.real_data
    async def test_initiate_recovery_success(self, recovery_manager, db_manager, sample_failure_context, mock_websocket_manager):
        """Test successful recovery initiation."""
        project_id = uuid4()
        task_id = uuid4()
        agent_type = "analyst"
        failure_reason = "timeout error"
        
        with db_manager.get_session() as session:
            def mock_get_session():
                yield session
            
            with patch('app.services.orchestrator.recovery_manager.get_session', mock_get_session), \
                 patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
                
                session_id = await recovery_manager.initiate_recovery(
                    project_id=project_id,
                    task_id=task_id,
                    agent_type=agent_type,
                    failure_reason=failure_reason,
                    failure_context=sample_failure_context
                )
                
                # Verify session was created
                assert session_id is not None
                assert isinstance(session_id, UUID)
                
                # Verify session is in active sessions
                assert str(session_id) in recovery_manager.active_sessions
                
                # Verify database record was created
                recovery_session = session.query(RecoverySessionDB).filter(
                    RecoverySessionDB.id == session_id
                ).first()
                
                assert recovery_session is not None
                assert recovery_session.project_id == project_id
                assert recovery_session.task_id == task_id
                assert recovery_session.agent_type == agent_type
                assert recovery_session.failure_reason == failure_reason
                assert recovery_session.status == "INITIATED"
                
                # Verify WebSocket broadcast was called
                mock_websocket_manager.broadcast_to_project.assert_called_once()

    @pytest.mark.real_data
    async def test_initiate_recovery_with_emergency_stop(self, recovery_manager, db_manager, sample_failure_context, mock_websocket_manager):
        """Test recovery initiation with emergency stop."""
        project_id = uuid4()
        task_id = uuid4()
        agent_type = "analyst"
        failure_reason = "emergency stop triggered"
        emergency_stop_id = uuid4()
        
        with db_manager.get_session() as session:
            # Create emergency stop record
            emergency_stop = EmergencyStopDB(
                id=emergency_stop_id,
                project_id=project_id,
                reason="Budget exceeded",
                triggered_by="system",
                status="ACTIVE"
            )
            session.add(emergency_stop)
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.orchestrator.recovery_manager.get_session', mock_get_session), \
                 patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
                
                session_id = await recovery_manager.initiate_recovery(
                    project_id=project_id,
                    task_id=task_id,
                    agent_type=agent_type,
                    failure_reason=failure_reason,
                    failure_context=sample_failure_context,
                    emergency_stop_id=emergency_stop_id
                )
                
                # Verify recovery session links to emergency stop
                recovery_session = session.query(RecoverySessionDB).filter(
                    RecoverySessionDB.id == session_id
                ).first()
                
                assert recovery_session.emergency_stop_id == emergency_stop_id

    @pytest.mark.real_data
    async def test_recovery_step_execution(self, recovery_manager):
        """Test recovery step execution."""
        # Create a recovery step
        step = RecoveryStep(
            step_id="test_step_1",
            description="Test recovery step",
            action_type="rollback",
            parameters={"checkpoint": "analysis_phase"},
            requires_approval=False,
            timeout_seconds=60
        )
        
        # Verify initial state
        assert step.status == "PENDING"
        assert step.started_at is None
        assert step.completed_at is None
        
        # Test step to_dict conversion
        step_dict = step.to_dict()
        assert isinstance(step_dict, dict)
        assert step_dict["step_id"] == "test_step_1"
        assert step_dict["action_type"] == "rollback"
        assert step_dict["status"] == "PENDING"
        assert step_dict["parameters"]["checkpoint"] == "analysis_phase"

    @pytest.mark.real_data
    async def test_recovery_step_with_approval(self, recovery_manager):
        """Test recovery step that requires approval."""
        step = RecoveryStep(
            step_id="approval_step",
            description="Step requiring human approval",
            action_type="rollback",
            requires_approval=True,
            timeout_seconds=300
        )
        
        assert step.requires_approval is True
        assert step.timeout_seconds == 300

    @pytest.mark.real_data
    async def test_recovery_session_tracking(self, recovery_manager, db_manager, sample_failure_context, mock_websocket_manager):
        """Test recovery session tracking in active sessions."""
        project_id = uuid4()
        task_id = uuid4()
        
        with db_manager.get_session() as session:
            def mock_get_session():
                yield session
            
            with patch('app.services.orchestrator.recovery_manager.get_session', mock_get_session), \
                 patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
                
                session_id = await recovery_manager.initiate_recovery(
                    project_id=project_id,
                    task_id=task_id,
                    agent_type="analyst",
                    failure_reason="test failure",
                    failure_context=sample_failure_context
                )
                
                # Verify session tracking
                active_session = recovery_manager.active_sessions[str(session_id)]
                assert "session" in active_session
                assert "steps" in active_session
                assert "strategy" in active_session
                
                assert isinstance(active_session["strategy"], RecoveryStrategy)
                assert isinstance(active_session["steps"], list)
                assert len(active_session["steps"]) > 0

    @pytest.mark.real_data
    async def test_broadcast_recovery_event(self, recovery_manager, db_manager, mock_websocket_manager):
        """Test recovery event broadcasting."""
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            # Create a recovery session
            recovery_session = RecoverySessionDB(
                project_id=project_id,
                task_id=uuid4(),
                agent_type="analyst",
                failure_reason="test failure",
                failure_context={"test": "context"},
                recovery_strategy="RETRY",
                recovery_steps=[],
                current_step=0,
                total_steps=3,
                status="INITIATED"
            )
            session.add(recovery_session)
            session.commit()
            session.refresh(recovery_session)
            
            with patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
                await recovery_manager._broadcast_recovery_event(recovery_session, "STARTED")
                
                # Verify WebSocket broadcast was called with correct data
                mock_websocket_manager.broadcast_to_project.assert_called_once()
                call_args = mock_websocket_manager.broadcast_to_project.call_args
                
                project_id_arg = call_args[0][0]
                event_arg = call_args[0][1]
                
                assert project_id_arg == str(project_id)
                assert event_arg.type.value == "RECOVERY_UPDATE"
                assert event_arg.data["session_id"] == str(recovery_session.id)
                assert event_arg.data["event_type"] == "STARTED"
                assert event_arg.data["strategy"] == "RETRY"

    @pytest.mark.real_data
    async def test_recovery_failure_context_analysis(self, recovery_manager):
        """Test analysis of different failure contexts."""
        failure_contexts = [
            {
                "context": {"budget_used": 950, "budget_limit": 1000},
                "reason": "budget approaching limit",
                "expected_strategy": RecoveryStrategy.ABORT
            },
            {
                "context": {"timeout_duration": 300, "max_timeout": 600},
                "reason": "timeout occurred",
                "expected_strategy": RecoveryStrategy.RETRY
            },
            {
                "context": {"emergency_triggered": True, "trigger_reason": "safety"},
                "reason": "emergency stop",
                "expected_strategy": RecoveryStrategy.ROLLBACK
            },
            {
                "context": {"validation_errors": ["schema_error"], "severity": "low"},
                "reason": "validation issues",
                "expected_strategy": RecoveryStrategy.CONTINUE
            }
        ]
        
        for test_case in failure_contexts:
            strategy = recovery_manager._determine_recovery_strategy(
                test_case["reason"],
                test_case["context"]
            )
            assert strategy == test_case["expected_strategy"]

    @pytest.mark.real_data
    async def test_recovery_step_parameters(self, recovery_manager):
        """Test recovery step parameter handling."""
        # Test step with complex parameters
        step = RecoveryStep(
            step_id="complex_step",
            description="Step with complex parameters",
            action_type="rollback",
            parameters={
                "checkpoint": "analysis_phase",
                "preserve_data": True,
                "cleanup_temp_files": False,
                "notification_targets": ["admin@example.com"],
                "retry_config": {
                    "max_retries": 3,
                    "backoff_multiplier": 2.0
                }
            }
        )
        
        step_dict = step.to_dict()
        params = step_dict["parameters"]
        
        assert params["checkpoint"] == "analysis_phase"
        assert params["preserve_data"] is True
        assert params["cleanup_temp_files"] is False
        assert params["notification_targets"] == ["admin@example.com"]
        assert params["retry_config"]["max_retries"] == 3

    @pytest.mark.real_data
    async def test_recovery_manager_error_handling(self, recovery_manager, mock_websocket_manager):
        """Test recovery manager error handling."""
        project_id = uuid4()
        task_id = uuid4()
        
        # Mock database session to raise an error
        def mock_get_session():
            raise Exception("Database connection failed")
        
        with patch('app.services.orchestrator.recovery_manager.get_session', mock_get_session), \
             patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
            
            # Should handle database errors gracefully
            with pytest.raises(Exception, match="Database connection failed"):
                await recovery_manager.initiate_recovery(
                    project_id=project_id,
                    task_id=task_id,
                    agent_type="analyst",
                    failure_reason="test failure",
                    failure_context={}
                )

    @pytest.mark.real_data
    async def test_multiple_concurrent_recovery_sessions(self, recovery_manager, db_manager, mock_websocket_manager):
        """Test handling multiple concurrent recovery sessions."""
        project_id = uuid4()
        
        with db_manager.get_session() as session:
            def mock_get_session():
                yield session
            
            with patch('app.services.orchestrator.recovery_manager.get_session', mock_get_session), \
                 patch('app.services.orchestrator.recovery_manager.websocket_manager', mock_websocket_manager):
                
                # Create multiple recovery sessions
                session_ids = []
                for i in range(3):
                    session_id = await recovery_manager.initiate_recovery(
                        project_id=project_id,
                        task_id=uuid4(),
                        agent_type="analyst",
                        failure_reason=f"failure_{i}",
                        failure_context={"iteration": i}
                    )
                    session_ids.append(session_id)
                
                # Verify all sessions are tracked
                assert len(recovery_manager.active_sessions) == 3
                
                for session_id in session_ids:
                    assert str(session_id) in recovery_manager.active_sessions
                
                # Verify database records
                recovery_sessions = session.query(RecoverySessionDB).filter(
                    RecoverySessionDB.project_id == project_id
                ).all()
                
                assert len(recovery_sessions) == 3