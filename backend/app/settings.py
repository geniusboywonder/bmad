"""Application configuration using Pydantic Settings."""

from typing import List, Optional, Literal # Added Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = Field(default="BotArmy Backend")  # Reads APP_NAME env var automatically
    app_version: str = Field(default="0.1.0")  # Reads APP_VERSION env var automatically
    debug: bool = Field(default=False)  # Reads DEBUG env var automatically
    log_level: str = Field(default="INFO")  # Reads LOG_LEVEL env var automatically
    
    # Database Configuration
    database_url: str  # Reads DATABASE_URL env var automatically
    database_test_url: Optional[str] = Field(default=None)  # Reads DATABASE_TEST_URL env var automatically
    database_pool_size: int = Field(default=10)  # Reads DATABASE_POOL_SIZE env var automatically
    database_max_overflow: int = Field(default=20)  # Reads DATABASE_MAX_OVERFLOW env var automatically
    database_pool_timeout: int = Field(default=30)  # Reads DATABASE_POOL_TIMEOUT env var automatically
    
    # Redis Configuration
    redis_url: str  # Reads REDIS_URL env var automatically
    redis_celery_url: str  # Reads REDIS_CELERY_URL env var automatically

    # Celery Configuration
    celery_broker_url: str  # Reads CELERY_BROKER_URL env var automatically
    celery_result_backend: str  # Reads CELERY_RESULT_BACKEND env var automatically
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1")  # Reads API_V1_PREFIX env var automatically
    api_host: str = Field(default="0.0.0.0")  # Reads API_HOST env var automatically
    api_port: int = Field(default=8000)  # Reads API_PORT env var automatically
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
        # Reads CORS_ORIGINS env var automatically
    )
    
    # WebSocket Configuration
    ws_heartbeat_interval: int = Field(default=30)  # Reads WS_HEARTBEAT_INTERVAL env var automatically
    ws_max_connections: int = Field(default=100)  # Reads WS_MAX_CONNECTIONS env var automatically
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None)  # Reads OPENAI_API_KEY env var automatically
    anthropic_api_key: Optional[str] = Field(default=None)  # Reads ANTHROPIC_API_KEY env var automatically
    google_api_key: Optional[str] = Field(default=None)  # Reads GOOGLE_API_KEY env var automatically
    gemini_key_key: Optional[str] = Field(default=None)  # Reads GEMINI_KEY_KEY env var automatically
    google_genai_api_key: Optional[str] = Field(default=None)  # Reads GOOGLE_GENAI_API_KEY env var automatically
    google_application_credentials: Optional[str] = Field(default=None)  # Reads GOOGLE_APPLICATION_CREDENTIALS env var automatically
    
    # Agent-to-LLM Mapping (New section)
    analyst_agent_provider: Literal["openai", "anthropic", "gemini"]  # Reads ANALYST_AGENT_PROVIDER env var automatically
    analyst_agent_model: str  # Reads ANALYST_AGENT_MODEL env var automatically
    architect_agent_provider: Literal["openai", "anthropic", "gemini"]  # Reads ARCHITECT_AGENT_PROVIDER env var automatically
    architect_agent_model: str  # Reads ARCHITECT_AGENT_MODEL env var automatically
    coder_agent_provider: Literal["openai", "anthropic", "gemini"]  # Reads CODER_AGENT_PROVIDER env var automatically
    coder_agent_model: str  # Reads CODER_AGENT_MODEL env var automatically
    tester_agent_provider: Literal["openai", "anthropic", "gemini"]  # Reads TESTER_AGENT_PROVIDER env var automatically
    tester_agent_model: str  # Reads TESTER_AGENT_MODEL env var automatically
    deployer_agent_provider: Literal["openai", "anthropic", "gemini"]  # Reads DEPLOYER_AGENT_PROVIDER env var automatically
    deployer_agent_model: str  # Reads DEPLOYER_AGENT_MODEL env var automatically
    
    # LLM Reliability Configuration
    llm_retry_max_attempts: int = Field(default=3)  # Reads LLM_RETRY_MAX_ATTEMPTS env var automatically
    llm_retry_base_delay: float = Field(default=1.0)  # Reads LLM_RETRY_BASE_DELAY env var automatically
    llm_response_timeout: int = Field(default=30)  # Reads LLM_RESPONSE_TIMEOUT env var automatically
    llm_max_response_size: int = Field(default=50000)  # Reads LLM_MAX_RESPONSE_SIZE env var automatically
    llm_enable_usage_tracking: bool = Field(default=True)  # Reads LLM_ENABLE_USAGE_TRACKING env var automatically

    # HITL Safety Configuration
    hitl_enabled: bool = Field(default=True)  # Reads HITL_ENABLED env var automatically
    hitl_approval_timeout_minutes: int = Field(default=30)  # Reads HITL_APPROVAL_TIMEOUT_MINUTES env var automatically
    hitl_budget_daily_limit: int = Field(default=10000)  # Reads HITL_BUDGET_DAILY_LIMIT env var automatically
    hitl_budget_session_limit: int = Field(default=2000)  # Reads HITL_BUDGET_SESSION_LIMIT env var automatically
    hitl_emergency_stop_enabled: bool = Field(default=True)  # Reads HITL_EMERGENCY_STOP_ENABLED env var automatically
    hitl_websocket_notifications: bool = Field(default=True)  # Reads HITL_WEBSOCKET_NOTIFICATIONS env var automatically
    
    # Security
    secret_key: str  # Reads SECRET_KEY env var automatically
    algorithm: str = Field(default="HS256")  # Reads ALGORITHM env var automatically
    access_token_expire_minutes: int = Field(default=30)  # Reads ACCESS_TOKEN_EXPIRE_MINUTES env var automatically
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Allow extra environment variables not explicitly defined
    )


# Global settings instance
settings = Settings()
