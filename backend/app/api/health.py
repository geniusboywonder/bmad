"""Health check API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import structlog

from app.database.connection import get_session
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])
logger = structlog.get_logger(__name__)


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
    
    # Check LLM connectivity (placeholder for future implementation)
    health_status["components"]["llm"] = {
        "status": "not_configured",
        "message": "LLM connectivity not yet implemented"
    }
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status


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
            "audit_system": False
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
        
        # Determine overall health status
        healthy_services = sum(checks.values())
        total_services = len(checks)
        health_percentage = (healthy_services / total_services) * 100
        
        # Response data
        response_data = {
            "status": "healthy" if healthy_services == total_services else "degraded",
            "service": "BotArmy Backend",
            "version": settings.app_version,
            "timestamp": "2024-09-13T12:00:00Z",
            "checks": {
                "database": "pass" if checks["database"] else "fail",
                "redis": "pass" if checks["redis"] else "fail", 
                "celery": "pass" if checks["celery"] else "fail",
                "audit_system": "pass" if checks["audit_system"] else "fail"
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
