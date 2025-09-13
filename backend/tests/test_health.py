"""Health check endpoint tests."""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_detailed_health_check():
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    # This might return 503 if database/Redis are not available
    assert response.status_code in [200, 503]
    data = response.json()
    assert "components" in data["detail"]
    assert "database" in data["detail"]["components"]
    assert "redis" in data["detail"]["components"]
    assert "celery" in data["detail"]["components"]


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/health/ready")
    # This might return 503 if services are not ready
    assert response.status_code in [200, 503]


class TestHealthzEndpoint:
    """Test Sprint 4 /healthz endpoint for comprehensive monitoring."""
    
    def test_healthz_endpoint_success(self):
        """Test /healthz endpoint with all services healthy."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup successful database connection
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            # Setup successful Redis connection
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Setup successful audit service
            mock_audit_instance = Mock()
            mock_audit_service.return_value = mock_audit_instance
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify comprehensive health response structure
            assert data["status"] == "healthy"
            assert data["service"] == "BotArmy Backend"
            assert "version" in data
            assert "timestamp" in data
            assert "checks" in data
            assert data["health_percentage"] == 100.0
            assert data["services_healthy"] == "5/5"  # Updated for LLM providers
            
            # Verify individual service checks
            checks = data["checks"]
            assert checks["database"] == "pass"
            assert checks["redis"] == "pass"
            assert checks["celery"] == "pass"
            assert checks["audit_system"] == "pass"
            assert checks["llm_providers"] == "pass"
    
    def test_healthz_endpoint_degraded_database_failure(self):
        """Test /healthz endpoint with database failure."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup failing database connection
            mock_get_session.side_effect = Exception("Database connection failed")
            
            # Setup successful Redis connection
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Setup successful audit service
            mock_audit_instance = Mock()
            mock_audit_service.return_value = mock_audit_instance
            
            response = client.get("/health/z")
            
            assert response.status_code == 200  # Still returns 200 but degraded
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["health_percentage"] == 80.0  # 4/5 services healthy
            assert data["services_healthy"] == "4/5"
            
            checks = data["checks"]
            assert checks["database"] == "fail"
            assert checks["redis"] == "pass"
            assert checks["celery"] == "pass"
            assert checks["audit_system"] == "pass"
            assert checks["llm_providers"] == "pass"
    
    def test_healthz_endpoint_degraded_redis_failure(self):
        """Test /healthz endpoint with Redis failure."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup successful database connection
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            # Setup failing Redis connection
            mock_redis.side_effect = Exception("Redis connection failed")
            
            # Setup successful audit service
            mock_audit_instance = Mock()
            mock_audit_service.return_value = mock_audit_instance
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["health_percentage"] == 60.0  # 3/5 services healthy (Redis + Celery fail)
            assert data["services_healthy"] == "3/5"
            
            checks = data["checks"]
            assert checks["database"] == "pass"
            assert checks["redis"] == "fail"
            assert checks["celery"] == "fail"  # Celery depends on Redis
            assert checks["audit_system"] == "pass"
            assert checks["llm_providers"] == "pass"
    
    def test_healthz_endpoint_unhealthy_multiple_failures(self):
        """Test /healthz endpoint with multiple service failures."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup failing database connection
            mock_get_session.side_effect = Exception("Database connection failed")
            
            # Setup failing Redis connection
            mock_redis.side_effect = Exception("Redis connection failed")
            
            # Setup failing audit service
            mock_audit_service.side_effect = Exception("Audit service failed")
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"  # Will be degraded not unhealthy since LLM providers pass
            assert data["health_percentage"] == 20.0  # 1/5 services healthy (only LLM providers pass)
            assert data["services_healthy"] == "1/5"
            
            checks = data["checks"]
            assert checks["database"] == "fail"
            assert checks["redis"] == "fail"
            assert checks["celery"] == "fail"
            assert checks["audit_system"] == "fail"
            assert checks["llm_providers"] == "pass"
    
    def test_healthz_endpoint_performance_requirement(self):
        """Test /healthz endpoint meets sub-200ms performance requirement."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup successful mocks
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            mock_audit_instance = Mock()
            mock_audit_service.return_value = mock_audit_instance
            
            # Measure response time
            start_time = time.time()
            
            response = client.get("/health/z")
            
            response_time = (time.time() - start_time) * 1000
            
            # Verify performance requirement (NFR-01)
            assert response_time < 200, f"Health check took {response_time}ms, exceeds NFR-01"
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_healthz_endpoint_kubernetes_compatibility(self):
        """Test /healthz endpoint format is Kubernetes-compatible."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.AuditService') as mock_audit_service:
            
            # Setup successful mocks
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            mock_audit_instance = Mock()
            mock_audit_service.return_value = mock_audit_instance
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify Kubernetes-compatible format
            required_fields = [
                "status", "service", "version", "timestamp", 
                "checks", "health_percentage", "services_healthy"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Verify status values are Kubernetes-compatible
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            
            # Verify checks format
            checks = data["checks"]
            required_checks = ["database", "redis", "celery", "audit_system", "llm_providers"]
            
            for check in required_checks:
                assert check in checks
                assert checks[check] in ["pass", "fail"]
    
    def test_healthz_concurrent_requests(self):
        """Test /healthz endpoint handles concurrent requests efficiently."""
        import concurrent.futures
        
        def make_health_request():
            with patch('app.api.health.get_session') as mock_get_session, \
                 patch('redis.from_url') as mock_redis, \
                 patch('app.api.health.AuditService') as mock_audit_service:
                
                mock_db = Mock()
                mock_db.execute.return_value = None
                mock_get_session.return_value = mock_db
                
                mock_redis_client = Mock()
                mock_redis_client.ping.return_value = True
                mock_redis.return_value = mock_redis_client
                
                mock_audit_instance = Mock()
                mock_audit_service.return_value = mock_audit_instance
                
                return client.get("/health/z")
        
        # Test concurrent health checks
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_health_request) for _ in range(5)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = (time.time() - start_time) * 1000
        
        # All responses should be successful
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
        
        # Average response time should be reasonable for concurrent requests
        avg_response_time = total_time / len(responses)
        assert avg_response_time < 300, f"Average concurrent response time {avg_response_time}ms too high"


