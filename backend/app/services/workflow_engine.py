"""
Workflow Engine - Backward compatibility alias module.

This module maintains backward compatibility while the workflow engine has been
refactored into focused, single-responsibility services following SOLID principles.
"""

from sqlalchemy.orm import Session

# Import the refactored workflow execution engine
from .workflow.execution_engine import ExecutionEngine

# For backward compatibility, expose WorkflowExecutionEngine and WorkflowEngine as aliases to ExecutionEngine
WorkflowExecutionEngine = ExecutionEngine
WorkflowEngine = ExecutionEngine

# Also expose individual services for direct access if needed
from .workflow import (
    StateManager,
    EventDispatcher,
    SdlcOrchestrator
)

__all__ = [
    "WorkflowExecutionEngine",
    "WorkflowEngine",
    "ExecutionEngine",
    "StateManager",
    "EventDispatcher",
    "SdlcOrchestrator"
]