"""Handoff System for Flow Guardian.

YAML checkpoints that track session state, enabling seamless context restoration
across sessions. The handoff file (.flow-guardian/handoff.yaml) contains:
- goal: What the user is trying to accomplish
- status: in_progress, completed, or blocked
- now: Current focus/activity
- hypothesis: Current working theory (optional)
- outcome: Result of hypothesis testing (optional)
- files: Files being worked on (optional)
- branch: Git branch name (optional)
- timestamp: ISO 8601 format
- session_id: For daemon tracking (optional)
"""
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import yaml


# ============ CONSTANTS ============

FLOW_GUARDIAN_DIR = ".flow-guardian"
HANDOFF_FILE = "handoff.yaml"
VALID_STATUSES = {"in_progress", "completed", "blocked"}

logger = logging.getLogger(__name__)


# ============ EXCEPTIONS ============

class HandoffError(Exception):
    """Base exception for handoff-related errors."""
    pass


class HandoffValidationError(HandoffError):
    """Raised when handoff data fails validation."""
    pass


# ============ PROJECT ROOT DETECTION ============

def find_project_root(cwd: Optional[str] = None) -> Path:
    """
    Find project root by looking for .flow-guardian/, .git/, or pyproject.toml.
    Returns current directory if none found.

    Args:
        cwd: Starting directory (defaults to current working directory)

    Returns:
        Path to project root directory
    """
    start_path = Path(cwd) if cwd else Path.cwd()
    start_path = start_path.resolve()

    # Walk up the directory tree
    current = start_path
    while True:
        # Check for project markers in priority order
        if (current / FLOW_GUARDIAN_DIR).is_dir():
            return current
        if (current / ".git").is_dir():
            return current
        if (current / "pyproject.toml").is_file():
            return current

        # Move to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root, return original directory
            return start_path
        current = parent


def get_handoff_path(project_root: Optional[Path] = None) -> Path:
    """
    Get path to handoff.yaml for a project.
    Returns .flow-guardian/handoff.yaml relative to project root.

    Args:
        project_root: Project root path (auto-detected if None)

    Returns:
        Path to handoff.yaml file
    """
    if project_root is None:
        project_root = find_project_root()
    return project_root / FLOW_GUARDIAN_DIR / HANDOFF_FILE


# ============ CORE FUNCTIONS ============

def load_handoff(project_root: Optional[Path] = None) -> Optional[dict]:
    """
    Load handoff.yaml from project.
    Returns None if file doesn't exist.
    Creates .flow-guardian/ directory if missing.

    Args:
        project_root: Project root path (auto-detected if None)

    Returns:
        Dictionary with handoff data, or None if file doesn't exist

    Raises:
        HandoffError: On permission errors or invalid YAML
    """
    if project_root is None:
        project_root = find_project_root()

    handoff_path = get_handoff_path(project_root)
    flow_guardian_dir = handoff_path.parent

    # Create .flow-guardian/ directory if missing
    try:
        flow_guardian_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise HandoffError(f"Permission denied creating {flow_guardian_dir}: {e}")

    # Return None if handoff file doesn't exist
    if not handoff_path.exists():
        return None

    # Load and parse YAML
    try:
        with open(handoff_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Handle empty file case
            if data is None:
                return None
            return data
    except PermissionError as e:
        raise HandoffError(f"Permission denied reading {handoff_path}: {e}")
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML in {handoff_path}: {e}")
        return None


def _validate_handoff(data: dict) -> None:
    """
    Validate required fields for saving handoff.

    Args:
        data: Handoff data to validate

    Raises:
        HandoffValidationError: If required fields are missing or invalid
    """
    # Check required fields exist and are non-empty strings
    if not data.get("goal") or not isinstance(data["goal"], str):
        raise HandoffValidationError("Missing or empty required field: goal")

    if not data.get("now") or not isinstance(data["now"], str):
        raise HandoffValidationError("Missing or empty required field: now")

    # Validate status
    status = data.get("status")
    if status is None:
        raise HandoffValidationError("Missing required field: status")
    if status not in VALID_STATUSES:
        raise HandoffValidationError(
            f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )


def save_handoff(data: dict, project_root: Optional[Path] = None) -> Path:
    """
    Save handoff data to handoff.yaml.
    Validates required fields.
    Creates directories as needed.

    Args:
        data: Handoff data to save (must include goal, status, now)
        project_root: Project root path (auto-detected if None)

    Returns:
        Path to saved file

    Raises:
        HandoffValidationError: If required fields missing or invalid
        HandoffError: On permission errors
    """
    if project_root is None:
        project_root = find_project_root()

    # Make a copy to avoid modifying original
    handoff_data = dict(data)

    # Auto-generate timestamp if missing
    if "timestamp" not in handoff_data or not handoff_data["timestamp"]:
        handoff_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Validate required fields
    _validate_handoff(handoff_data)

    handoff_path = get_handoff_path(project_root)
    flow_guardian_dir = handoff_path.parent

    # Create directory if needed
    try:
        flow_guardian_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        raise HandoffError(f"Permission denied creating {flow_guardian_dir}: {e}")

    # Write YAML atomically (write to temp, then rename)
    temp_path = handoff_path.with_suffix('.yaml.tmp')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                handoff_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
        # Atomic rename
        temp_path.replace(handoff_path)
    except PermissionError as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise HandoffError(f"Permission denied writing {handoff_path}: {e}")
    except Exception as e:
        # Clean up temp file if it exists
        if temp_path.exists():
            temp_path.unlink()
        raise HandoffError(f"Error writing handoff file: {e}")

    return handoff_path


def update_handoff(updates: dict, project_root: Optional[Path] = None) -> dict:
    """
    Merge updates into existing handoff.
    Creates new handoff if none exists.
    Always updates timestamp.

    Args:
        updates: Dictionary of fields to update
        project_root: Project root path (auto-detected if None)

    Returns:
        Updated handoff data

    Raises:
        HandoffValidationError: If resulting handoff is invalid
        HandoffError: On permission errors
    """
    if project_root is None:
        project_root = find_project_root()

    # Load existing handoff or start fresh
    existing = load_handoff(project_root) or {}

    # Merge updates into existing
    merged = {**existing, **updates}

    # Always update timestamp
    merged["timestamp"] = datetime.now(timezone.utc).isoformat()

    # If creating a new handoff and missing required fields, provide defaults
    if not existing:
        if "goal" not in merged:
            merged["goal"] = "Working on project"
        if "status" not in merged:
            merged["status"] = "in_progress"
        if "now" not in merged:
            merged["now"] = updates.get("goal", "Working on project")

    # Save (will validate)
    save_handoff(merged, project_root)

    return merged


def clear_handoff(project_root: Optional[Path] = None) -> bool:
    """
    Delete the handoff file.

    Args:
        project_root: Project root path (auto-detected if None)

    Returns:
        True if file was deleted, False if it didn't exist

    Raises:
        HandoffError: On permission errors
    """
    if project_root is None:
        project_root = find_project_root()

    handoff_path = get_handoff_path(project_root)

    if not handoff_path.exists():
        return False

    try:
        handoff_path.unlink()
        return True
    except PermissionError as e:
        raise HandoffError(f"Permission denied deleting {handoff_path}: {e}")
