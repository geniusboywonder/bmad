"""
Test suite for enhanced startup service.
Includes HITL cleanup and simplified Redis configuration.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from uuid import uuid4

from app.services.startup_service import StartupService, startup_service
from app.database.models import AgentStatusDB, TaskDB, HitlAgentApprovalDB
from app.models.agent import AgentStatus, AgentType
from app.models.task import TaskStatus
from tests.utils.database_test_utils import DatabaseTestManager


class TestEnhancedStartupService:
    """Test enhanced startup service with HITL cleanup."""
    
    @pytest.fixture
    def startup_service_instance(self):
        """Create StartupService instance for testing."""
        return StartupService()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing."""
        mock_client = Mock()
        mock_client.keys.return_value = ["test_key_1", "test_key_2"]
        mock_client.delete.return_value = 2
        mock_client.exists.return_value = True
        return mock_client
    
    @pytest.fixture
    def mock_celery_app(self):
        """Mock Celery app for testing."""
        mock_app = Mock()
        mock_app.control.purge.return_value = 5
        return mock_app

    # Redis Cleanup Tests
    
    @pytest.mark.real_data
    async def test_flush_redis_queues_success(self, startup_service_instance, mock_redis_client):
        """Test successful Redis queue flushing."""
        with patch.object(startup_service_instance, '_get_redis_client', return_value=mock_redis_client):
            result = await startup_service_instance.flush_redis_queues()
            
            assert result is True
            
            # Verify Redis operations were called
            mock_redis_client.keys.assert_called()
            mock_redis_client.delete.assert_called()

    @pytest.mark.real_data
    async def test_flush_redis_queues_with_patterns(self, startup_service_instance, mock_redis_client):
        """Test Redis queue flushing with wildcard patterns."""
        # Mock different key patterns
        def mock_keys(pattern):
            if pattern == "bmad:*":
                return ["bmad:session:1", "bmad:session:2"]
            elif pattern == "_kombu.binding.*":
                return ["_kombu.binding.celery", "_kombu.binding.agent_tasks"]
            else:
                return []
        
        mock_redis_client.keys.side_effect = mock_keys
        
        with patch.object(startup_service_instance, '_get_redis_client', return_value=mock_redis_client):
            result = await startup_service_instance.flush_redis_queues()
            
            assert result is True
            
            # Verify pattern-based key deletion
            expected_calls = ["bmad:*", "_kombu.binding.*", "_kombu.*"]
            for pattern in expected_calls:
                mock_redis_client.keys.assert_any_call(pattern)

    @pytest.mark.real_data
    async def test_flush_redis_queues_error_handling(self, startup_service_instance):
        """Test Redis queue flushing error handling."""
        mock_redis_client = Mock()
        mock_redis_client.keys.side_effect = Exception("Redis connection error")
        
        with patch.object(startup_service_instance, '_get_redis_client', return_value=mock_redis_client):
            result = await startup_service_instance.flush_redis_queues()
            
            assert result is False

    @pytest.mark.real_data
    async def test_startup_redis_single_db_cleanup(self, startup_service_instance):
        """Test Redis cleanup with single database configuration."""
        mock_redis_client = Mock()
        mock_redis_client.keys.return_value = [
            "celery:task:1", 
            "websocket:session:1", 
            "cache:data:1"
        ]
        mock_redis_client.delete.return_value = 3
        
        with patch.object(startup_service_instance, '_get_redis_client', return_value=mock_redis_client):
            result = await startup_service_instance.flush_redis_queues()
            
            assert result is True
            
            # Verify single Redis database is used (no separate DB1/DB0 logic)
            # All keys should be handled by single client instance
            mock_redis_client.keys.assert_called()
            mock_redis_client.delete.assert_called()

    # Celery Cleanup Tests
    
    @pytest.mark.real_data
    async def test_purge_celery_queues_success(self, startup_service_instance, mock_celery_app):
        """Test successful Celery queue purging."""
        startup_service_instance.celery_app = mock_celery_app
        
        result = await startup_service_instance.purge_celery_queues()
        
        assert result is True
        mock_celery_app.control.purge.assert_called()

    @pytest.mark.real_data
    async def test_purge_celery_queues_error_handling(self, startup_service_instance):
        """Test Celery queue purging error handling."""
        mock_celery_app = Mock()
        mock_celery_app.control.purge.side_effect = Exception("Celery connection error")
        startup_service_instance.celery_app = mock_celery_app
        
        result = await startup_service_instance.purge_celery_queues()
        
        assert result is False

    # Agent Status Reset Tests
    
    @pytest.mark.real_data
    async def test_reset_agent_statuses_success(self, startup_service_instance, db_manager):
        """Test successful agent status reset."""
        with db_manager.get_session() as session:
            # Create test agent status records
            working_agent = AgentStatusDB(
                agent_type=AgentType.ANALYST,
                status=AgentStatus.WORKING,
                current_task_id=uuid4(),
                error_message="Previous error"
            )
            session.add(working_agent)
            session.commit()
            
            # Mock the database session generator
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.reset_agent_statuses()
                
                assert result is True
                
                # Verify agent status was reset
                session.refresh(working_agent)
                assert working_agent.status == AgentStatus.IDLE
                assert working_agent.current_task_id is None
                assert working_agent.error_message is None

    @pytest.mark.real_data
    async def test_reset_agent_statuses_creates_missing_agents(self, startup_service_instance, db_manager):
        """Test agent status reset creates missing standard agent records."""
        with db_manager.get_session() as session:
            # Start with empty agent status table
            session.query(AgentStatusDB).delete()
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.reset_agent_statuses()
                
                assert result is True
                
                # Verify all standard agents were created
                agent_statuses = session.query(AgentStatusDB).all()
                agent_types = {agent.agent_type for agent in agent_statuses}
                
                expected_types = {
                    AgentType.ANALYST, 
                    AgentType.ARCHITECT, 
                    AgentType.CODER, 
                    AgentType.TESTER, 
                    AgentType.DEPLOYER
                }
                assert agent_types == expected_types
                
                # All should be IDLE
                for agent in agent_statuses:
                    assert agent.status == AgentStatus.IDLE

    @pytest.mark.real_data
    async def test_reset_agent_statuses_error_handling(self, startup_service_instance):
        """Test agent status reset error handling."""
        def mock_get_session():
            raise Exception("Database connection error")
        
        with patch('app.services.startup_service.get_session', mock_get_session):
            result = await startup_service_instance.reset_agent_statuses()
            
            assert result is False

    # Task Reset Tests
    
    @pytest.mark.real_data
    async def test_reset_pending_tasks_success(self, startup_service_instance, db_manager):
        """Test successful pending task reset."""
        with db_manager.get_session() as session:
            # Create test tasks in various states
            pending_task = TaskDB(
                project_id=uuid4(),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.PENDING,
                instructions="Test pending task"
            )
            working_task = TaskDB(
                project_id=uuid4(),
                agent_type=AgentType.CODER,
                status=TaskStatus.WORKING,
                instructions="Test working task"
            )
            completed_task = TaskDB(
                project_id=uuid4(),
                agent_type=AgentType.TESTER,
                status=TaskStatus.COMPLETED,
                instructions="Test completed task"
            )
            
            session.add_all([pending_task, working_task, completed_task])
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.reset_pending_tasks()
                
                assert result is True
                
                # Verify pending/working tasks were cancelled
                session.refresh(pending_task)
                session.refresh(working_task)
                session.refresh(completed_task)
                
                assert pending_task.status == TaskStatus.CANCELLED
                assert working_task.status == TaskStatus.CANCELLED
                assert completed_task.status == TaskStatus.COMPLETED  # Unchanged
                
                # Verify error messages were set
                assert "server restart" in pending_task.error_message.lower()
                assert "server restart" in working_task.error_message.lower()

    @pytest.mark.real_data
    async def test_reset_pending_tasks_no_pending_tasks(self, startup_service_instance, db_manager):
        """Test pending task reset when no pending tasks exist."""
        with db_manager.get_session() as session:
            # Create only completed tasks
            completed_task = TaskDB(
                project_id=uuid4(),
                agent_type=AgentType.ANALYST,
                status=TaskStatus.COMPLETED,
                instructions="Test completed task"
            )
            session.add(completed_task)
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.reset_pending_tasks()
                
                assert result is True
                
                # Completed task should remain unchanged
                session.refresh(completed_task)
                assert completed_task.status == TaskStatus.COMPLETED

    # HITL Cleanup Tests
    
    @pytest.mark.real_data
    async def test_startup_hitl_cleanup(self, startup_service_instance, db_manager):
        """Test HITL approval cleanup on startup."""
        with db_manager.get_session() as session:
            now = datetime.now(timezone.utc)
            
            # Create test HITL approval records
            pending_approval = HitlAgentApprovalDB(
                project_id=uuid4(),
                task_id=uuid4(),
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="PENDING",
                estimated_tokens=100,
                estimated_cost=0.002,
                expires_at=now + timedelta(minutes=30)
            )
            
            expired_approval = HitlAgentApprovalDB(
                project_id=uuid4(),
                task_id=uuid4(),
                agent_type="coder",
                request_type="PRE_EXECUTION",
                status="PENDING",
                estimated_tokens=200,
                estimated_cost=0.004,
                expires_at=now - timedelta(minutes=10)  # Expired
            )
            
            approved_approval = HitlAgentApprovalDB(
                project_id=uuid4(),
                task_id=uuid4(),
                agent_type="tester",
                request_type="PRE_EXECUTION",
                status="APPROVED",
                estimated_tokens=150,
                estimated_cost=0.003,
                expires_at=now + timedelta(minutes=15)
            )
            
            session.add_all([pending_approval, expired_approval, approved_approval])
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.cleanup_stale_hitl_approvals()
                
                assert result is True
                
                # Verify pending approvals were rejected
                session.refresh(pending_approval)
                session.refresh(expired_approval)
                session.refresh(approved_approval)
                
                assert pending_approval.status == "REJECTED"
                assert expired_approval.status == "REJECTED"
                assert approved_approval.status == "APPROVED"  # Unchanged
                
                # Verify rejection reasons
                assert "server restart" in pending_approval.user_response.lower()
                assert "server restart" in expired_approval.user_response.lower()
                assert pending_approval.responded_at is not None

    @pytest.mark.real_data
    async def test_cleanup_stale_hitl_approvals_no_pending(self, startup_service_instance, db_manager):
        """Test HITL cleanup when no pending approvals exist."""
        with db_manager.get_session() as session:
            # Create only approved/rejected approvals
            approved_approval = HitlAgentApprovalDB(
                project_id=uuid4(),
                task_id=uuid4(),
                agent_type="analyst",
                request_type="PRE_EXECUTION",
                status="APPROVED",
                estimated_tokens=100,
                estimated_cost=0.002
            )
            session.add(approved_approval)
            session.commit()
            
            def mock_get_session():
                yield session
            
            with patch('app.services.startup_service.get_session', mock_get_session):
                result = await startup_service_instance.cleanup_stale_hitl_approvals()
                
                assert result is True
                
                # Approved approval should remain unchanged
                session.refresh(approved_approval)
                assert approved_approval.status == "APPROVED"

    # Complete Startup Cleanup Tests
    
    @pytest.mark.real_data
    async def test_perform_startup_cleanup_success(self, startup_service_instance):
        """Test complete startup cleanup sequence success."""
        # Mock all cleanup methods to succeed
        with patch.object(startup_service_instance, 'flush_redis_queues', return_value=True), \
             patch.object(startup_service_instance, 'purge_celery_queues', return_value=True), \
             patch.object(startup_service_instance, 'reset_agent_statuses', return_value=True), \
             patch.object(startup_service_instance, 'reset_pending_tasks', return_value=True), \
             patch.object(startup_service_instance, 'cleanup_stale_hitl_approvals', return_value=True):
            
            results = await startup_service_instance.perform_startup_cleanup()
            
            # Verify all steps succeeded
            assert results["redis_flush"] is True
            assert results["celery_purge"] is True
            assert results["agent_reset"] is True
            assert results["task_reset"] is True
            assert results["hitl_cleanup"] is True
            assert results["overall_success"] is True

    @pytest.mark.real_data
    async def test_perform_startup_cleanup_partial_failure(self, startup_service_instance):
        """Test startup cleanup with some failures."""
        # Mock some methods to fail
        with patch.object(startup_service_instance, 'flush_redis_queues', return_value=False), \
             patch.object(startup_service_instance, 'purge_celery_queues', return_value=True), \
             patch.object(startup_service_instance, 'reset_agent_statuses', return_value=True), \
             patch.object(startup_service_instance, 'reset_pending_tasks', return_value=False), \
             patch.object(startup_service_instance, 'cleanup_stale_hitl_approvals', return_value=True):
            
            results = await startup_service_instance.perform_startup_cleanup()
            
            # Verify partial success
            assert results["redis_flush"] is False
            assert results["celery_purge"] is True
            assert results["agent_reset"] is True
            assert results["task_reset"] is False
            assert results["hitl_cleanup"] is True
            assert results["overall_success"] is False

    @pytest.mark.real_data
    async def test_perform_startup_cleanup_complete_failure(self, startup_service_instance):
        """Test startup cleanup with all failures."""
        # Mock all methods to fail
        with patch.object(startup_service_instance, 'flush_redis_queues', return_value=False), \
             patch.object(startup_service_instance, 'purge_celery_queues', return_value=False), \
             patch.object(startup_service_instance, 'reset_agent_statuses', return_value=False), \
             patch.object(startup_service_instance, 'reset_pending_tasks', return_value=False), \
             patch.object(startup_service_instance, 'cleanup_stale_hitl_approvals', return_value=False):
            
            results = await startup_service_instance.perform_startup_cleanup()
            
            # Verify complete failure
            assert all(not results[key] for key in results if key != "overall_success")
            assert results["overall_success"] is False

    # Singleton Service Tests
    
    @pytest.mark.mock_data
    def test_startup_service_singleton(self):
        """Test that startup_service is properly initialized."""
        from app.services.startup_service import startup_service
        
        assert startup_service is not None
        assert isinstance(startup_service, StartupService)

    # Redis Client Tests
    
    @pytest.mark.mock_data
    def test_get_redis_client_initialization(self, startup_service_instance):
        """Test Redis client initialization."""
        with patch('app.services.startup_service.redis.from_url') as mock_from_url:
            mock_client = Mock()
            mock_from_url.return_value = mock_client
            
            client = startup_service_instance._get_redis_client()
            
            assert client == mock_client
            mock_from_url.assert_called_once()

    @pytest.mark.mock_data
    def test_get_redis_client_reuse(self, startup_service_instance):
        """Test Redis client reuse on subsequent calls."""
        mock_client = Mock()
        startup_service_instance.redis_client = mock_client
        
        client = startup_service_instance._get_redis_client()
        
        assert client == mock_client

    # Error Recovery Tests
    
    @pytest.mark.real_data
    async def test_database_session_cleanup_on_error(self, startup_service_instance):
        """Test proper database session cleanup on errors."""
        def mock_get_session():
            session = Mock()
            session.query.side_effect = Exception("Database error")
            yield session
        
        with patch('app.services.startup_service.get_session', mock_get_session):
            # Should handle error gracefully and not leave sessions open
            result = await startup_service_instance.reset_agent_statuses()
            
            assert result is False

    @pytest.mark.real_data
    async def test_redis_connection_recovery(self, startup_service_instance):
        """Test Redis connection error recovery."""
        mock_redis_client = Mock()
        # First call fails, second succeeds
        mock_redis_client.keys.side_effect = [Exception("Connection error"), ["key1"]]
        mock_redis_client.delete.return_value = 1
        
        with patch.object(startup_service_instance, '_get_redis_client', return_value=mock_redis_client):
            # First attempt should fail
            result1 = await startup_service_instance.flush_redis_queues()
            assert result1 is False
            
            # Reset side effect for second attempt
            mock_redis_client.keys.side_effect = None
            mock_redis_client.keys.return_value = ["key1"]
            
            # Second attempt should succeed
            result2 = await startup_service_instance.flush_redis_queues()
            assert result2 is True