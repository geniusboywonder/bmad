"""Orchestrator service - backward compatibility layer and service exports.

PHASE 3 TARGETED CLEANUP (October 2025):
- Consolidated ProjectLifecycleManager + StatusTracker → ProjectManager
- Extracted RecoveryManager to separate file
- Maintains backward compatibility for existing API endpoints
"""

import structlog

logger = structlog.get_logger(__name__)

# Import the refactored orchestrator core
from .orchestrator.orchestrator_core import OrchestratorCore

# For backward compatibility, expose OrchestratorService as an alias to OrchestratorCore
OrchestratorService = OrchestratorCore

# Import consolidated and specialized services
from .orchestrator.project_manager import ProjectManager
from .orchestrator.agent_coordinator import AgentCoordinator
from .orchestrator.workflow_integrator import WorkflowIntegrator
from .orchestrator.handoff_manager import HandoffManager
from .orchestrator.context_manager import ContextManager
from .orchestrator.recovery_manager import RecoveryManager, RecoveryStrategy, RecoveryStep

# Backward compatibility aliases
ProjectLifecycleManager = ProjectManager  # Consolidated into ProjectManager
StatusTracker = ProjectManager  # Consolidated into ProjectManager

__all__ = [
    "OrchestratorService",
    "OrchestratorCore",
    "ProjectManager",
    "ProjectLifecycleManager",  # Backward compat alias
    "StatusTracker",  # Backward compat alias
    "AgentCoordinator",
    "WorkflowIntegrator",
    "HandoffManager",
    "ContextManager",
    "RecoveryManager",
    "RecoveryStrategy",
    "RecoveryStep"
]