"""
ADK Analyst Agent - Alias for compatibility.

This is an alias module for backward compatibility with tests.
"""

# Import from the existing ADK agent implementation
from .bmad_adk_wrapper import BMADADKWrapper

# Create alias for tests
ADKAnalystAgent = BMADADKWrapper

__all__ = ["ADKAnalystAgent"]