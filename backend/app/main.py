"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.settings import settings
from app.api import projects, hitl, health, websocket, agents, artifacts, audit, workflows, adk, hitl_safety, hitl_request_endpoints
from app.database.connection import get_engine, Base

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("BotArmy Backend starting up",
                version=settings.app_version,
                debug=settings.debug)
    yield
    # Shutdown
    logger.info("BotArmy Backend shutting down")


# Create FastAPI application
app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="BotArmy POC Backend Services - Multi-Agent Orchestration Platform",
    summary="Complete backend API for BotArmy multi-agent system with HITL oversight and workflow orchestration",
    debug=settings.debug,
    contact={
        "name": "BotArmy Development Team",
        "url": "https://github.com/your-org/bmad",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "projects",
            "description": "Project lifecycle management and task orchestration",
        },
        {
            "name": "hitl",
            "description": "Human-in-the-Loop oversight and approval workflows",
        },
        {
            "name": "agents",
            "description": "Real-time agent status monitoring and management",
        },
        {
            "name": "artifacts",
            "description": "Project artifact generation and download management",
        },
        {
            "name": "workflows",
            "description": "BMAD Core template system and workflow orchestration",
        },
        {
            "name": "audit",
            "description": "Comprehensive audit trail and event logging system",
        },
        {
            "name": "health",
            "description": "System health monitoring and service status checks",
        },
        {
            "name": "adk",
            "description": "ADK (Agent Development Kit) agent lifecycle management and rollout configuration",
        },
        {
            "name": "adk-orchestration",
            "description": "Multi-agent workflow orchestration and collaborative analysis",
        },
        {
            "name": "adk-handoff",
            "description": "Agent handoff management and context transfer between agents",
        },
        {
            "name": "adk-templates",
            "description": "ADK workflow templates and agent compatibility management",
        },
        {
            "name": "adk-tools",
            "description": "ADK tool registry, execution, and enterprise controls",
        },
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables (only when database is available)
# Base.metadata.create_all(bind=engine)

# Include API routers
app.include_router(projects.router, prefix=settings.api_v1_prefix)
app.include_router(hitl.router)
app.include_router(health.router)
app.include_router(websocket.router)
app.include_router(agents.router)
app.include_router(artifacts.router)
app.include_router(audit.router, prefix=settings.api_v1_prefix)
app.include_router(workflows.router)
app.include_router(adk.router)
app.include_router(hitl_safety.router)
app.include_router(hitl_request_endpoints.router)




@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error("Unhandled exception", 
                path=request.url.path,
                method=request.method,
                error=str(exc),
                exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=getattr(settings, 'api_host', '0.0.0.0'),
        port=getattr(settings, 'api_port', 8000),
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
