#!/usr/bin/env python3
"""Flow Guardian Unified Server

Single entry point that can run:
1. Daemon mode - Background watcher for auto-capture
2. HTTP API mode - FastAPI server for external access
3. MCP mode - Model Context Protocol for Claude Code
4. Combined mode - All of the above

Usage:
    python server.py daemon          # Background auto-capture
    python server.py api             # HTTP API on port 8090
    python server.py mcp             # MCP server (stdio)
    python server.py all             # Daemon + HTTP API together
    python server.py --help          # Show help
"""
import argparse
import asyncio
import json
import os
import re
import signal
import sys
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ============ CONFIGURATION ============

STATE_DIR = Path.home() / ".flow-guardian"
DAEMON_DIR = STATE_DIR / "daemon"
PID_FILE = DAEMON_DIR / "server.pid"
LOG_FILE = DAEMON_DIR / "server.log"
STATE_FILE = DAEMON_DIR / "state.json"

# Daemon settings
POLL_INTERVAL = 10
MIN_MESSAGES_BATCH = 5
MAX_EXTRACTION_INTERVAL = 300
MAX_CHUNK_CHARS = 30000


# ============ LOGGING ============

def log(message: str, level: str = "INFO"):
    """Write to log file and stdout if interactive."""
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    if sys.stdout.isatty():
        print(line, end="")


# ============ SHARED SERVICES ============

