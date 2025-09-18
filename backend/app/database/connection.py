"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
from typing import Generator
import os

from app.config import settings

# Global variables for lazy initialization
_engine = None
_SessionLocal = None
engine = None  # Backward compatibility


def get_engine():
    """Get the database engine, creating it if necessary."""
    global _engine
    if _engine is None:
        # Enhanced connection pooling for production performance
        if "postgresql" in settings.database_url:
            # PostgreSQL production configuration
            _engine = create_engine(
                settings.database_url.replace("postgresql://", "postgresql+psycopg://"),
                poolclass=QueuePool,
                pool_size=settings.database_pool_size,  # Maximum number of connections in pool
                max_overflow=settings.database_max_overflow,  # Maximum overflow connections
                pool_timeout=settings.database_pool_timeout,  # Timeout for getting connection from pool
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Test connections before use
                echo=settings.debug,
            )
        else:
            # SQLite development configuration
            _engine = create_engine(
                settings.database_url.replace("postgresql://", "postgresql+psycopg://"),
                poolclass=StaticPool,
                connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
                echo=settings.debug,
            )
    return _engine


def get_session_local():
    """Get the session factory, creating it if necessary."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# Create base class for models
Base = declarative_base()


def get_database_url() -> str:
    """Get the database URL from settings."""
    return settings.database_url


def get_session() -> Generator:
    """Get a database session."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Backward compatibility - create engine reference
engine = None


def _ensure_engine_initialized():
    """Ensure engine is initialized for backward compatibility."""
    global engine
    if engine is None:
        engine = get_engine()
    return engine


# Initialize engine on module load for backward compatibility
def __getattr__(name):
    """Dynamic attribute access for backward compatibility."""
    if name == 'engine':
        return _ensure_engine_initialized()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
