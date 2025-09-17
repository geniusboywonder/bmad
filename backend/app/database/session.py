"""
Database session management - Alias for compatibility.

This is an alias module for backward compatibility with tests.
"""

# Import from the existing connection module
from .connection import get_session, get_session_local, get_engine

# Create alias for common database session function
get_db_session = get_session

__all__ = ["get_db_session", "get_session", "get_session_local", "get_engine"]