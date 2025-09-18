"""Application configuration using Pydantic Settings."""

from typing import List, Optional, Literal # Added Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = Field(default="BotArmy Backend", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database Configuration
    database_url: str = Field(env="DATABASE_URL")
    database_test_url: Optional[str] = Field(default=None, env="DATABASE_TEST_URL")
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE") # New
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW") # New
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT") # New
    
    # Redis Configuration
    redis_url: str = Field(env="REDIS_URL")
    redis_celery_url: str = Field(env="REDIS_CELERY_URL")

    # Celery Configuration
    celery_broker_url: str = Field(env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND")
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # WebSocket Configuration
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    ws_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    gemini_key_key: Optional[str] = Field(default=None, env="GEMINI_KEY_KEY")
    google_genai_api_key: Optional[str] = Field(default=None, env="GOOGLE_GENAI_API_KEY")
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS") # New, as per plan
    
    # Agent-to-LLM Mapping (New section)
    analyst_agent_provider: Literal["openai", "anthropic", "gemini"] = Field(env="ANALYST_AGENT_PROVIDER") # New
    analyst_agent_model: str = Field(env="ANALYST_AGENT_MODEL") # New
    architect_agent_provider: Literal["openai", "anthropic", "gemini"] = Field(env="ARCHITECT_AGENT_PROVIDER") # New
    architect_agent_model: str = Field(env="ARCHITECT_AGENT_MODEL") # New
    coder_agent_provider: Literal["openai", "anthropic", "gemini"] = Field(env="CODER_AGENT_PROVIDER") # New
    coder_agent_model: str = Field(env="CODER_AGENT_MODEL") # New
    tester_agent_provider: Literal["openai", "anthropic", "gemini"] = Field(env="TESTER_AGENT_PROVIDER") # New
    tester_agent_model: str = Field(env="TESTER_AGENT_MODEL") # New
    deployer_agent_provider: Literal["openai", "anthropic", "gemini"] = Field(env="DEPLOYER_AGENT_PROVIDER") # New
    deployer_agent_model: str = Field(env="DEPLOYER_AGENT_MODEL") # New
    
    # LLM Reliability Configuration
    llm_retry_max_attempts: int = Field(default=3, env="LLM_RETRY_MAX_ATTEMPTS")
    llm_retry_base_delay: float = Field(default=1.0, env="LLM_RETRY_BASE_DELAY")
    llm_response_timeout: int = Field(default=30, env="LLM_RESPONSE_TIMEOUT")
    llm_max_response_size: int = Field(default=50000, env="LLM_MAX_RESPONSE_SIZE")
    llm_enable_usage_tracking: bool = Field(default=True, env="LLM_ENABLE_USAGE_TRACKING")

    # HITL Safety Configuration
    hitl_enabled: bool = Field(default=True, env="HITL_ENABLED")
    hitl_approval_timeout_minutes: int = Field(default=30, env="HITL_APPROVAL_TIMEOUT_MINUTES")
    hitl_budget_daily_limit: int = Field(default=10000, env="HITL_BUDGET_DAILY_LIMIT")
    hitl_budget_session_limit: int = Field(default=2000, env="HITL_BUDGET_SESSION_LIMIT")
    hitl_emergency_stop_enabled: bool = Field(default=True, env="HITL_EMERGENCY_STOP_ENABLED")
    hitl_websocket_notifications: bool = Field(default=True, env="HITL_WEBSOCKET_NOTIFICATIONS")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore" # New: Allow extra environment variables not explicitly defined


# Global settings instance
settings = Settings()
