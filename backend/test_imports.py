#!/usr/bin/env python3
"""Test script to verify all imports work correctly."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports."""
    print("🔍 Testing imports...")
    
    try:
        print("  - Testing basic imports...")
        import fastapi
        import uvicorn
        import pydantic
        import sqlalchemy
        import redis
        import celery
        import structlog
        print("  ✅ Basic imports successful")
    except ImportError as e:
        print(f"  ❌ Basic imports failed: {e}")
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
        from app.config import settings
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
        print("  - Testing database connection...")
        from app.database.connection import get_engine
        engine = get_engine()
        print("  ✅ Database engine created successfully")
    except ImportError as e:
        print(f"  ❌ Database connection failed: {e}")
        return False
    
    try:
        print("  - Testing FastAPI app...")
        from app.main import app
        print("  ✅ FastAPI app loaded successfully")
    except ImportError as e:
        print(f"  ❌ FastAPI app import failed: {e}")
        return False
    
    print("🎉 All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
