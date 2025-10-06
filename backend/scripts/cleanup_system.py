#!/usr/bin/env python3
"""
System cleanup script for BotArmy backend.

This script performs a complete cleanup of:
1. All database tables (projects, tasks, HITL requests, etc.)
2. All Redis queues and cached data (both DB 0 and DB 1)
3. Celery task queues and results
4. Agent status tracking

Can be run repeatedly for development/testing purposes.

Usage:
    python scripts/cleanup_system.py [--confirm] [--db-only] [--redis-only]
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from typing import List
import requests

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Load environment variables from .env file before importing settings
from dotenv import load_dotenv
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
dotenv_path = os.path.join(backend_dir, '.env')
load_dotenv(dotenv_path)

import redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.database.connection import get_engine
from app.database.models import (
    ProjectDB, TaskDB, AgentStatusDB, ContextArtifactDB,
    HitlRequestDB, HitlAgentApprovalDB, AgentBudgetControlDB,
    EmergencyStopDB, ResponseApprovalDB, RecoverySessionDB,
    WebSocketNotificationDB, WorkflowStateDB, EventLogDB
)
from app.settings import settings


class SystemCleaner:
    """Comprehensive system cleanup utility."""

    def __init__(self):
        self.engine = get_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.redis_main = None
        self.redis_celery = None

    def connect_redis(self):
        """Connect to Redis databases."""
        try:
            # Connect to main Redis database (DB 0)
            redis_url_main = settings.redis_url
            if not redis_url_main.endswith('/0'):
                redis_url_main = redis_url_main.rstrip('/') + '/0'
            self.redis_main = redis.from_url(redis_url_main)

            # Connect to Redis (single database for all services)
            redis_url_celery = settings.redis_url
            self.redis_celery = redis.from_url(redis_url_celery)

            # Test connections
            self.redis_main.ping()
            self.redis_celery.ping()
            print("✅ Connected to Redis databases")

        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print(f"Main Redis URL: {redis_url_main}")
            print(f"Celery Redis URL: {redis_url_celery}")
            raise

    def cleanup_database_tables(self):
        """Clean all database tables in dependency order."""
        print("\n🗄️  Cleaning database tables...")

        db = self.SessionLocal()
        try:
            # Tables to clean in dependency order (children first, then parents)
            tables_to_clean = [
                # Child tables first
                EventLogDB,
                ResponseApprovalDB,
                RecoverySessionDB,
                WebSocketNotificationDB,
                WorkflowStateDB,
                HitlAgentApprovalDB,
                HitlRequestDB,
                ContextArtifactDB,
                TaskDB,
                AgentBudgetControlDB,
                EmergencyStopDB,
                AgentStatusDB,
                # Parent tables last
                ProjectDB,
            ]

            total_deleted = 0
            for table_model in tables_to_clean:
                try:
                    count = db.query(table_model).count()
                    if count > 0:
                        deleted = db.query(table_model).delete()
                        total_deleted += deleted
                        print(f"  ✅ Cleaned {table_model.__tablename__}: {deleted} records")
                    else:
                        print(f"  ✅ {table_model.__tablename__}: already clean")
                except Exception as e:
                    print(f"  ❌ Error cleaning {table_model.__tablename__}: {e}")
                    # Continue with other tables

            # Reset sequences for PostgreSQL (if using PostgreSQL)
            if "postgresql" in settings.database_url:
                try:
                    # Reset all sequences to start from 1
                    reset_sequences_sql = """
                    DO $$
                    DECLARE
                        seq_record RECORD;
                    BEGIN
                        FOR seq_record IN
                            SELECT schemaname, sequencename
                            FROM pg_sequences
                            WHERE schemaname = 'public'
                        LOOP
                            EXECUTE 'ALTER SEQUENCE ' || seq_record.schemaname || '.' || seq_record.sequencename || ' RESTART WITH 1';
                        END LOOP;
                    END $$;
                    """
                    db.execute(text(reset_sequences_sql))
                    print("  ✅ Reset PostgreSQL sequences")
                except Exception as e:
                    print(f"  ⚠️  Could not reset sequences: {e}")

            db.commit()
            print(f"✅ Database cleanup complete: {total_deleted} total records deleted")

        except Exception as e:
            db.rollback()
            print(f"❌ Database cleanup failed: {e}")
            raise
        finally:
            db.close()

    def cleanup_redis_queues(self):
        """Clean all Redis queues and cached data."""
        print("\n🔴 Cleaning Redis queues and cache...")

        try:
            # Clean main Redis database (DB 0) - WebSocket sessions, general cache
            if self.redis_main:
                main_keys = self.redis_main.keys("*")
                if main_keys:
                    deleted_main = self.redis_main.delete(*main_keys)
                    print(f"  ✅ Cleaned Redis DB 0: {deleted_main} keys deleted")
                else:
                    print("  ✅ Redis DB 0: already clean")

            # Clean Celery Redis database (DB 1) - Task queues, results
            if self.redis_celery:
                celery_keys = self.redis_celery.keys("*")
                if celery_keys:
                    deleted_celery = self.redis_celery.delete(*celery_keys)
                    print(f"  ✅ Cleaned Redis DB 1 (Celery): {deleted_celery} keys deleted")
                else:
                    print("  ✅ Redis DB 1 (Celery): already clean")

                # Clear specific Celery structures
                self.redis_celery.delete(
                    "agent_tasks",  # Agent task queue
                    "celery",       # Default celery queue
                    "_kombu.binding.agent_tasks",
                    "_kombu.binding.celery"
                )
                print("  ✅ Cleared Celery-specific queues")

            print("✅ Redis cleanup complete")

        except Exception as e:
            print(f"❌ Redis cleanup failed: {e}")
            raise

    def cleanup_agent_status(self):
        """Reset all agent status to idle."""
        print("\n🤖 Resetting agent status...")

        db = self.SessionLocal()
        try:
            # This will be handled by the database cleanup, but we can log it
            agents_count = db.query(AgentStatusDB).count()
            print(f"  ✅ Agent status entries will be cleaned: {agents_count} agents")

        except Exception as e:
            print(f"❌ Agent status cleanup failed: {e}")
        finally:
            db.close()

    def trigger_frontend_storage_cleanup(self):
        """Trigger frontend localStorage cleanup via API endpoint."""
        print("\n🧹 Triggering frontend storage cleanup...")

        try:
            # Call the backend API endpoint to get cleanup instructions
            backend_url = getattr(settings, 'api_base_url', 'http://localhost:8000')
            cleanup_url = f"{backend_url}/api/system/clear-frontend-storage"

            response = requests.post(cleanup_url, timeout=10)

            if response.status_code == 200:
                cleanup_data = response.json()
                print(f"  ✅ Frontend cleanup API called successfully")
                print(f"  📋 Stores to clear: {', '.join(cleanup_data.get('cleared_stores', []))}")
                print(f"  💬 Message: {cleanup_data.get('message', 'No message')}")

                # Display instructions for manual cleanup
                print("\n📌 Frontend cleanup instructions:")
                print("  The following localStorage stores should be cleared:")
                for store in cleanup_data.get('cleared_stores', []):
                    print(f"    • {store}")
                print("\n  Note: Frontend applications should automatically clear these stores")
                print("        when they receive the cleanup signal from this API.")

            else:
                print(f"  ⚠️  Frontend cleanup API returned status {response.status_code}")
                print(f"      Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  Could not connect to backend API for frontend cleanup: {e}")
            print("     This is normal if the backend is not running.")
            print("     Frontend storage will need to be cleared manually or when the frontend next loads.")
        except Exception as e:
            print(f"  ❌ Frontend cleanup failed: {e}")

    def verify_cleanup(self):
        """Verify that the cleanup was successful."""
        print("\n🔍 Verifying cleanup...")

        db = self.SessionLocal()
        try:
            # Check database tables
            table_models = [
                ProjectDB, TaskDB, AgentStatusDB, ContextArtifactDB,
                HitlRequestDB, HitlAgentApprovalDB, EventLogDB
            ]

            all_clean = True
            for model in table_models:
                count = db.query(model).count()
                if count > 0:
                    print(f"  ⚠️  {model.__tablename__}: {count} records remain")
                    all_clean = False
                else:
                    print(f"  ✅ {model.__tablename__}: clean")

            # Check Redis
            try:
                main_count = len(self.redis_main.keys("*")) if self.redis_main else 0
                celery_count = len(self.redis_celery.keys("*")) if self.redis_celery else 0

                if main_count > 0:
                    print(f"  ⚠️  Redis DB 0: {main_count} keys remain")
                    all_clean = False
                else:
                    print("  ✅ Redis DB 0: clean")

                if celery_count > 0:
                    print(f"  ⚠️  Redis DB 1: {celery_count} keys remain")
                    all_clean = False
                else:
                    print("  ✅ Redis DB 1: clean")

            except Exception as e:
                print(f"  ⚠️  Could not verify Redis cleanup: {e}")
                all_clean = False

            if all_clean:
                print("✅ Verification complete: System is fully clean")
            else:
                print("⚠️  Verification complete: Some data remains")

        except Exception as e:
            print(f"❌ Verification failed: {e}")
        finally:
            db.close()

    def run_cleanup(self, db_only=False, redis_only=False):
        """Run the complete cleanup process."""
        print("🧹 Starting BotArmy system cleanup...")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)

        try:
            if not redis_only:
                self.cleanup_database_tables()
                self.cleanup_agent_status()

            if not db_only:
                self.connect_redis()
                self.cleanup_redis_queues()

            # Trigger frontend storage cleanup
            self.trigger_frontend_storage_cleanup()

            self.verify_cleanup()

            print("\n" + "=" * 60)
            print("🎉 System cleanup completed successfully!")
            print("The system is now in a clean state for development/testing.")

        except Exception as e:
            print(f"\n💥 Cleanup failed: {e}")
            sys.exit(1)
        finally:
            # Close Redis connections
            if self.redis_main:
                self.redis_main.close()
            if self.redis_celery:
                self.redis_celery.close()


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Clean BotArmy system (database + Redis)")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="Clean database only (skip Redis)"
    )
    parser.add_argument(
        "--redis-only",
        action="store_true",
        help="Clean Redis only (skip database)"
    )

    args = parser.parse_args()

    if args.db_only and args.redis_only:
        print("❌ Error: Cannot specify both --db-only and --redis-only")
        sys.exit(1)

    # Confirmation prompt (unless --confirm is used)
    if not args.confirm:
        print("⚠️  WARNING: This will DELETE ALL DATA from:")
        if not args.redis_only:
            print("  • All database tables (projects, tasks, HITL requests, etc.)")
        if not args.db_only:
            print("  • All Redis queues and cached data")
            print("  • All Celery task queues and results")
        print("\nThis action CANNOT be undone!")

        response = input("\nDo you want to continue? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Cleanup cancelled by user")
            sys.exit(0)

    # Run cleanup
    cleaner = SystemCleaner()
    cleaner.run_cleanup(db_only=args.db_only, redis_only=args.redis_only)


if __name__ == "__main__":
    main()