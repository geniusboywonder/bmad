"""Orchestrator service package - refactored into focused, single-responsibility services."""

from .orchestrator_core import OrchestratorCore
from .project_lifecycle_manager import ProjectLifecycleManager
from .agent_coordinator import AgentCoordinator
from .workflow_integrator import WorkflowIntegrator
from .handoff_manager import HandoffManager
from .status_tracker import StatusTracker
from .context_manager import ContextManager

# For backward compatibility, expose OrchestratorService as an alias to OrchestratorCore
OrchestratorService = OrchestratorCore

__all__ = [
    "OrchestratorService",  # Backward compatibility
    "OrchestratorCore",
    "ProjectLifecycleManager",
    "AgentCoordinator",
    "WorkflowIntegrator",
    "HandoffManager",
    "StatusTracker",
    "ContextManager"
]