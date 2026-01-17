"""Local storage module for Flow Guardian.

Handles local file-based storage as a fallback when Backboard.io is unavailable.
All data is stored in ~/.flow-guardian/ directory.
"""
import json
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


# ============ CONFIGURATION ============

STORAGE_DIR = Path.home() / ".flow-guardian"
SESSIONS_DIR = STORAGE_DIR / "sessions"
CONFIG_FILE = STORAGE_DIR / "config.json"
SESSIONS_INDEX = SESSIONS_DIR / "index.json"
LEARNINGS_FILE = STORAGE_DIR / "learnings.json"


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
    index.insert(0, {
        "id": session_id,
        "timestamp": session["timestamp"],
        "branch": session.get("git", {}).get("branch") or session.get("branch", "unknown"),
        "summary": session.get("context", {}).get("summary") or session.get("summary", ""),
        "file": f"{session_id}.json"
    })

    _atomic_write(SESSIONS_INDEX, index)

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


def list_sessions(limit: int = 10, branch: Optional[str] = None) -> list[dict]:
    """
    List session summaries.

    Args:
        limit: Maximum number of sessions to return (default: 10)
        branch: Filter by branch name (optional)

    Returns:
        List of session summary dictionaries
    """
    init_storage()

    index = _safe_read(SESSIONS_INDEX, [])
    if not isinstance(index, list):
        return []

    # Filter by branch if specified
    if branch:
        index = [s for s in index if s.get("branch") == branch]

    # Apply limit
    return index[:limit]


# ============ LEARNINGS MANAGEMENT ============

def save_learning(learning: dict) -> str:
    """
    Save a learning to local storage.

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
