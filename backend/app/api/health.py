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
