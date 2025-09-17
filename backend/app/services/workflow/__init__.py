"""Workflow service package - refactored into focused, single-responsibility services."""

from .execution_engine import ExecutionEngine
from .state_manager import StateManager
from .sdlc_orchestrator import SdlcOrchestrator
from .event_dispatcher import EventDispatcher

# For backward compatibility, expose WorkflowExecutionEngine as an alias to ExecutionEngine
WorkflowExecutionEngine = ExecutionEngine

__all__ = [
    "WorkflowExecutionEngine",  # Backward compatibility
    "ExecutionEngine",
    "StateManager",
    "SdlcOrchestrator",
    "EventDispatcher"
]