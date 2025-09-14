"""FastAPI dependencies for database and services."""

from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.services.context_store import ContextStoreService
from app.services.orchestrator import OrchestratorService
from app.services.agent_service import AgentService


def get_context_store_service(db: Session = Depends(get_session)) -> ContextStoreService:
    """Get ContextStoreService instance."""
    return ContextStoreService(db)


def get_orchestrator_service(db: Session = Depends(get_session)) -> OrchestratorService:
    """Get OrchestratorService instance."""
    return OrchestratorService(db)


def get_agent_service(db: Session = Depends(get_session)) -> AgentService:
    """Get AgentService instance."""
    return AgentService(db)


def get_db_session() -> Generator[Session, None, None]:
    """Get database session."""
    yield from get_session()
