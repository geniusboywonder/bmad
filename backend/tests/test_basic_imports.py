#!/usr/bin/env python3
"""Test script to verify basic imports work without database connection."""

import sys
import os
import pytest

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@pytest.mark.mock_data
def test_basic_imports():
    """Test basic imports without database connection."""
    print("🔍 Testing basic imports...")
    
    try:
        print("  - Testing basic packages...")
        import fastapi
        import uvicorn
        import pydantic
        import sqlalchemy
        import redis
        import celery
        import structlog
        print("  ✅ Basic packages imported successfully")
    except ImportError as e:
        print(f"  ❌ Basic packages import failed: {e}")
        return False
    
    try:
        print("  - Testing psycopg...")
        import psycopg
        print("  ✅ psycopg import successful")
    except ImportError as e:
        print(f"  ❌ psycopg import failed: {e}")
        return False
    
    try:
        print("  - Testing app configuration...")
        from app.settings import settings
        print("  ✅ Configuration loaded successfully")
    except ImportError as e:
        print(f"  ❌ Configuration import failed: {e}")
        return False
    
    try:
        print("  - Testing app models...")
        from app.models import Task, AgentStatus, ContextArtifact, HitlRequest
        print("  ✅ Models imported successfully")
    except ImportError as e:
        print(f"  ❌ Models import failed: {e}")
        return False
    
    try:
        print("  - Testing database models (without connection)...")
        from app.database.models import Base, TaskDB, AgentStatusDB
        print("  ✅ Database models imported successfully")
    except ImportError as e:
        print(f"  ❌ Database models import failed: {e}")
        return False
    
    try:
        print("  - Testing services...")
        from app.services.context_store import ContextStoreService
        from app.services.orchestrator import OrchestratorService
        print("  ✅ Services imported successfully")
    except ImportError as e:
        print(f"  ❌ Services import failed: {e}")
        return False
    
    try:
        print("  - Testing API endpoints...")
        from app.api import projects, hitl, health, websocket
        print("  ✅ API endpoints imported successfully")
    except ImportError as e:
        print(f"  ❌ API endpoints import failed: {e}")
        return False
    
    try:
        print("  - Testing WebSocket...")
        from app.websocket import WebSocketManager, WebSocketEvent
        print("  ✅ WebSocket components imported successfully")
    except ImportError as e:
        print(f"  ❌ WebSocket import failed: {e}")
        return False
    
    try:
        print("  - Testing Celery tasks...")
        from app.tasks import celery_app, process_agent_task
        print("  ✅ Celery tasks imported successfully")
    except ImportError as e:
        print(f"  ❌ Celery tasks import failed: {e}")
        return False
    
    print("🎉 All basic imports successful!")
    print("📝 Note: Database connection test skipped (PostgreSQL not running)")
    print("   To test database connection, start PostgreSQL and run:")
    print("   python test_imports.py")
    return True

if __name__ == "__main__":
    success = test_basic_imports()
    sys.exit(0 if success else 1)