class TestLLMProviderHealthChecks:
    """Test suite for LLM provider health checking functionality."""
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_openai_configured_healthy(self):
        """Test health check with OpenAI configured and healthy."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            mock_settings.anthropic_api_key = None
            mock_settings.google_api_key = None
            
            # Mock successful OpenAI client creation and timing
            with patch('autogen_ext.models.openai.OpenAIChatCompletionClient'), \
                 patch('autogen_core.models.UserMessage'), \
                 patch('app.api.health.time.time', side_effect=[0, 0.245]):  # 245ms response
                
                from app.api.health import check_llm_providers
                result = await check_llm_providers()
                
                assert "openai" in result
                assert result["openai"]["status"] == "healthy"
                assert result["openai"]["response_time_ms"] == 245.0
                assert result["openai"]["model"] == "gpt-4o-mini"
                assert result["openai"]["message"] == "OpenAI API connectivity verified"
                
                assert result["anthropic"]["status"] == "not_configured"
                assert result["google"]["status"] == "not_configured"
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_openai_authentication_error(self):
        """Test health check with OpenAI authentication error."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = "invalid-key"
            mock_settings.anthropic_api_key = None
            mock_settings.google_api_key = None
            
            # Mock authentication error
            with patch('autogen_ext.models.openai.OpenAIChatCompletionClient', 
                      side_effect=Exception("Invalid API key")):
                
                from app.api.health import check_llm_providers
                result = await check_llm_providers()
                
                assert result["openai"]["status"] == "unhealthy"
                assert result["openai"]["error_type"] == "authentication_error"
                assert "Invalid API key" in result["openai"]["error"]
                assert "authentication_error" in result["openai"]["message"]
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_openai_rate_limit_error(self):
        """Test health check with rate limit error."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            
            # Mock rate limit error
            with patch('autogen_ext.models.openai.OpenAIChatCompletionClient',
                      side_effect=Exception("Rate limit exceeded")):
                
                from app.api.health import check_llm_providers
                result = await check_llm_providers()
                
                assert result["openai"]["status"] == "unhealthy"
                assert result["openai"]["error_type"] == "rate_limit_error"
                assert "Rate limit exceeded" in result["openai"]["error"]
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_openai_timeout_error(self):
        """Test health check with timeout error."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = "test-key"
            
            # Mock timeout error
            with patch('autogen_ext.models.openai.OpenAIChatCompletionClient',
                      side_effect=Exception("Request timed out")):
                
                from app.api.health import check_llm_providers
                result = await check_llm_providers()
                
                assert result["openai"]["status"] == "unhealthy"
                assert result["openai"]["error_type"] == "timeout_error"
                assert "Request timed out" in result["openai"]["error"]
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_anthropic_configured(self):
        """Test health check with Anthropic configured but not tested."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = "test-anthropic-key"
            mock_settings.google_api_key = None
            
            from app.api.health import check_llm_providers
            result = await check_llm_providers()
            
            assert result["openai"]["status"] == "not_configured"
            assert result["anthropic"]["status"] == "not_tested"
            assert "configured but health check not implemented" in result["anthropic"]["message"]
            assert result["google"]["status"] == "not_configured"
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_google_configured(self):
        """Test health check with Google configured but not tested."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.google_api_key = "test-google-key"
            
            from app.api.health import check_llm_providers
            result = await check_llm_providers()
            
            assert result["openai"]["status"] == "not_configured"
            assert result["anthropic"]["status"] == "not_configured"
            assert result["google"]["status"] == "not_tested"
            assert "configured but health check not implemented" in result["google"]["message"]
    
    @pytest.mark.asyncio
    async def test_check_llm_providers_all_not_configured(self):
        """Test health check with no providers configured."""
        with patch('app.api.health.settings') as mock_settings:
            mock_settings.openai_api_key = None
            mock_settings.anthropic_api_key = None
            mock_settings.google_api_key = None
            
            from app.api.health import check_llm_providers
            result = await check_llm_providers()
            
            assert result["openai"]["status"] == "not_configured"
            assert result["anthropic"]["status"] == "not_configured"
            assert result["google"]["status"] == "not_configured"


