"""
ADK Tools - Alias for compatibility.

This is an alias module for backward compatibility with tests.
"""

# Import from the existing ADK tools implementation
from .adk_dev_tools import *

# Re-export everything from adk_dev_tools
from .adk_dev_tools import __all__ as _all

__all__ = _all if '_all' in locals() else []