"""Context capture module for Flow Guardian.

Handles git state extraction and context analysis via Cerebras.
"""
import subprocess
from datetime import datetime
from typing import Optional

import cerebras_client


# ============ GIT STATE EXTRACTION ============

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


def is_git_repo() -> bool:
    """
    Check if current directory is a git repository.
    """
    success, _ = _run_git_command(["rev-parse", "--git-dir"])
    return success


def capture_git_state() -> dict:
    """
    Capture current git repository state.

    Returns:
        Dictionary with:
        - branch: Current branch name
        - uncommitted_files: List of modified/staged files
        - recent_commits: List of recent commit messages
        - last_commit: Most recent commit (hash + message)
        - is_git: Whether this is a git repo
    """
    if not is_git_repo():
        return {
            "is_git": False,
            "branch": None,
            "uncommitted_files": [],
            "recent_commits": [],
            "last_commit": None
        }

    # Get current branch
    success, branch = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if not success:
        branch = "unknown"

    # Get uncommitted files (staged + unstaged)
    uncommitted_files = []
    success, status_output = _run_git_command(["status", "--porcelain"])
    if success and status_output:
        for line in status_output.split("\n"):
            if line.strip():
                # Format: "XY filename" where XY is status code
                file_path = line[3:].strip()
                # Handle renamed files (old -> new)
                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1]
                uncommitted_files.append(file_path)

    # Get recent commits (last 5)
    recent_commits = []
    success, log_output = _run_git_command([
        "log", "--oneline", "-n", "5", "--format=%h %s"
    ])
    if success and log_output:
        recent_commits = log_output.split("\n")

    # Get last commit details
    last_commit = None
    success, commit_output = _run_git_command([
        "log", "-1", "--format=%H|%s"
    ])
    if success and commit_output and "|" in commit_output:
        parts = commit_output.split("|", 1)
        last_commit = {
            "hash": parts[0],
            "message": parts[1] if len(parts) > 1 else ""
        }

    return {
        "is_git": True,
        "branch": branch,
        "uncommitted_files": uncommitted_files,
        "recent_commits": recent_commits,
        "last_commit": last_commit
    }


def get_diff_summary() -> str:
    """
    Get a summary of uncommitted changes.

    Returns:
        String summary of changes (stats format)
    """
    if not is_git_repo():
        return ""

    # Get diff stat for staged changes
    success, staged_diff = _run_git_command(["diff", "--cached", "--stat"])

    # Get diff stat for unstaged changes
    success2, unstaged_diff = _run_git_command(["diff", "--stat"])

    parts = []
    if staged_diff:
        parts.append(f"Staged:\n{staged_diff}")
    if unstaged_diff:
        parts.append(f"Unstaged:\n{unstaged_diff}")

    return "\n".join(parts) if parts else "No changes"


def get_detailed_diff(max_lines: int = 100) -> str:
    """
    Get detailed diff of uncommitted changes.

    Args:
        max_lines: Maximum lines to return (to limit context)

    Returns:
        String diff output
    """
    if not is_git_repo():
        return ""

    # Get combined diff (staged + unstaged)
    success, diff_output = _run_git_command(["diff", "HEAD"])

    if not success or not diff_output:
        return ""

    # Limit output to max_lines
    lines = diff_output.split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append(f"\n... (truncated, {len(lines)} more lines)")

    return "\n".join(lines)


# ============ CONTEXT ANALYSIS ============

def analyze_context(
    git_state: dict,
    user_message: Optional[str] = None
) -> dict:
    """
    Analyze session context using Cerebras.

    Args:
        git_state: Git state from capture_git_state()
        user_message: Optional user-provided message/note

    Returns:
        Dictionary with analyzed context:
        - summary: One-sentence description
        - hypothesis: Current theory/approach
        - next_steps: List of likely next actions
        - decisions: Key decisions made
        - learnings: Insights discovered
        - files: Relevant files (from git state)
    """
    branch = git_state.get("branch", "unknown")
    files = git_state.get("uncommitted_files", [])
    diff_summary = get_diff_summary()

    try:
        # Use Cerebras to analyze the context
        analysis = cerebras_client.analyze_session_context(
            branch=branch,
            files=files,
            diff_summary=diff_summary,
            user_message=user_message
        )

        # Add files to the analysis
        analysis["files"] = files

        return analysis

    except cerebras_client.CerebrasError:
        # Fallback if Cerebras is unavailable
        return {
            "summary": user_message or f"Working on branch {branch}",
            "hypothesis": None,
            "next_steps": [],
            "decisions": [],
            "learnings": [],
            "files": files,
        }


# ============ SESSION BUILDER ============

def build_session(
    user_message: Optional[str] = None,
    tags: Optional[list[str]] = None
) -> dict:
    """
    Build a complete session checkpoint.

    Args:
        user_message: Optional user-provided message/note
        tags: Optional list of tags

    Returns:
        Complete session dictionary ready for storage
    """
    timestamp = datetime.now()
    session_id = f"session_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

    # Capture git state
    git_state = capture_git_state()

    # Analyze context
    context = analyze_context(git_state, user_message)

    # Build session object
    session = {
        "id": session_id,
        "timestamp": timestamp.isoformat(),
        "version": 1,
        "context": {
            "summary": context.get("summary"),
            "hypothesis": context.get("hypothesis"),
            "files": context.get("files", []),
            "next_steps": context.get("next_steps", []),
        },
        "decisions": context.get("decisions", []),
        "learnings": context.get("learnings", []),
        "git": {
            "branch": git_state.get("branch"),
            "uncommitted_files": git_state.get("uncommitted_files", []),
            "last_commit": git_state.get("last_commit"),
        },
        "metadata": {
            "message": user_message,
            "tags": tags or [],
            "trigger": "manual",
        }
    }

    return session
