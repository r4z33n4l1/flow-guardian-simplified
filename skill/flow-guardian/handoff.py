#!/usr/bin/env python3
"""Handoff System for Flow Guardian (OpenClaw Edition).

YAML checkpoints that track session state, enabling seamless context restoration
across sessions. Writes to $WORKSPACE/memory/handoff.yaml where WORKSPACE
defaults to ~/.openclaw/workspace.

The handoff file contains:
- goal: What the user is trying to accomplish
- status: in_progress, completed, or blocked
- now: Current focus/activity
- hypothesis: Current working theory (optional)
- outcome: Result of hypothesis testing (optional)
- files: Files being worked on (optional)
- branch: Git branch name (optional)
- timestamp: ISO 8601 format

Usage:
    python3 handoff.py save --goal "Implement JWT auth" --status in_progress --now "Debugging token expiry"
    python3 handoff.py load
    python3 handoff.py update --now "Fix verified, writing tests" --status completed
"""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


# ============ CONSTANTS ============

VALID_STATUSES = {"in_progress", "completed", "blocked"}


# ============ PATH RESOLUTION ============

def get_workspace() -> Path:
    """Get the OpenClaw workspace directory."""
    workspace = os.environ.get("WORKSPACE") or os.environ.get("OPENCLAW_WORKSPACE")
    if workspace:
        return Path(workspace)
    return Path.home() / ".openclaw" / "workspace"


def get_handoff_path() -> Path:
    """Get path to handoff.yaml in the workspace memory directory."""
    return get_workspace() / "memory" / "handoff.yaml"


# ============ CORE FUNCTIONS ============

def load_handoff() -> dict | None:
    """
    Load handoff.yaml from workspace.

    Returns:
        Dictionary with handoff data, or None if file doesn't exist.
    """
    handoff_path = get_handoff_path()

    if not handoff_path.exists():
        return None

    try:
        with open(handoff_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data if data else None
    except (PermissionError, yaml.YAMLError) as e:
        print(f"Error loading handoff: {e}", file=sys.stderr)
        return None


def save_handoff(data: dict) -> Path:
    """
    Save handoff data to handoff.yaml.
    Validates required fields. Creates directories as needed.

    Args:
        data: Handoff data (must include goal, status, now)

    Returns:
        Path to saved file

    Raises:
        ValueError: If required fields are missing or invalid
    """
    handoff_data = dict(data)

    # Auto-generate timestamp
    handoff_data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Validate
    if not handoff_data.get("goal"):
        raise ValueError("Missing required field: goal")
    if not handoff_data.get("now"):
        raise ValueError("Missing required field: now")
    status = handoff_data.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")

    handoff_path = get_handoff_path()
    handoff_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically
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
        temp_path.replace(handoff_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise

    return handoff_path


def update_handoff(updates: dict) -> dict:
    """
    Merge updates into existing handoff.
    Creates new handoff if none exists.

    Args:
        updates: Dictionary of fields to update

    Returns:
        Updated handoff data
    """
    existing = load_handoff() or {}
    merged = {**existing, **updates}

    # Defaults for new handoffs
    if not existing:
        merged.setdefault("goal", "Working on project")
        merged.setdefault("status", "in_progress")
        merged.setdefault("now", updates.get("goal", "Working on project"))

    save_handoff(merged)
    return merged


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(
        description="Flow Guardian handoff management. Save/load/update session state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # save
    save_parser = subparsers.add_parser("save", help="Save a handoff checkpoint")
    save_parser.add_argument("--goal", "-g", required=True, help="Session goal")
    save_parser.add_argument("--status", "-s", choices=sorted(VALID_STATUSES), default="in_progress", help="Status")
    save_parser.add_argument("--now", "-n", required=True, help="Current focus")
    save_parser.add_argument("--hypothesis", help="Current working hypothesis")
    save_parser.add_argument("--outcome", help="Outcome of hypothesis testing")
    save_parser.add_argument("--files", help="Comma-separated list of files being worked on")
    save_parser.add_argument("--branch", help="Git branch name")

    # load
    subparsers.add_parser("load", help="Load the current handoff")

    # update
    update_parser = subparsers.add_parser("update", help="Partially update the current handoff")
    update_parser.add_argument("--goal", "-g", help="Update goal")
    update_parser.add_argument("--status", "-s", choices=sorted(VALID_STATUSES), help="Update status")
    update_parser.add_argument("--now", "-n", help="Update current focus")
    update_parser.add_argument("--hypothesis", help="Update hypothesis")
    update_parser.add_argument("--outcome", help="Update outcome")
    update_parser.add_argument("--files", help="Update files (comma-separated)")
    update_parser.add_argument("--branch", help="Update branch")

    args = parser.parse_args()

    if args.command == "save":
        data = {
            "goal": args.goal,
            "status": args.status,
            "now": args.now,
        }
        if args.hypothesis:
            data["hypothesis"] = args.hypothesis
        if args.outcome:
            data["outcome"] = args.outcome
        if args.files:
            data["files"] = [f.strip() for f in args.files.split(",")]
        if args.branch:
            data["branch"] = args.branch

        try:
            path = save_handoff(data)
            print(f"Handoff saved to {path}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "load":
        handoff = load_handoff()
        if handoff is None:
            print("No handoff found.", file=sys.stderr)
            sys.exit(1)
        print(yaml.safe_dump(handoff, default_flow_style=False, sort_keys=False), end="")

    elif args.command == "update":
        updates = {}
        if args.goal:
            updates["goal"] = args.goal
        if args.status:
            updates["status"] = args.status
        if args.now:
            updates["now"] = args.now
        if args.hypothesis:
            updates["hypothesis"] = args.hypothesis
        if args.outcome:
            updates["outcome"] = args.outcome
        if args.files:
            updates["files"] = [f.strip() for f in args.files.split(",")]
        if args.branch:
            updates["branch"] = args.branch

        if not updates:
            print("No updates provided.", file=sys.stderr)
            sys.exit(1)

        try:
            result = update_handoff(updates)
            print(yaml.safe_dump(result, default_flow_style=False, sort_keys=False), end="")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
