"""Inject Module for Flow Guardian.

Generates context injection for Claude Code sessions. Combines:
- Handoff state (current session state from handoff.yaml)
- Semantic recall from Backboard.io
- TLDR compression for token efficiency

Used by:
- `flow inject` command for manual injection
- SessionStart hook for automatic context injection
- PreCompact hook for state preservation
"""
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from handoff import (
    find_project_root,
    load_handoff,
    save_handoff,
    update_handoff,
)
from tldr import summarize_handoff, summarize_recall, summarize_context
from git_utils import get_current_branch, get_uncommitted_files


logger = logging.getLogger(__name__)


# ============ CONSTANTS ============

DEFAULT_LEVEL = "L1"
INJECTION_HEADER = "<flow-guardian-context>"
INJECTION_FOOTER = "</flow-guardian-context>"


# ============ CONTEXT GENERATION ============

async def generate_injection(
    level: str = "L1",
    quiet: bool = False,
    project_root: Optional[Path] = None
) -> str:
    """
    Generate context injection for Claude.

    1. Load handoff.yaml
    2. Query Backboard for relevant memory
    3. TLDR if needed
    4. Format output

    Args:
        level: TLDR depth (L0, L1, L2, L3)
        quiet: If True, plain output without Rich formatting
        project_root: Project root path (auto-detected if None)

    Returns:
        Formatted context string for Claude
    """
    if project_root is None:
        project_root = find_project_root()

    # Load handoff state
    handoff = load_handoff(project_root)

    # Get memory from Backboard if available
    memory_results = await _recall_for_injection(handoff)

    # Format the injection
    return format_injection(handoff, memory_results, level, quiet)


async def _recall_for_injection(handoff: Optional[dict], limit: int = 10) -> list:
    """
    Query Backboard for context relevant to current session.

    Uses context-aware queries with project, branch, and focus info.
    Falls back to local memory if Backboard is unavailable.

    Args:
        handoff: Current handoff state (for building contextual query)
        limit: Maximum number of results to return

    Returns:
        List of recall results with metadata
    """
    thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
    if not thread_id:
        logger.debug("No BACKBOARD_PERSONAL_THREAD_ID, skipping Backboard recall")
        return _local_fallback(handoff, limit)

    try:
        from backboard_client import recall, BackboardError

        # Build contextual query for session start
        query = _build_recall_query(handoff)

        # Call Backboard recall
        result = await recall(thread_id, query)

        # Parse result into list format
        if result:
            # Wrap the result and categorize
            parsed_results = [{"content": result, "metadata": {"type": "context"}}]
            # Apply relevance scoring and limit
            return _score_and_filter_results(parsed_results, handoff, limit)
        return []

    except Exception as e:
        logger.warning(f"Backboard recall failed: {e}")
        return _local_fallback(handoff, limit)


def _build_recall_query(handoff: Optional[dict]) -> str:
    """
    Build a contextual query for Backboard recall.

    Includes project name, goal, current focus, and branch info
    for better semantic matching.

    Args:
        handoff: Current handoff state

    Returns:
        Query string for Backboard recall
    """
    query_parts = []

    # Add project context
    project_name = Path.cwd().name
    query_parts.append(f"What do I need to know about {project_name}?")

    # Add handoff context if available
    if handoff:
        if handoff.get("goal"):
            query_parts.append(f"Goal: {handoff['goal']}")
        if handoff.get("now"):
            query_parts.append(f"Current focus: {handoff['now']}")
        if handoff.get("branch"):
            query_parts.append(f"Branch: {handoff['branch']}")
        if handoff.get("hypothesis"):
            query_parts.append(f"Hypothesis: {handoff['hypothesis']}")
        if handoff.get("files"):
            files = handoff.get("files", [])
            if files:
                # Include relevant files for context matching
                query_parts.append(f"Working on files: {', '.join(files[:5])}")

    query = ". ".join(query_parts)
    query += "\n\nInclude: recent work, key decisions, important learnings, current blockers."

    return query


