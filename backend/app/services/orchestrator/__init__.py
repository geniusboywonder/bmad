"""Orchestrator service package - consolidated services following Phase 3 targeted cleanup.

PHASE 3 TARGETED CLEANUP (October 2025):
- Consolidated ProjectLifecycleManager + StatusTracker → ProjectManager
- Extracted RecoveryManager to separate file
- Maintains backward compatibility via aliases
"""

from .orchestrator_core import OrchestratorCore
from .project_manager import ProjectManager
from .agent_coordinator import AgentCoordinator
from .workflow_integrator import WorkflowIntegrator
from .handoff_manager import HandoffManager
from .context_manager import ContextManager
from .recovery_manager import RecoveryManager, RecoveryStrategy, RecoveryStep

# Backward compatibility aliases
OrchestratorService = OrchestratorCore
ProjectLifecycleManager = ProjectManager  # Consolidated
StatusTracker = ProjectManager  # Consolidated

__all__ = [
    "OrchestratorService",  # Backward compatibility
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