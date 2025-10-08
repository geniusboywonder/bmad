"""
Service for managing HITL (Human-in-the-Loop) counters and settings in Redis.

This service provides the core logic for the "session governor" functionality,
tracking agent actions and enforcing limits on a per-project basis.
"""

import redis
import structlog
from uuid import UUID
from typing import Dict, Any, Optional

from app.settings import settings

logger = structlog.get_logger(__name__)

class HitlCounterService:
    """Manages HITL state for each project using a Redis backend."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initializes the Redis connection.

        Args:
            redis_url: The Redis connection URL. Defaults to the one in settings.
        """
        url = redis_url or settings.redis_url
        try:
            self.redis_client = redis.from_url(url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis for HitlCounterService.")
        except redis.exceptions.ConnectionError as e:
            logger.error("Failed to connect to Redis for HitlCounterService.", error=str(e))
            raise

    def _get_project_key(self, project_id: UUID) -> str:
        """Generates the Redis key for a given project."""
        return f"hitl:project:{str(project_id)}"

    def get_settings(self, project_id: UUID) -> Dict[str, Any]:
        """
        Retrieves the current HITL settings for a project.
        If no settings exist, it initializes them with defaults.

        Args:
            project_id: The ID of the project.

        Returns:
            A dictionary with the project's HITL settings.
        """
        project_key = self._get_project_key(project_id)
        settings_data = self.redis_client.hgetall(project_key)

        if not settings_data:
            logger.info("No HITL settings found for project, initializing with defaults.", project_id=str(project_id))
            default_settings = {
                "enabled": str(settings.hitl_default_enabled),
                "limit": str(settings.hitl_default_counter),
                "remaining": str(settings.hitl_default_counter),
            }
            self.redis_client.hset(project_key, mapping=default_settings)
            return {
                "enabled": settings.hitl_default_enabled,
                "limit": settings.hitl_default_counter,
                "remaining": settings.hitl_default_counter,
            }

        return {
            "enabled": settings_data.get("enabled", "True").lower() == "true",
            "limit": int(settings_data.get("limit", "10")),
            "remaining": int(settings_data.get("remaining", "10")),
        }

    def check_and_decrement_counter(self, project_id: UUID) -> (bool, bool):
        """
        Checks if an agent action is allowed and decrements the counter if so.
        This is an atomic operation to prevent race conditions.

        Args:
            project_id: The ID of the project.

        Returns:
            A tuple: (is_action_allowed, limit_was_just_reached)
        """
        project_key = self._get_project_key(project_id)

        lua_script = """
        local enabled = redis.call('HGET', KEYS[1], 'enabled')
        if enabled == 'False' then
            return {1, 0} -- {action_allowed, limit_just_reached}
        end

        local remaining = tonumber(redis.call('HGET', KEYS[1], 'remaining'))
        if remaining == nil or remaining <= 0 then
            return {0, 0}
        end

        local new_remaining = redis.call('HINCRBY', KEYS[1], 'remaining', -1)

        local limit_just_reached = 0
        if new_remaining == 0 then
            limit_just_reached = 1
        end

        return {1, limit_just_reached}
        """

        try:
            script = self.redis_client.register_script(lua_script)
            result = script(keys=[project_key])

            is_action_allowed = (result[0] == 1)
            limit_was_just_reached = (result[1] == 1)

            if is_action_allowed:
                logger.info("HITL check passed and counter decremented.", project_id=str(project_id))
                if limit_was_just_reached:
                    logger.warning("HITL counter limit was just reached.", project_id=str(project_id))
            else:
                logger.warning("HITL check failed, action limit reached.", project_id=str(project_id))

            return is_action_allowed, limit_was_just_reached
        except Exception as e:
            logger.error("Error executing Redis script for HITL counter.", error=str(e), project_id=str(project_id))
            return False, False

    def update_settings(self, project_id: UUID, new_limit: Optional[int] = None, new_status: Optional[bool] = None) -> Dict[str, Any]:
        """
        Updates the HITL settings for a project and resets the remaining counter.

        Args:
            project_id: The ID of the project.
            new_limit: The new action limit.
            new_status: The new enabled status for HITL.

        Returns:
            The updated settings dictionary.
        """
        project_key = self._get_project_key(project_id)
        current_settings = self.get_settings(project_id)

        update_data = {}

        if new_limit is not None:
            update_data["limit"] = str(new_limit)
            # When the limit is updated, also reset the remaining counter.
            update_data["remaining"] = str(new_limit)
            current_settings["limit"] = new_limit
            current_settings["remaining"] = new_limit

        if new_status is not None:
            update_data["enabled"] = str(new_status)
            current_settings["enabled"] = new_status

        if update_data:
            self.redis_client.hset(project_key, mapping=update_data)
            logger.info("Updated HITL settings for project.", project_id=str(project_id), updates=update_data)

        return current_settings