# Spec: Memory Module (`memory.py`)

## Overview

The memory module handles local storage and serves as a fallback when Backboard.io is unavailable. It manages sessions and learnings in a local file structure.

## Storage Location

```
~/.flow-guardian/
├── config.json          # User config (assistant IDs, settings)
├── sessions/
│   ├── index.json       # Session index for quick listing
│   └── session_*.json   # Individual session files
└── learnings.json       # Local learnings store
```

## Data Structures

### config.json
```json
{
  "user": "mike",
  "backboard": {
    "personal_assistant_id": "...",
    "personal_thread_id": "...",
    "team_assistant_id": "...",
    "team_thread_id": "..."
  },
  "settings": {
    "auto_save": false,
    "default_tags": []
  }
}
```

### sessions/index.json
```json
{
  "sessions": [
    {
      "id": "session_2026-01-17_10-30-00",
      "timestamp": "2026-01-17T10:30:00Z",
      "branch": "fix/jwt-expiry",
      "summary": "Debugging JWT token expiry",
      "file": "session_2026-01-17_10-30-00.json"
    }
  ]
}
```

### learnings.json
```json
{
  "learnings": [
    {
      "id": "learning_001",
      "timestamp": "2026-01-17T10:45:00Z",
      "text": "JWT tokens use UTC timestamps",
      "tags": ["jwt", "auth"],
      "team": false,
      "synced": true
    }
  ]
}
```

## API

### Session Management

```python
def init_storage() -> None:
    """Initialize local storage directory structure."""

def save_session(session: dict) -> str:
    """Save a session checkpoint locally. Returns session ID."""

def load_session(session_id: str) -> dict | None:
    """Load a specific session by ID."""

def get_latest_session() -> dict | None:
    """Get the most recent session."""

def list_sessions(limit: int = 10, branch: str = None) -> list[dict]:
    """List sessions, optionally filtered by branch."""
```

### Learnings Management

```python
def save_learning(learning: dict) -> str:
    """Save a learning locally. Returns learning ID."""

def search_learnings(query: str, tags: list = None) -> list[dict]:
    """Search learnings by keyword/tags."""

def get_all_learnings(team: bool = None) -> list[dict]:
    """Get all learnings, optionally filtered by team flag."""
```

### Config Management

```python
def get_config() -> dict:
    """Load user config."""

def set_config(key: str, value: any) -> None:
    """Update a config value."""
```

## Requirements

### Functional

1. All operations must be atomic (no partial writes)
2. Must handle concurrent access gracefully
3. Must validate data before writing
4. Must create directories if they don't exist

### Non-Functional

- **Performance**: All operations <100ms
- **Reliability**: Never corrupt existing data on failure
- **Compatibility**: JSON format for easy debugging/editing

## Edge Cases

- First run: Create all directories/files
- Corrupted file: Log warning, return empty/default
- Disk full: Raise clear error
- Permission denied: Raise clear error

## Dependencies

- Standard library only (json, pathlib, datetime)
