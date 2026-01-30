"""Pydantic models for Flow Guardian API.

Request and response models shared by HTTP API and MCP server.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============ CAPTURE ============

class CaptureRequest(BaseModel):
    """Request to capture current coding context."""
    summary: str = Field(..., description="Brief description of current work")
    decisions: Optional[list[str]] = Field(default=[], description="Key decisions made")
    next_steps: Optional[list[str]] = Field(default=[], description="What to do next")
    blockers: Optional[list[str]] = Field(default=[], description="Any blockers")
    tags: Optional[list[str]] = Field(default=[], description="Tags for organization")
    message: Optional[str] = Field(default=None, description="User-provided note")


class CaptureResponse(BaseModel):
    """Response after capturing context."""
    success: bool
    session_id: str
    timestamp: str
    branch: Optional[str] = "unknown"
    files: list[str] = []
    summary: str
    stored_backboard: bool
    stored_local: bool


# ============ RECALL ============

class RecallRequest(BaseModel):
    """Request to recall previous context."""
    query: str = Field(..., description="What to search for")
    tags: Optional[list[str]] = Field(default=[], description="Filter by tags")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


class RecallResponse(BaseModel):
    """Response with recalled context."""
    success: bool
    query: str
    results: list[dict] = []
    source: str = Field(..., description="'vector', 'backboard', or 'local'")


# ============ LEARN ============

class LearnRequest(BaseModel):
    """Request to store a learning."""
    insight: str = Field(..., description="The learning to store")
    tags: Optional[list[str]] = Field(default=[], description="Tags to categorize")
    share_with_team: bool = Field(default=False, description="Share with team")


class LearnResponse(BaseModel):
    """Response after storing a learning."""
    success: bool
    learning_id: str
    insight: str
    tags: list[str] = []
    scope: str = Field(..., description="'personal' or 'team'")
    stored_backboard: bool
    stored_vector: bool = False


# ============ TEAM ============

class TeamQueryRequest(BaseModel):
    """Request to search team knowledge."""
    query: str = Field(..., description="What to search in team knowledge")
    tags: Optional[list[str]] = Field(default=[], description="Filter by tags")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")


class TeamQueryResponse(BaseModel):
    """Response with team knowledge."""
    success: bool
    query: str
    results: str = ""
    team_configured: bool


# ============ STATUS ============

class StatusResponse(BaseModel):
    """Flow Guardian status response."""
    success: bool
    user: Optional[str] = None
    last_save: Optional[str] = None
    branch: Optional[str] = None
    working_on: Optional[str] = None
    sessions_count: int = 0
    personal_learnings: int = 0
    team_learnings: int = 0
    storage: str = "local"
    backboard_connected: bool = False
    team_configured: bool = False


# ============ HEALTH ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    backboard_status: str = "unknown"
    cerebras_status: str = "unknown"