class FlowService:
    """Core business logic shared by all modes."""

    def __init__(self):
        self._backboard = None
        self._cerebras = None
        self._memory = None

    @property
    def backboard(self):
        if self._backboard is None:
            import backboard_client
            self._backboard = backboard_client
        return self._backboard

    @property
    def cerebras(self):
        if self._cerebras is None:
            import cerebras_client
            self._cerebras = cerebras_client
        return self._cerebras

    @property
    def memory(self):
        if self._memory is None:
            import memory
            self._memory = memory
        return self._memory

    def backboard_available(self) -> bool:
        return bool(os.environ.get("BACKBOARD_API_KEY"))

    def team_available(self) -> bool:
        return bool(os.environ.get("BACKBOARD_TEAM_THREAD_ID"))

    # ---- Capture ----
    async def capture_context(
        self,
        summary: str,
        decisions: list[str] = None,
        next_steps: list[str] = None,
        blockers: list[str] = None,
    ) -> dict:
        """Save current coding context."""
        import capture

        # Get git info
        git_info = capture.capture_git_state()

        # Build context
        context = {
            "summary": summary,
            "decisions": decisions or [],
            "next_steps": next_steps or [],
            "blockers": blockers or [],
            "timestamp": datetime.now().isoformat(),
            "git": git_info,
        }

        # Save locally as session
        self.memory.save_session({
            "context": context,
            "git": git_info,
            "summary": summary,
        })

        # Save to Backboard if available
        if self.backboard_available():
            thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
            if thread_id:
                content = self._format_context_for_storage(context)
                await self.backboard.store_message(thread_id, content, {
                    "type": "context_capture",
                    "cwd": os.getcwd(),
                })

        return {
            "saved": True,
            "local": True,
            "cloud": self.backboard_available(),
            "branch": git_info.get("branch") or "unknown",
        }

    def _format_context_for_storage(self, context: dict) -> str:
        lines = [f"**Context Capture**: {context['summary']}"]
        if context.get("decisions"):
            lines.append("\n**Decisions:**")
            for d in context["decisions"]:
                lines.append(f"- {d}")
        if context.get("next_steps"):
            lines.append("\n**Next Steps:**")
            for s in context["next_steps"]:
                lines.append(f"- {s}")
        if context.get("blockers"):
            lines.append("\n**Blockers:**")
            for b in context["blockers"]:
                lines.append(f"- {b}")
        return "\n".join(lines)

    # ---- Recall ----
    def _extract_search_terms(self, query: str) -> list[str]:
        """Use Cerebras to extract search terms from user query."""
        try:
            response = self.cerebras.complete(
                prompt=f"""Extract 3-5 key search terms from this question. Return only a JSON array of strings.
Question: {query}

Example output: ["auth", "jwt", "token", "refresh"]""",
                system="Extract search keywords. Return only a JSON array, no explanation.",
                json_mode=True,
                max_tokens=100
            )
            import json
            terms = json.loads(response)
            if isinstance(terms, list):
                return [str(t).lower() for t in terms[:5]]
        except Exception as e:
            log(f"Search term extraction failed: {e}", "DEBUG")
        # Fallback: split query into words
        return [w.lower() for w in query.split() if len(w) > 2][:5]

    async def recall_context(self, query: str, local_only: bool = False) -> dict:
        """Search memory for relevant context.

        Args:
            query: The search query
            local_only: If True, skip Backboard (fast path)
        """
        results = []

        # Fast keyword extraction - no API call needed
        # Filter out stop words and clean punctuation
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why',
                      'when', 'where', 'who', 'which', 'this', 'that', 'these', 'those',
                      'can', 'could', 'would', 'should', 'will', 'did', 'does', 'do',
                      'have', 'has', 'had', 'been', 'being', 'for', 'with', 'about',
                      'into', 'from', 'our', 'your', 'their', 'its', 'and', 'but', 'or'}

        # Clean and filter words
        words = re.findall(r'\b[a-zA-Z0-9]+\b', query.lower())
        search_terms = [w for w in words if len(w) > 2 and w not in stop_words][:8]
        log(f"Search terms for '{query}': {search_terms}", "INFO")

        # ALWAYS include recent learnings first (active knowledge cache)
        recent_learnings = self.memory.get_all_learnings()[:10]
        seen_learnings = set()
        for learning in recent_learnings:
            learning_id = learning.get("id") or learning.get("timestamp", "")
            insight = learning.get("insight") or learning.get("text", "")
            if learning_id and insight:
                seen_learnings.add(learning_id)
                # Check if this learning matches the query for scoring
                insight_lower = insight.lower()
                match_score = 1  # Base score for recent
                for term in search_terms:
                    if term in insight_lower:
                        match_score += 3  # Boost for matching
                results.append({
                    "content": insight,
                    "source": "learning",
                    "timestamp": learning.get("timestamp"),
                    "tags": learning.get("tags", []),
                    "score": match_score,
                })

        # Search local sessions by keyword
        all_sessions = self.memory.list_sessions(limit=50)
        for session in all_sessions:
            summary = session.get("summary", "")
            branch = session.get("branch", "")
            context = session.get("context", {})
            summary_lower = summary.lower()
            branch_lower = branch.lower()

            # Check if any search term matches summary, branch, or context
            match_score = 0
            for term in search_terms:
                if term in summary_lower:
                    match_score += 3
                if term in branch_lower:
                    match_score += 2

                # Check in decisions, blockers, next_steps
                for key in ["decisions", "blockers", "next_steps"]:
                    items = context.get(key, [])
                    for item in items:
                        if term in item.lower():
                            match_score += 2

            if match_score > 0:
                content_parts = [f"**Session:** {summary}"]
                content_parts.append(f"Branch: {branch}")
                if context.get("decisions"):
                    content_parts.append(f"Decisions: {', '.join(context['decisions'][:3])}")
                if context.get("blockers"):
                    content_parts.append(f"Blockers: {', '.join(context['blockers'][:3])}")
                if context.get("next_steps"):
                    content_parts.append(f"Next steps: {', '.join(context['next_steps'][:3])}")

                results.append({
                    "content": "\n".join(content_parts),
                    "source": "session",
                    "timestamp": session.get("timestamp"),
                    "score": match_score,
                })

        # Search ALL learnings (not just recent) with each search term
        for term in search_terms:
            local_results = self.memory.search_learnings(term)
            for learning in local_results:
                learning_id = learning.get("id") or learning.get("timestamp", "")
                if learning_id not in seen_learnings:
                    seen_learnings.add(learning_id)
                    results.append({
                        "content": learning.get("insight") or learning.get("text", ""),
                        "source": "learning",
                        "timestamp": learning.get("timestamp"),
                        "tags": learning.get("tags", []),
                        "score": 4,  # High score - actually matched query!
                    })

        # Only search Backboard if local results are insufficient
        # This saves an API call for most queries
        local_has_good_results = any(r.get("score", 0) >= 3 for r in results)

        if not local_only and not local_has_good_results and self.backboard_available():
            thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
            if thread_id:
                try:
                    log("Local context insufficient, querying Backboard...", "INFO")
                    enhanced_query = " ".join(search_terms) if search_terms else query
                    cloud_response = await self.backboard.recall(thread_id, enhanced_query)
                    if cloud_response and len(cloud_response) > 20:
                        results.append({
                            "content": cloud_response,
                            "source": "backboard",
                            "timestamp": datetime.now().isoformat(),
                            "score": 2,  # Lower than good local matches
                        })
                except Exception as e:
                    log(f"Backboard search error: {e}", "WARN")

        # Sort by score (higher first) and limit
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        results = results[:10]  # Limit to top 10 results

        # If no results, include recent sessions as fallback context
        if not results:
            recent_sessions = self.memory.list_sessions(limit=5)
            for session in recent_sessions:
                summary = session.get("summary", "")
                branch = session.get("branch", "")
                context = session.get("context", {})

                content_parts = [f"**Recent Session:** {summary}"]
                content_parts.append(f"Branch: {branch}")
                if context.get("decisions"):
                    content_parts.append(f"Decisions: {', '.join(context['decisions'][:3])}")
                if context.get("blockers"):
                    content_parts.append(f"Blockers: {', '.join(context['blockers'][:3])}")

                results.append({
                    "content": "\n".join(content_parts),
                    "source": "recent-session",
                    "timestamp": session.get("timestamp"),
                })

        return {
            "query": query,
            "results": results,
            "sources": {
                "local": True,
                "cloud": self.backboard_available(),
            }
        }

    # ---- Learn ----
    async def store_learning(
        self,
        insight: str,
        tags: list[str] = None,
        share_with_team: bool = False,
    ) -> dict:
        """Store a learning or insight."""
        learning = {
            "insight": insight,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
            "shared": share_with_team,
        }

        # Save locally
        self.memory.save_learning(learning)

        # Save to Backboard
        stored_personal = False
        stored_team = False

        if self.backboard_available():
            thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
            if thread_id:
                tag_str = " ".join(f"#{t}" for t in (tags or []))
                content = f"**Learning**: {insight}\n{tag_str}"
                await self.backboard.store_message(thread_id, content, {
                    "type": "learning",
                    "tags": tags or [],
                })
                stored_personal = True

            if share_with_team and self.team_available():
                team_thread = os.environ.get("BACKBOARD_TEAM_THREAD_ID")
                if team_thread:
                    await self.backboard.store_message(team_thread, content, {
                        "type": "team_learning",
                        "tags": tags or [],
                    })
                    stored_team = True

        return {
            "stored": True,
            "personal": stored_personal,
            "team": stored_team,
        }

    # ---- Team ----
    async def query_team(self, query: str) -> dict:
        """Search team knowledge base."""
        if not self.team_available():
            return {
                "available": False,
                "results": [],
                "message": "Team knowledge not configured",
            }

        team_thread = os.environ.get("BACKBOARD_TEAM_THREAD_ID")
        try:
            response = await self.backboard.query_team_memory(team_thread, query)
            return {
                "available": True,
                "query": query,
                "results": [{"content": response, "source": "team"}] if response else [],
            }
        except Exception as e:
            return {
                "available": True,
                "error": str(e),
                "results": [],
            }

    # ---- Status ----
    async def get_status(self) -> dict:
        """Get Flow Guardian status."""
        # Check last session
        last_session = self.memory.get_latest_session()

        return {
            "backboard_connected": self.backboard_available(),
            "team_available": self.team_available(),
            "last_capture": last_session.get("timestamp") if last_session else None,
            "last_summary": last_session.get("summary") or (
                last_session.get("context", {}).get("summary") if last_session else None
            ),
        }