def _score_and_filter_results(
    results: list,
    handoff: Optional[dict],
    limit: int = 10
) -> list:
    """
    Score and filter recall results for relevance.

    Applies local relevance scoring:
    - Recency boost: Items from last 24h get priority
    - Branch match: Same branch = higher relevance
    - File overlap: Matching files = higher relevance

    Args:
        results: Raw recall results
        handoff: Current handoff state for context matching
        limit: Maximum results to return

    Returns:
        Scored and filtered list of results
    """
    from datetime import timedelta

    if not results:
        return []

    # Get current context for matching
    current_branch = handoff.get("branch") if handoff else None
    current_files = set(handoff.get("files", [])) if handoff else set()
    now = datetime.now(timezone.utc)

    scored_results = []
    for item in results:
        score = 0.0
        metadata = item.get("metadata", {})

        # Recency boost (24h window)
        timestamp_str = metadata.get("timestamp")
        if timestamp_str:
            try:
                item_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                hours_ago = (now - item_time).total_seconds() / 3600
                if hours_ago < 24:
                    score += 0.3 * (1 - hours_ago / 24)  # Max 0.3 boost for recent items
            except (ValueError, TypeError):
                pass

        # Branch match boost
        item_branch = metadata.get("branch")
        if item_branch and current_branch and item_branch == current_branch:
            score += 0.3

        # File overlap boost
        item_files = set(metadata.get("files", []))
        if item_files and current_files:
            overlap = len(item_files & current_files)
            if overlap > 0:
                score += 0.2 * min(overlap / 3, 1.0)  # Max 0.2 boost for file overlap

        # Type priority (learnings and decisions higher than context)
        item_type = metadata.get("type", "context")
        if item_type in ("learning", "learnings"):
            score += 0.1
        elif item_type in ("decision", "decisions"):
            score += 0.1

        scored_results.append((score, item))

    # Sort by score (descending) and return top N
    scored_results.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_results[:limit]]


def categorize_recall(results: list) -> dict:
    """
    Group recall results by type.

    Args:
        results: List of recall results with metadata

    Returns:
        Dictionary with categorized results:
        {
            "learnings": [...],
            "decisions": [...],
            "context": [...],
            "insights": [...]
        }
    """
    categories = {
        "learnings": [],
        "decisions": [],
        "context": [],
        "insights": [],
    }

    for item in results:
        metadata = item.get("metadata", {})
        item_type = metadata.get("type", "context")

        # Normalize type names
        if item_type in ("learning", "learnings"):
            categories["learnings"].append(item)
        elif item_type in ("decision", "decisions"):
            categories["decisions"].append(item)
        elif item_type in ("insight", "insights", "auto_learning"):
            categories["insights"].append(item)
        else:
            categories["context"].append(item)

    return categories


def _local_fallback(handoff: Optional[dict] = None, limit: int = 10) -> list:
    """
    Fall back to local memory when Backboard unavailable.

    Searches local learnings and sessions, then applies
    relevance scoring for better results.

    Args:
        handoff: Current handoff state for context matching
        limit: Maximum number of results to return

    Returns:
        List of local memory results with metadata
    """
    try:
        from memory import search_learnings, get_latest_session

        results = []

        # Build search query from handoff
        query = ""
        if handoff:
            if handoff.get("goal"):
                query += handoff["goal"] + " "
            if handoff.get("now"):
                query += handoff["now"] + " "

        # Get recent learnings (search by query if available)
        learnings = search_learnings(query.strip() or "", limit=limit)
        for learning in learnings:
            results.append({
                "content": learning.get("text", ""),
                "metadata": {
                    "type": "learning",
                    "timestamp": learning.get("timestamp"),
                    "tags": learning.get("tags", []),
                    **learning.get("metadata", {})
                }
            })

        # Get latest session context
        session = get_latest_session()
        if session:
            context = session.get("context", {})
            if context.get("summary"):
                results.append({
                    "content": f"Previous session: {context.get('summary')}",
                    "metadata": {
                        "type": "context",
                        "timestamp": session.get("timestamp"),
                        "branch": session.get("git", {}).get("branch"),
                        "files": context.get("files", []),
                    }
                })

        # Apply relevance scoring
        return _score_and_filter_results(results, handoff, limit)

    except Exception as e:
        logger.debug(f"Local fallback failed: {e}")
        return []


