"""Celery application configuration."""

from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "botarmy",
    broker=settings.redis_celery_url,
    backend=settings.redis_celery_url,
    include=["app.tasks.agent_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    task_default_priority=5,
    broker_transport_options={
        'priority_steps': list(range(10)),
    },
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.agent_tasks.*": {"queue": "agent_tasks"},
}