# Global service instance
_service: Optional[FlowService] = None

def get_service() -> FlowService:
    global _service
    if _service is None:
        _service = FlowService()
    return _service


# ============ DAEMON MODE ============

class DaemonMode:
    """Background watcher for automatic context capture."""

    def __init__(self, service: FlowService):
        self.service = service
        self.state = self._load_state()
        self.running = False

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {"sessions": {}, "extractions_count": 0}

    def _save_state(self):
        DAEMON_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2, default=str))

    async def _maybe_generate_docs(self, new_insights_count: int):
        """Check if we should generate documentation based on activity.

        Triggers report generation when:
        - 5+ new insights captured in a session (significant session)
        - 20+ total extractions since last report
        - 6+ hours since last report
        """
        try:
            import report_generator

            last_report = self.state.get("last_report_time")
            extractions_since_report = self.state.get("extractions_since_report", 0) + 1
            self.state["extractions_since_report"] = extractions_since_report

            should_generate = False
            reason = ""

            # Significant session (5+ insights at once)
            if new_insights_count >= 5:
                should_generate = True
                reason = f"Significant session ({new_insights_count} insights)"

            # Activity threshold
            elif extractions_since_report >= 20:
                should_generate = True
                reason = f"Activity threshold ({extractions_since_report} extractions)"

            # Time-based (6 hours)
            elif last_report:
                try:
                    last_dt = datetime.fromisoformat(last_report)
                    hours_since = (datetime.now() - last_dt).total_seconds() / 3600
                    if hours_since >= 6:
                        should_generate = True
                        reason = f"Scheduled ({hours_since:.1f}h since last report)"
                except (ValueError, TypeError):
                    pass
            else:
                # No previous report - generate first one after some activity
                if extractions_since_report >= 3:
                    should_generate = True
                    reason = "Initial report"

            if should_generate:
                log(f"[AutoDocs] Generating documentation... Reason: {reason}")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                reports_dir = STATE_DIR / "reports"
                reports_dir.mkdir(parents=True, exist_ok=True)

                # Import Linear client for document storage
                try:
                    import linear_client
                    linear_available = bool(os.environ.get("LINEAR_API_KEY"))
                except ImportError:
                    linear_available = False

                # Generate FAQ from learnings
                try:
                    faq = await report_generator.generate_faq_from_solved(days=30)
                    faq_path = reports_dir / f"auto_faq_{timestamp}.md"
                    faq_path.write_text(faq)
                    log(f"[AutoDocs] Generated FAQ: {faq_path.name}")

                    # Store in Linear Docs
                    if linear_available:
                        doc = await linear_client.create_or_update_document(
                            title="Flow Guardian FAQ",
                            content=faq
                        )
                        if doc:
                            log(f"[AutoDocs] Stored FAQ in Linear: {doc.get('url', doc.get('id'))}")
                except Exception as e:
                    log(f"[AutoDocs] FAQ generation failed: {e}", "WARN")

                # Generate weekly summary
                try:
                    summary = await report_generator.generate_weekly_summary()
                    summary_path = reports_dir / f"auto_weekly_{timestamp}.md"
                    summary_path.write_text(summary)
                    log(f"[AutoDocs] Generated weekly summary: {summary_path.name}")

                    # Store in Linear Docs
                    if linear_available:
                        doc = await linear_client.create_or_update_document(
                            title="Flow Guardian Weekly Summary",
                            content=summary
                        )
                        if doc:
                            log(f"[AutoDocs] Stored weekly summary in Linear: {doc.get('url', doc.get('id'))}")
                except Exception as e:
                    log(f"[AutoDocs] Weekly summary failed: {e}", "WARN")

                # Update state
                self.state["last_report_time"] = datetime.now().isoformat()
                self.state["extractions_since_report"] = 0
                self._save_state()

        except ImportError:
            pass  # report_generator not available
        except Exception as e:
            log(f"[AutoDocs] Error: {e}", "ERROR")

    async def extract_insights(self, conversation: str) -> list[dict]:
        """Use Cerebras to extract insights from conversation."""
        if not conversation.strip():
            return []

        prompt = f"""Analyze this Claude Code conversation and extract key insights.

Focus on:
1. LEARNINGS - Technical discoveries, solutions found
2. DECISIONS - Architectural choices, approach decisions
3. CONTEXT - What the user is working on, their goals

Format as JSON array:
[{{"category": "learning", "insight": "..."}}, ...]

Only extract genuinely useful insights. If none, return [].

CONVERSATION:
{conversation[:MAX_CHUNK_CHARS]}"""

        try:
            response = self.service.cerebras.complete(
                prompt=prompt,
                system="Extract technical insights as JSON only.",
                json_mode=True,
                max_tokens=2000
            )

            # Parse response
            import re
            # Try direct parse
            try:
                result = json.loads(response)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

            # Try markdown extraction
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if match:
                try:
                    result = json.loads(match.group(1))
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass

            # Try array extraction
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                try:
                    result = json.loads(match.group())
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            log(f"Extraction error: {e}", "ERROR")

        return []

    async def process_session(self, session_path: Path) -> int:
        """Process a session file and return number of insights stored."""
        import session_parser

        session_id = session_path.stem
        session_state = self.state["sessions"].get(session_id, {
            "last_line": 0,
            "last_extraction": None,
            "pending_messages": 0,
        })

        # Get new conversation
        conversation, new_line = session_parser.get_conversation_text(
            session_path,
            since_line=session_state.get("last_line", 0),
            max_chars=MAX_CHUNK_CHARS
        )

        if new_line <= session_state.get("last_line", 0):
            return 0

        # Update pending count
        new_messages = new_line - session_state.get("last_line", 0)
        pending = session_state.get("pending_messages", 0) + new_messages
        session_state["last_line"] = new_line
        session_state["pending_messages"] = pending
        self.state["sessions"][session_id] = session_state

        # Check if we should extract
        time_since = float("inf")
        if session_state.get("last_extraction"):
            try:
                last_dt = datetime.fromisoformat(session_state["last_extraction"])
                time_since = (datetime.now() - last_dt).total_seconds()
            except (ValueError, TypeError):
                pass

        should_extract = (
            pending >= MIN_MESSAGES_BATCH or
            time_since >= MAX_EXTRACTION_INTERVAL
        )

        if not should_extract:
            self._save_state()
            return 0

        log(f"Extracting from {session_id[:8]}... ({pending} messages)")

        # Get more context for extraction
        full_conv, _ = session_parser.get_conversation_text(
            session_path,
            since_line=max(0, new_line - 50),
            max_chars=MAX_CHUNK_CHARS
        )

        insights = await self.extract_insights(full_conv)

        if insights:
            # Get cwd
            cwd = "unknown"
            for msg in session_parser.parse_session_messages(session_path, 0):
                if msg.get("cwd"):
                    cwd = msg["cwd"]
                    break

            # Store insights
            for insight in insights:
                await self.service.store_learning(
                    insight=insight.get("insight", ""),
                    tags=[insight.get("category", "learning"), "auto-captured"],
                )

            log(f"Stored {len(insights)} insights from {session_id[:8]}")
            self.state["extractions_count"] = self.state.get("extractions_count", 0) + 1

            # Check if we should generate documentation
            await self._maybe_generate_docs(len(insights))

        session_state["last_extraction"] = datetime.now().isoformat()
        session_state["pending_messages"] = 0
        self.state["sessions"][session_id] = session_state
        self._save_state()

        return len(insights)

    async def watch_loop(self):
        """Main daemon loop."""
        import session_parser

        self.running = True
        self.state["started_at"] = datetime.now().isoformat()
        self._save_state()

        log("Daemon started, watching for sessions...")

        while self.running:
            try:
                if session_parser.CLAUDE_PROJECTS_DIR.exists():
                    for project_dir in session_parser.CLAUDE_PROJECTS_DIR.iterdir():
                        if not project_dir.is_dir():
                            continue

                        session_id = session_parser.get_active_session(project_dir)
                        if not session_id:
                            continue

                        session_path = session_parser.get_session_path(project_dir, session_id)
                        if session_path.exists():
                            await self.process_session(session_path)

            except Exception as e:
                log(f"Watch loop error: {e}", "ERROR")

            await asyncio.sleep(POLL_INTERVAL)

    def stop(self):
        self.running = False


