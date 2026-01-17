# Spec: Backboard.io Client (`backboard_client.py`)

## Overview

Async client for Backboard.io API — handles persistent memory storage and semantic recall.

## Configuration

```python
# Environment variables
BACKBOARD_API_KEY = os.environ.get("BACKBOARD_API_KEY")
BACKBOARD_BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
```

## API Endpoints Used

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create Assistant | POST | `/assistants` |
| Create Thread | POST | `/assistants/{id}/threads` |
| Send Message | POST | `/threads/{id}/messages` |

## Key Concepts

### Assistants
- Isolated memory containers
- One per user (personal) + one per team (shared)

### Threads
- Conversation sessions within an assistant
- We use one thread per assistant (simplicity for MVP)

### Messages
- Content with metadata
- `send_to_llm: False` → Just store (no LLM response)
- `send_to_llm: True` + `memory: "auto"` → Semantic recall

## API Functions

### Setup

```python
async def create_assistant(name: str, llm_provider: str = "cerebras") -> str:
    """Create a new Backboard assistant. Returns assistant ID."""

async def create_thread(assistant_id: str) -> str:
    """Create a new thread in an assistant. Returns thread ID."""

async def health_check() -> bool:
    """Check if Backboard.io is reachable."""
```

### Storage (No LLM)

```python
async def store_message(
    thread_id: str,
    content: str,
    metadata: dict = None
) -> dict:
    """
    Store a message without LLM response.
    Used for: session checkpoints, learnings.
    """

async def store_session(thread_id: str, session: dict) -> dict:
    """Store a session checkpoint."""

async def store_learning(
    thread_id: str,
    text: str,
    tags: list = None,
    author: str = None
) -> dict:
    """Store a learning."""
```

### Recall (With LLM)

```python
async def recall(thread_id: str, query: str) -> str:
    """
    Semantic search with LLM response.
    Uses memory="auto" for automatic context retrieval.
    Returns the LLM's response.
    """

async def get_restoration_context(
    thread_id: str,
    changes_summary: str
) -> str:
    """
    Generate a "welcome back" message based on stored context.
    """
```

## Error Handling

```python
class BackboardError(Exception):
    """Base exception for Backboard.io errors."""

class BackboardAuthError(BackboardError):
    """Authentication failed."""

class BackboardConnectionError(BackboardError):
    """Cannot reach Backboard.io."""

class BackboardRateLimitError(BackboardError):
    """Rate limited."""
```

## Retry Logic

- Retry on 5xx errors (max 3 attempts)
- Exponential backoff (1s, 2s, 4s)
- No retry on 4xx errors (client error)

## Requirements

### Functional

1. All functions must be async
2. Must handle network errors gracefully
3. Must validate responses
4. Must timeout after 30 seconds

### Non-Functional

- **Reliability**: Graceful degradation when unavailable
- **Security**: Never log API keys
- **Performance**: Connection pooling via httpx

## Dependencies

- httpx (async HTTP client)
- Standard library (os, datetime, json)
