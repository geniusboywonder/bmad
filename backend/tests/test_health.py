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
            assert data["services_healthy"] == "4/4"
            
            # Verify individual service checks
            checks = data["checks"]
            assert checks["database"] == "pass"
            assert checks["redis"] == "pass"
            assert checks["celery"] == "pass"
            assert checks["audit_system"] == "pass"
    
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
            assert data["health_percentage"] == 75.0  # 3/4 services healthy
            assert data["services_healthy"] == "3/4"
            
            checks = data["checks"]
            assert checks["database"] == "fail"
            assert checks["redis"] == "pass"
            assert checks["celery"] == "pass"
            assert checks["audit_system"] == "pass"
    
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
            assert data["health_percentage"] == 50.0  # 2/4 services healthy (Redis + Celery fail)
            assert data["services_healthy"] == "2/4"
            
            checks = data["checks"]
            assert checks["database"] == "pass"
            assert checks["redis"] == "fail"
            assert checks["celery"] == "fail"  # Celery depends on Redis
            assert checks["audit_system"] == "pass"
    
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
            
            assert data["status"] == "unhealthy"
            assert data["health_percentage"] == 0.0  # All services failing
            assert data["services_healthy"] == "0/4"
            
            checks = data["checks"]
            assert checks["database"] == "fail"
            assert checks["redis"] == "fail"
            assert checks["celery"] == "fail"
            assert checks["audit_system"] == "fail"
    
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
            required_checks = ["database", "redis", "celery", "audit_system"]
            
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
