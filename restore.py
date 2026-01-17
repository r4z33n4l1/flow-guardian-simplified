"""Context restoration module for Flow Guardian.

Handles change detection and restoration message generation.
"""
import subprocess
from datetime import datetime
from typing import Optional

import cerebras_client


# ============ HELPERS ============

def _run_git_command(args: list[str]) -> tuple[bool, str]:
    """
    Run a git command and return (success, output).
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, ""
    except FileNotFoundError:
        return False, ""


def _is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    success, _ = _run_git_command(["rev-parse", "--git-dir"])
    return success


# ============ TIME CALCULATIONS ============

def calculate_time_elapsed(timestamp: str) -> str:
    """
    Calculate human-readable time elapsed since timestamp.

    Args:
        timestamp: ISO 8601 timestamp string

    Returns:
        Human-readable duration (e.g., "2h 15m", "3 days")
    """
    try:
        # Parse timestamp
        if "T" in timestamp:
            checkpoint_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            checkpoint_time = datetime.fromisoformat(timestamp)

        # Make sure we compare naive datetimes
        if checkpoint_time.tzinfo is not None:
            checkpoint_time = checkpoint_time.replace(tzinfo=None)

        now = datetime.now()
        delta = now - checkpoint_time

        # Format the duration
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return "just now"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        else:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            if days == 1:
                return f"1 day {hours}h" if hours else "1 day"
            return f"{days} days"

    except (ValueError, TypeError):
        return "unknown time"


def is_session_stale(timestamp: str, threshold_days: int = 7) -> bool:
    """
    Check if a session is older than the threshold.

    Args:
        timestamp: ISO 8601 timestamp string
        threshold_days: Number of days after which session is considered stale

    Returns:
        True if session is stale
    """
    try:
        if "T" in timestamp:
            checkpoint_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            checkpoint_time = datetime.fromisoformat(timestamp)

        if checkpoint_time.tzinfo is not None:
            checkpoint_time = checkpoint_time.replace(tzinfo=None)

        delta = datetime.now() - checkpoint_time
        return delta.days >= threshold_days

    except (ValueError, TypeError):
        return False


# ============ CHANGE DETECTION ============

def get_changes_since(checkpoint_timestamp: str) -> dict:
    """
    Detect what changed since the checkpoint.

    Args:
        checkpoint_timestamp: ISO 8601 timestamp of the checkpoint

    Returns:
        Dictionary with:
        - elapsed: Human-readable time elapsed
        - commits: List of commit summaries since checkpoint
        - files_changed: List of files changed by commits
        - is_stale: Whether the session is >7 days old
    """
    elapsed = calculate_time_elapsed(checkpoint_timestamp)
    is_stale = is_session_stale(checkpoint_timestamp)

    if not _is_git_repo():
        return {
            "elapsed": elapsed,
            "commits": [],
            "files_changed": [],
            "is_stale": is_stale
        }

    # Get commits since the timestamp
    commits = []
    try:
        # Parse the timestamp for git log
        if "T" in checkpoint_timestamp:
            checkpoint_time = datetime.fromisoformat(
                checkpoint_timestamp.replace("Z", "+00:00")
            )
        else:
            checkpoint_time = datetime.fromisoformat(checkpoint_timestamp)

        if checkpoint_time.tzinfo is not None:
            checkpoint_time = checkpoint_time.replace(tzinfo=None)

        # Format for git: YYYY-MM-DD HH:MM:SS
        since_str = checkpoint_time.strftime("%Y-%m-%d %H:%M:%S")

        success, log_output = _run_git_command([
            "log", f"--since={since_str}", "--oneline", "-n", "20"
        ])

        if success and log_output:
            commits = log_output.split("\n")

    except (ValueError, TypeError):
        pass

    # Get files changed in those commits
    files_changed = []
    if commits:
        success, diff_output = _run_git_command([
            "diff", "--name-only", f"HEAD~{len(commits)}", "HEAD"
        ])
        if success and diff_output:
            files_changed = diff_output.split("\n")

    return {
        "elapsed": elapsed,
        "commits": commits,
        "files_changed": files_changed,
        "is_stale": is_stale
    }


def detect_conflicts(session: dict) -> list[str]:
    """
    Detect if current state conflicts with the checkpoint.

    Args:
        session: Session checkpoint data

    Returns:
        List of conflict descriptions
    """
    conflicts: list[str] = []

    if not _is_git_repo():
        return conflicts

    # Check branch mismatch
    checkpoint_branch = session.get("git", {}).get("branch")
    if checkpoint_branch:
        success, current_branch = _run_git_command([
            "rev-parse", "--abbrev-ref", "HEAD"
        ])
        if success and current_branch != checkpoint_branch:
            conflicts.append(
                f"Branch changed: was '{checkpoint_branch}', now '{current_branch}'"
            )

    # Check for uncommitted changes that might conflict
    checkpoint_files = set(session.get("git", {}).get("uncommitted_files", []))
    if checkpoint_files:
        success, status = _run_git_command(["status", "--porcelain"])
        if success and status:
            current_files = set()
            for line in status.split("\n"):
                if line.strip():
                    file_path = line[3:].strip()
                    if " -> " in file_path:
                        file_path = file_path.split(" -> ")[1]
                    current_files.add(file_path)

            # Files that were uncommitted before but now are different
            common_files = checkpoint_files & current_files
            if common_files:
                conflicts.append(
                    f"Files still uncommitted: {', '.join(list(common_files)[:3])}"
                )

    return conflicts


def get_current_branch() -> Optional[str]:
    """Get the current git branch name."""
    if not _is_git_repo():
        return None
    success, branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return branch if success else None


# ============ RESTORATION MESSAGE ============

def generate_restoration_message(session: dict, changes: dict) -> str:
    """
    Generate a "welcome back" message using Cerebras.

    Args:
        session: Session checkpoint data
        changes: Changes detected since checkpoint

    Returns:
        Natural language restoration message
    """
    # Build context from session
    context = {
        "summary": session.get("context", {}).get("summary", "unknown"),
        "hypothesis": session.get("context", {}).get("hypothesis"),
        "files": session.get("context", {}).get("files", []),
        "branch": session.get("git", {}).get("branch", "unknown"),
        "learnings": [
            item.get("text", item) if isinstance(item, dict) else item
            for item in session.get("learnings", [])
        ],
    }

    try:
        return cerebras_client.generate_restoration_message(context, changes)
    except cerebras_client.CerebrasError:
        # Fallback message
        return _build_fallback_message(session, changes)


def _build_fallback_message(session: dict, changes: dict) -> str:
    """
    Build a basic restoration message when Cerebras is unavailable.
    """
    context = session.get("context", {})
    git = session.get("git", {})

    lines = []
    lines.append("Welcome back!")
    lines.append("")

    # What you were working on
    summary = context.get("summary")
    if summary:
        lines.append(f"You were working on: {summary}")

    # Hypothesis
    hypothesis = context.get("hypothesis")
    if hypothesis:
        lines.append(f"Your approach: {hypothesis}")

    # Branch and files
    branch = git.get("branch")
    if branch:
        lines.append(f"Branch: {branch}")

    files = context.get("files", [])
    if files:
        lines.append(f"Key files: {', '.join(files[:5])}")

    # Time away
    elapsed = changes.get("elapsed", "unknown")
    lines.append(f"Time away: {elapsed}")

    # Changes
    commits = changes.get("commits", [])
    if commits:
        lines.append(f"New commits: {len(commits)}")

    files_changed = changes.get("files_changed", [])
    if files_changed:
        lines.append(f"Files changed: {len(files_changed)}")

    # Next steps
    next_steps = context.get("next_steps", [])
    if next_steps:
        lines.append("")
        lines.append("Suggested next steps:")
        for step in next_steps[:3]:
            lines.append(f"  - {step}")

    return "\n".join(lines)


def build_raw_context(session: dict, changes: dict) -> str:
    """
    Build raw markdown context for piping to Claude.

    Args:
        session: Session checkpoint data
        changes: Changes detected since checkpoint

    Returns:
        Markdown-formatted context string
    """
    context = session.get("context", {})
    git = session.get("git", {})
    learnings = session.get("learnings", [])

    lines = []

    # Session context
    lines.append("## Session Context")
    lines.append("")
    lines.append(f"**Working on:** {context.get('summary', 'unknown')}")

    hypothesis = context.get("hypothesis")
    if hypothesis:
        lines.append(f"**Hypothesis:** {hypothesis}")

    files = context.get("files", [])
    if files:
        lines.append(f"**Files:** {', '.join(files)}")

    branch = git.get("branch")
    if branch:
        lines.append(f"**Branch:** {branch}")

    lines.append("")

    # Previous learnings
    if learnings:
        lines.append("## Previous Learnings")
        lines.append("")
        for learning in learnings:
            if isinstance(learning, dict):
                text = learning.get("text", "")
                tags = learning.get("tags", [])
                if tags:
                    lines.append(f"- {text} (tags: {', '.join(tags)})")
                else:
                    lines.append(f"- {text}")
            else:
                lines.append(f"- {learning}")
        lines.append("")

    # Changes since last session
    lines.append("## Changes Since Last Session")
    lines.append("")
    lines.append(f"**Time away:** {changes.get('elapsed', 'unknown')}")

    commits = changes.get("commits", [])
    if commits:
        lines.append(f"**New commits:** {len(commits)}")
        for commit in commits[:5]:
            lines.append(f"  - {commit}")

    files_changed = changes.get("files_changed", [])
    if files_changed:
        lines.append(f"**Files changed:** {', '.join(files_changed[:10])}")

    lines.append("")

    # Next steps
    next_steps = context.get("next_steps", [])
    if next_steps:
        lines.append("## Suggested Next Steps")
        lines.append("")
        for step in next_steps:
            lines.append(f"- {step}")

    return "\n".join(lines)
