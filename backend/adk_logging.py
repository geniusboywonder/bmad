#!/usr/bin/env python3
"""Unified Logging Configuration for ADK System.

This module provides standardized logging configuration for all ADK components,
ensuring consistent log formats, levels, and structured logging across the system.
"""

import sys
import logging
from typing import Dict, Any, Optional
import structlog
from datetime import datetime


def setup_structlog() -> structlog.WriteLogger:
    """Configure structlog for consistent logging across all modules."""
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        stream=sys.stdout
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger()


# Global logger instance
logger = setup_structlog()


def get_logger(name: str) -> structlog.WriteLogger:
    """Get a logger instance with the specified name."""
    return structlog.get_logger(name)


def set_log_level(level: str) -> None:
    """Set the global logging level."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    if level.upper() in level_map:
        logging.getLogger().setLevel(level_map[level.upper()])
        logger.info(f"Log level set to {level.upper()}")
    else:
        logger.warning(f"Invalid log level: {level}. Using INFO.")


class ADKLogger:
    """Enhanced logger with ADK-specific logging methods."""

    def __init__(self, name: str = "adk"):
        self.logger = get_logger(name)
        self.context = {}

    def with_context(self, **kwargs) -> 'ADKLogger':
        """Add context to all log messages."""
        new_logger = ADKLogger()
        new_logger.logger = self.logger
        new_logger.context = {**self.context, **kwargs}
        return new_logger

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **{**self.context, **kwargs})

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **{**self.context, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **{**self.context, **kwargs})

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        if exc_info:
            kwargs["exc_info"] = exc_info
        self.logger.error(message, **{**self.context, **kwargs})

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, **{**self.context, **kwargs})

    def log_agent_creation(self, agent_type: str, implementation: str, **kwargs) -> None:
        """Log agent creation event."""
        self.info(
            f"Agent created: {agent_type}",
            event="agent_creation",
            agent_type=agent_type,
            implementation=implementation,
            **kwargs
        )

    def log_performance_metric(self, metric_name: str, value: Any, **kwargs) -> None:
        """Log performance metric."""
        self.info(
            f"Performance metric: {metric_name} = {value}",
            event="performance_metric",
            metric_name=metric_name,
            metric_value=value,
            **kwargs
        )

    def log_error_with_context(self, error: Exception, operation: str, **kwargs) -> None:
        """Log error with operation context."""
        self.error(
            f"Error in {operation}: {str(error)}",
            event="operation_error",
            operation=operation,
            error_type=type(error).__name__,
            **kwargs
        )

    def log_adk_operation(self, operation: str, status: str, duration: Optional[float] = None, **kwargs) -> None:
        """Log ADK-specific operation."""
        message = f"ADK operation: {operation} - {status}"
        if duration:
            message += f" ({duration:.2f}s)"

        self.info(
            message,
            event="adk_operation",
            operation=operation,
            status=status,
            duration=duration,
            **kwargs
        )


# Global ADK logger instance
adk_logger = ADKLogger("adk")


def create_operation_logger(operation: str) -> ADKLogger:
    """Create a logger for a specific operation."""
    return adk_logger.with_context(operation=operation)


def log_agent_lifecycle_event(event: str, agent_type: str, **kwargs) -> None:
    """Log agent lifecycle events."""
    adk_logger.info(
        f"Agent {event}: {agent_type}",
        event="agent_lifecycle",
        lifecycle_event=event,
        agent_type=agent_type,
        **kwargs
    )


def log_system_health_check(status: str, score: int, **kwargs) -> None:
    """Log system health check results."""
    adk_logger.info(
        f"System health check: {status} (score: {score})",
        event="health_check",
        health_status=status,
        health_score=score,
        **kwargs
    )


def log_migration_event(event: str, phase: str, **kwargs) -> None:
    """Log migration-related events."""
    adk_logger.info(
        f"Migration {event}: {phase}",
        event="migration",
        migration_event=event,
        migration_phase=phase,
        **kwargs
    )


if __name__ == "__main__":
    print("🚀 ADK Logging Configuration Demo")
    print("=" * 50)

    # Test basic logging
    logger.info("Basic logging test", test="value")

    # Test ADK logger
    adk_logger.info("ADK logger test", component="demo")

    # Test context logger
    ctx_logger = adk_logger.with_context(user="test_user", session="123")
    ctx_logger.info("Context logging test", action="demo_action")

    # Test operation logger
    op_logger = create_operation_logger("demo_operation")
    op_logger.info("Operation logging test", status="success")

    # Test specialized logging functions
    log_agent_lifecycle_event("created", "analyst", user_id="user123")
    log_system_health_check("healthy", 85, components_checked=5)
    log_migration_event("started", "rollout", agents_migrated=3)

    print("\n✅ Logging configuration working correctly")
