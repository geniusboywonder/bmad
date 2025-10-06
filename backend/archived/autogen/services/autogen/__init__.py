"""
AutoGen Service Package - Refactored into focused services following SOLID principles.

This package maintains backward compatibility while providing specialized services:
- AutoGenCore: Main coordination logic
- AgentFactory: Agent creation and configuration
- ConversationManager: Conversation handling and response processing
"""

from .autogen_core import AutoGenCore
from .agent_factory import AgentFactory
from .conversation_manager import ConversationManager

# For backward compatibility, expose AutoGenCore as AutoGenService
AutoGenService = AutoGenCore

__all__ = [
    "AutoGenCore",
    "AutoGenService",  # Backward compatibility alias
    "AgentFactory",
    "ConversationManager"
]