"""
AutoGen Service - Backward compatibility alias module.

This module maintains backward compatibility while the AutoGen service has been
refactored into focused, single-responsibility services following SOLID principles.
"""

# Import the refactored AutoGen core service
from .autogen import AutoGenCore

# For backward compatibility, expose AutoGenCore as AutoGenService
AutoGenService = AutoGenCore

# Also expose individual services for direct access if needed
from .autogen import (
    AgentFactory,
    ConversationManager
)

__all__ = [
    "AutoGenService",
    "AutoGenCore",
    "AgentFactory",
    "ConversationManager"
]