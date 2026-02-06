#!/usr/bin/env python3
"""Git state capture for Flow Guardian (OpenClaw Edition).

Captures current git repository state and outputs JSON to stdout.
Uses subprocess for git commands — no external dependencies.

Output includes:
- branch: Current branch name
- uncommitted_files: Modified/staged files
- last_commit_files: Files changed in last commit (fallback when tree is clean)
- recent_commits: Last 5 commit summaries
- last_commit: Most recent commit hash + message
- diff_summary: Stat output for staged + unstaged changes
- is_git: Whether this is a git repo

Usage:
    python3 git_capture.py                     # capture from cwd
    python3 git_capture.py --repo /path/to/repo
    python3 git_capture.py --compact            # minimal output
"""
import argparse
import json
import os
import subprocess
import sys


def run_git(args: list[str], cwd: str = None, timeout: int = 10) -> tuple[bool, str]:
    """
    Run a git command and return (success, output).

    Args:
        args: Git subcommand arguments (without 'git' prefix)
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout_stripped)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def is_git_repo(cwd: str = None) -> bool:
    """Check if directory is inside a git repository."""
    success, _ = run_git(["rev-parse", "--git-dir"], cwd=cwd)
    return success


def capture_git_state(cwd: str = None) -> dict:
    """
    Capture current git repository state.

    Args:
        cwd: Working directory (defaults to current directory)

    Returns:
        Dictionary with git state information
    """
    if not is_git_repo(cwd):
        return {
            "is_git": False,
            "branch": None,
            "uncommitted_files": [],
            "last_commit_files": [],
            "recent_commits": [],
            "last_commit": None,
            "diff_summary": "",
        }

    # Current branch
    success, branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    if not success:
        branch = "unknown"

    # Uncommitted files (staged + unstaged)
    uncommitted_files = []
    success, status_output = run_git(["status", "--porcelain"], cwd=cwd)
    if success and status_output:
        for line in status_output.split("\n"):
            if line.strip():
                parts = line.split(maxsplit=1)
                if len(parts) >= 2:
                    file_path = parts[1].strip()
                else:
                    file_path = parts[0].strip()
                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1]
                uncommitted_files.append(file_path)

    # Recent commits (last 5)
    recent_commits = []
    success, log_output = run_git(
        ["log", "--oneline", "-n", "5", "--format=%h %s"], cwd=cwd
    )
    if success and log_output:
        recent_commits = [line for line in log_output.split("\n") if line.strip()]

    # Last commit details
    last_commit = None
    success, commit_output = run_git(
        ["log", "-1", "--format=%H|%s"], cwd=cwd
    )
    if success and commit_output and "|" in commit_output:
        parts = commit_output.split("|", 1)
        last_commit = {
            "hash": parts[0],
            "message": parts[1] if len(parts) > 1 else "",
        }

    # Files from last commit (fallback when tree is clean)
    last_commit_files = []
    if not uncommitted_files:
        success, files_output = run_git(
            ["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=cwd
        )
        if success and files_output:
            last_commit_files = [f.strip() for f in files_output.split("\n") if f.strip()]

    # Diff summary
    diff_parts = []
    success, staged_diff = run_git(["diff", "--cached", "--stat"], cwd=cwd)
    if success and staged_diff:
        diff_parts.append(f"Staged:\n{staged_diff}")

    success, unstaged_diff = run_git(["diff", "--stat"], cwd=cwd)
    if success and unstaged_diff:
        diff_parts.append(f"Unstaged:\n{unstaged_diff}")

    diff_summary = "\n".join(diff_parts) if diff_parts else ""

    return {
        "is_git": True,
        "branch": branch,
        "uncommitted_files": uncommitted_files,
        "last_commit_files": last_commit_files,
        "recent_commits": recent_commits,
        "last_commit": last_commit,
        "diff_summary": diff_summary,
    }


def format_pretty(state: dict) -> str:
    """Format git state as human-readable text."""
    if not state.get("is_git"):
        return "Not a git repository."

    lines = []
    branch = state.get("branch", "unknown")
    lines.append(f"🌿 Branch: {branch}")

    last_commit = state.get("last_commit")
    if last_commit:
        short_hash = last_commit["hash"][:8]
        lines.append(f"📌 Last commit: {short_hash} {last_commit['message']}")

    uncommitted = state.get("uncommitted_files", [])
    if uncommitted:
        lines.append(f"\n📝 Uncommitted files ({len(uncommitted)}):")
        for f in uncommitted:
            lines.append(f"   • {f}")
    else:
        lines.append("\n✅ Working tree clean")

    last_commit_files = state.get("last_commit_files", [])
    if last_commit_files:
        lines.append(f"\n📦 Last commit files ({len(last_commit_files)}):")
        for f in last_commit_files:
            lines.append(f"   • {f}")

    diff_summary = state.get("diff_summary", "")
    if diff_summary:
        lines.append(f"\n📊 Diff summary:")
        for line in diff_summary.split("\n"):
            lines.append(f"   {line}")

    recent = state.get("recent_commits", [])
    if recent:
        lines.append(f"\n🕐 Recent commits:")
        for commit in recent:
            lines.append(f"   {commit}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Capture git repository state. Outputs JSON to stdout."
    )
    parser.add_argument(
        "--repo", "-r",
        default=None,
        help="Path to git repository (default: current directory)"
    )
    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Compact JSON output (no indentation)"
    )
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Human-readable formatted output instead of JSON"
    )

    args = parser.parse_args()

    cwd = args.repo or os.getcwd()

    state = capture_git_state(cwd)

    if args.pretty:
        print(format_pretty(state))
    else:
        indent = None if args.compact else 2
        print(json.dumps(state, indent=indent))


if __name__ == "__main__":
    main()
