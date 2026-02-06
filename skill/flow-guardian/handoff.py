#!/usr/bin/env python3
"""Handoff System for Flow Guardian (OpenClaw Edition).

YAML checkpoints that track session state, enabling seamless context restoration
across sessions. Writes to $WORKSPACE/memory/handoff.yaml where WORKSPACE
defaults to ~/.openclaw/workspace.

Core fields (always present):
- goal: What the user is trying to accomplish (shown in statusline)
- status: in_progress, completed, or blocked
- now: Current focus / what next session should do first (shown in statusline)
- timestamp: ISO 8601 format

Extended fields (optional, inspired by continuous-claude patterns):
- hypothesis: Current working theory
- outcome: SUCCEEDED, PARTIAL_PLUS, PARTIAL_MINUS, FAILED
- files: Files being worked on
- branch: Git branch name
- done_this_session: List of completed tasks with file references
- decisions: Key decisions with rationale
- findings: Key learnings/discoveries
- worked: Approaches that worked (repeat these)
- failed: Approaches that failed (avoid these)
- next: Ordered action items for next session
- blockers: Blocking issues
- test: Command to verify this work

Usage:
    python3 handoff.py save --goal "Implement JWT auth" --status in_progress --now "Debugging token expiry"
    python3 handoff.py save --goal "Fix auth" --now "Writing tests" --outcome SUCCEEDED --worked "TDD approach" --failed-approach "Mocking entire DB"
    python3 handoff.py load
    python3 handoff.py load --json
    python3 handoff.py update --now "Fix verified, writing tests" --status completed
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


# ============ CONSTANTS ============

VALID_STATUSES = {"in_progress", "completed", "blocked"}
VALID_OUTCOMES = {"SUCCEEDED", "PARTIAL_PLUS", "PARTIAL_MINUS", "FAILED"}


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

    # Validate required fields
    if not handoff_data.get("goal"):
        raise ValueError("Missing required field: goal")
    if not handoff_data.get("now"):
        raise ValueError("Missing required field: now")
    status = handoff_data.get("status")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}")

    # Validate outcome if provided
    outcome = handoff_data.get("outcome")
    if outcome and outcome not in VALID_OUTCOMES:
        raise ValueError(f"Invalid outcome '{outcome}'. Must be one of: {', '.join(sorted(VALID_OUTCOMES))}")

    # Reorder fields for readability: core fields first, then extended
    ordered = _order_handoff_fields(handoff_data)

    handoff_path = get_handoff_path()
    handoff_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically
    temp_path = handoff_path.with_suffix('.yaml.tmp')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                ordered,
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


def _order_handoff_fields(data: dict) -> dict:
    """Order handoff fields for readability."""
    # Desired field order: core fields first, then extended
    field_order = [
        "goal", "status", "now", "outcome", "branch", "timestamp",
        "hypothesis", "test",
        "done_this_session", "decisions", "findings",
        "worked", "failed",
        "files", "blockers", "next",
    ]
    ordered = {}
    for key in field_order:
        if key in data:
            ordered[key] = data[key]
    # Add any remaining fields not in the order list
    for key, val in data.items():
        if key not in ordered:
            ordered[key] = val
    return ordered


def update_handoff(updates: dict) -> dict:
    """
    Merge updates into existing handoff.
    Creates new handoff if none exists.

    For list fields (done_this_session, decisions, findings, worked, failed,
    files, blockers, next), new values are appended rather than replaced.
    Use _replace=True in updates dict to override this behavior.

    Args:
        updates: Dictionary of fields to update

    Returns:
        Updated handoff data
    """
    existing = load_handoff() or {}

    # List fields that should be appended rather than replaced
    append_fields = {"done_this_session", "decisions", "findings", "worked",
                     "failed", "blockers", "next"}

    replace_mode = updates.pop("_replace", False)

    merged = dict(existing)
    for key, val in updates.items():
        if key in append_fields and not replace_mode and key in existing:
            existing_val = existing[key]
            if isinstance(existing_val, list) and isinstance(val, list):
                merged[key] = existing_val + val
            else:
                merged[key] = val
        else:
            merged[key] = val

    # Defaults for new handoffs
    if not existing:
        merged.setdefault("goal", "Working on project")
        merged.setdefault("status", "in_progress")
        merged.setdefault("now", updates.get("goal", "Working on project"))

    save_handoff(merged)
    return merged


# ============ CLI ============

def _add_extended_args(parser):
    """Add extended handoff arguments to a parser."""
    parser.add_argument("--hypothesis", help="Current working hypothesis")
    parser.add_argument("--outcome", choices=sorted(VALID_OUTCOMES),
                        help="Session outcome: SUCCEEDED, PARTIAL_PLUS, PARTIAL_MINUS, FAILED")
    parser.add_argument("--files", help="Comma-separated list of files being worked on")
    parser.add_argument("--branch", help="Git branch name")
    parser.add_argument("--test", help="Command to verify this work (e.g. 'pytest tests/')")
    parser.add_argument("--done", action="append", metavar="TASK",
                        help="Task completed this session (repeatable, e.g. --done 'Fixed auth bug')")
    parser.add_argument("--done-files", action="append", metavar="FILES",
                        help="Files for the last --done entry (comma-separated)")
    parser.add_argument("--decision", action="append", metavar="NAME=RATIONALE",
                        help="Decision with rationale (repeatable, e.g. --decision 'use_jwt=Better for stateless APIs')")
    parser.add_argument("--finding", action="append", metavar="FINDING",
                        help="Key finding/learning (repeatable)")
    parser.add_argument("--worked", action="append", metavar="APPROACH",
                        help="Approach that worked (repeatable)")
    parser.add_argument("--failed-approach", action="append", metavar="APPROACH",
                        help="Approach that failed (repeatable)")
    parser.add_argument("--blocker", action="append", metavar="BLOCKER",
                        help="Blocking issue (repeatable)")
    parser.add_argument("--next-step", action="append", metavar="STEP",
                        help="Next action item (repeatable, ordered)")


def _extract_extended_data(args) -> dict:
    """Extract extended fields from parsed args into a data dict."""
    data = {}

    if getattr(args, 'hypothesis', None):
        data["hypothesis"] = args.hypothesis
    if getattr(args, 'outcome', None):
        data["outcome"] = args.outcome
    if getattr(args, 'files', None):
        data["files"] = [f.strip() for f in args.files.split(",")]
    if getattr(args, 'branch', None):
        data["branch"] = args.branch
    if getattr(args, 'test', None):
        data["test"] = args.test

    # Build done_this_session list
    done_tasks = getattr(args, 'done', None) or []
    done_files_list = getattr(args, 'done_files', None) or []
    if done_tasks:
        done_this_session = []
        for i, task in enumerate(done_tasks):
            entry = {"task": task}
            if i < len(done_files_list) and done_files_list[i]:
                entry["files"] = [f.strip() for f in done_files_list[i].split(",")]
            done_this_session.append(entry)
        data["done_this_session"] = done_this_session

    # Build decisions list
    decisions_raw = getattr(args, 'decision', None) or []
    if decisions_raw:
        decisions = []
        for d in decisions_raw:
            if "=" in d:
                name, rationale = d.split("=", 1)
                decisions.append({name.strip(): rationale.strip()})
            else:
                decisions.append(d)
        data["decisions"] = decisions

    # Simple list fields
    findings = getattr(args, 'finding', None)
    if findings:
        data["findings"] = findings

    worked = getattr(args, 'worked', None)
    if worked:
        data["worked"] = worked

    failed = getattr(args, 'failed_approach', None)
    if failed:
        data["failed"] = failed

    blockers = getattr(args, 'blocker', None)
    if blockers:
        data["blockers"] = blockers

    next_steps = getattr(args, 'next_step', None)
    if next_steps:
        data["next"] = next_steps

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Flow Guardian handoff management. Save/load/update session state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # save
    save_parser = subparsers.add_parser("save", help="Save a handoff checkpoint")
    save_parser.add_argument("--goal", "-g", required=True, help="Session goal (shown in statusline)")
    save_parser.add_argument("--status", "-s", choices=sorted(VALID_STATUSES), default="in_progress", help="Status")
    save_parser.add_argument("--now", "-n", required=True, help="Current focus / what next session should do (shown in statusline)")
    _add_extended_args(save_parser)

    # load
    load_parser = subparsers.add_parser("load", help="Load the current handoff")
    load_parser.add_argument("--json", "-j", action="store_true", help="Output as JSON instead of YAML")

    # update
    update_parser = subparsers.add_parser("update", help="Partially update the current handoff")
    update_parser.add_argument("--goal", "-g", help="Update goal")
    update_parser.add_argument("--status", "-s", choices=sorted(VALID_STATUSES), help="Update status")
    update_parser.add_argument("--now", "-n", help="Update current focus")
    update_parser.add_argument("--replace", action="store_true",
                               help="Replace list fields instead of appending")
    _add_extended_args(update_parser)

    args = parser.parse_args()

    if args.command == "save":
        data = {
            "goal": args.goal,
            "status": args.status,
            "now": args.now,
        }
        data.update(_extract_extended_data(args))

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
        if args.json:
            print(json.dumps(handoff, indent=2, default=str))
        else:
            print(yaml.safe_dump(handoff, default_flow_style=False, sort_keys=False), end="")

    elif args.command == "update":
        updates = {}
        if args.goal:
            updates["goal"] = args.goal
        if args.status:
            updates["status"] = args.status
        if args.now:
            updates["now"] = args.now
        if getattr(args, 'replace', False):
            updates["_replace"] = True

        updates.update(_extract_extended_data(args))

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