class TestHealthEndpointLLMIntegration:
    """Test suite for health endpoint integration with LLM providers."""
    
    def test_detailed_health_check_includes_llm_providers(self):
        """Test that detailed health check includes LLM provider status."""
        with patch('app.api.health.check_llm_providers') as mock_check_llm, \
             patch('app.database.connection.get_session'), \
             patch('redis.from_url'):
            
            # Mock successful LLM provider status
            mock_check_llm.return_value = {
                "openai": {"status": "healthy", "response_time_ms": 250},
                "anthropic": {"status": "not_configured"},
                "google": {"status": "not_configured"}
            }
            
            response = client.get("/health/detailed")
            
            # May return 503 due to database/redis issues in test env, but should include LLM data
            data = response.json()
            
            assert "components" in data["detail"]
            assert "llm_providers" in data["detail"]["components"]
            assert data["detail"]["components"]["llm_providers"]["openai"]["status"] == "healthy"
    
    def test_detailed_health_check_degraded_with_unhealthy_llm(self):
        """Test that health check shows degraded status with unhealthy LLM."""
        with patch('app.api.health.check_llm_providers') as mock_check_llm, \
             patch('app.database.connection.get_session'), \
             patch('redis.from_url'):
            
            # Mock unhealthy LLM provider
            mock_check_llm.return_value = {
                "openai": {"status": "unhealthy", "error": "Connection failed"},
                "anthropic": {"status": "not_configured"},
                "google": {"status": "not_configured"}
            }
            
            response = client.get("/health/detailed")
            data = response.json()
            
            # Health should be degraded due to unhealthy LLM
            assert data["detail"]["status"] == "degraded"
    
    def test_healthz_endpoint_includes_llm_providers_healthy(self):
        """Test that /healthz endpoint includes LLM provider checks when healthy."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.check_llm_providers') as mock_check_llm:
            
            # Setup successful database and redis
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Mock healthy LLM providers
            mock_check_llm.return_value = {
                "openai": {"status": "healthy"},
                "anthropic": {"status": "not_configured"},
                "google": {"status": "not_configured"}
            }
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "checks" in data
            assert "llm_providers" in data["checks"]
            assert data["checks"]["llm_providers"] == "pass"
    
    def test_healthz_endpoint_fails_llm_providers_unhealthy(self):
        """Test that /healthz shows failed LLM providers when all unhealthy."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.check_llm_providers') as mock_check_llm:
            
            # Setup successful database and redis
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            # Mock all providers unhealthy
            mock_check_llm.return_value = {
                "openai": {"status": "unhealthy"},
                "anthropic": {"status": "unhealthy"},
                "google": {"status": "unhealthy"}
            }
            
            response = client.get("/health/z")
            
            assert response.status_code == 200  # Still returns 200 but degraded
            data = response.json()
            
            assert data["checks"]["llm_providers"] == "fail"
            assert data["status"] == "degraded"  # Not fully healthy
    
    def test_healthz_endpoint_llm_exception_handling(self):
        """Test health check handles LLM provider check exceptions gracefully."""
        with patch('app.api.health.get_session') as mock_get_session, \
             patch('redis.from_url') as mock_redis, \
             patch('app.api.health.check_llm_providers', side_effect=Exception("LLM check failed")):
            
            # Setup successful database and redis
            mock_db = Mock()
            mock_db.execute.return_value = None
            mock_get_session.return_value = mock_db
            
            mock_redis_client = Mock()
            mock_redis_client.ping.return_value = True
            mock_redis.return_value = mock_redis_client
            
            response = client.get("/health/z")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should handle exception gracefully
            assert "checks" in data
            assert data["checks"]["llm_providers"] == "fail"
            assert data["status"] == "degraded"  # Not fully healthy due to LLM check failure
