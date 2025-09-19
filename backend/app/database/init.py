"""Database initialization and management utilities."""

import os
import logging
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database.connection import get_engine, Base
from app.settings import settings

logger = logging.getLogger(__name__)


def detect_database_type() -> str:
    """Detect the database type from the connection URL."""
    url = settings.database_url.lower()
    if "postgresql" in url:
        return "postgresql"
    elif "sqlite" in url:
        return "sqlite"
    elif "mysql" in url:
        return "mysql"
    else:
        return "unknown"


def ensure_sqlite_directory():
    """Ensure SQLite database directory exists."""
    if "sqlite" in settings.database_url.lower():
        # Extract directory from sqlite:///path/to/db.db
        db_path = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]

        db_dir = Path(db_path).parent
        if db_dir != Path("."):
            db_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created SQLite database directory: {db_dir}")


def test_database_connection() -> bool:
    """Test database connectivity."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Use a simple query that works across database types
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info(f"Database connection successful: {detect_database_type()}")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def initialize_database():
    """Initialize database tables and setup."""
    try:
        db_type = detect_database_type()
        logger.info(f"Initializing {db_type} database...")

        # Ensure directory exists for SQLite
        if db_type == "sqlite":
            ensure_sqlite_directory()

        # Test connection first
        if not test_database_connection():
            raise OperationalError("Database connection test failed", None, None)

        # Create all tables
        engine = get_engine()
        Base.metadata.create_all(bind=engine)

        logger.info(f"Database initialization completed successfully")
        return True

    except ImportError as e:
        if "psycopg" in str(e):
            logger.error(
                "PostgreSQL driver not available. "
                "For PostgreSQL support, install: pip install 'psycopg[binary]>=3.2.0'"
            )
            logger.info("Falling back to SQLite if available...")
            return False
        raise
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_database_info() -> dict:
    """Get information about the current database setup."""
    db_type = detect_database_type()

    info = {
        "type": db_type,
        "url": settings.database_url,
        "connection_successful": test_database_connection()
    }

    if db_type == "sqlite":
        db_path = settings.database_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]
        info["file_path"] = os.path.abspath(db_path)
        info["file_exists"] = os.path.exists(db_path)
        if os.path.exists(db_path):
            info["file_size"] = os.path.getsize(db_path)

    return info


if __name__ == "__main__":
    # Allow running as script for database initialization
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        initialize_database()
    else:
        info = get_database_info()
        print(f"Database info: {info}")