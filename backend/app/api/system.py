"""System administration API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/system", tags=["system"])


class CleanupResponse(BaseModel):
    """Response model for cleanup operations."""
    success: bool
    message: str
    cleared_stores: list[str]


@router.post("/clear-frontend-storage", response_model=CleanupResponse)
async def clear_frontend_storage():
    """
    Signal to clear frontend localStorage and sessionStorage.

    This endpoint returns instructions for the frontend to clear its local storage.
    The frontend should call this endpoint and then clear its storage based on the response.
    """

    stores_to_clear = [
        "hitl-store",
        "log-store",
        "conversation-store",
        "agent-store",
        "notification-store",
        "project-store"
    ]

    return CleanupResponse(
        success=True,
        message="Frontend storage should be cleared",
        cleared_stores=stores_to_clear
    )


@router.get("/cleanup-status")
async def get_cleanup_status():
    """Get the current cleanup status and instructions."""
    return {
        "backend_cleared": True,
        "frontend_storage_keys": [
            "hitl-store",
            "log-store",
            "conversation-store",
            "agent-store"
        ],
        "instructions": {
            "localStorage": "Clear all BotArmy-related keys",
            "sessionStorage": "Clear all session data",
            "zustand_stores": "Reset all persisted Zustand stores"
        }
    }