def format_injection(
    handoff: Optional[dict],
    memory: list,
    level: str = "L1",
    quiet: bool = False
) -> str:
    """
    Format handoff + memory for injection.

    Args:
        handoff: Handoff state dictionary
        memory: List of memory/recall results
        level: TLDR level
        quiet: If True, plain text output; otherwise structured

    Returns:
        Formatted injection string
    """
    parts = []

    if not quiet:
        parts.append(INJECTION_HEADER)
        parts.append("")

    # Current session state
    if handoff:
        parts.append("## Current Session State")
        parts.append("")

        if handoff.get("goal"):
            parts.append(f"**Goal:** {handoff['goal']}")

        if handoff.get("status"):
            parts.append(f"**Status:** {handoff['status']}")

        if handoff.get("now"):
            parts.append(f"**Now:** {handoff['now']}")

        if handoff.get("hypothesis"):
            parts.append(f"**Hypothesis:** {handoff['hypothesis']}")

        if handoff.get("branch"):
            parts.append(f"**Branch:** {handoff['branch']}")

        files = handoff.get("files", [])
        if files:
            if level == "L0":
                parts.append(f"**Files:** {', '.join(files)}")
            elif level == "L1" and len(files) > 5:
                parts.append(f"**Files:** {', '.join(files[:5])} (+{len(files) - 5} more)")
            else:
                parts.append(f"**Files:** {', '.join(files)}")

        parts.append("")

    # Memory recall
    if memory:
        parts.append("## Relevant Memory")
        parts.append("")

        # Summarize recall results based on level
        recall_summary = summarize_recall(memory, level)
        if recall_summary:
            parts.append(recall_summary)
        parts.append("")

    # If no context at all, provide minimal message
    if not handoff and not memory:
        project_name = Path.cwd().name
        parts.append(f"## New Session: {project_name}")
        parts.append("")
        parts.append("No previous context found. This appears to be a new session.")
        parts.append("")

    if not quiet:
        parts.append(INJECTION_FOOTER)

    return "\n".join(parts).strip()


# ============ STATE SAVING ============

async def save_current_state(project_root: Optional[Path] = None) -> dict:
    """
    Save current session state to handoff.yaml.
    Called by PreCompact hook before context compaction.

    Args:
        project_root: Project root path (auto-detected if None)

    Returns:
        Saved handoff data
    """
    if project_root is None:
        project_root = find_project_root()

    # Get current git state
    try:
        branch = get_current_branch()
    except Exception:
        branch = None

    try:
        files = get_uncommitted_files()
    except Exception:
        files = []

    # Load existing handoff or create minimal one
    existing = load_handoff(project_root)

    if existing:
        # Update existing handoff
        updates = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if branch:
            updates["branch"] = branch
        if files:
            updates["files"] = files

        return update_handoff(updates, project_root)
    else:
        # Create new handoff with minimal info
        project_name = project_root.name
        data = {
            "goal": f"Working on {project_name}",
            "status": "in_progress",
            "now": "Session in progress",
            "branch": branch,
            "files": files,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        save_handoff(data, project_root)
        return data


# ============ SYNC WRAPPERS ============

def generate_injection_sync(
    level: str = "L1",
    quiet: bool = False,
    project_root: Optional[Path] = None
) -> str:
    """
    Synchronous wrapper for generate_injection.

    Args:
        level: TLDR depth (L0, L1, L2, L3)
        quiet: If True, plain output
        project_root: Project root path

    Returns:
        Formatted context string
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                generate_injection(level, quiet, project_root)
            )
            return future.result()
    else:
        return asyncio.run(generate_injection(level, quiet, project_root))


def save_current_state_sync(project_root: Optional[Path] = None) -> dict:
    """
    Synchronous wrapper for save_current_state.

    Args:
        project_root: Project root path

    Returns:
        Saved handoff data
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(
                asyncio.run,
                save_current_state(project_root)
            )
            return future.result()
    else:
        return asyncio.run(save_current_state(project_root))
