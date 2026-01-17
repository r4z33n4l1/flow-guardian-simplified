"""Backboard.io API client for Flow Guardian.

Provides persistent memory storage and semantic recall capabilities.
Uses async HTTP with connection pooling and retry logic.
"""
import os
import asyncio
from datetime import datetime
from typing import Optional

import httpx


# ============ CONFIGURATION ============

BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
API_KEY = os.environ.get("BACKBOARD_API_KEY")
TIMEOUT = 30.0
MAX_RETRIES = 3
BACKOFF_MULTIPLIER = 1  # seconds


# ============ EXCEPTIONS ============

class BackboardError(Exception):
    """Base exception for Backboard.io errors."""
    pass


class BackboardAuthError(BackboardError):
    """Authentication failure with Backboard.io API."""
    pass


class BackboardConnectionError(BackboardError):
    """Network connectivity issues with Backboard.io."""
    pass


class BackboardRateLimitError(BackboardError):
    """Rate limit exceeded on Backboard.io API."""
    pass


# ============ HELPERS ============

def _headers() -> dict:
    """Get authorization headers."""
    if not API_KEY:
        raise BackboardAuthError("BACKBOARD_API_KEY environment variable not set")
    return {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }


async def _request_with_retry(
    method: str,
    url: str,
    **kwargs
) -> httpx.Response:
    """
    Make an HTTP request with retry logic.

    Retries on 5xx errors with exponential backoff.
    No retry on 4xx errors.
    """
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await getattr(client, method)(url, **kwargs)

                # Handle specific error codes
                if response.status_code == 401:
                    raise BackboardAuthError("Invalid API key")
                elif response.status_code == 429:
                    raise BackboardRateLimitError("Rate limit exceeded")
                elif 400 <= response.status_code < 500:
                    # Client errors - don't retry
                    response.raise_for_status()
                elif response.status_code >= 500:
                    # Server errors - retry with backoff
                    if attempt < MAX_RETRIES - 1:
                        wait_time = BACKOFF_MULTIPLIER * (2 ** attempt)
                        await asyncio.sleep(wait_time)
                        continue
                    response.raise_for_status()

                return response

        except httpx.ConnectError as e:
            last_exception = BackboardConnectionError(f"Connection failed: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = BACKOFF_MULTIPLIER * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
            raise last_exception

        except httpx.TimeoutException as e:
            last_exception = BackboardConnectionError(f"Request timeout: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = BACKOFF_MULTIPLIER * (2 ** attempt)
                await asyncio.sleep(wait_time)
                continue
            raise last_exception

        except (BackboardAuthError, BackboardRateLimitError):
            raise

        except httpx.HTTPStatusError as e:
            raise BackboardError(f"HTTP error: {e}")

    if last_exception:
        raise last_exception
    raise BackboardError("Request failed after retries")


# ============ SETUP FUNCTIONS ============

async def create_assistant(name: str, llm_provider: str = "cerebras") -> str:
    """
    Create a Backboard assistant (memory container).

    Args:
        name: Assistant name (e.g., "flow-guardian-personal")
        llm_provider: LLM provider to use (default: "cerebras")

    Returns:
        Assistant ID
    """
    response = await _request_with_retry(
        "post",
        f"{BASE_URL}/assistants",
        headers=_headers(),
        json={
            "name": name,
            "llm_provider": llm_provider,
            "llm_model_name": "gemini-2.5-flash",
            "tools": []
            "description": name,
        }
    )
    return response.json()["assistant_id"]


async def create_thread(assistant_id: str) -> str:
    """
    Create a conversation thread within an assistant.

    Args:
        assistant_id: The assistant to create the thread in

    Returns:
        Thread ID
    """
    response = await _request_with_retry(
        "post",
        f"{BASE_URL}/assistants/{assistant_id}/threads",
        headers=_headers(),
        json={}
    )
    return response.json()["thread_id"]


async def health_check() -> bool:
    """
    Check if Backboard.io is available.

    Returns:
        True if service is reachable, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{BASE_URL}/health",
                headers=_headers()
            )
            return response.status_code == 200
    except Exception:
        return False


# ============ STORAGE FUNCTIONS (No LLM) ============

async def store_message(
    thread_id: str,
    content: str,
    metadata: Optional[dict] = None
) -> dict:
    """
    Store a message without calling the LLM.

    Args:
        thread_id: Thread to store the message in
        content: Message content
        metadata: Optional metadata dictionary

    Returns:
        Response from API
    """
    import json
    if not API_KEY:
        raise BackboardAuthError("BACKBOARD_API_KEY environment variable not set")

    # Backboard API uses multipart/form-data with string values
    form_data = {
        "content": content,
        "send_to_llm": "false"
    }
    if metadata:
        form_data["metadata"] = json.dumps(metadata)

    # Don't include Content-Type header for form data - httpx sets it
    headers = {"X-API-Key": API_KEY}

    response = await _request_with_retry(
        "post",
        f"{BASE_URL}/threads/{thread_id}/messages",
        headers=headers,
        data=form_data  # Use data= for form data, not json=
    )
    return response.json()


async def store_session(thread_id: str, session: dict) -> dict:
    """
    Store a session checkpoint.

    Args:
        thread_id: Thread to store the session in
        session: Session data dictionary

    Returns:
        Response from API
    """
    context = session.get("context", {})
    git = session.get("git", {})

    content = f"""## Context Snapshot
**Working on:** {context.get('summary', 'unknown')}
**Hypothesis:** {context.get('hypothesis', 'none')}
**Files:** {', '.join(context.get('files', [])) if context.get('files') else 'none'}
**Branch:** {git.get('branch', 'unknown')}
**Next steps:** {', '.join(context.get('next_steps', [])) if context.get('next_steps') else 'none'}"""

    metadata = {
        "type": "context_snapshot",
        "session_id": session.get("id"),
        "timestamp": session.get("timestamp") or datetime.now().isoformat(),
        "branch": git.get("branch"),
        "files": context.get("files", []),
        "tags": session.get("metadata", {}).get("tags", [])
    }

    return await store_message(thread_id, content, metadata)


async def store_learning(
    thread_id: str,
    text: str,
    tags: Optional[list[str]] = None,
    author: Optional[str] = None
) -> dict:
    """
    Store a learning/insight.

    Args:
        thread_id: Thread to store the learning in
        text: The learning text
        tags: Optional list of tags
        author: Optional author name

    Returns:
        Response from API
    """
    content = f"**Learning:** {text}"

    metadata = {
        "type": "learning",
        "timestamp": datetime.now().isoformat(),
        "tags": tags or [],
    }
    if author:
        metadata["author"] = author

    return await store_message(thread_id, content, metadata)


# ============ RECALL FUNCTIONS (With LLM) ============

async def recall(thread_id: str, query: str) -> str:
    """
    Query memory with semantic recall.

    Uses memory="auto" to automatically retrieve relevant past context.

    Args:
        thread_id: Thread to search in
        query: Natural language query

    Returns:
        LLM response with relevant context
    """
    # Backboard API uses multipart/form-data with string values
    form_data = {
        "content": query,
        "memory": "auto",
        "send_to_llm": "true"
    }
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    if not API_KEY:
        raise BackboardAuthError("BACKBOARD_API_KEY environment variable not set")

    response = await _request_with_retry(
        "post",
        f"{BASE_URL}/threads/{thread_id}/messages",
        headers=headers,
        data=form_data
    )
    return response.json().get("content", "")


async def get_restoration_context(thread_id: str, changes_summary: str) -> str:
    """
    Generate a welcome-back message using stored context.

    Args:
        thread_id: Thread with stored context
        changes_summary: Summary of what changed while away

    Returns:
        Natural language restoration message
    """
    query = f"""Based on my most recent context snapshot, generate a concise "welcome back" summary.

Also consider these changes that happened while I was away:
{changes_summary}

Format:
1. What I was working on (1 sentence)
2. My hypothesis (if any)
3. What changed while away (highlight if it affects my work!)
4. Suggested next action

Keep it under 10 lines. Be direct."""

    return await recall(thread_id, query)


# ============ TEAM MEMORY ============

async def store_team_learning(
    team_thread_id: str,
    learning: str,
    author: str,
    tags: Optional[list[str]] = None
) -> dict:
    """
    Store a learning to the team's shared memory.

    Args:
        team_thread_id: Team thread ID
        learning: The learning text
        author: Who shared the learning
        tags: Optional list of tags

    Returns:
        Response from API
    """
    content = f"**Team Learning** (from {author}): {learning}"

    metadata = {
        "type": "team_learning",
        "author": author,
        "timestamp": datetime.now().isoformat(),
        "tags": tags or []
    }

    return await store_message(team_thread_id, content, metadata)


async def query_team_memory(team_thread_id: str, query: str) -> str:
    """
    Search the team's shared learnings.

    Args:
        team_thread_id: Team thread ID
        query: Search query

    Returns:
        LLM response with relevant team learnings
    """
    full_query = f"""Search team learnings for: {query}

Summarize relevant learnings from the team. Include who shared each insight."""

    return await recall(team_thread_id, full_query)


# ============ SYNC HELPERS ============

def run_async(coro):
    """
    Helper to run async functions from sync context.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We're in an async context, create a new loop in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)