# ============ HTTP API MODE ============

def create_api_app(service: FlowService):
    """Create FastAPI application."""
    from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    from typing import List

    app = FastAPI(
        title="Flow Guardian API",
        description="Persistent memory for AI coding sessions",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request/Response models
    class CaptureRequest(BaseModel):
        summary: str
        decisions: list[str] = []
        next_steps: list[str] = []
        blockers: list[str] = []

    class RecallRequest(BaseModel):
        query: str
        local_only: bool = False  # Skip Backboard for faster responses

    class LearnRequest(BaseModel):
        insight: str
        tags: list[str] = []
        share_with_team: bool = False

    class TeamRequest(BaseModel):
        query: str

    # Routes
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "flow-guardian"}

    @app.get("/status")
    async def status():
        return await service.get_status()

    @app.post("/capture")
    async def capture(req: CaptureRequest, background_tasks: BackgroundTasks):
        result = await service.capture_context(
            summary=req.summary,
            decisions=req.decisions,
            next_steps=req.next_steps,
            blockers=req.blockers,
        )

        # Agentically create Linear issues for blockers
        if req.blockers and len(req.blockers) > 0:
            background_tasks.add_task(
                create_linear_issues_for_blockers,
                blockers=req.blockers,
                summary=req.summary or ""
            )

        return result

    @app.post("/recall")
    async def recall(req: RecallRequest):
        return await service.recall_context(req.query, local_only=req.local_only)

    @app.post("/learn")
    async def learn(req: LearnRequest, background_tasks: BackgroundTasks):
        result = await service.store_learning(
            insight=req.insight,
            tags=req.tags,
            share_with_team=req.share_with_team,
        )

        # Check if this learning might warrant a Linear issue (bugs, errors, etc.)
        background_tasks.add_task(
            process_learning_for_linear,
            insight=req.insight,
            tags=req.tags or []
        )

        return result

    @app.post("/team")
    async def team(req: TeamRequest):
        return await service.query_team(req.query)

    # ---- Linear Agent Analysis Endpoint ----
    class AnalyzeRequest(BaseModel):
        conversation: str

    @app.post("/analyze-for-linear")
    async def analyze_for_linear(req: AnalyzeRequest, background_tasks: BackgroundTasks):
        """Analyze a chat conversation and create Linear issues if warranted.

        This is called by the web chat after each conversation to intelligently
        decide if issues should be created.
        """
        background_tasks.add_task(
            analyze_conversation_for_issues,
            conversation=req.conversation
        )
        return {"status": "analyzing", "message": "Conversation queued for analysis"}

    # ---- Web UI Endpoints ----

    @app.get("/sessions")
    async def list_sessions(
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        branch: Optional[str] = Query(default=None),
    ):
        """List sessions with pagination."""
        # Get all sessions (we need total count for pagination)
        all_sessions = service.memory.list_sessions(limit=1000, branch=branch)
        total = len(all_sessions)

        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        sessions = all_sessions[start:end]

        return {
            "sessions": sessions,
            "total": total,
            "page": page,
        }

    @app.get("/learnings")
    async def list_learnings(
        page: int = Query(default=1, ge=1),
        limit: int = Query(default=10, ge=1, le=100),
        tag: Optional[str] = Query(default=None),
        team: Optional[bool] = Query(default=None),
    ):
        """List learnings with pagination."""
        # Get all learnings filtered by team flag
        all_learnings = service.memory.get_all_learnings(team=team)

        # Filter by tag if specified
        if tag:
            all_learnings = [
                l for l in all_learnings
                if tag in l.get("tags", [])
            ]

        total = len(all_learnings)

        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        learnings = all_learnings[start:end]

        return {
            "learnings": learnings,
            "total": total,
        }

    @app.get("/stats")
    async def get_stats():
        """Get dashboard statistics."""
        stats = service.memory.get_stats()

        # Calculate top tags
        all_learnings = service.memory.get_all_learnings()
        tag_counts = {}
        for learning in all_learnings:
            for tag in learning.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count and get top 10
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "sessions_count": stats.get("sessions_count", 0),
            "learnings_count": stats.get("total_learnings", 0),
            "team_learnings": stats.get("team_learnings", 0),
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags],
        }

    @app.post("/documents")
    async def upload_document(
        file: UploadFile = File(...),
        note: str = Form(default=""),
        tags: str = Form(default=""),
    ):
        """Upload and process a document (PDF supported)."""
        import uuid

        # Parse tags (comma-separated string)
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        # Read file content
        content = await file.read()
        filename = file.filename or "unknown"

        # Extract text based on file type
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            try:
                import fitz  # PyMuPDF

                # Open PDF from bytes
                doc = fitz.open(stream=content, filetype="pdf")
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())
                doc.close()
                extracted_text = "\n".join(text_parts)
            except ImportError:
                raise HTTPException(
                    status_code=500,
                    detail="PyMuPDF (fitz) not installed. Install with: pip install pymupdf"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to extract text from PDF: {str(e)}"
                )
        else:
            # For non-PDF files, try to decode as text
            try:
                extracted_text = content.decode("utf-8")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Only PDF and text files are supported."
                )

        # Generate a summary (first 500 chars or use note)
        summary = note if note else extracted_text[:500].strip()
        if len(summary) > 500:
            summary = summary[:497] + "..."

        # Generate document ID
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        # Store to Backboard if available
        if service.backboard_available():
            thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
            if thread_id:
                tag_str = " ".join(f"#{t}" for t in tag_list)
                content_to_store = f"**Document**: {filename}\n{tag_str}\n\n{note}\n\n---\n\n{extracted_text[:10000]}"
                try:
                    await service.backboard.store_message(thread_id, content_to_store, {
                        "type": "document",
                        "filename": filename,
                        "doc_id": doc_id,
                        "tags": tag_list,
                    })
                except Exception as e:
                    log(f"Failed to store document to Backboard: {e}", "WARN")

        # Also store as a learning for local search
        service.memory.save_learning({
            "id": doc_id,
            "insight": f"Document: {filename} - {summary}",
            "text": extracted_text[:5000],  # Store first 5000 chars for search
            "tags": tag_list + ["document"],
            "filename": filename,
        })

        return {
            "id": doc_id,
            "filename": filename,
            "summary": summary,
            "tags": tag_list,
        }

    return app


