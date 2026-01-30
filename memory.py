"""Local storage module for Flow Guardian.

Handles local file-based storage as a fallback when Backboard.io is unavailable.
All data is stored in ~/.flow-guardian/ directory.

Also supports dual-write to the vector store for semantic search when available.
"""
import json
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

# Lazy-loaded vector store components
_vector_store = None
_embeddings = None
_vector_write_enabled = None


# ============ CONFIGURATION ============

STORAGE_DIR = Path.home() / ".flow-guardian"
SESSIONS_DIR = STORAGE_DIR / "sessions"
CONFIG_FILE = STORAGE_DIR / "config.json"
SESSIONS_INDEX = SESSIONS_DIR / "index.json"
LEARNINGS_FILE = STORAGE_DIR / "learnings.json"


# ============ VECTOR STORE HELPERS ============

def _is_vector_write_enabled() -> bool:
    """Check if vector store dual-write is enabled."""
    global _vector_write_enabled
    if _vector_write_enabled is None:
        # Enable if USE_VECTOR_STORE=true or if embeddings are available
        env_val = os.environ.get("USE_VECTOR_STORE", "auto").lower()
        if env_val in ("true", "1", "yes"):
            _vector_write_enabled = True
        elif env_val in ("false", "0", "no"):
            _vector_write_enabled = False
        else:  # auto
            try:
                import embeddings
                _vector_write_enabled = embeddings.is_available()
            except ImportError:
                _vector_write_enabled = False
    return _vector_write_enabled


def _get_vector_store():
    """Get the vector store instance (lazy load)."""
    global _vector_store
    if _vector_store is None:
        try:
            import vector_storage
            _vector_store = vector_storage.get_store()
        except ImportError:
            _vector_store = False  # Mark as unavailable
    return _vector_store if _vector_store else None


def _get_embedding(text: str) -> list[float]:
    """Generate embedding for text (lazy load)."""
    global _embeddings
    if _embeddings is None:
        try:
            import embeddings as emb_module
            _embeddings = emb_module
        except ImportError:
            return []
    try:
        return _embeddings.get_embedding(text)
    except Exception:
        return []


def _store_to_vector(
    content: str,
    content_type: str,
    metadata: dict = None,
    memory_id: str = None,
    namespace: str = "personal",
) -> bool:
    """
    Store content to the vector store if available.

    Returns True if stored, False if not available or failed.
    """
    if not _is_vector_write_enabled():
        return False

    store = _get_vector_store()
    if store is None:
        return False

    try:
        embedding = _get_embedding(content)
        if not embedding:
            # Store without embedding (will use keyword search only)
            embedding = [0.0] * 768  # Zero vector

        store.store(
            content=content,
            embedding=embedding,
            namespace=namespace,
            content_type=content_type,
            metadata=metadata,
            memory_id=memory_id,
        )
        return True
    except Exception as e:
        print(f"Warning: Failed to store to vector store: {e}")
        return False


# ============ INITIALIZATION ============

def init_storage() -> None:
    """
    Initialize local storage directory structure.
    Creates all required directories and files if they don't exist.
    """
    # Create directories
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize config file
    if not CONFIG_FILE.exists():
        _atomic_write(CONFIG_FILE, {
            "user": os.environ.get("FLOW_GUARDIAN_USER", "unknown"),
            "backboard": {
                "personal_assistant_id": None,
                "personal_thread_id": None,
                "team_assistant_id": None,
                "team_thread_id": None,
            },
            "settings": {
                "auto_save": False,
                "default_tags": [],
            }
        })

    # Initialize sessions index
    if not SESSIONS_INDEX.exists():
        _atomic_write(SESSIONS_INDEX, [])

    # Initialize learnings file
    if not LEARNINGS_FILE.exists():
        _atomic_write(LEARNINGS_FILE, [])


# ============ ATOMIC FILE OPERATIONS ============

