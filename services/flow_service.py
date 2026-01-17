"""Flow Guardian core business logic.

Provides shared service functions for CLI, HTTP API, and MCP server.
Reuses existing modules: capture, memory, restore, backboard_client.
"""
from datetime import datetime
from typing import Optional

import capture
import memory
import restore
import backboard_client
from backboard_client import BackboardError

from services.config import FlowConfig
from services.models import (
    CaptureRequest,
    CaptureResponse,
    RecallRequest,
    RecallResponse,
    LearnRequest,
    LearnResponse,
    TeamQueryRequest,
    TeamQueryResponse,
    StatusResponse,
)


class FlowService:
    """Core Flow Guardian business logic."""

    def __init__(self, config: FlowConfig):
        """Initialize with configuration."""
        self.config = config

    async def capture_context(self, request: CaptureRequest) -> CaptureResponse:
        """
        Capture current coding context.

        Stores to Backboard.io (if available) and local storage.
        Extracted from flow.py save command.
        """
        # Build session using existing capture module
        session = capture.build_session(
            user_message=request.message,
            tags=request.tags or []
        )

        # Override context with request data if provided
        if request.summary:
            session["context"]["summary"] = request.summary
        if request.decisions:
            session["decisions"] = request.decisions
        if request.next_steps:
            session["context"]["next_steps"] = request.next_steps
        if request.blockers:
            # Store blockers in metadata
            session["metadata"]["blockers"] = request.blockers

        # Store locally first (always works)
        session_id = memory.save_session(session)

        # Try to store to Backboard.io
        backboard_stored = False
        if self.config.personal_thread_id:
            try:
                await backboard_client.store_session(
                    self.config.personal_thread_id, session
                )
                backboard_stored = True
            except BackboardError:
                pass

        return CaptureResponse(
            success=True,
            session_id=session_id,
            timestamp=session.get("timestamp", datetime.now().isoformat()),
            branch=session.get("git", {}).get("branch") or "unknown",
            files=session.get("context", {}).get("files", []),
            summary=session.get("context", {}).get("summary", ""),
            stored_backboard=backboard_stored,
            stored_local=True,
        )

    async def recall_context(self, request: RecallRequest) -> RecallResponse:
        """
        Search for relevant context/learnings.

        Uses Backboard.io semantic search when available,
        falls back to local keyword search.
        Extracted from flow.py recall command.
        """
        results = []
        used_backboard = False

        # Try Backboard.io first
        if self.config.personal_thread_id:
            try:
                response = await backboard_client.recall(
                    self.config.personal_thread_id, request.query
                )
                if response:
                    results = [{"type": "recall", "content": response}]
                    used_backboard = True
            except BackboardError:
                pass

        # Fallback to local search
        if not results:
            local_results = memory.search_learnings(
                request.query, request.tags or None
            )
            results = local_results[: request.limit]

        return RecallResponse(
            success=True,
            query=request.query,
            results=results,
            source="backboard" if used_backboard else "local",
        )

    async def store_learning(self, request: LearnRequest) -> LearnResponse:
        """
        Store a learning or insight.

        Stores to team or personal memory based on share_with_team flag.
        Extracted from flow.py learn command.
        """
        # Build learning object
        learning = {
            "text": request.insight,
            "tags": request.tags or [],
            "team": request.share_with_team,
            "author": self.config.user,
        }

        # Store locally first
        learning_id = memory.save_learning(learning)

        # Try to store to Backboard.io
        backboard_stored = False
        thread_id = (
            self.config.team_thread_id
            if request.share_with_team
            else self.config.personal_thread_id
        )

        if thread_id:
            try:
                if request.share_with_team:
                    await backboard_client.store_team_learning(
                        thread_id,
                        request.insight,
                        self.config.user,
                        request.tags or [],
                    )
                else:
                    await backboard_client.store_learning(
                        thread_id,
                        request.insight,
                        request.tags or [],
                        self.config.user,
                    )
                backboard_stored = True
            except BackboardError:
                pass

        return LearnResponse(
            success=True,
            learning_id=learning_id,
            insight=request.insight,
            tags=request.tags or [],
            scope="team" if request.share_with_team else "personal",
            stored_backboard=backboard_stored,
        )

    async def query_team(self, request: TeamQueryRequest) -> TeamQueryResponse:
        """
        Search team's shared knowledge.

        Extracted from flow.py team command.
        """
        if not self.config.team_thread_id:
            return TeamQueryResponse(
                success=False,
                query=request.query,
                results="Team memory not configured.",
                team_configured=False,
            )

        try:
            response = await backboard_client.query_team_memory(
                self.config.team_thread_id, request.query
            )
            return TeamQueryResponse(
                success=True,
                query=request.query,
                results=response or "No team learnings found.",
                team_configured=True,
            )
        except BackboardError as e:
            return TeamQueryResponse(
                success=False,
                query=request.query,
                results=f"Team search unavailable: {e}",
                team_configured=True,
            )

    async def get_status(self) -> StatusResponse:
        """
        Get current Flow Guardian status.

        Extracted from flow.py status command.
        """
        # Get local data
        latest = memory.get_latest_session()
        stats = memory.get_stats()

        # Get current git branch
        current_branch = None
        try:
            current_branch = restore.get_current_branch()
        except Exception:
            pass

        # Calculate time since last save
        last_save = None
        working_on = None
        if latest:
            timestamp = latest.get("timestamp", "")
            if timestamp:
                elapsed = restore.calculate_time_elapsed(timestamp)
                last_save = f"{elapsed} ago"
            working_on = latest.get("context", {}).get("summary", "")

        # Determine storage status
        storage = "backboard+local" if self.config.backboard_available else "local"

        return StatusResponse(
            success=True,
            user=self.config.user,
            last_save=last_save,
            branch=current_branch,
            working_on=working_on,
            sessions_count=stats.get("sessions_count", 0),
            personal_learnings=stats.get("personal_learnings", 0),
            team_learnings=stats.get("team_learnings", 0),
            storage=storage,
            backboard_connected=self.config.backboard_available,
            team_configured=self.config.team_available,
        )
