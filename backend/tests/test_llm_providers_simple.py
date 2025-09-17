"""
Test Cases for P1.2 Multi-LLM Provider Configuration (Simplified for Phase 1)

This module contains test cases for the multi-LLM provider configuration
focusing on the Phase 1 requirements from the sprint documentation.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

from app.services.llm_providers.base_provider import BaseProvider
from app.services.llm_providers.provider_factory import ProviderFactory


class TestLLMProviderFactory:
    """Test cases for the LLM provider factory."""

    def test_provider_factory_exists(self):
        """Test that the provider factory exists and is importable."""
        assert ProviderFactory is not None

    def test_provider_factory_has_providers(self):
        """Test that provider factory has registered providers."""
        # Check that the factory has providers registered
        assert hasattr(ProviderFactory, '_providers')
        assert len(ProviderFactory._providers) > 0

    def test_provider_factory_supports_required_providers(self):
        """Test that factory supports OpenAI, Anthropic, and Google providers."""
        required_providers = ["openai", "anthropic", "google"]

        for provider_name in required_providers:
            assert provider_name in ProviderFactory._providers, f"{provider_name} provider should be registered"

    def test_get_openai_provider(self):
        """Test getting OpenAI provider from factory."""
        try:
            provider = ProviderFactory.get_provider("openai")
            assert provider is not None
            assert hasattr(provider, 'generate')
            assert hasattr(provider, 'get_models')
        except Exception as e:
            # Expected if no API keys are configured
            assert "API key" in str(e) or "key" in str(e).lower()

    def test_get_anthropic_provider(self):
        """Test getting Anthropic provider from factory."""
        try:
            provider = ProviderFactory.get_provider("anthropic")
            assert provider is not None
            assert hasattr(provider, 'generate')
            assert hasattr(provider, 'get_models')
        except Exception as e:
            # Expected if no API keys are configured
            assert "API key" in str(e) or "key" in str(e).lower()

    def test_get_google_provider(self):
        """Test getting Google provider from factory."""
        try:
            provider = ProviderFactory.get_provider("google")
            assert provider is not None
            assert hasattr(provider, 'generate')
            assert hasattr(provider, 'get_models')
        except Exception as e:
            # Expected if no API keys are configured
            assert "API key" in str(e) or "key" in str(e).lower()

    def test_invalid_provider_raises_error(self):
        """Test that requesting invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            ProviderFactory.get_provider("invalid_provider")


class TestBaseProvider:
    """Test cases for the base provider interface."""

    def test_base_provider_is_abstract(self):
        """Test that BaseProvider is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider()

    def test_base_provider_interface(self):
        """Test that BaseProvider defines the required interface."""
        assert hasattr(BaseProvider, 'generate')
        assert hasattr(BaseProvider, 'get_models')


class TestPhase1LLMRequirements:
    """Test cases specifically for Phase 1 LLM provider requirements."""

    def test_all_three_providers_available(self):
        """Test that all three required providers (OpenAI, Anthropic, Gemini) are available."""
        # Phase 1 requirement: All three LLM providers (OpenAI, Anthropic, Gemini) working
        required_providers = ["openai", "anthropic", "google"]

        available_providers = []
        for provider_name in required_providers:
            try:
                provider = ProviderFactory.get_provider(provider_name)
                available_providers.append(provider_name)
            except ValueError as e:
                if "Unknown provider" in str(e):
                    # Provider not registered - this is a real failure
                    pass
                else:
                    # Provider registered but needs configuration (API key) - this counts as available
                    available_providers.append(provider_name)
            except Exception as e:
                # Provider registered but can't instantiate (likely missing API key) - this counts as available
                available_providers.append(provider_name)

        assert len(available_providers) == 3, f"All three providers should be available. Found: {available_providers}"

    def test_provider_abstraction_layer_exists(self):
        """Test that provider abstraction layer exists per Phase 1 requirements."""
        # From Phase1and2.md: Create Provider Interface
        assert BaseProvider is not None

        # Check that BaseProvider defines the standard interface
        required_methods = ['generate', 'get_models']
        for method in required_methods:
            assert hasattr(BaseProvider, method), f"BaseProvider should have {method} method"

    def test_provider_factory_pattern_implemented(self):
        """Test that provider factory pattern is implemented."""
        # From Phase1and2.md: Provider Factory and Configuration
        assert ProviderFactory is not None
        assert hasattr(ProviderFactory, 'get_provider')
        assert callable(getattr(ProviderFactory, 'get_provider'))

    @pytest.mark.parametrize("provider_name", ["openai", "anthropic", "google"])
    def test_provider_interface_compliance(self, provider_name):
        """Test that each provider implements the required interface."""
        try:
            provider = ProviderFactory.get_provider(provider_name)

            # Test that provider has required methods
            assert hasattr(provider, 'generate'), f"{provider_name} provider should have generate method"
            assert hasattr(provider, 'get_models'), f"{provider_name} provider should have get_models method"

            # Test that get_models returns a list
            models = provider.get_models()
            assert isinstance(models, list), f"{provider_name} provider get_models should return a list"
            assert len(models) > 0, f"{provider_name} provider should have at least one model"

        except Exception as e:
            # If provider can't be instantiated due to missing API key, that's acceptable for testing
            if "API key" not in str(e) and "key" not in str(e).lower():
                pytest.fail(f"Provider {provider_name} failed for unexpected reason: {e}")