# ============ LINEAR AGENT INTEGRATION ============

async def create_linear_issues_for_blockers(blockers: list[str], summary: str):
    """Background task to analyze blockers and create Linear issues if needed.

    Uses Cerebras to analyze blockers and determine if they should become
    Linear issues, then creates them automatically.
    """
    try:
        import linear_agent

        # Build content for analysis
        content = f"Session: {summary}\n\nBlockers:\n"
        for blocker in blockers:
            content += f"- {blocker}\n"

        log(f"[LinearAgent] Analyzing {len(blockers)} blockers for potential issues...")

        # Use Cerebras to analyze and identify actionable issues
        issues_to_create = await linear_agent.analyze_for_issues(content)

        if not issues_to_create:
            log("[LinearAgent] No actionable issues identified from blockers")
            return

        log(f"[LinearAgent] Creating {len(issues_to_create)} Linear issues...")

        # Create issues in Linear
        for issue in issues_to_create:
            created = await linear_agent.create_linear_issue(
                title=issue.get("title", "Untitled"),
                description=issue.get("description", ""),
                issue_type=issue.get("type", "blocker"),
                priority=issue.get("priority", 2)  # Default high priority for blockers
            )
            if created:
                log(f"[LinearAgent] Created issue: {created.get('identifier')} - {issue.get('title')}")

    except ImportError:
        log("[LinearAgent] linear_agent module not available", "WARN")
    except Exception as e:
        log(f"[LinearAgent] Error creating issues: {e}", "ERROR")


