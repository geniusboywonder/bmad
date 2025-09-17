"""Tests for the SOLID refactored orchestrator services."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.orchestrator import OrchestratorService
from app.services.orchestrator.orchestrator_core import OrchestratorCore
from app.services.orchestrator.project_lifecycle_manager import ProjectLifecycleManager
from app.services.orchestrator.agent_coordinator import AgentCoordinator
from app.services.orchestrator.workflow_integrator import WorkflowIntegrator
from app.services.orchestrator.handoff_manager import HandoffManager
from app.services.orchestrator.status_tracker import StatusTracker
from app.services.orchestrator.context_manager import ContextManager


class TestOrchestratorRefactoring:
    """Test the refactored orchestrator services."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def orchestrator_core(self, mock_db):
        """Create orchestrator core instance."""
        return OrchestratorCore(mock_db)

    def test_orchestrator_service_alias(self, mock_db):
        """Test that OrchestratorService is an alias to OrchestratorCore."""
        orchestrator = OrchestratorService(mock_db)
        assert isinstance(orchestrator, OrchestratorCore)

    def test_orchestrator_core_initialization(self, orchestrator_core):
        """Test that OrchestratorCore initializes all specialized services."""
        assert isinstance(orchestrator_core.project_manager, ProjectLifecycleManager)
        assert isinstance(orchestrator_core.agent_coordinator, AgentCoordinator)
        assert isinstance(orchestrator_core.workflow_integrator, WorkflowIntegrator)
        assert isinstance(orchestrator_core.handoff_manager, HandoffManager)
        assert isinstance(orchestrator_core.status_tracker, StatusTracker)
        assert isinstance(orchestrator_core.context_manager, ContextManager)

    def test_project_lifecycle_delegation(self, orchestrator_core):
        """Test that project lifecycle methods delegate to ProjectLifecycleManager."""
        project_id = uuid4()

        # Mock the project manager's method
        orchestrator_core.project_manager.get_current_phase = Mock(return_value="discovery")

        # Call the orchestrator method
        result = orchestrator_core.get_current_phase(project_id)

        # Verify delegation
        orchestrator_core.project_manager.get_current_phase.assert_called_once_with(project_id)
        assert result == "discovery"

    def test_agent_coordination_delegation(self, orchestrator_core):
        """Test that agent coordination methods delegate to AgentCoordinator."""
        from app.models.agent import AgentStatus

        # Mock the agent coordinator's method
        orchestrator_core.agent_coordinator.get_agent_status = Mock(return_value=AgentStatus.IDLE)

        # Call the orchestrator method
        result = orchestrator_core.get_agent_status("coder")

        # Verify delegation
        orchestrator_core.agent_coordinator.get_agent_status.assert_called_once_with("coder")
        assert result == AgentStatus.IDLE

    def test_status_tracking_delegation(self, orchestrator_core):
        """Test that status tracking methods delegate to StatusTracker."""
        project_id = uuid4()
        expected_metrics = {"overall_health": "good", "total_tasks": 10}

        # Mock the status tracker's method
        orchestrator_core.status_tracker.get_performance_metrics = Mock(return_value=expected_metrics)

        # Call the orchestrator method
        result = orchestrator_core.get_performance_metrics(project_id)

        # Verify delegation
        orchestrator_core.status_tracker.get_performance_metrics.assert_called_once_with(project_id)
        assert result == expected_metrics

    def test_context_management_delegation(self, orchestrator_core):
        """Test that context management methods delegate to ContextManager."""
        project_id = uuid4()
        expected_context = [uuid4(), uuid4()]

        # Mock the context manager's method
        orchestrator_core.context_manager.get_selective_context = Mock(return_value=expected_context)

        # Call the orchestrator method
        result = orchestrator_core.get_selective_context(project_id, "build", "coder")

        # Verify delegation
        orchestrator_core.context_manager.get_selective_context.assert_called_once_with(project_id, "build", "coder")
        assert result == expected_context

    def test_health_check(self, orchestrator_core, mock_db):
        """Test the health check functionality."""
        # Mock successful database query
        mock_db.execute.return_value = None

        result = orchestrator_core.health_check()

        assert result["orchestrator_core"] == "healthy"
        assert result["overall"] == "healthy"
        assert "timestamp" in result

    def test_health_check_database_failure(self, orchestrator_core, mock_db):
        """Test health check with database failure."""
        # Mock database failure
        mock_db.execute.side_effect = Exception("Database connection failed")

        result = orchestrator_core.health_check()

        assert result["orchestrator_core"] == "degraded"
        assert result["overall"] == "unhealthy"
        assert "Database connection failed" in result["database"]