def _atomic_write(filepath: Path, data: dict | list) -> None:
    """
    Atomically write data to a JSON file.
    Writes to a temp file first, then renames to prevent corruption.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (ensures same filesystem for rename)
    fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=".tmp_",
        suffix=".json"
    )
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        # Atomic rename
        shutil.move(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _safe_read(filepath: Path, default: dict | list) -> dict | list:
    """
    Safely read a JSON file, returning default on error.
    """
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Log warning but don't crash
        print(f"Warning: Could not read {filepath}: {e}")
    return default


# ============ SESSION MANAGEMENT ============

def save_session(session: dict) -> str:
    """
    Save a session checkpoint to local storage.

    Also stores to vector store if available for semantic search.

    Args:
        session: Session data dictionary containing context, git state, etc.

    Returns:
        Session ID (format: session_YYYY-MM-DD_HH-MM-SS)
    """
    init_storage()

    # Generate session ID if not present
    timestamp = datetime.now()
    session_id = session.get("id") or f"session_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

    # Ensure required fields
    session["id"] = session_id
    session["timestamp"] = session.get("timestamp") or timestamp.isoformat()
    session["version"] = session.get("version", 1)

    # Write session file
    session_file = SESSIONS_DIR / f"{session_id}.json"
    _atomic_write(session_file, session)

    # Update index
    index = _safe_read(SESSIONS_INDEX, [])
    if not isinstance(index, list):
        index = []

    # Add to index (remove old entry if exists)
    index = [s for s in index if s.get("id") != session_id]
    context = session.get("context", {})
    git = session.get("git", {})
    summary = context.get("summary") or session.get("summary", "")
    branch = git.get("branch") or session.get("branch", "unknown")

    index.insert(0, {
        "id": session_id,
        "timestamp": session["timestamp"],
        "branch": branch,
        "summary": summary,
        "file": f"{session_id}.json"
    })

    _atomic_write(SESSIONS_INDEX, index)

    # Dual-write to vector store for semantic search
    if _is_vector_write_enabled():
        # Build content string for embedding
        content_parts = [f"**Session:** {summary}"]
        content_parts.append(f"Branch: {branch}")
        if context.get("decisions"):
            content_parts.append(f"Decisions: {', '.join(context['decisions'])}")
        if context.get("next_steps"):
            content_parts.append(f"Next steps: {', '.join(context['next_steps'])}")
        if context.get("blockers"):
            content_parts.append(f"Blockers: {', '.join(context['blockers'])}")

        _store_to_vector(
            content="\n".join(content_parts),
            content_type="session",
            metadata={
                "session_id": session_id,
                "branch": branch,
                "files": context.get("files", []),
                "tags": session.get("metadata", {}).get("tags", []),
            },
            memory_id=session_id,
        )

    return session_id


def load_session(session_id: str) -> Optional[dict]:
    """
    Load a specific session by ID.

    Args:
        session_id: The session identifier

    Returns:
        Session dictionary or None if not found
    """
    init_storage()

    session_file = SESSIONS_DIR / f"{session_id}.json"
    if session_file.exists():
        result = _safe_read(session_file, {})
        if isinstance(result, dict) and result:
            return result
    return None


def get_latest_session() -> Optional[dict]:
    """
    Get the most recent session checkpoint.

    Returns:
        Session dictionary or None if no sessions exist
    """
    init_storage()

    index = _safe_read(SESSIONS_INDEX, [])
    if not isinstance(index, list) or not index:
        return None

    # Index is sorted with most recent first
    latest = index[0]
    return load_session(latest.get("id", ""))


def list_sessions(limit: int = 10, branch: Optional[str] = None, full: bool = False) -> list[dict]:
    """
    List session summaries or full session data.

    Args:
        limit: Maximum number of sessions to return (default: 10)
        branch: Filter by branch name (optional)
        full: If True, return full session data instead of just summaries (default: False)

    Returns:
        List of session dictionaries (summaries or full data)
    """
    init_storage()

    index = _safe_read(SESSIONS_INDEX, [])
    if not isinstance(index, list):
        return []

    # Filter by branch if specified
    if branch:
        index = [s for s in index if s.get("branch") == branch]

    # Apply limit
    sessions = index[:limit]

    # If full data requested, load each session
    if full:
        full_sessions = []
        for summary in sessions:
            session_id = summary.get("id", "")
            full_data = load_session(session_id)
            if full_data:
                full_sessions.append(full_data)
            else:
                # Fallback to summary if full data not found
                full_sessions.append(summary)
        return full_sessions

    return sessions


# ============ LEARNINGS MANAGEMENT ============

def save_learning(learning: dict) -> str:
    """
    Save a learning to local storage.

    Also stores to vector store if available for semantic search.

    Args:
        learning: Learning data with text, tags, etc.

    Returns:
        Learning ID (format: learning_YYYY-MM-DD_HH-MM-SS)
    """
    init_storage()

    # Generate learning ID if not present
    timestamp = datetime.now()
    learning_id = learning.get("id") or f"learning_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

    # Ensure required fields
    learning["id"] = learning_id
    learning["timestamp"] = learning.get("timestamp") or timestamp.isoformat()
    learning["synced"] = learning.get("synced", False)

    # Load existing learnings
    learnings = _safe_read(LEARNINGS_FILE, [])
    if not isinstance(learnings, list):
        learnings = []

    # Add new learning at the beginning
    learnings.insert(0, learning)

    _atomic_write(LEARNINGS_FILE, learnings)

    # Dual-write to vector store for semantic search
    if _is_vector_write_enabled():
        insight = learning.get("insight") or learning.get("text", "")
        tags = learning.get("tags", [])
        is_team = learning.get("team", False) or learning.get("shared", False)

        content = f"**Learning:** {insight}"

        _store_to_vector(
            content=content,
            content_type="learning",
            metadata={
                "tags": tags,
                "author": learning.get("author"),
                "shared": is_team,
            },
            memory_id=learning_id,
            namespace="team" if is_team else "personal",
        )

    return learning_id


def search_learnings(query: str, tags: Optional[list[str]] = None) -> list[dict]:
    """
    Search learnings by keyword and/or tags.
    Uses simple keyword matching as fallback for semantic search.

    Args:
        query: Search query string
        tags: Optional list of tags to filter by

    Returns:
        List of matching learnings, sorted by relevance score
    """
    init_storage()

    learnings = _safe_read(LEARNINGS_FILE, [])
    if not isinstance(learnings, list):
        return []

    query_lower = query.lower()
    results = []

    for learning in learnings:
        score = 0

        # Score based on text match (check both "insight" and "text" fields)
        text = (learning.get("insight", "") or learning.get("text", "")).lower()
        if query_lower in text:
            score += 2

        # Score based on tag match
        learning_tags = learning.get("tags", [])
        if tags:
            # Filter by required tags
            if not all(t in learning_tags for t in tags):
                continue

        for tag in learning_tags:
            if query_lower in tag.lower():
                score += 1

        if score > 0:
            results.append((score, learning))

    # Sort by score descending, then by timestamp descending
    results.sort(key=lambda x: (x[0], x[1].get("timestamp", "")), reverse=True)

    return [learning for _, learning in results]


def get_all_learnings(team: Optional[bool] = None) -> list[dict]:
    """
    Get all learnings, optionally filtered by team flag.

    Args:
        team: If True, return only team learnings.
              If False, return only personal learnings.
              If None, return all learnings.

    Returns:
        List of learning dictionaries
    """
    init_storage()

    learnings = _safe_read(LEARNINGS_FILE, [])
    if not isinstance(learnings, list):
        return []

    if team is None:
        return learnings

    return [item for item in learnings if item.get("team", False) == team]


# ============ CONFIG MANAGEMENT ============

def get_config() -> dict:
    """
    Load and return user configuration.

    Returns:
        Configuration dictionary
    """
    init_storage()

    result = _safe_read(CONFIG_FILE, {})
    if isinstance(result, dict):
        return result
    return {}


def set_config(key: str, value) -> None:
    """
    Update a specific configuration value.
    Supports nested keys using dot notation (e.g., "backboard.personal_thread_id").

    Args:
        key: Configuration key (supports dot notation)
        value: Value to set
    """
    init_storage()

    config = get_config()

    # Handle nested keys
    keys = key.split(".")
    current = config
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]

    current[keys[-1]] = value

    _atomic_write(CONFIG_FILE, config)


# ============ STATISTICS ============

def get_stats() -> dict:
    """
    Get storage statistics.

    Returns:
        Dictionary with counts of sessions and learnings
    """
    init_storage()

    index = _safe_read(SESSIONS_INDEX, [])
    learnings = _safe_read(LEARNINGS_FILE, [])

    sessions_count = len(index) if isinstance(index, list) else 0
    learnings_list = learnings if isinstance(learnings, list) else []

    personal_learnings = len([item for item in learnings_list if not item.get("team", False)])
    team_learnings = len([item for item in learnings_list if item.get("team", False)])

    return {
        "sessions_count": sessions_count,
        "personal_learnings": personal_learnings,
        "team_learnings": team_learnings,
        "total_learnings": len(learnings_list),
    }