async def process_learning_for_linear(insight: str, tags: list[str]):
    """Background task to check if a learning should create a Linear issue.

    Only processes learnings that look like bugs or actionable issues.
    """
    try:
        import linear_agent

        # Quick check - only process if it looks like a bug or issue
        bug_indicators = ["bug", "error", "fix", "broken", "issue", "problem", "fail", "crash", "exception"]
        insight_lower = insight.lower()
        tags_lower = [t.lower() for t in tags]

        is_potential_issue = (
            any(ind in insight_lower for ind in bug_indicators) or
            any(ind in tag for tag in tags_lower for ind in bug_indicators)
        )

        if not is_potential_issue:
            return  # Skip - not a bug-related learning

        log(f"[LinearAgent] Processing learning for potential Linear issue...")

        # Analyze with Cerebras
        content = f"Learning: {insight}\nTags: {', '.join(tags)}"
        issues = await linear_agent.analyze_for_issues(content)

        if issues:
            issue = issues[0]  # Take first suggested issue
            created = await linear_agent.create_linear_issue(
                title=issue.get("title", "Untitled"),
                description=issue.get("description", ""),
                issue_type=issue.get("type", "bug"),
                priority=issue.get("priority", 2)
            )
            if created:
                log(f"[LinearAgent] Created issue from learning: {created.get('identifier')}")

    except ImportError:
        pass  # linear_agent not available, silently skip
    except Exception as e:
        log(f"[LinearAgent] Error processing learning: {e}", "ERROR")


