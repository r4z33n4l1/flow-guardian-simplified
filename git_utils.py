"""Shared git utilities for Flow Guardian.

Provides common git operations used by capture.py and restore.py.
"""
import subprocess
from typing import Optional


def run_git_command(args: list[str], timeout: int = 10) -> tuple[bool, str]:
    """
    Run a git command and return (success, output).

    Args:
        args: List of git command arguments (without 'git' prefix)
        timeout: Command timeout in seconds (default: 10)

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, ""
    except FileNotFoundError:
        return False, ""


def is_git_repo() -> bool:
    """
    Check if current directory is a git repository.

    Returns:
        True if in a git repository, False otherwise
    """
    success, _ = run_git_command(["rev-parse", "--git-dir"])
    return success


def get_current_branch() -> Optional[str]:
    """
    Get the current git branch name.

    Returns:
        Branch name if in a git repo, None otherwise
    """
    if not is_git_repo():
        return None
    success, branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    return branch if success else None


def get_uncommitted_files() -> list[str]:
    """
    Get list of uncommitted files (staged + unstaged).

    Returns:
        List of file paths with uncommitted changes
    """
    if not is_git_repo():
        return []

    uncommitted_files = []
    success, status_output = run_git_command(["status", "--porcelain"])
    if success and status_output:
        for line in status_output.split("\n"):
            if line.strip():
                # Format: "XY filename" where XY is status code
                file_path = line[3:].strip()
                # Handle renamed files (old -> new)
                if " -> " in file_path:
                    file_path = file_path.split(" -> ")[1]
                uncommitted_files.append(file_path)

    return uncommitted_files