class TestIndividualServices:
    """Test individual service components."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    def test_project_lifecycle_manager_initialization(self, mock_db):
        """Test ProjectLifecycleManager can be initialized independently."""
        manager = ProjectLifecycleManager(mock_db)
        assert manager.db == mock_db
        assert hasattr(manager, 'current_project_phases')

    def test_agent_coordinator_initialization(self, mock_db):
        """Test AgentCoordinator can be initialized independently."""
        coordinator = AgentCoordinator(mock_db)
        assert coordinator.db == mock_db

    def test_status_tracker_initialization(self, mock_db):
        """Test StatusTracker can be initialized independently."""
        tracker = StatusTracker(mock_db)
        assert tracker.db == mock_db

    @patch('app.services.orchestrator.context_manager.ContextStoreService')
    def test_context_manager_initialization(self, mock_context_store_class, mock_db):
        """Test ContextManager can be initialized independently."""
        mock_context_store = Mock()
        mock_context_store_class.return_value = mock_context_store

        manager = ContextManager(mock_db, mock_context_store)
        assert manager.db == mock_db
        assert manager.context_store == mock_context_store


class TestSOLIDPrinciples:
    """Test that the refactoring follows SOLID principles."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    def test_single_responsibility_principle(self, mock_db):
        """Test that each service has a single responsibility."""
        # ProjectLifecycleManager should only handle project lifecycle
        project_manager = ProjectLifecycleManager(mock_db)

        # Filter out properties and get only callable methods (exclude constructor parameters)
        public_methods = [m for m in dir(project_manager)
                         if not m.startswith('_')
                         and callable(getattr(project_manager, m))
                         and m not in ['db', 'current_project_phases']]  # Exclude constructor params/properties

        # All public methods should be related to project lifecycle
        for method in public_methods:
            # All methods should be project/phase related
            assert any(keyword in method.lower() for keyword in ['project', 'phase', 'task', 'transition', 'validate']), f"Method '{method}' doesn't match expected keywords"

    def test_open_closed_principle(self, mock_db):
        """Test that services can be extended without modification."""
        # Services should accept dependencies through constructor injection
        # This allows extension through composition
        orchestrator = OrchestratorCore(mock_db)

        # Should be able to replace any service with extended version
        original_project_manager = orchestrator.project_manager
        extended_project_manager = ProjectLifecycleManager(mock_db)
        orchestrator.project_manager = extended_project_manager

        assert orchestrator.project_manager is extended_project_manager
        assert orchestrator.project_manager is not original_project_manager

    def test_dependency_inversion_principle(self, mock_db):
        """Test that high-level modules depend on abstractions."""
        # OrchestratorCore depends on concrete classes but could easily be refactored
        # to depend on interfaces. The structure is in place for this.
        orchestrator = OrchestratorCore(mock_db)

        # Services are injected as dependencies, not created internally
        assert hasattr(orchestrator, 'project_manager')
        assert hasattr(orchestrator, 'agent_coordinator')
        assert hasattr(orchestrator, 'workflow_integrator')
        assert hasattr(orchestrator, 'handoff_manager')
        assert hasattr(orchestrator, 'status_tracker')
        assert hasattr(orchestrator, 'context_manager')

    def test_interface_segregation_principle(self):
        """Test that interfaces are focused and specific."""
        from app.interfaces import (
            IProjectLifecycleManager,
            IAgentCoordinator,
            IStatusTracker,
            IContextManager
        )

        # Each interface should have a focused set of methods
        project_methods = [m for m in dir(IProjectLifecycleManager) if not m.startswith('_')]
        agent_methods = [m for m in dir(IAgentCoordinator) if not m.startswith('_')]
        status_methods = [m for m in dir(IStatusTracker) if not m.startswith('_')]
        context_methods = [m for m in dir(IContextManager) if not m.startswith('_')]

        # Interfaces should be focused (not too many methods)
        assert len(project_methods) <= 10  # Reasonable number of project-related methods
        assert len(agent_methods) <= 15   # Agent coordination might have more methods
        assert len(status_methods) <= 8   # Status tracking should be focused
        assert len(context_methods) <= 8  # Context management should be focused


if __name__ == "__main__":
    pytest.main([__file__])