async def analyze_conversation_for_issues(conversation: str):
    """Analyze a chat conversation and create Linear issues if warranted.

    Uses Cerebras to intelligently determine if the conversation contains
    actionable items that should become Linear issues.
    """
    try:
        import linear_agent
        import cerebras_client

        log("[LinearAgent] Analyzing conversation for potential issues...")

        # Use Cerebras to analyze the conversation
        analysis_prompt = f"""Analyze this chat conversation and determine if any Linear issues should be created.

CONVERSATION:
{conversation[:8000]}

Look for:
1. BUGS - Errors, failures, broken functionality mentioned
2. BLOCKERS - Things preventing progress
3. FEATURE REQUESTS - New functionality discussed
4. ACTION ITEMS - Tasks that need to be done

For each potential issue, provide:
- title: Clear, concise title
- description: What needs to be done
- type: "bug", "blocker", "feature", or "task"
- priority: 1 (urgent), 2 (high), 3 (medium), 4 (low)
- reason: Why this should be a Linear issue

IMPORTANT: Only create issues for ACTIONABLE items. Don't create issues for:
- General questions or discussions
- Completed work
- Things already resolved in the conversation

Return a JSON array. If nothing warrants an issue, return [].

Example:
[{{"title": "Fix Stripe webhook silent failures", "description": "Webhook fails silently with Apple Pay - no error logs", "type": "bug", "priority": 1, "reason": "Critical payment issue affecting revenue"}}]

Respond with ONLY the JSON array."""

        response = await cerebras_client.quick_answer(
            analysis_prompt,
            system="You are a project manager analyzing conversations to identify actionable work items. Be selective - only flag truly important items."
        )

        # Parse response
        import json
        try:
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                issues = json.loads(response[start:end])
                if not isinstance(issues, list):
                    issues = []
            else:
                issues = []
        except json.JSONDecodeError:
            issues = []

        if not issues:
            log("[LinearAgent] No actionable issues found in conversation")
            return

        log(f"[LinearAgent] Found {len(issues)} potential issues in conversation")

        # Create issues in Linear
        for issue in issues:
            log(f"[LinearAgent] Creating issue: {issue.get('title')} (reason: {issue.get('reason', 'N/A')})")
            created = await linear_agent.create_linear_issue(
                title=issue.get("title", "Untitled"),
                description=f"{issue.get('description', '')}\n\n---\n_Reason: {issue.get('reason', 'Identified from chat conversation')}_",
                issue_type=issue.get("type", "task"),
                priority=issue.get("priority", 3)
            )
            if created:
                log(f"[LinearAgent] Created: {created.get('identifier')} - {issue.get('title')}")

    except ImportError as e:
        log(f"[LinearAgent] Module not available: {e}", "WARN")
    except Exception as e:
        log(f"[LinearAgent] Error analyzing conversation: {e}", "ERROR")


async def run_api(service: FlowService, port: int = 8090):
    """Run HTTP API server."""
    import uvicorn

    app = create_api_app(service)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


# ============ MCP MODE ============

