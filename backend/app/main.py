"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.settings import settings
from app.api import projects, hitl, health, websocket, agents, artifacts, audit, workflows, adk, hitl_safety  # hitl_request_endpoints removed due to endpoint duplication
from app.api.v1.endpoints import status
from app.database.connection import get_engine, Base
from app.services.startup_service import startup_service

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

    # Perform startup cleanup: flush queues and reset agent statuses
    try:
        cleanup_results = await startup_service.perform_startup_cleanup()
        if cleanup_results["overall_success"]:
            logger.info("✅ Startup cleanup completed successfully")
        else:
            logger.warning("⚠️ Startup cleanup completed with some issues",
                          results=cleanup_results)
    except Exception as e:
        logger.error("❌ Failed to perform startup cleanup",
                    error=str(e),
                    exc_info=True)

    yield
    # Shutdown
    logger.info("BotArmy Backend shutting down")


# Create FastAPI application
app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## 🤖 BotArmy Multi-Agent Orchestration Platform

    **Production-ready backend services for coordinating AI agent teams with human oversight and enterprise controls.**

    ### 🎯 Key Features
    - **🏗️ Project Lifecycle Management** - Complete SDLC orchestration with multi-agent coordination
    - **👤 Human-in-the-Loop (HITL) Controls** - Mandatory approval workflows and safety mechanisms
    - **🚀 Agent Development Kit (ADK)** - Enterprise-grade agent framework with gradual rollout
    - **🛡️ Safety & Compliance** - Budget controls, emergency stops, and comprehensive audit trails
    - **🔄 Workflow Automation** - BMAD Core integration with template-driven processes
    - **📊 Real-time Monitoring** - Live agent status, performance metrics, and system health

    ### 🔗 Quick Start
    1. **Health Check**: GET `/health` - Verify system status
    2. **Create Project**: POST `/api/v1/projects` - Start a new multi-agent project
    3. **Monitor Agents**: GET `/api/v1/agents` - Track agent activity
    4. **HITL Oversight**: GET `/api/v1/hitl` - Manage human approval workflows

    ### 🔒 Safety First
    All agent operations require human approval via HITL safety controls. No agent can execute without explicit permission.
    """,
    summary="Enterprise multi-agent system with HITL safety controls and workflow orchestration",
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
        # 🏗️ CORE PROJECT MANAGEMENT
        {
            "name": "projects",
            "description": "🏗️ **Project Lifecycle** - Create, manage, and orchestrate multi-agent projects through SDLC phases",
        },

        # 🤖 AGENT ECOSYSTEM
        {
            "name": "agents",
            "description": "🤖 **Agent Management** - Monitor agent status, performance metrics, and real-time activity",
        },
        {
            "name": "adk",
            "description": "🚀 **Agent Development Kit (ADK)** - Production-grade agent framework with enterprise controls and gradual rollout",
        },
        {
            "name": "adk-orchestration",
            "description": "🎭 **Multi-Agent Orchestration** - Coordinate collaborative workflows between multiple agents",
        },
        {
            "name": "adk-handoff",
            "description": "🔄 **Agent Handoffs** - Manage seamless context transfer and task transitions between agents",
        },
        {
            "name": "adk-templates",
            "description": "📋 **Workflow Templates** - ADK-compatible templates for structured agent workflows",
        },
        {
            "name": "adk-tools",
            "description": "🛠️ **Agent Tools** - Function registry, OpenAPI integration, and enterprise tool controls",
        },

        # 👤 HUMAN OVERSIGHT & SAFETY
        {
            "name": "hitl",
            "description": "👤 **Human-in-the-Loop (HITL)** - Human oversight, approval workflows, and quality gates",
        },
        {
            "name": "hitl-safety",
            "description": "🛡️ **HITL Safety Controls** - Mandatory agent approval system and runaway prevention",
        },

        # 🔄 WORKFLOW & AUTOMATION
        {
            "name": "workflows",
            "description": "🔄 **Workflow Engine** - BMAD Core template system, execution engine, and SDLC automation",
        },
        {
            "name": "artifacts",
            "description": "📦 **Project Artifacts** - Generate, manage, and download project deliverables and ZIP packages",
        },

        # 📊 MONITORING & OBSERVABILITY
        {
            "name": "health",
            "description": "❤️ **System Health** - Service status, database connectivity, and infrastructure monitoring",
        },
        {
            "name": "audit",
            "description": "📊 **Audit Trail** - Comprehensive event logging, compliance tracking, and system analytics",
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
app.include_router(status.router, prefix=settings.api_v1_prefix)
# app.include_router(hitl_request_endpoints.router)  # Commented out - duplicates hitl.router endpoints




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
