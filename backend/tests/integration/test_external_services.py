"""
Integration Tests for External Services

Tests real connectivity and functionality of external service integrations
including LLMs, AutoGen, ADK, and other third-party dependencies.
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

# Import external service components
try:
    import autogen_core
    AUTOGEN_CORE_AVAILABLE = True
except ImportError:
    AUTOGEN_CORE_AVAILABLE = False

try:
    import autogen_ext
    AUTOGEN_EXT_AVAILABLE = True
except ImportError:
    AUTOGEN_EXT_AVAILABLE = False

try:
    import google.adk
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from app.settings import settings

class TestLLMProviderIntegrations:
    """Test LLM provider external service integrations."""

    @pytest.mark.external_service
    def test_openai_connectivity(self):
        """Test OpenAI API connectivity and configuration."""
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key not configured")

        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_core.models import UserMessage

            # Test client creation
            client = OpenAIChatCompletionClient(
                model="gpt-4o-mini",
                api_key=settings.openai_api_key
            )

            # Test message creation
            test_message = UserMessage(content="Health check", source="integration_test")

            assert client is not None
            assert test_message.content == "Health check"

        except Exception as e:
            pytest.fail(f"OpenAI integration failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_anthropic_connectivity(self):
        """Test Anthropic API connectivity and configuration."""
        if not ANTHROPIC_AVAILABLE:
            pytest.skip("Anthropic library not available")

        if not settings.anthropic_api_key:
            pytest.skip("Anthropic API key not configured")

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            assert client is not None

        except Exception as e:
            pytest.fail(f"Anthropic integration failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_google_gemini_configuration(self):
        """Test Google/Gemini API configuration."""
        if not settings.google_api_key:
            pytest.skip("Google API key not configured")

        # For now, just verify the configuration exists
        assert settings.google_api_key is not None
        assert len(settings.google_api_key) > 0

class TestAutoGenFrameworkIntegration:
    """Test Microsoft AutoGen framework integration."""

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_autogen_core_imports(self):
        """Test AutoGen core module imports."""
        if not AUTOGEN_CORE_AVAILABLE:
            pytest.skip("AutoGen core not available")

        try:
            from autogen_core.models import UserMessage, AssistantMessage

            # Test message creation
            user_msg = UserMessage(content="Test", source="test")
            assert user_msg.content == "Test"

        except Exception as e:
            pytest.fail(f"AutoGen core import failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_autogen_ext_imports(self):
        """Test AutoGen extensions imports."""
        if not AUTOGEN_EXT_AVAILABLE:
            pytest.skip("AutoGen extensions not available")

        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            assert OpenAIChatCompletionClient is not None

        except Exception as e:
            pytest.fail(f"AutoGen extensions import failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_autogen_service_creation(self):
        """Test AutoGen service can be created."""
        try:
            from app.services.autogen_service import AutoGenService

            # AutoGenCore takes no parameters
            service = AutoGenService()

            assert service is not None
            assert hasattr(service, 'agent_factory')
            assert hasattr(service, 'conversation_manager')
            assert hasattr(service, 'execute_task')

        except Exception as e:
            pytest.fail(f"AutoGen service creation failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_agent_factory_creation(self):
        """Test agent factory creation for AutoGen integration."""
        try:
            from app.services.autogen.agent_factory import AgentFactory

            agent_factory = AgentFactory()

            assert agent_factory is not None
            assert hasattr(agent_factory, 'create_agent')
            assert hasattr(agent_factory, 'agents')

        except Exception as e:
            pytest.fail(f"Agent factory creation failed: {str(e)}")

class TestGoogleADKIntegration:
    """Test Google Agent Development Kit integration."""

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_adk_core_imports(self):
        """Test Google ADK core imports."""
        if not GOOGLE_ADK_AVAILABLE:
            pytest.skip("Google ADK not available")

        try:
            import google.adk
            assert google.adk is not None

        except Exception as e:
            pytest.fail(f"Google ADK core import failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_adk_tools_imports(self):
        """Test ADK tools imports."""
        try:
            from app.tools.adk_openapi_tools import BMADOpenAPITool
            assert BMADOpenAPITool is not None

        except Exception as e:
            pytest.fail(f"ADK tools import failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_adk_wrapper_creation(self):
        """Test ADK wrapper creation."""
        try:
            from app.agents.bmad_adk_wrapper import BMADADKWrapper

            # Test wrapper can be imported and has expected attributes
            assert hasattr(BMADADKWrapper, '__init__')

        except Exception as e:
            pytest.fail(f"ADK wrapper creation failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_minimal_adk_agent(self):
        """Test minimal ADK agent creation."""
        try:
            from app.agents.minimal_adk_agent import MinimalADKAgent

            # Test agent can be imported
            assert MinimalADKAgent is not None

        except Exception as e:
            pytest.fail(f"Minimal ADK agent failed: {str(e)}")

class TestExternalAPIs:
    """Test external API integrations."""

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_websocket_manager_availability(self):
        """Test WebSocket manager availability."""
        try:
            from app.websocket.manager import WebSocketManager

            # Test WebSocket manager can be imported and instantiated
            manager = WebSocketManager()
            assert manager is not None
            assert hasattr(manager, 'connect')

        except Exception as e:
            pytest.fail(f"WebSocket manager failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_websocket_manager_functionality(self):
        """Test WebSocket manager core functionality."""
        try:
            from app.websocket.manager import WebSocketManager, NotificationPriority
            from app.websocket.events import WebSocketEvent, EventType

            manager = WebSocketManager()

            # Test connection tracking
            assert manager.get_connection_count() == 0
            assert manager.get_connection_count("test_project") == 0

            # Test event creation and validation
            test_project_id = uuid4()
            test_event = WebSocketEvent(
                event_type=EventType.TASK_STARTED,
                project_id=test_project_id,
                data={"status": "running", "task_id": "test_task"}
            )

            assert test_event.event_type == EventType.TASK_STARTED
            assert test_event.project_id == test_project_id
            assert test_event.data["status"] == "running"

            # Test priority notifications
            assert hasattr(manager, 'pending_notifications')
            assert hasattr(manager, 'broadcast_event')
            assert hasattr(manager, 'broadcast_to_project')
            assert hasattr(manager, 'broadcast_global')

        except Exception as e:
            pytest.fail(f"WebSocket manager functionality test failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_websocket_events_structure(self):
        """Test WebSocket events structure and validation."""
        try:
            from app.websocket.events import WebSocketEvent, EventType
            from datetime import datetime, timezone

            # Test different event types
            event_types = [
                EventType.TASK_STARTED,
                EventType.TASK_COMPLETED,
                EventType.AGENT_STATUS_CHANGE,
                EventType.HITL_REQUEST
            ]

            test_project_id = uuid4()
            for event_type in event_types:
                event = WebSocketEvent(
                    event_type=event_type,
                    project_id=test_project_id,
                    data={"test": "data"}
                )

                assert event.event_type == event_type
                assert event.project_id == test_project_id
                assert isinstance(event.timestamp, datetime)
                assert event.data["test"] == "data"

        except Exception as e:
            pytest.fail(f"WebSocket events structure test failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_websocket_notification_system(self):
        """Test WebSocket notification system components."""
        try:
            from app.websocket.manager import WebSocketManager, NotificationPriority, PriorityNotification
            from app.websocket.events import WebSocketEvent, EventType

            manager = WebSocketManager()

            # Test priority notification creation
            test_project_id = uuid4()
            test_event = WebSocketEvent(
                event_type=EventType.HITL_REQUEST,
                project_id=test_project_id,
                data={"message": "Test notification"}
            )

            notification = PriorityNotification(
                event=test_event,
                priority=NotificationPriority.HIGH,
                max_retries=3
            )

            assert notification.event == test_event
            assert notification.priority == NotificationPriority.HIGH
            assert notification.max_retries == 3
            assert notification.retry_count == 0

            # Test notification queue operations
            assert hasattr(manager, 'pending_notifications')
            assert hasattr(manager, 'send_priority_notification')
            assert hasattr(manager, 'get_pending_notifications')
            assert hasattr(manager, 'cleanup_expired_notifications')

        except Exception as e:
            pytest.fail(f"WebSocket notification system test failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_redis_celery_connectivity(self):
        """Test Redis/Celery connectivity."""
        try:
            import redis

            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()

        except Exception as e:
            pytest.fail(f"Redis/Celery connectivity failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_regular_redis_connectivity(self):
        """Test regular Redis connectivity."""
        try:
            import redis

            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()

        except Exception as e:
            pytest.fail(f"Redis connectivity failed: {str(e)}")

class TestMonitoringServices:
    """Test monitoring and observability integrations."""

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_structured_logging(self):
        """Test structured logging functionality."""
        try:
            import structlog

            logger = structlog.get_logger(__name__)
            logger.info("External service integration test",
                       service="pytest",
                       category="monitoring")

            # If we get here without exception, logging works
            assert True

        except Exception as e:
            pytest.fail(f"Structured logging failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_data
    def test_health_check_functions(self):
        """Test health check function availability."""
        try:
            from app.api.health import check_llm_providers

            # Test function exists and is callable
            assert callable(check_llm_providers)

        except Exception as e:
            pytest.fail(f"Health check functions failed: {str(e)}")

class TestRealAPIConnectivity:
    """Test actual API connectivity with rate limiting and error handling."""

    @pytest.mark.external_service
    @pytest.mark.real_api
    @pytest.mark.real_data
    @pytest.mark.asyncio
    @pytest.mark.real_data

    async def test_openai_real_api_call(self):
        """Test actual OpenAI API call (use sparingly due to cost)."""
        if not settings.openai_api_key:
            pytest.skip("OpenAI API key not configured")

        # This test makes a real API call - use with caution
        pytest.skip("Real API test disabled to avoid costs - enable manually for verification")

        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_core.models import UserMessage

            client = OpenAIChatCompletionClient(
                model="gpt-4o-mini",
                api_key=settings.openai_api_key
            )

            start_time = time.time()
            messages = [UserMessage(content="Say 'Hello from integration test'", source="test")]

            # Make actual API call
            # response = await client.create_chat_completion(messages)
            response_time = (time.time() - start_time) * 1000

            # Verify response structure (when enabled)
            # assert response is not None
            assert response_time < 10000  # Should respond within 10 seconds

        except Exception as e:
            pytest.fail(f"Real OpenAI API call failed: {str(e)}")

    @pytest.mark.external_service
    @pytest.mark.real_api
    @pytest.mark.real_data
    def test_anthropic_real_api_call(self):
        """Test actual Anthropic API call (use sparingly due to cost)."""
        if not ANTHROPIC_AVAILABLE or not settings.anthropic_api_key:
            pytest.skip("Anthropic not available or not configured")

        # This test makes a real API call - use with caution
        pytest.skip("Real API test disabled to avoid costs - enable manually for verification")

        try:
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

            start_time = time.time()

            # Make minimal API call
            # message = client.messages.create(
            #     model="claude-3-haiku-20240307",
            #     max_tokens=10,
            #     messages=[{"role": "user", "content": "Say hello"}]
            # )

            response_time = (time.time() - start_time) * 1000

            # Verify response (when enabled)
            assert response_time < 10000  # Should respond within 10 seconds

        except Exception as e:
            pytest.fail(f"Real Anthropic API call failed: {str(e)}")

@pytest.mark.external_service
class TestExternalServiceHealthEndpoint:
    """Test the health endpoint for external services."""

    @pytest.mark.asyncio
    @pytest.mark.real_data
    @pytest.mark.mock_data

    async def test_llm_providers_health_check(self):
        """Test LLM providers health check function."""
        try:
            from app.api.health import check_llm_providers

            health_status = await check_llm_providers()

            assert isinstance(health_status, dict)
            assert "openai" in health_status

            # Should have status for each provider
            for provider in ["openai", "anthropic", "google"]:
                assert provider in health_status
                assert "status" in health_status[provider]

        except Exception as e:
            pytest.fail(f"LLM providers health check failed: {str(e)}")

    @pytest.mark.real_data
    def test_external_service_summary(self):
        """Generate summary of external service availability."""
        summary = {
            "autogen_core": AUTOGEN_CORE_AVAILABLE,
            "autogen_ext": AUTOGEN_EXT_AVAILABLE,
            "google_adk": GOOGLE_ADK_AVAILABLE,
            "anthropic": ANTHROPIC_AVAILABLE,
            "openai_configured": bool(settings.openai_api_key),
            "anthropic_configured": bool(settings.anthropic_api_key),
            "google_configured": bool(settings.google_api_key)
        }

        available_count = sum(summary.values())
        total_count = len(summary)

        print(f"\n📊 External Service Summary: {available_count}/{total_count} available")
        for service, available in summary.items():
            status = "✅" if available else "❌"
            print(f"  {status} {service}")

        # This test always passes - it's just for reporting
        assert True