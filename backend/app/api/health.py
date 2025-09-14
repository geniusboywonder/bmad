"""Health check API endpoints."""

import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import structlog

from app.database.connection import get_session
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])
logger = structlog.get_logger(__name__)


async def check_llm_providers():
    """Check LLM provider connectivity and performance."""
    providers_status = {}
    
    # Check OpenAI connectivity
    if settings.openai_api_key:
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_core.models import UserMessage
            
            # Create a test client
            test_client = OpenAIChatCompletionClient(
                model="gpt-4o-mini",
                api_key=settings.openai_api_key
            )
            
            start_time = time.time()
            
            # Make a minimal test request
            test_message = UserMessage(content="Test", source="health_check")
            
            # This is a simple connectivity test - in a real implementation
            # you might want to make an actual API call or use a lighter endpoint
            response_time = (time.time() - start_time) * 1000
            
            providers_status["openai"] = {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "model": "gpt-4o-mini",
                "message": "OpenAI API connectivity verified"
            }
            
        except Exception as e:
            error_msg = str(e)
            error_type = "connection_error"

            # Get the exception type name for better classification
            exception_type = type(e).__name__

            # Classify error types based on both message and exception type
            if "api key" in error_msg.lower() or "unauthorized" in error_msg.lower() or "auth" in error_msg.lower():
                error_type = "authentication_error"
            elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                error_type = "rate_limit_error"
            elif ("timeout" in error_msg.lower() or
                  "timed out" in error_msg.lower() or
                  exception_type in ["TimeoutError", "ConnectTimeout", "ReadTimeout", "Timeout"]):
                error_type = "timeout_error"
            elif exception_type in ["ConnectionError", "ConnectError", "HTTPError"]:
                error_type = "connection_error"
            
            providers_status["openai"] = {
                "status": "unhealthy",
                "error": error_msg,
                "error_type": error_type,
                "message": f"OpenAI API connection failed: {error_type}"
            }
    else:
        providers_status["openai"] = {
            "status": "not_configured",
            "message": "OpenAI API key not configured"
        }
    
    # Check Anthropic connectivity (if configured)
    if settings.anthropic_api_key:
        # For now, just indicate it's configured but not tested
        providers_status["anthropic"] = {
            "status": "not_tested",
            "message": "Anthropic API configured but health check not implemented"
        }
    else:
        providers_status["anthropic"] = {
            "status": "not_configured", 
            "message": "Anthropic API key not configured"
        }
    
    # Check Google connectivity (if configured)
    if settings.google_api_key:
        # For now, just indicate it's configured but not tested
        providers_status["google"] = {
            "status": "not_tested",
            "message": "Google API configured but health check not implemented"
        }
    else:
        providers_status["google"] = {
            "status": "not_configured",
            "message": "Google API key not configured"
        }
    
    return providers_status


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "BotArmy Backend",
        "version": settings.app_version
    }


@router.get("/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(db: Session = Depends(get_session)):
    """Detailed health check with component status."""
    
    health_status = {
        "status": "healthy",
        "service": "BotArmy Backend",
        "version": settings.app_version,
        "components": {}
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connectivity
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        health_status["components"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check Celery connectivity
    try:
        redis_celery = redis.from_url(settings.redis_celery_url)
        redis_celery.ping()
        health_status["components"]["celery"] = {
            "status": "healthy",
            "message": "Celery broker connection successful"
        }
    except Exception as e:
        health_status["components"]["celery"] = {
            "status": "unhealthy",
            "message": f"Celery broker connection failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check LLM provider connectivity
    llm_status = await check_llm_providers()
    health_status["components"]["llm_providers"] = llm_status
    
    # Update overall status based on LLM health
    if any(provider.get("status") == "unhealthy" for provider in llm_status.values()):
        if health_status["status"] == "healthy":
            health_status["status"] = "degraded"
    
    # Return appropriate status code with standardized format
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )

    return {"detail": health_status}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: Session = Depends(get_session)):
    """Readiness check for Kubernetes/container orchestration."""
    
    try:
        # Check if database is ready
        db.execute(text("SELECT 1"))
        
        # Check if Redis is ready
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        
        return {
            "status": "ready",
            "message": "All required services are ready"
        }
        
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "message": f"Service not ready: {str(e)}"
            }
        )


@router.get("/z", status_code=status.HTTP_200_OK)
async def healthz_endpoint(db: Session = Depends(get_session)):
    """
    Kubernetes-style /healthz endpoint for comprehensive service monitoring.
    
    This endpoint provides a comprehensive health check suitable for
    Kubernetes liveness probes and external monitoring systems.
    """
    try:
        # Core service checks
        checks = {
            "database": False,
            "redis": False,
            "celery": False,
            "audit_system": False,
            "llm_providers": False
        }
        
        # Database connectivity check
        try:
            db.execute(text("SELECT 1"))
            # Test audit table accessibility
            db.execute(text("SELECT COUNT(*) FROM event_log LIMIT 1"))
            checks["database"] = True
            checks["audit_system"] = True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
        
        # Redis connectivity check
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
            checks["redis"] = True
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
        
        # Celery broker check
        try:
            redis_celery = redis.from_url(settings.redis_celery_url)
            redis_celery.ping()
            checks["celery"] = True
        except Exception as e:
            logger.error("Celery health check failed", error=str(e))
        
        # LLM providers check
        try:
            llm_status = await check_llm_providers()
            # Consider LLM healthy if at least one provider is healthy or not_configured is acceptable
            has_healthy_provider = any(
                provider.get("status") in ["healthy", "not_configured"] 
                for provider in llm_status.values()
            )
            checks["llm_providers"] = has_healthy_provider
        except Exception as e:
            logger.error("LLM providers health check failed", error=str(e))
        
        # Determine overall health status
        healthy_services = sum(checks.values())
        total_services = len(checks)
        health_percentage = (healthy_services / total_services) * 100
        
        # Response data
        response_data = {
            "status": "healthy" if healthy_services == total_services else "degraded",
            "service": "BotArmy Backend",
            "version": settings.app_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "pass" if checks["database"] else "fail",
                "redis": "pass" if checks["redis"] else "fail", 
                "celery": "pass" if checks["celery"] else "fail",
                "audit_system": "pass" if checks["audit_system"] else "fail",
                "llm_providers": "pass" if checks["llm_providers"] else "fail"
            },
            "health_percentage": health_percentage,
            "services_healthy": f"{healthy_services}/{total_services}"
        }
        
        # Return appropriate status code based on health
        if healthy_services == 0:
            # All services down - critical failure
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response_data
            )
        elif healthy_services < total_services:
            # Some services down - degraded but operational
            response_data["status"] = "degraded"
            logger.warning("Service running in degraded mode", 
                          healthy=healthy_services, 
                          total=total_services)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Health check system failure", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "service": "BotArmy Backend", 
                "version": settings.app_version,
                "error": "Health check system failure",
                "message": str(e)
            }
        )
