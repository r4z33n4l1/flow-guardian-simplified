# Handoff System Specification

## Overview

YAML checkpoints that track session state, enabling seamless context restoration across sessions.

---

## File Location

```
.flow-guardian/handoff.yaml   # Per-project, in project root
```

---

## Schema

```yaml
# .flow-guardian/handoff.yaml
goal: "Implement user authentication with JWT"
status: in_progress  # in_progress | completed | blocked
now: "Debugging token expiry in auth.py"
hypothesis: "Off-by-one error in timestamp comparison"
outcome: null  # null until resolved, then "success" or description
files:
  - src/auth.py
  - tests/test_auth.py
branch: fix/jwt-expiry
timestamp: 2026-01-17T10:30:00Z
session_id: "abc123"  # Claude Code session ID
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `goal` | string | Yes | What the user is trying to accomplish |
| `status` | enum | Yes | `in_progress`, `completed`, `blocked` |
| `now` | string | Yes | Current focus/activity |
| `hypothesis` | string | No | Current working theory |
| `outcome` | string | No | Result of hypothesis testing |
| `files` | list[string] | No | Files being worked on |
| `branch` | string | No | Git branch name |
| `timestamp` | datetime | Yes | ISO 8601 format |
| `session_id` | string | No | For daemon tracking |

---

## Module: `handoff.py`

### Functions

```python
def find_project_root(cwd: str = None) -> Path:
    """
    Find project root by looking for .flow-guardian/, .git/, or pyproject.toml.
    Returns current directory if none found.
    """

def get_handoff_path(project_root: Path = None) -> Path:
    """
    Get path to handoff.yaml for a project.
    Returns .flow-guardian/handoff.yaml relative to project root.
    """

def load_handoff(project_root: Path = None) -> dict | None:
    """
    Load handoff.yaml from project.
    Returns None if file doesn't exist.
    Creates .flow-guardian/ directory if missing.
    """

def save_handoff(data: dict, project_root: Path = None) -> Path:
    """
    Save handoff data to handoff.yaml.
    Validates required fields.
    Creates directories as needed.
    Returns path to saved file.
    """

def update_handoff(updates: dict, project_root: Path = None) -> dict:
    """
    Merge updates into existing handoff.
    Creates new handoff if none exists.
    Always updates timestamp.
    Returns updated handoff data.
    """
```

### Validation

Required fields for save:
- `goal` (non-empty string)
- `status` (one of: `in_progress`, `completed`, `blocked`)
- `now` (non-empty string)
- `timestamp` (auto-generated if missing)

---

## Auto-Update Triggers

### 1. Manual Save (`flow save`)
```python
# In flow_cli.py save command
handoff.save_handoff({
    "goal": analyzed_context.get("summary", user_message),
    "status": "in_progress",
    "now": user_message or "Working on project",
    "hypothesis": analyzed_context.get("hypothesis"),
    "files": git_state.get("uncommitted_files", []),
    "branch": git_state.get("branch"),
    "timestamp": datetime.now().isoformat(),
})
```

### 2. Daemon Extraction
```python
# In daemon.py after extracting insights
handoff.update_handoff({
    "now": latest_insight.get("insight"),
    "session_id": session_id,
})
```

### 3. PreCompact Hook
```python
# Hook calls: flow inject --save-state
# Before context compaction, save current working state
```

---

## Error Handling

- Invalid YAML: Log warning, return None (don't crash)
- Missing directory: Auto-create `.flow-guardian/`
- Permission errors: Raise with clear message
- Validation failure: Raise ValueError with missing field

---

## Testing

```python
def test_load_nonexistent():
    """Returns None for missing file."""

def test_save_creates_directory():
    """Creates .flow-guardian/ if missing."""

def test_save_validates_required():
    """Raises ValueError if required fields missing."""

def test_update_merges():
    """Merges updates into existing handoff."""

def test_find_project_root_git():
    """Finds .git directory as project root."""

def test_find_project_root_flow_guardian():
    """Finds .flow-guardian as project root marker."""
```