async def run_mcp(service: FlowService):
    """Run MCP server for Claude Code."""
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

    server = Server("flow-guardian")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="flow_recall",
                description="Recall previous coding context from memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="flow_capture",
                description="Capture current coding context to memory",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Brief description of current work"},
                        "decisions": {"type": "array", "items": {"type": "string"}},
                        "next_steps": {"type": "array", "items": {"type": "string"}},
                        "blockers": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["summary"]
                }
            ),
            Tool(
                name="flow_learn",
                description="Store a learning or insight",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "insight": {"type": "string", "description": "The learning to store"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "share_with_team": {"type": "boolean", "default": False},
                    },
                    "required": ["insight"]
                }
            ),
            Tool(
                name="flow_team",
                description="Search team's shared knowledge base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="flow_status",
                description="Get Flow Guardian status",
                inputSchema={"type": "object", "properties": {}}
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "flow_recall":
                result = await service.recall_context(arguments["query"])
                text = f"Found {len(result['results'])} results for '{result['query']}':\n"
                for r in result["results"][:5]:
                    text += f"\n- {r.get('content', r)[:200]}..."
                return [TextContent(type="text", text=text)]

            elif name == "flow_capture":
                result = await service.capture_context(
                    summary=arguments["summary"],
                    decisions=arguments.get("decisions", []),
                    next_steps=arguments.get("next_steps", []),
                    blockers=arguments.get("blockers", []),
                )
                return [TextContent(
                    type="text",
                    text=f"Context saved (local: {result['local']}, cloud: {result['cloud']})"
                )]

            elif name == "flow_learn":
                result = await service.store_learning(
                    insight=arguments["insight"],
                    tags=arguments.get("tags", []),
                    share_with_team=arguments.get("share_with_team", False),
                )
                return [TextContent(
                    type="text",
                    text=f"Learning stored (personal: {result['personal']}, team: {result['team']})"
                )]

            elif name == "flow_team":
                result = await service.query_team(arguments["query"])
                if not result["available"]:
                    return [TextContent(type="text", text="Team knowledge not configured")]
                text = f"Team results for '{result['query']}':\n"
                for r in result.get("results", [])[:5]:
                    text += f"\n- {r.get('content', r)[:200]}..."
                return [TextContent(type="text", text=text)]

            elif name == "flow_status":
                result = await service.get_status()
                lines = [
                    f"Backboard: {'Connected' if result['backboard_connected'] else 'Not configured'}",
                    f"Team: {'Available' if result['team_available'] else 'Not configured'}",
                ]
                if result.get("last_capture"):
                    lines.append(f"Last capture: {result['last_capture']}")
                    lines.append(f"Summary: {result.get('last_summary', 'N/A')}")
                return [TextContent(type="text", text="\n".join(lines))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


# ============ COMBINED MODE ============

async def run_combined(service: FlowService, port: int = 8090):
    """Run daemon + HTTP API together."""
    daemon = DaemonMode(service)

    # Run both concurrently
    await asyncio.gather(
        daemon.watch_loop(),
        run_api(service, port),
    )


# ============ PROCESS MANAGEMENT ============

def is_running() -> Optional[int]:
    """Check if server is running."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        PID_FILE.unlink(missing_ok=True)
        return None


def write_pid():
    DAEMON_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def cleanup_pid(*args):
    PID_FILE.unlink(missing_ok=True)
    log("Server stopped")
    sys.exit(0)


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(
        description="Flow Guardian Unified Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "mode",
        choices=["daemon", "api", "mcp", "all", "status", "stop"],
        help="Server mode to run"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8090,
        help="HTTP API port (default: 8090)"
    )
    parser.add_argument(
        "--foreground", "-f",
        action="store_true",
        help="Run in foreground (don't daemonize)"
    )

    args = parser.parse_args()

    if args.mode == "status":
        pid = is_running()
        if pid:
            print(f"Server running (PID: {pid})")
            state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
            print(f"Started: {state.get('started_at', 'unknown')}")
            print(f"Extractions: {state.get('extractions_count', 0)}")
        else:
            print("Server not running")
        return

    if args.mode == "stop":
        pid = is_running()
        if pid:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped server (PID: {pid})")
        else:
            print("Server not running")
        return

    if is_running() and args.mode != "mcp":
        print(f"Server already running (PID: {is_running()})")
        return

    service = get_service()

    # Set up signal handlers
    signal.signal(signal.SIGINT, cleanup_pid)
    signal.signal(signal.SIGTERM, cleanup_pid)

    if args.mode == "mcp":
        # MCP runs on stdio, no PID file needed
        asyncio.run(run_mcp(service))

    elif args.foreground or args.mode == "api":
        write_pid()
        try:
            if args.mode == "daemon":
                daemon = DaemonMode(service)
                asyncio.run(daemon.watch_loop())
            elif args.mode == "api":
                asyncio.run(run_api(service, args.port))
            elif args.mode == "all":
                asyncio.run(run_combined(service, args.port))
        finally:
            PID_FILE.unlink(missing_ok=True)

    else:
        # Daemonize
        pid = os.fork()
        if pid > 0:
            print(f"Server started (PID: {pid})")
            return

        os.setsid()
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        write_pid()
        sys.stdout = open(LOG_FILE, "a")
        sys.stderr = sys.stdout

        try:
            if args.mode == "daemon":
                daemon = DaemonMode(service)
                asyncio.run(daemon.watch_loop())
            elif args.mode == "all":
                asyncio.run(run_combined(service, args.port))
        finally:
            PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
