"""
Test suite for simplified settings configuration.
Tests the consolidated 20-variable configuration system.
"""

import pytest
import os
from typing import Dict, Any
from unittest.mock import patch, Mock

from app.settings import Settings
from pydantic import ValidationError


class TestSimplifiedSettings:
    """Test simplified configuration system."""
    
    @pytest.fixture
    def minimal_env_vars(self):
        """Minimal required environment variables."""
        return {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
            "LLM_API_KEY": "test-api-key-12345",
            "SECRET_KEY": "test-secret-key-for-development"
        }
    
    @pytest.fixture
    def complete_env_vars(self, minimal_env_vars):
        """Complete set of environment variables."""
        return {
            **minimal_env_vars,
            "APP_NAME": "BMAD Test Backend",
            "APP_VERSION": "1.0.0",
            "ENVIRONMENT": "testing",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "REDIS_URL": "redis://localhost:6379/1",
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "gpt-4o",
            "OPENAI_API_KEY": "sk-test-openai-key",
            "ANTHROPIC_API_KEY": "sk-ant-test-key",
            "GOOGLE_API_KEY": "test-google-key",
            "HITL_DEFAULT_ENABLED": "false",
            "HITL_DEFAULT_COUNTER": "5",
            "HITL_APPROVAL_TIMEOUT_MINUTES": "15",
            "API_V1_PREFIX": "/api/v2",
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001"
        }

    @pytest.mark.mock_data
    def test_redis_single_url_configuration(self, minimal_env_vars):
        """Test single Redis URL configuration."""
        env_vars = {
            **minimal_env_vars,
            "REDIS_URL": "redis://localhost:6379/0"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            # Should use single Redis URL for all services
            assert settings.redis_url == "redis://localhost:6379/0"
            
            # Should not have separate Celery Redis configuration
            assert not hasattr(settings, 'redis_celery_url')
            assert not hasattr(settings, 'celery_broker_url')
            assert not hasattr(settings, 'celery_result_backend')

    @pytest.mark.mock_data
    def test_redis_default_configuration(self, minimal_env_vars):
        """Test Redis default configuration when not specified."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Should use default Redis URL
            assert settings.redis_url == "redis://localhost:6379/0"

    @pytest.mark.mock_data
    def test_llm_provider_agnostic_config(self, minimal_env_vars):
        """Test provider-agnostic LLM configuration."""
        # Test Anthropic as primary provider
        anthropic_env = {
            **minimal_env_vars,
            "LLM_PROVIDER": "anthropic",
            "LLM_API_KEY": "sk-ant-test-key",
            "LLM_MODEL": "claude-3-5-sonnet-20241022"
        }
        
        with patch.dict(os.environ, anthropic_env, clear=True):
            settings = Settings()
            
            assert settings.llm_provider == "anthropic"
            assert settings.llm_api_key == "sk-ant-test-key"
            assert settings.llm_model == "claude-3-5-sonnet-20241022"

    @pytest.mark.mock_data
    def test_llm_provider_switching(self, minimal_env_vars):
        """Test easy switching between LLM providers."""
        providers_config = [
            ("openai", "sk-openai-key", "gpt-4o"),
            ("anthropic", "sk-ant-key", "claude-3-5-sonnet-20241022"),
            ("google", "google-key", "gemini-1.5-pro")
        ]
        
        for provider, api_key, model in providers_config:
            env_vars = {
                **minimal_env_vars,
                "LLM_PROVIDER": provider,
                "LLM_API_KEY": api_key,
                "LLM_MODEL": model
            }
            
            with patch.dict(os.environ, env_vars, clear=True):
                settings = Settings()
                
                assert settings.llm_provider == provider
                assert settings.llm_api_key == api_key
                assert settings.llm_model == model

    @pytest.mark.mock_data
    def test_llm_multiple_api_keys(self, minimal_env_vars):
        """Test configuration with multiple LLM API keys."""
        env_vars = {
            **minimal_env_vars,
            "LLM_PROVIDER": "anthropic",
            "LLM_API_KEY": "sk-ant-primary-key",
            "OPENAI_API_KEY": "sk-openai-secondary-key",
            "ANTHROPIC_API_KEY": "sk-ant-secondary-key",
            "GOOGLE_API_KEY": "google-secondary-key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            # Primary configuration
            assert settings.llm_provider == "anthropic"
            assert settings.llm_api_key == "sk-ant-primary-key"
            
            # Secondary API keys available
            assert settings.openai_api_key == "sk-openai-secondary-key"
            assert settings.anthropic_api_key == "sk-ant-secondary-key"
            assert settings.google_api_key == "google-secondary-key"

    @pytest.mark.mock_data
    def test_hitl_simplified_settings(self, minimal_env_vars):
        """Test simplified HITL settings."""
        env_vars = {
            **minimal_env_vars,
            "HITL_DEFAULT_ENABLED": "false",
            "HITL_DEFAULT_COUNTER": "25",
            "HITL_APPROVAL_TIMEOUT_MINUTES": "45"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.hitl_default_enabled is False
            assert settings.hitl_default_counter == 25
            assert settings.hitl_approval_timeout_minutes == 45

    @pytest.mark.mock_data
    def test_hitl_default_settings(self, minimal_env_vars):
        """Test HITL default settings when not specified."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Should use sensible defaults
            assert settings.hitl_default_enabled is True
            assert settings.hitl_default_counter == 10
            assert settings.hitl_approval_timeout_minutes == 30

    @pytest.mark.mock_data
    def test_backward_compatibility_getattr(self, minimal_env_vars):
        """Test backward compatibility with getattr defaults."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Test accessing removed/legacy configuration with defaults
            legacy_value = getattr(settings, 'legacy_setting', 'default_value')
            assert legacy_value == 'default_value'
            
            # Test accessing removed Redis settings
            celery_url = getattr(settings, 'redis_celery_url', settings.redis_url)
            assert celery_url == settings.redis_url
            
            broker_url = getattr(settings, 'celery_broker_url', settings.redis_url)
            assert broker_url == settings.redis_url

    @pytest.mark.mock_data
    def test_core_configuration_defaults(self, minimal_env_vars):
        """Test core configuration defaults."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Core defaults
            assert settings.app_name == "BMAD Backend"
            assert settings.app_version == "0.1.0"
            assert settings.environment == "development"
            assert settings.debug is False
            assert settings.log_level == "INFO"

    @pytest.mark.mock_data
    def test_api_configuration_defaults(self, minimal_env_vars):
        """Test API configuration defaults."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # API defaults
            assert settings.api_v1_prefix == "/api/v1"
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000
            assert settings.cors_origins == ["http://localhost:3000"]

    @pytest.mark.mock_data
    def test_cors_origins_parsing(self, minimal_env_vars):
        """Test CORS origins parsing from comma-separated string."""
        env_vars = {
            **minimal_env_vars,
            "CORS_ORIGINS": "http://localhost:3000,http://localhost:3001,https://app.example.com"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            expected_origins = [
                "http://localhost:3000",
                "http://localhost:3001", 
                "https://app.example.com"
            ]
            assert settings.cors_origins == expected_origins

    @pytest.mark.mock_data
    def test_agent_llm_mapping_defaults(self, minimal_env_vars):
        """Test agent-to-LLM mapping defaults."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Verify agent-specific LLM configurations
            assert settings.analyst_agent_provider == "anthropic"
            assert settings.analyst_agent_model == "claude-3-5-sonnet-20241022"
            
            assert settings.architect_agent_provider == "openai"
            assert settings.architect_agent_model == "gpt-4o"
            
            assert settings.coder_agent_provider == "openai"
            assert settings.coder_agent_model == "gpt-4o"
            
            assert settings.tester_agent_provider == "google"
            assert settings.tester_agent_model == "gemini-1.5-pro"
            
            assert settings.deployer_agent_provider == "openai"
            assert settings.deployer_agent_model == "gpt-4o"

    @pytest.mark.mock_data
    def test_agent_llm_mapping_overrides(self, minimal_env_vars):
        """Test agent-to-LLM mapping with overrides."""
        env_vars = {
            **minimal_env_vars,
            "ANALYST_AGENT_PROVIDER": "openai",
            "ANALYST_AGENT_MODEL": "gpt-4o-mini",
            "TESTER_AGENT_PROVIDER": "anthropic",
            "TESTER_AGENT_MODEL": "claude-3-haiku"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            # Overridden values
            assert settings.analyst_agent_provider == "openai"
            assert settings.analyst_agent_model == "gpt-4o-mini"
            assert settings.tester_agent_provider == "anthropic"
            assert settings.tester_agent_model == "claude-3-haiku"
            
            # Default values for non-overridden agents
            assert settings.architect_agent_provider == "openai"
            assert settings.coder_agent_provider == "openai"

    @pytest.mark.mock_data
    def test_complete_configuration_loading(self, complete_env_vars):
        """Test loading complete configuration with all variables."""
        with patch.dict(os.environ, complete_env_vars, clear=True):
            settings = Settings()
            
            # Verify all values loaded correctly
            assert settings.app_name == "BMAD Test Backend"
            assert settings.app_version == "1.0.0"
            assert settings.environment == "testing"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            
            assert settings.redis_url == "redis://localhost:6379/1"
            
            assert settings.llm_provider == "openai"
            assert settings.llm_model == "gpt-4o"
            assert settings.openai_api_key == "sk-test-openai-key"
            
            assert settings.hitl_default_enabled is False
            assert settings.hitl_default_counter == 5
            assert settings.hitl_approval_timeout_minutes == 15
            
            assert settings.api_v1_prefix == "/api/v2"
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000

    # Validation Tests
    
    @pytest.mark.mock_data
    def test_missing_required_database_url(self):
        """Test validation error for missing DATABASE_URL."""
        env_vars = {
            "LLM_API_KEY": "test-key",
            "SECRET_KEY": "test-secret"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "database_url" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_missing_required_llm_api_key(self):
        """Test validation error for missing LLM_API_KEY."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
            "SECRET_KEY": "test-secret"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "llm_api_key" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_missing_required_secret_key(self):
        """Test validation error for missing SECRET_KEY."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
            "LLM_API_KEY": "test-key"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "secret_key" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_invalid_llm_provider(self, minimal_env_vars):
        """Test validation error for invalid LLM provider."""
        env_vars = {
            **minimal_env_vars,
            "LLM_PROVIDER": "invalid_provider"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "llm_provider" in str(exc_info.value)

    @pytest.mark.mock_data
    def test_invalid_boolean_values(self, minimal_env_vars):
        """Test handling of invalid boolean values."""
        env_vars = {
            **minimal_env_vars,
            "DEBUG": "invalid_boolean",
            "HITL_DEFAULT_ENABLED": "not_a_boolean"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    @pytest.mark.mock_data
    def test_invalid_integer_values(self, minimal_env_vars):
        """Test handling of invalid integer values."""
        env_vars = {
            **minimal_env_vars,
            "API_PORT": "not_a_number",
            "HITL_DEFAULT_COUNTER": "invalid_int"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    # Configuration Reduction Tests
    
    @pytest.mark.mock_data
    def test_configuration_variable_count(self, complete_env_vars):
        """Test that configuration has been reduced to ~20 core variables."""
        with patch.dict(os.environ, complete_env_vars, clear=True):
            settings = Settings()
            
            # Count actual configuration fields (excluding methods)
            config_fields = [
                field for field in dir(settings) 
                if not field.startswith('_') and not callable(getattr(settings, field))
            ]
            
            # Should have approximately 20 core configuration fields
            # (allowing some variance for agent-specific mappings)
            assert 15 <= len(config_fields) <= 30

    @pytest.mark.mock_data
    def test_eliminated_redis_variables(self, minimal_env_vars):
        """Test that redundant Redis variables have been eliminated."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # These variables should not exist in simplified configuration
            eliminated_vars = [
                'redis_celery_url',
                'celery_broker_url', 
                'celery_result_backend'
            ]
            
            for var in eliminated_vars:
                assert not hasattr(settings, var)

    @pytest.mark.mock_data
    def test_preserved_functionality(self, minimal_env_vars):
        """Test that all essential functionality is preserved."""
        with patch.dict(os.environ, minimal_env_vars, clear=True):
            settings = Settings()
            
            # Essential functionality should be preserved
            essential_fields = [
                'database_url',
                'redis_url',
                'llm_provider',
                'llm_api_key',
                'secret_key',
                'hitl_default_enabled'
            ]
            
            for field in essential_fields:
                assert hasattr(settings, field)
                assert getattr(settings, field) is not None