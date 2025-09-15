#!/usr/bin/env python3
"""Configuration Management for ADK System.

This module provides centralized configuration management for all ADK components,
using environment variables with sensible defaults for deployment flexibility.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import structlog

from adk_logging import adk_logger

logger = adk_logger


class ADKConfig:
    """Centralized configuration management for ADK system."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv("ADK_CONFIG_FILE")
        self._config = {}
        self._load_defaults()
        self._load_from_env()
        self._load_from_file()
        self._validate_config()

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            # System settings
            "max_memory_mb": 1024,
            "max_cpu_percent": 80.0,
            "max_response_time_sec": 5.0,
            "target_cache_hit_rate": 0.85,
            "metrics_collection_interval": 30,
            "health_check_interval": 60,
            "log_level": "INFO",

            # Performance settings
            "enable_performance_monitoring": True,
            "performance_baseline_window_days": 7,
            "cache_ttl_seconds": 3600,
            "max_cache_size": 100,
            "enable_response_caching": True,
            "enable_connection_pooling": True,

            # ADK settings
            "enable_multi_model": True,
            "default_model": "gemini-2.0-flash",
            "model_timeout_seconds": 30,
            "max_tokens_per_request": 4096,
            "enable_model_fallback": True,

            # Agent settings
            "agent_creation_timeout": 10,
            "max_agents_per_user": 10,
            "agent_cache_enabled": True,
            "agent_health_check_interval": 300,

            # Security settings
            "enable_input_validation": True,
            "max_input_length": 10000,
            "enable_content_filtering": True,
            "security_log_level": "WARNING",

            # Feature flags
            "enable_adk_optimization": True,
            "enable_custom_tools": True,
            "enable_observability": True,
            "enable_advanced_logging": True,

            # Migration settings
            "migration_batch_size": 5,
            "migration_timeout_seconds": 300,
            "rollback_timeout_seconds": 60,

            # Tool settings
            "tool_execution_timeout": 60,
            "max_tool_concurrent_executions": 3,
            "tool_retry_attempts": 3,
            "tool_retry_delay_seconds": 1,

            # Database settings (if needed)
            "db_connection_pool_size": 10,
            "db_connection_timeout": 30,
            "db_max_connections": 20,

            # External service settings
            "external_api_timeout": 10,
            "external_api_retry_attempts": 2,
            "external_api_rate_limit_per_minute": 60,

            # Development settings
            "development_mode": False,
            "debug_enabled": False,
            "test_mode": False,
        }

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            # System settings
            "ADK_MAX_MEMORY_MB": ("max_memory_mb", int),
            "ADK_MAX_CPU_PERCENT": ("max_cpu_percent", float),
            "ADK_MAX_RESPONSE_TIME_SEC": ("max_response_time_sec", float),
            "ADK_TARGET_CACHE_HIT_RATE": ("target_cache_hit_rate", float),
            "ADK_METRICS_INTERVAL": ("metrics_collection_interval", int),
            "ADK_HEALTH_CHECK_INTERVAL": ("health_check_interval", int),
            "ADK_LOG_LEVEL": ("log_level", str),

            # Performance settings
            "ADK_ENABLE_PERF_MONITORING": ("enable_performance_monitoring", self._str_to_bool),
            "ADK_PERF_BASELINE_WINDOW": ("performance_baseline_window_days", int),
            "ADK_CACHE_TTL_SECONDS": ("cache_ttl_seconds", int),
            "ADK_MAX_CACHE_SIZE": ("max_cache_size", int),
            "ADK_ENABLE_RESPONSE_CACHING": ("enable_response_caching", self._str_to_bool),
            "ADK_ENABLE_CONNECTION_POOLING": ("enable_connection_pooling", self._str_to_bool),

            # ADK settings
            "ADK_ENABLE_MULTI_MODEL": ("enable_multi_model", self._str_to_bool),
            "ADK_DEFAULT_MODEL": ("default_model", str),
            "ADK_MODEL_TIMEOUT": ("model_timeout_seconds", int),
            "ADK_MAX_TOKENS": ("max_tokens_per_request", int),
            "ADK_ENABLE_MODEL_FALLBACK": ("enable_model_fallback", self._str_to_bool),

            # Agent settings
            "ADK_AGENT_CREATION_TIMEOUT": ("agent_creation_timeout", int),
            "ADK_MAX_AGENTS_PER_USER": ("max_agents_per_user", int),
            "ADK_AGENT_CACHE_ENABLED": ("agent_cache_enabled", self._str_to_bool),
            "ADK_AGENT_HEALTH_CHECK_INTERVAL": ("agent_health_check_interval", int),

            # Security settings
            "ADK_ENABLE_INPUT_VALIDATION": ("enable_input_validation", self._str_to_bool),
            "ADK_MAX_INPUT_LENGTH": ("max_input_length", int),
            "ADK_ENABLE_CONTENT_FILTERING": ("enable_content_filtering", self._str_to_bool),
            "ADK_SECURITY_LOG_LEVEL": ("security_log_level", str),

            # Feature flags
            "ADK_ENABLE_OPTIMIZATION": ("enable_adk_optimization", self._str_to_bool),
            "ADK_ENABLE_CUSTOM_TOOLS": ("enable_custom_tools", self._str_to_bool),
            "ADK_ENABLE_OBSERVABILITY": ("enable_observability", self._str_to_bool),
            "ADK_ENABLE_ADVANCED_LOGGING": ("enable_advanced_logging", self._str_to_bool),

            # Migration settings
            "ADK_MIGRATION_BATCH_SIZE": ("migration_batch_size", int),
            "ADK_MIGRATION_TIMEOUT": ("migration_timeout_seconds", int),
            "ADK_ROLLBACK_TIMEOUT": ("rollback_timeout_seconds", int),

            # Tool settings
            "ADK_TOOL_EXECUTION_TIMEOUT": ("tool_execution_timeout", int),
            "ADK_MAX_TOOL_CONCURRENT": ("max_tool_concurrent_executions", int),
            "ADK_TOOL_RETRY_ATTEMPTS": ("tool_retry_attempts", int),
            "ADK_TOOL_RETRY_DELAY": ("tool_retry_delay_seconds", int),

            # Database settings
            "ADK_DB_POOL_SIZE": ("db_connection_pool_size", int),
            "ADK_DB_CONNECTION_TIMEOUT": ("db_connection_timeout", int),
            "ADK_DB_MAX_CONNECTIONS": ("db_max_connections", int),

            # External service settings
            "ADK_EXTERNAL_API_TIMEOUT": ("external_api_timeout", int),
            "ADK_EXTERNAL_API_RETRY": ("external_api_retry_attempts", int),
            "ADK_EXTERNAL_API_RATE_LIMIT": ("external_api_rate_limit_per_minute", int),

            # Development settings
            "ADK_DEVELOPMENT_MODE": ("development_mode", self._str_to_bool),
            "ADK_DEBUG_ENABLED": ("debug_enabled", self._str_to_bool),
            "ADK_TEST_MODE": ("test_mode", self._str_to_bool),
        }

        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    self._config[config_key] = converter(value)
                    logger.debug(f"Loaded config from env: {config_key} = {self._config[config_key]}")
                except Exception as e:
                    logger.warning(f"Failed to parse env var {env_var}: {e}")

    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_file:
            return

        config_path = Path(self.config_file)
        if not config_path.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return

        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)

            # Merge file config with existing config
            for key, value in file_config.items():
                if key in self._config:
                    self._config[key] = value
                    logger.debug(f"Loaded config from file: {key} = {value}")
                else:
                    logger.warning(f"Unknown config key in file: {key}")

        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")

    def _validate_config(self) -> None:
        """Validate configuration values."""
        validations = {
            "max_memory_mb": lambda x: isinstance(x, int) and x > 0,
            "max_cpu_percent": lambda x: isinstance(x, (int, float)) and 0 < x <= 100,
            "max_response_time_sec": lambda x: isinstance(x, (int, float)) and x > 0,
            "target_cache_hit_rate": lambda x: isinstance(x, (int, float)) and 0 <= x <= 1,
            "metrics_collection_interval": lambda x: isinstance(x, int) and x > 0,
            "health_check_interval": lambda x: isinstance(x, int) and x > 0,
            "log_level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "cache_ttl_seconds": lambda x: isinstance(x, int) and x > 0,
            "max_cache_size": lambda x: isinstance(x, int) and x >= 0,
            "agent_creation_timeout": lambda x: isinstance(x, (int, float)) and x > 0,
            "max_agents_per_user": lambda x: isinstance(x, int) and x > 0,
            "max_input_length": lambda x: isinstance(x, int) and x > 0,
            "migration_batch_size": lambda x: isinstance(x, int) and x > 0,
            "tool_execution_timeout": lambda x: isinstance(x, (int, float)) and x > 0,
        }

        for key, validator in validations.items():
            if key in self._config and not validator(self._config[key]):
                logger.warning(f"Invalid config value for {key}: {self._config[key]}")
                # Reset to default
                self._load_defaults()
                break

    def _str_to_bool(self, value: str) -> bool:
        """Convert string to boolean."""
        if isinstance(value, bool):
            return value
        return value.lower() in ('true', '1', 'yes', 'on')

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if key in self._config:
            self._config[key] = value
            logger.debug(f"Config updated: {key} = {value}")
        else:
            logger.warning(f"Attempted to set unknown config key: {key}")

    def all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    def save_to_file(self, file_path: str) -> bool:
        """Save current configuration to file."""
        try:
            config_path = Path(file_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=2)

            logger.info(f"Configuration saved to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            return False

    def get_section(self, section_prefix: str) -> Dict[str, Any]:
        """Get configuration values for a specific section."""
        section = {}
        for key, value in self._config.items():
            if key.startswith(section_prefix):
                section[key] = value
        return section

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._load_defaults()
        logger.info("Configuration reset to defaults")

    def get_environment_variables(self) -> Dict[str, str]:
        """Get mapping of config keys to environment variable names."""
        return {
            "max_memory_mb": "ADK_MAX_MEMORY_MB",
            "max_cpu_percent": "ADK_MAX_CPU_PERCENT",
            "max_response_time_sec": "ADK_MAX_RESPONSE_TIME_SEC",
            "target_cache_hit_rate": "ADK_TARGET_CACHE_HIT_RATE",
            "metrics_collection_interval": "ADK_METRICS_INTERVAL",
            "health_check_interval": "ADK_HEALTH_CHECK_INTERVAL",
            "log_level": "ADK_LOG_LEVEL",
            "enable_performance_monitoring": "ADK_ENABLE_PERF_MONITORING",
            "cache_ttl_seconds": "ADK_CACHE_TTL_SECONDS",
            "max_cache_size": "ADK_MAX_CACHE_SIZE",
            "enable_multi_model": "ADK_ENABLE_MULTI_MODEL",
            "default_model": "ADK_DEFAULT_MODEL",
            "enable_input_validation": "ADK_ENABLE_INPUT_VALIDATION",
            "max_input_length": "ADK_MAX_INPUT_LENGTH",
            "development_mode": "ADK_DEVELOPMENT_MODE",
        }


# Global configuration instance
config = ADKConfig()


# Convenience functions for accessing common config values
def get_max_memory_mb() -> int:
    """Get maximum memory usage in MB."""
    return config.get("max_memory_mb")


def get_max_cpu_percent() -> float:
    """Get maximum CPU usage percentage."""
    return config.get("max_cpu_percent")


def get_max_response_time_sec() -> float:
    """Get maximum response time in seconds."""
    return config.get("max_response_time_sec")


def get_target_cache_hit_rate() -> float:
    """Get target cache hit rate."""
    return config.get("target_cache_hit_rate")


def get_metrics_collection_interval() -> int:
    """Get metrics collection interval in seconds."""
    return config.get("metrics_collection_interval")


def get_health_check_interval() -> int:
    """Get health check interval in seconds."""
    return config.get("health_check_interval")


def get_log_level() -> str:
    """Get logging level."""
    return config.get("log_level")


def is_performance_monitoring_enabled() -> bool:
    """Check if performance monitoring is enabled."""
    return config.get("enable_performance_monitoring")


def is_multi_model_enabled() -> bool:
    """Check if multi-model support is enabled."""
    return config.get("enable_multi_model")


def get_default_model() -> str:
    """Get default model name."""
    return config.get("default_model")


def is_development_mode() -> bool:
    """Check if development mode is enabled."""
    return config.get("development_mode")


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return config.get("debug_enabled")


if __name__ == "__main__":
    print("🚀 ADK Configuration Management Demo")
    print("=" * 50)

    # Display current configuration
    print("Current Configuration:")
    for key, value in sorted(config.all().items()):
        print(f"  {key}: {value}")

    print("\nEnvironment Variables Mapping:")
    env_vars = config.get_environment_variables()
    for config_key, env_var in sorted(env_vars.items()):
        print(f"  {config_key} -> {env_var}")

    # Test configuration updates
    print("\nTesting Configuration Updates:")
    original_value = config.get("max_memory_mb")
    config.set("max_memory_mb", 2048)
    print(f"Updated max_memory_mb: {original_value} -> {config.get('max_memory_mb')}")

    # Test section retrieval
    print("\nPerformance Settings:")
    perf_config = config.get_section("enable_")
    for key, value in sorted(perf_config.items()):
        print(f"  {key}: {value}")

    print("\n✅ Configuration management working correctly")
