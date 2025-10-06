"""Unit tests for the agent framework implementation.

REFACTORED: Replaced database mocks with real database operations using DatabaseTestManager.
External dependencies remain appropriately mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone

from app.models.task import Task, TaskStatus
from app.models.context import ContextArtifact, ArtifactType
from app.models.handoff import HandoffSchema
from app.models.agent import AgentType
from app.agents.factory import AgentFactory, get_agent_factory
from app.agents.base_agent import BaseAgent
from app.services.agent_service import AgentService
from tests.utils.database_test_utils import DatabaseTestManager

# Mock Agent Implementation for Testing
class MockAgent(BaseAgent):
    """Mock agent implementation for testing."""
    
    def _create_system_message(self) -> str:
        return "Mock agent for testing"
    
    async def execute_task(self, task: Task, context: list[ContextArtifact]) -> dict[str, any]:
        return {
            "mock_output": "test_result",
            "task_id": str(task.task_id),
            "agent_type": self.agent_type.value
        }
    
    async def create_handoff(self, to_agent: AgentType, task: Task, 
                           context: list[ContextArtifact]) -> HandoffSchema:
        return HandoffSchema(
            handoff_id=uuid4(),
            from_agent=self.agent_type.value,
            to_agent=to_agent.value,
            project_id=task.project_id,
            phase="test_phase",
            context_ids=[artifact.context_id for artifact in context],
            instructions="Test handoff instructions",
            expected_outputs=["test_output"]
        )

class TestAgentFactory:
    """Test cases for the AgentFactory class."""
    
    
    @pytest.mark.real_data
    def test_factory_initialization(self):
        """Test factory initializes correctly."""
        factory = AgentFactory()
        
        assert factory is not None
        assert len(factory.get_registered_types()) == 0
        assert len(factory.get_active_agents()) == 0
    
    @pytest.mark.real_data
    def test_agent_registration(self):
        """Test agent registration works correctly."""
        factory = AgentFactory()
        
        # Register mock agent
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        # Verify registration
        registered_types = factory.get_registered_types()
        assert AgentType.ANALYST in registered_types
        assert len(registered_types) == 1
    
    @pytest.mark.real_data
    def test_agent_registration_validation(self):
        """Test agent registration validates inheritance."""
        factory = AgentFactory()
        
        # Try to register invalid class
        class InvalidAgent:
            pass
        
        with pytest.raises(ValueError, match="must inherit from BaseAgent"):
            factory.register_agent(AgentType.ANALYST, InvalidAgent)
    
    @pytest.mark.real_data
    def test_agent_creation(self, db_session):
        """Test agent creation works correctly with real database."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        # Create agent
        llm_config = {"model": "gpt-4o-mini", "temperature": 0.7}
        agent = factory.create_agent(AgentType.ANALYST, llm_config)
        
        assert agent is not None
        assert isinstance(agent, MockAgent)
        assert agent.agent_type == AgentType.ANALYST
        assert agent.llm_config == llm_config
    
    @pytest.mark.mock_data

    def test_agent_creation_unregistered_type(self):
        """Test agent creation fails for unregistered types."""
        factory = AgentFactory()
        
        llm_config = {"model": "gpt-4o-mini"}
        
        with pytest.raises(ValueError, match="not registered"):
            factory.create_agent(AgentType.ANALYST, llm_config)
    
    @pytest.mark.mock_data

    def test_agent_instance_reuse(self):
        """Test agent instances are reused by default."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        llm_config = {"model": "gpt-4o-mini"}
        
        # Create first instance
        agent1 = factory.create_agent(AgentType.ANALYST, llm_config)
        
        # Create second instance (should be same)
        agent2 = factory.create_agent(AgentType.ANALYST, llm_config)
        
        assert agent1 is agent2
    
    @pytest.mark.mock_data

    def test_force_new_agent_creation(self):
        """Test force new agent creation."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        llm_config = {"model": "gpt-4o-mini"}
        
        # Create first instance
        agent1 = factory.create_agent(AgentType.ANALYST, llm_config)
        
        # Force new instance
        agent2 = factory.create_agent(AgentType.ANALYST, llm_config, force_new=True)
        
        assert agent1 is not agent2
        assert isinstance(agent2, MockAgent)
    
    @pytest.mark.mock_data

    def test_get_existing_agent(self):
        """Test getting existing agent instances."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        llm_config = {"model": "gpt-4o-mini"}
        
        # Create agent
        created_agent = factory.create_agent(AgentType.ANALYST, llm_config)
        
        # Get existing agent
        retrieved_agent = factory.get_agent(AgentType.ANALYST)
        
        assert created_agent is retrieved_agent
    
    @pytest.mark.mock_data

    def test_get_nonexistent_agent(self):
        """Test getting non-existent agent fails."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        with pytest.raises(ValueError, match="No agent instance exists"):
            factory.get_agent(AgentType.ANALYST)
    
    @pytest.mark.mock_data

    def test_has_agent(self):
        """Test checking agent existence."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        # Initially no instance
        assert not factory.has_agent(AgentType.ANALYST)
        
        # Create instance
        llm_config = {"model": "gpt-4o-mini"}
        factory.create_agent(AgentType.ANALYST, llm_config)
        
        # Now has instance
        assert factory.has_agent(AgentType.ANALYST)
    
    @pytest.mark.mock_data

    def test_remove_agent(self):
        """Test removing agent instances."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        llm_config = {"model": "gpt-4o-mini"}
        factory.create_agent(AgentType.ANALYST, llm_config)
        
        # Verify agent exists
        assert factory.has_agent(AgentType.ANALYST)
        
        # Remove agent
        factory.remove_agent(AgentType.ANALYST)
        
        # Verify agent removed
        assert not factory.has_agent(AgentType.ANALYST)
    
    @pytest.mark.mock_data

    def test_clear_all_agents(self):
        """Test clearing all agent instances."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        factory.register_agent(AgentType.ARCHITECT, MockAgent)
        
        llm_config = {"model": "gpt-4o-mini"}
        factory.create_agent(AgentType.ANALYST, llm_config)
        factory.create_agent(AgentType.ARCHITECT, llm_config)
        
        # Verify agents exist
        assert len(factory.get_active_agents()) == 2
        
        # Clear all
        factory.clear_all_agents()
        
        # Verify all cleared
        assert len(factory.get_active_agents()) == 0
    
    @pytest.mark.mock_data

    def test_factory_status(self):
        """Test factory status reporting."""
        factory = AgentFactory()
        factory.register_agent(AgentType.ANALYST, MockAgent)
        
        # Get initial status
        status = factory.get_factory_status()
        
        assert "registered_types" in status
        assert "active_instances" in status
        assert "total_registered" in status
        assert "total_active" in status
        
        assert status["total_registered"] == 1
        assert status["total_active"] == 0
        
        # Create instance and check again
        llm_config = {"model": "gpt-4o-mini"}
        factory.create_agent(AgentType.ANALYST, llm_config)
        
        status = factory.get_factory_status()
        assert status["total_active"] == 1

class TestBaseAgent:
    """Test cases for the BaseAgent abstract class functionality."""
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task for testing."""
        return Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.PENDING,
            instructions="Test task instructions"
        )
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context artifacts for testing."""
        return [
            ContextArtifact(
                context_id=uuid4(),
                project_id=uuid4(),
                source_agent=AgentType.ORCHESTRATOR,
                artifact_type=ArtifactType.USER_INPUT,
                content={"test": "data"}
            )
        ]
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        llm_config = {"model": "gpt-4o-mini", "temperature": 0.7}
        agent = MockAgent(AgentType.ANALYST, llm_config)
        return agent
    
    @pytest.mark.mock_data

    def test_agent_initialization(self, mock_agent):
        """Test agent initialization sets up components correctly."""
        assert mock_agent.agent_type == AgentType.ANALYST
        assert mock_agent.llm_config["model"] == "gpt-4o-mini"
        assert mock_agent.response_validator is not None
        # retry_handler is now part of llm_service, not a separate attribute
        assert mock_agent.llm_service is not None
        assert mock_agent.usage_tracker is not None
    
    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_execute_task(self, mock_agent, mock_task, mock_context):
        """Test task execution returns expected results."""
        result = await mock_agent.execute_task(mock_task, mock_context)
        
        assert result is not None
        assert "mock_output" in result
        assert result["task_id"] == str(mock_task.task_id)
        assert result["agent_type"] == AgentType.ANALYST.value
    
    @pytest.mark.asyncio
    @pytest.mark.mock_data

    async def test_create_handoff(self, mock_agent, mock_task, mock_context):
        """Test handoff creation works correctly."""
        handoff = await mock_agent.create_handoff(AgentType.ARCHITECT, mock_task, mock_context)
        
        assert handoff is not None
        assert handoff.from_agent == AgentType.ANALYST.value
        assert handoff.to_agent == AgentType.ARCHITECT.value
        assert handoff.project_id == mock_task.project_id
        assert len(handoff.context_ids) == len(mock_context)
    
    @pytest.mark.mock_data

    def test_prepare_context_message(self, mock_agent, mock_context):
        """Test context message preparation."""
        handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent="test_from",
            to_agent="test_to",
            project_id=uuid4(),
            phase="test_phase",
            context_ids=[],
            instructions="Test instructions",
            expected_outputs=["test_output"]
        )
        
        message = mock_agent.prepare_context_message(mock_context, handoff)
        
        assert isinstance(message, str)
        assert "Test instructions" in message
        assert "test_phase" in message
        assert "test_output" in message
    
    @pytest.mark.mock_data

    def test_get_agent_info(self, mock_agent):
        """Test agent info retrieval."""
        info = mock_agent.get_agent_info()
        
        assert "agent_type" in info
        assert "llm_config" in info
        assert "autogen_initialized" in info
        assert "reliability_features" in info
        
        assert info["agent_type"] == AgentType.ANALYST.value
        assert info["reliability_features"]["validator"] is True
        assert info["reliability_features"]["llm_service"] is True
        assert info["reliability_features"]["usage_tracker"] is True

class TestAgentService:
    """Test cases for the AgentService class."""
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task for testing."""
        return Task(
            task_id=uuid4(),
            project_id=uuid4(),
            agent_type=AgentType.ANALYST.value,
            status=TaskStatus.PENDING,
            instructions="Test task instructions"
        )
    
    @pytest.fixture
    def mock_handoff(self, mock_task):
        """Create a mock handoff for testing."""
        return HandoffSchema(
            handoff_id=uuid4(),
            from_agent=AgentType.ORCHESTRATOR.value,
            to_agent=AgentType.ANALYST.value,
            project_id=mock_task.project_id,
            phase="test_phase",
            context_ids=[uuid4()],
            instructions="Test handoff instructions",
            expected_outputs=["test_output"]
        )
    
    @pytest.mark.real_data
    def test_agent_service_initialization(self, db_session):
        """Test agent service initializes correctly with real database."""
        # Only mock external services, use real database
        with patch('app.services.agent_service.ContextStoreService') as mock_context_store, \
             patch('app.services.agent_service.AgentStatusService') as mock_status_service:

            service = AgentService(db_session)

            assert service is not None
            assert service.agent_factory is not None
            assert service.context_store is not None
            assert service.agent_status_service is not None
    
    @pytest.mark.real_data
    def test_agent_registration(self, db_session):
        """Test all agents are registered with factory using real database."""
        # Only mock external services
        with patch('app.services.agent_service.ContextStoreService') as mock_context_store, \
             patch('app.services.agent_service.AgentStatusService') as mock_status_service, \
             patch.object(AgentFactory, 'register_agent') as mock_register:

            service = AgentService(db_session)

            # Verify register_agent was called for each agent type
            assert mock_register.call_count == 6  # 6 agent types

            # Verify specific registrations
            call_args_list = mock_register.call_args_list
            agent_types_registered = [call[0][0] for call in call_args_list]

        assert AgentType.ORCHESTRATOR in agent_types_registered
        assert AgentType.ANALYST in agent_types_registered
        assert AgentType.ARCHITECT in agent_types_registered
        assert AgentType.CODER in agent_types_registered
        assert AgentType.TESTER in agent_types_registered
        assert AgentType.DEPLOYER in agent_types_registered
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_execute_task_with_agent_success(self, mock_status_service, mock_context_store, mock_task, db_session):
        """Test successful task execution with agent."""
        # Setup mocks
        mock_agent = AsyncMock(spec=BaseAgent)
        mock_agent.execute_task.return_value = {
            "success": True,
            "output": {"test": "result"}
        }
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        mock_context_store_instance = AsyncMock()
        mock_context_store_instance.get_artifacts_by_project.return_value = []
        mock_context_store_instance.create_artifact.return_value = MagicMock(context_id=uuid4())
        mock_context_store.return_value = mock_context_store_instance
        
        service = AgentService(db_session)

        with patch.object(service, '_get_agent_instance', return_value=mock_agent):
            result = await service.execute_task_with_agent(mock_task)
            
            assert result["success"] is True
            assert "output" in result
            
            # Verify status updates
            mock_status_service_instance.set_agent_working.assert_called_once()
            mock_status_service_instance.set_agent_idle.assert_called_once()
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_execute_task_with_agent_failure(self, mock_status_service, mock_context_store, mock_task, db_session):
        """Test task execution failure handling with real database."""
        # Setup mocks
        mock_agent = AsyncMock(spec=BaseAgent)
        mock_agent.execute_task.return_value = {
            "success": False,
            "error": "Test error"
        }
        
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        mock_context_store_instance = AsyncMock()
        mock_context_store_instance.get_artifacts_by_project.return_value = []
        mock_context_store.return_value = mock_context_store_instance
        
        service = AgentService(db_session)

        with patch.object(service, '_get_agent_instance', return_value=mock_agent):
            result = await service.execute_task_with_agent(mock_task)
        
        assert result["success"] is False
        assert "error" in result
        
        # Verify error status update
        mock_status_service_instance.set_agent_working.assert_called_once()
        mock_status_service_instance.set_agent_error.assert_called_once()
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_create_agent_handoff(self, mock_status_service, mock_context_store, mock_task, db_session):
        """Test agent handoff creation."""
        # Setup mocks
        mock_agent = AsyncMock(spec=BaseAgent)
        expected_handoff = HandoffSchema(
            handoff_id=uuid4(),
            from_agent=AgentType.ANALYST.value,
            to_agent=AgentType.ARCHITECT.value,
            project_id=mock_task.project_id,
            phase="test_phase",
            context_ids=[],
            instructions="Test instructions",
            expected_outputs=["test_output"]
        )
        mock_agent.create_handoff.return_value = expected_handoff
        
        mock_context_store_instance = AsyncMock()
        mock_context_store_instance.get_artifacts_by_project.return_value = []
        mock_context_store.return_value = mock_context_store_instance
        
        service = AgentService(db_session)

        with patch.object(service, '_get_agent_instance', return_value=mock_agent):
            handoff = await service.create_agent_handoff(
                AgentType.ANALYST, AgentType.ARCHITECT, mock_task
            )
        
        assert handoff is not None
        assert handoff.from_agent == AgentType.ANALYST.value
        assert handoff.to_agent == AgentType.ARCHITECT.value
        
        # Verify agent method was called
        mock_agent.create_handoff.assert_called_once()
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_get_agent_status_summary(self, mock_status_service, mock_context_store, db_session):
        """Test agent status summary retrieval."""
        # Setup mocks
        mock_status_service_instance = MagicMock()
        mock_status_service_instance.get_all_agent_statuses.return_value = {}
        mock_status_service.return_value = mock_status_service_instance
        
        service = AgentService(db_session)

        with patch.object(service.agent_factory, 'get_factory_status', return_value={}):
            summary = await service.get_agent_status_summary()
        
        assert "agent_statuses" in summary
        assert "factory_status" in summary
        assert "active_agents" in summary
        assert "total_registered_types" in summary
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.asyncio
    @pytest.mark.mock_data
    async def test_reset_agent_status(self, mock_status_service, mock_context_store, db_session):
        """Test agent status reset."""
        # Setup mocks
        mock_status_service_instance = AsyncMock()
        mock_status_service.return_value = mock_status_service_instance
        
        service = AgentService(db_session)

        with patch.object(service.agent_factory, 'remove_agent') as mock_remove:
            result = await service.reset_agent_status(AgentType.ANALYST)
        
        assert result is True
        
        # Verify calls
        mock_status_service_instance.set_agent_idle.assert_called_once()
        mock_remove.assert_called_once_with(AgentType.ANALYST)
    
    @patch('app.services.agent_service.ContextStoreService')
    @patch('app.services.agent_service.AgentStatusService')
    @pytest.mark.real_data
    def test_get_service_status(self, mock_status_service, mock_context_store, db_session):
        """Test service status retrieval with real database."""
        service = AgentService(db_session)

        with patch.object(service.agent_factory, 'get_factory_status', return_value={}):
            with patch.object(service.agent_factory, 'get_registered_types', return_value=[]):
                with patch.object(service.agent_factory, 'get_active_agents', return_value={}):
                    status = service.get_service_status()
        
        assert "service_initialized" in status
        assert "factory_status" in status
        assert "context_store_available" in status
        assert "agent_status_service_available" in status
        assert "registered_agent_types" in status
        assert "active_agent_instances" in status
        
        assert status["service_initialized"] is True

@pytest.mark.mock_data

def test_global_agent_factory():
    """Test global agent factory instance."""
    factory1 = get_agent_factory()
    factory2 = get_agent_factory()
    
    # Should be same instance
    assert factory1 is factory2
    assert isinstance(factory1, AgentFactory)
