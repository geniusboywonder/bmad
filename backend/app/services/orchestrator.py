"""Orchestrator service - refactored to use SOLID principles with specialized services.

This module serves as the main entry point for orchestrator functionality,
delegating to specialized services that follow Single Responsibility Principle.
"""

from sqlalchemy.orm import Session

# Import the refactored orchestrator core
from .orchestrator.orchestrator_core import OrchestratorCore

# For backward compatibility, expose OrchestratorService as an alias to OrchestratorCore
OrchestratorService = OrchestratorCore

# Also expose individual services for direct access if needed
from .orchestrator import (
    ProjectLifecycleManager,
    AgentCoordinator,
    WorkflowIntegrator,
    HandoffManager,
    StatusTracker,
    ContextManager
)

__all__ = [
    "OrchestratorService",
    "OrchestratorCore",
    "ProjectLifecycleManager",
    "AgentCoordinator",
    "WorkflowIntegrator",
    "HandoffManager",
    "StatusTracker",
    "ContextManager"
]