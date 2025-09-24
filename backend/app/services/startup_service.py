"""Startup service for queue management and agent status reset."""

import redis
import structlog
from celery import Celery
from sqlalchemy.orm import Session
from typing import List

from app.settings import settings
from app.database.connection import get_session
from app.database.models import AgentStatusDB, TaskDB
from app.models.agent import AgentStatus, AgentType
from app.models.task import TaskStatus
from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


class StartupService:
    """Service for handling server startup cleanup and initialization."""

    def __init__(self):
        self.redis_client = None
        self.celery_app = celery_app

    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client instance."""
        if not self.redis_client:
            # Parse Redis URL from settings
            redis_url = settings.redis_celery_url
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client

    async def flush_redis_queues(self) -> bool:
        """Flush all Redis queues used by the application."""
        try:
            redis_client = self._get_redis_client()

            # Common queue names used by the application
            queue_patterns = [
                "celery",           # Default Celery queue
                "agent_tasks",      # Custom agent task queue
                "bmad:*",          # Application-specific keys
                "_kombu.binding.*", # Kombu (Celery) bindings
            ]

            flushed_keys = 0

            # Flush specific queues and patterns
            for pattern in queue_patterns:
                if "*" in pattern:
                    # Handle wildcard patterns
                    keys = redis_client.keys(pattern)
                    if keys:
                        deleted = redis_client.delete(*keys)
                        flushed_keys += deleted
                        logger.info(f"Flushed Redis pattern",
                                   pattern=pattern,
                                   keys_deleted=deleted)
                else:
                    # Handle specific queue names
                    if redis_client.exists(pattern):
                        redis_client.delete(pattern)
                        flushed_keys += 1
                        logger.info(f"Flushed Redis queue", queue=pattern)

            # Additional Celery-specific cleanup
            celery_keys = redis_client.keys("_kombu.*")
            if celery_keys:
                deleted = redis_client.delete(*celery_keys)
                flushed_keys += deleted
                logger.info("Flushed Celery internal keys", keys_deleted=deleted)

            logger.info("Redis queue flush completed",
                       total_keys_flushed=flushed_keys)
            return True

        except Exception as e:
            logger.error("Failed to flush Redis queues",
                        error=str(e),
                        exc_info=True)
            return False

    async def purge_celery_queues(self) -> bool:
        """Purge all Celery task queues."""
        try:
            # Purge the main agent task queue
            purged_count = self.celery_app.control.purge()

            # Also purge specific queues
            queue_names = ["agent_tasks", "celery"]

            for queue_name in queue_names:
                try:
                    # Use Celery's management commands to purge queues
                    result = self.celery_app.control.purge()
                    logger.info(f"Purged Celery queue",
                               queue=queue_name,
                               purged_tasks=result)
                except Exception as queue_error:
                    logger.warning(f"Could not purge queue {queue_name}",
                                  error=str(queue_error))

            logger.info("Celery queue purge completed",
                       total_purged=purged_count)
            return True

        except Exception as e:
            logger.error("Failed to purge Celery queues",
                        error=str(e),
                        exc_info=True)
            return False

    async def reset_agent_statuses(self) -> bool:
        """Reset all agent statuses to IDLE."""
        try:
            # Use generator pattern for database session
            db_gen = get_session()
            db = next(db_gen)
            try:
                # Get all agent status records
                agent_statuses = db.query(AgentStatusDB).all()

                reset_count = 0
                for agent_status in agent_statuses:
                    if agent_status.status != AgentStatus.IDLE:
                        agent_status.status = AgentStatus.IDLE
                        agent_status.current_task_id = None
                        agent_status.error_message = None
                        reset_count += 1

                        logger.info("Reset agent status to IDLE",
                                   agent_type=agent_status.agent_type.value,
                                   previous_status=agent_status.status.value if agent_status.status else "unknown")

                # Also ensure we have status records for all standard agent types
                standard_agents = [AgentType.ANALYST, AgentType.ARCHITECT, AgentType.CODER, AgentType.TESTER, AgentType.DEPLOYER]
                existing_types = {agent.agent_type for agent in agent_statuses}

                created_count = 0
                for agent_type in standard_agents:
                    if agent_type not in existing_types:
                        new_agent_status = AgentStatusDB(
                            agent_type=agent_type,
                            status=AgentStatus.IDLE,
                            current_task_id=None
                        )
                        db.add(new_agent_status)
                        created_count += 1
                        logger.info("Created agent status record",
                                   agent_type=agent_type.value)

                db.commit()

                logger.info("Agent status reset completed",
                           reset_count=reset_count,
                           created_count=created_count)
                return True

            finally:
                # Properly close the database session
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        except Exception as e:
            logger.error("Failed to reset agent statuses",
                        error=str(e),
                        exc_info=True)
            return False

    async def reset_pending_tasks(self) -> bool:
        """Reset all pending/working tasks to cancelled state."""
        try:
            # Use generator pattern for database session
            db_gen = get_session()
            db = next(db_gen)
            try:
                # Find all tasks that are still in PENDING or WORKING state
                pending_tasks = db.query(TaskDB).filter(
                    TaskDB.status.in_([TaskStatus.PENDING, TaskStatus.WORKING])
                ).all()

                cancelled_count = 0
                for task in pending_tasks:
                    task.status = TaskStatus.CANCELLED
                    task.error_message = "Cancelled due to server restart"
                    cancelled_count += 1

                    logger.info("Cancelled orphaned task",
                               task_id=str(task.id),
                               agent_type=task.agent_type,
                               previous_status=task.status.value if task.status else "unknown")

                db.commit()

                logger.info("Pending task reset completed",
                           cancelled_count=cancelled_count)
                return True

            finally:
                # Properly close the database session
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        except Exception as e:
            logger.error("Failed to reset pending tasks",
                        error=str(e),
                        exc_info=True)
            return False

    async def perform_startup_cleanup(self) -> dict:
        """Perform complete startup cleanup sequence."""
        logger.info("🚀 Starting server startup cleanup sequence")

        results = {
            "redis_flush": False,
            "celery_purge": False,
            "agent_reset": False,
            "task_reset": False,
            "overall_success": False
        }

        # 1. Flush Redis queues
        logger.info("🔄 Step 1: Flushing Redis queues...")
        results["redis_flush"] = await self.flush_redis_queues()

        # 2. Purge Celery queues
        logger.info("🔄 Step 2: Purging Celery queues...")
        results["celery_purge"] = await self.purge_celery_queues()

        # 3. Reset agent statuses
        logger.info("🔄 Step 3: Resetting agent statuses...")
        results["agent_reset"] = await self.reset_agent_statuses()

        # 4. Reset pending tasks
        logger.info("🔄 Step 4: Resetting pending tasks...")
        results["task_reset"] = await self.reset_pending_tasks()

        # Determine overall success
        results["overall_success"] = all([
            results["redis_flush"],
            results["celery_purge"],
            results["agent_reset"],
            results["task_reset"]
        ])

        if results["overall_success"]:
            logger.info("✅ Server startup cleanup completed successfully", results=results)
        else:
            logger.warning("⚠️ Server startup cleanup completed with some failures", results=results)

        return results


# Create singleton instance
startup_service = StartupService()