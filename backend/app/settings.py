"""Application configuration using Pydantic Settings - SIMPLIFIED."""

from typing import List, Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Simplified application settings with consolidated configuration."""
    
    # Core Configuration
    app_name: str = Field(default="BMAD Backend")
    app_version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # Database
    database_url: str
    
    # Redis (SINGLE URL for all services)
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # LLM Provider-Agnostic Configuration
    llm_provider: Literal["anthropic", "openai", "google"] = Field(default="anthropic")
    llm_api_key: str  # Primary API key based on llm_provider
    llm_model: str = Field(default="claude-3-5-sonnet-20241022")
    
    # Additional LLM API Keys (optional)
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    
    # HITL Safety (Simplified)
    hitl_default_enabled: bool = Field(default=True)
    hitl_default_counter: int = Field(default=10)
    hitl_approval_timeout_minutes: int = Field(default=30)
    
    # Security
    secret_key: str
    
    # API Configuration (Essential only)
    api_v1_prefix: str = Field(default="/api/v1")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: List[str] = Field(default=["http://localhost:3000"])
    
    # Agent-to-LLM Mapping (Simplified - use defaults with override capability)
    analyst_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="anthropic")
    analyst_agent_model: str = Field(default="claude-3-5-sonnet-20241022")
    architect_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="openai")
    architect_agent_model: str = Field(default="gpt-4o")
    coder_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="openai")
    coder_agent_model: str = Field(default="gpt-4o")
    tester_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="google")
    tester_agent_model: str = Field(default="gemini-1.5-pro")
    deployer_agent_provider: Literal["openai", "anthropic", "google"] = Field(default="openai")
    deployer_agent_model: str = Field(default="gpt-4o")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
