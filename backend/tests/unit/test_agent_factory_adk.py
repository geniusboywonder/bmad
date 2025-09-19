"""Tests for ADK integration in AgentFactory."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.models.agent import AgentType
from app.agents.factory import AgentFactory
from app.agents.bmad_adk_wrapper import BMADADKWrapper
from app.agents.base_agent import BaseAgent
from app.models.task import Task
from app.models.context import ContextArtifact
from app.models.handoff import HandoffSchema

class MockBaseAgent(BaseAgent):
    """Mock BaseAgent implementation for testing."""

    def __init__(self, agent_type, llm_config):
        # Initialize with minimal setup to avoid dependencies
        self.agent_type = agent_type
        self.llm_config = llm_config
        self.is_adk_agent = False

    def _create_system_message(self) -> str:
        return f"Mock {self.agent_type.value} agent system message"

    async def execute_task(self, task: Task, context: list) -> Dict[str, Any]:
        return {
            "status": "completed",
            "output": f"Mock {self.agent_type.value} output",
            "artifacts": []
        }

    async def create_handoff(self, to_agent: AgentType, task: Task, context: list) -> HandoffSchema:
        return HandoffSchema(
            from_agent=self.agent_type,
            to_agent=to_agent,
            phase="mock_phase",
            instructions="Mock handoff instructions",
            expected_outputs=["mock_output"]
        )

@pytest.fixture
def agent_factory():
    """Create a fresh AgentFactory instance for testing."""
    factory = AgentFactory()
    factory.clear_all_agents()  # Clear any existing instances
    return factory

@pytest.fixture
def mock_adk_wrapper():
    """Create a mock BMADADKWrapper for testing."""
    wrapper = Mock(spec=BMADADKWrapper)
    wrapper.agent_name = "test_adk_agent"
    wrapper.agent_type = "analyst"
    wrapper.is_initialized = True
    wrapper.is_adk_agent = True
    return wrapper

class TestAgentFactoryADKIntegration:
    """Test ADK integration in AgentFactory."""

    @pytest.mark.mock_data

    def test_factory_initialization_with_adk_configs(self, agent_factory):
        """Test that factory initializes with ADK configurations."""
        # Check that ADK configs are initialized
        assert hasattr(agent_factory, '_adk_agent_configs')
        assert AgentType.ANALYST in agent_factory._adk_agent_configs

        analyst_config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert analyst_config["use_adk"] is True
        assert analyst_config["rollout_percentage"] == 25
        assert analyst_config["model"] == "gemini-2.0-flash"

    @pytest.mark.mock_data

    def test_should_use_adk_logic(self, agent_factory):
        """Test the ADK usage decision logic."""
        # Test with explicit override
        assert agent_factory._should_use_adk(AgentType.ANALYST, override=True) is True
        assert agent_factory._should_use_adk(AgentType.ANALYST, override=False) is False

        # Test with config - analyst should potentially use ADK (25% rollout)
        result = agent_factory._should_use_adk(AgentType.ANALYST, override=None)
        assert isinstance(result, bool)

        # Test architect (0% rollout)
        result = agent_factory._should_use_adk(AgentType.ARCHITECT, override=None)
        assert result is False

    @pytest.mark.mock_data

    def test_adk_rollout_percentage_update(self, agent_factory):
        """Test updating ADK rollout percentage."""
        # Update analyst rollout to 50%
        agent_factory.update_adk_rollout(AgentType.ANALYST, 50)

        config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert config["rollout_percentage"] == 50

        # Test boundary values
        agent_factory.update_adk_rollout(AgentType.ANALYST, 0)
        config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert config["rollout_percentage"] == 0

        agent_factory.update_adk_rollout(AgentType.ANALYST, 100)
        config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert config["rollout_percentage"] == 100

        # Test invalid values get clamped
        agent_factory.update_adk_rollout(AgentType.ANALYST, -10)
        config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert config["rollout_percentage"] == 0

        agent_factory.update_adk_rollout(AgentType.ANALYST, 150)
        config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert config["rollout_percentage"] == 100

    @pytest.mark.mock_data

    def test_agent_instruction_generation(self, agent_factory):
        """Test that agent instructions are generated properly."""
        analyst_instruction = agent_factory._get_analyst_instruction()
        assert isinstance(analyst_instruction, str)
        assert len(analyst_instruction) > 0
        assert "analyst" in analyst_instruction.lower()

        architect_instruction = agent_factory._get_architect_instruction()
        assert isinstance(architect_instruction, str)
        assert len(architect_instruction) > 0
        assert "architect" in architect_instruction.lower()

    @patch('app.agents.factory.BMADADKWrapper')
    @pytest.mark.mock_data

    def test_create_agent_with_adk(self, mock_wrapper_class, agent_factory, mock_adk_wrapper):
        """Test creating agent with ADK enabled."""
        mock_wrapper_class.return_value = mock_adk_wrapper

        # Register a proper agent class for testing (must inherit from BaseAgent)
        agent_factory.register_agent(AgentType.ANALYST, MockBaseAgent)

        # Create agent with ADK explicitly enabled
        agent = agent_factory.create_agent(
            AgentType.ANALYST,
            {"model": "gemini-2.0-flash"},
            use_adk=True
        )

        assert agent is mock_adk_wrapper
        assert hasattr(agent, 'is_adk_agent')
        assert agent.is_adk_agent is True
        mock_wrapper_class.assert_called_once()

    @pytest.mark.mock_data

    def test_create_agent_without_adk(self, agent_factory):
        """Test creating legacy agent when ADK is disabled."""
        # Register a proper legacy agent class
        agent_factory.register_agent(AgentType.ARCHITECT, MockBaseAgent)

        # Create agent with ADK explicitly disabled
        agent = agent_factory.create_agent(
            AgentType.ARCHITECT,
            {"model": "gpt-4"},
            use_adk=False
        )

        assert isinstance(agent, MockBaseAgent)
        assert agent.is_adk_agent is False
        assert agent.agent_type == AgentType.ARCHITECT

    @pytest.mark.mock_data

    def test_factory_status_includes_adk_info(self, agent_factory):
        """Test that factory provides ADK status information."""
        status = agent_factory.get_factory_status()

        assert "adk_status" in status
        assert isinstance(status["adk_status"], dict)

        # Check analyst status
        analyst_status = status["adk_status"]["analyst"]
        assert "use_adk" in analyst_status
        assert "rollout_percentage" in analyst_status
        assert "has_instance" in analyst_status
        assert "is_adk_instance" in analyst_status

        # Analyst should be configured for ADK
        assert analyst_status["use_adk"] is True
        assert analyst_status["rollout_percentage"] == 25

    @pytest.mark.mock_data

    def test_agent_instance_reuse(self, agent_factory):
        """Test that existing agent instances are reused when appropriate."""
        # Register a proper agent class
        agent_factory.register_agent(AgentType.TESTER, MockBaseAgent)

        # Create first instance (legacy)
        agent1 = agent_factory.create_agent(AgentType.TESTER, {}, use_adk=False)

        # Try to create again with same ADK preference - should reuse
        agent2 = agent_factory.create_agent(AgentType.TESTER, {}, use_adk=False)

        assert agent1 is agent2  # Same instance reused

    @pytest.mark.mock_data

    def test_agent_instance_recreation_when_adk_changes(self, agent_factory):
        """Test that new instances are created when ADK preference changes."""
        # Register proper agent class
        agent_factory.register_agent(AgentType.TESTER, MockBaseAgent)

        # Create legacy instance first
        agent1 = agent_factory.create_agent(AgentType.TESTER, {}, use_adk=False)

        # Change ADK preference - should create new instance
        with patch.object(agent_factory, '_create_adk_agent') as mock_create_adk:
            mock_adk_instance = Mock()
            mock_adk_instance.is_adk_agent = True
            mock_create_adk.return_value = mock_adk_instance

            agent2 = agent_factory.create_agent(AgentType.TESTER, {}, use_adk=True, force_new=True)

            assert agent1 is not agent2
            assert agent1.is_adk_agent is False
            assert agent2.is_adk_agent is True

    @pytest.mark.mock_data

    def test_error_handling_for_unknown_agent_type(self, agent_factory):
        """Test error handling when trying to create unknown agent type."""
        with pytest.raises(ValueError, match="not registered"):
            agent_factory.create_agent(AgentType.DEPLOYER, {})  # Not registered

    @pytest.mark.mock_data

    def test_adk_config_completeness(self, agent_factory):
        """Test that all ADK configurations have required fields."""
        expected_agent_types = [
            AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER,
            AgentType.TESTER, AgentType.DEPLOYER
        ]

        for agent_type in expected_agent_types:
            config = agent_factory._adk_agent_configs[agent_type]

            # All configs should have required fields
            assert "use_adk" in config
            assert "rollout_percentage" in config
            assert "model" in config
            assert "instruction" in config
            assert "tools" in config

            # Rollout percentage should be valid
            assert 0 <= config["rollout_percentage"] <= 100

            # Model should be valid
            assert config["model"].startswith("gemini-")

            # Instruction should be meaningful
            assert len(config["instruction"]) > 50

    @pytest.mark.mock_data

    def test_agent_tools_configuration(self, agent_factory):
        """Test that agent tools are configured properly."""
        # Test that coder tools are available
        coder_tools = agent_factory._get_coder_tools()
        assert isinstance(coder_tools, list)

        # Currently empty but should be a list
        assert coder_tools == []

    @pytest.mark.mock_data

    def test_factory_lifecycle_methods(self, agent_factory):
        """Test factory lifecycle management methods."""
        # Test registration and retrieval methods
        agent_factory.register_agent(AgentType.ARCHITECT, MockBaseAgent)

        assert agent_factory.has_agent(AgentType.ARCHITECT) is False

        # Create agent
        agent = agent_factory.create_agent(AgentType.ARCHITECT, {}, use_adk=False)

        # Test has_agent and get_agent
        assert agent_factory.has_agent(AgentType.ARCHITECT) is True
        retrieved_agent = agent_factory.get_agent(AgentType.ARCHITECT)
        assert retrieved_agent is agent

        # Test remove_agent
        agent_factory.remove_agent(AgentType.ARCHITECT)
        assert agent_factory.has_agent(AgentType.ARCHITECT) is False

    @pytest.mark.mock_data

    def test_get_agent_without_instance_fails(self, agent_factory):
        """Test that getting non-existent agent fails gracefully."""
        with pytest.raises(ValueError, match="No agent instance exists"):
            agent_factory.get_agent(AgentType.DEPLOYER)

    @pytest.mark.mock_data

    def test_get_registered_types(self, agent_factory):
        """Test retrieving registered agent types."""
        agent_factory.register_agent(AgentType.ARCHITECT, MockBaseAgent)

        registered_types = agent_factory.get_registered_types()
        assert AgentType.ARCHITECT in registered_types

    @pytest.mark.mock_data

    def test_get_active_agents(self, agent_factory):
        """Test retrieving active agent instances."""
        # Initially empty
        active_agents = agent_factory.get_active_agents()
        assert len(active_agents) == 0

        # Create an agent
        agent_factory.register_agent(AgentType.ARCHITECT, MockBaseAgent)

        agent = agent_factory.create_agent(AgentType.ARCHITECT, {}, use_adk=False)

        # Should now have one active agent
        active_agents = agent_factory.get_active_agents()
        assert len(active_agents) == 1
        assert AgentType.ARCHITECT in active_agents
        assert active_agents[AgentType.ARCHITECT] is agent

    @pytest.mark.mock_data

    def test_clear_all_agents(self, agent_factory):
        """Test clearing all agent instances."""
        # Create some agents
        agent_factory.register_agent(AgentType.ARCHITECT, MockBaseAgent)

        agent_factory.create_agent(AgentType.ARCHITECT, {}, use_adk=False)

        # Verify agent exists
        assert agent_factory.has_agent(AgentType.ARCHITECT) is True

        # Clear all agents
        agent_factory.clear_all_agents()

        # Verify all agents cleared
        assert agent_factory.has_agent(AgentType.ARCHITECT) is False
        assert len(agent_factory.get_active_agents()) == 0

class TestADKConfigurationConsistency:
    """Test ADK configuration consistency and validation."""

    @pytest.mark.mock_data

    def test_model_configuration_validation(self, agent_factory):
        """Test that model configurations are valid."""
        for agent_type, config in agent_factory._adk_agent_configs.items():
            model = config["model"]

            # Should be a valid Gemini model
            assert model.startswith("gemini-")
            assert "flash" in model or "pro" in model

    @pytest.mark.mock_data

    def test_instruction_quality_validation(self, agent_factory):
        """Test that instructions are high quality."""
        for agent_type, config in agent_factory._adk_agent_configs.items():
            instruction = config["instruction"]

            # Instructions should be meaningful and specific
            assert len(instruction) > 100  # Substantial instruction
            assert agent_type.value.lower() in instruction.lower()  # Mentions role
            assert "responsibilities" in instruction.lower()  # Has clear responsibilities

    @pytest.mark.mock_data

    def test_rollout_configuration_sanity(self, agent_factory):
        """Test rollout configuration makes sense."""
        # Analyst should be the first to roll out
        analyst_config = agent_factory._adk_agent_configs[AgentType.ANALYST]
        assert analyst_config["use_adk"] is True
        assert analyst_config["rollout_percentage"] > 0

        # Others should start disabled
        for agent_type in [AgentType.ARCHITECT, AgentType.CODER, AgentType.TESTER, AgentType.DEPLOYER]:
            config = agent_factory._adk_agent_configs[agent_type]
            assert config["use_adk"] is False
            assert config["rollout_percentage"] == 0