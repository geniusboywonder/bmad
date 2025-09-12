"""HITL (Human-in-the-Loop) request/response schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from app.models.hitl import HitlAction


class HitlResponseRequest(BaseModel):
    """Schema for HITL response requests."""
    
    action: HitlAction = Field(description="Action to take (approve, reject, amend)")
    response_content: Optional[str] = Field(default=None, description="Optional response content")
    amended_data: Optional[Dict[str, Any]] = Field(default=None, description="Amended data if action is amend")
    comment: Optional[str] = Field(default=None, description="Additional comment")
    user_id: Optional[str] = Field(default=None, description="User providing the response")


class HitlCreateRequest(BaseModel):
    """Schema for creating HITL requests."""
    
    project_id: UUID = Field(description="Project ID this request belongs to")
    task_id: UUID = Field(description="Task ID that triggered this request") 
    question: str = Field(description="Question or request for the user")
    options: Optional[list[str]] = Field(default=None, description="Available response options")


class HitlStatusUpdate(BaseModel):
    """Schema for updating HITL request status."""
    
    status: str = Field(description="New status")
    user_response: Optional[str] = Field(default=None, description="User response")
    amended_content: Optional[Dict[str, Any]] = Field(default=None, description="Amended content")