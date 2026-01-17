"""Parse Claude Code session files for insight extraction.

Reads JSONL session transcripts and extracts conversation content
for analysis by Cerebras.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Iterator, Optional


# Claude Code stores sessions here
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def get_project_dir(cwd: str) -> Path:
    """Convert a working directory to its Claude Code project path."""
    # Claude uses path with dashes instead of slashes
    project_name = cwd.replace("/", "-")
    if project_name.startswith("-"):
        project_name = project_name  # Keep leading dash
    return CLAUDE_PROJECTS_DIR / project_name


def get_sessions_index(project_dir: Path) -> dict:
    """Read the sessions index for a project."""
    index_path = project_dir / "sessions-index.json"
    if index_path.exists():
        with open(index_path) as f:
            return json.load(f)
    return {}


def get_active_session(project_dir: Path) -> Optional[str]:
    """Get the most recently modified session ID."""
    jsonl_files = list(project_dir.glob("*.jsonl"))
    if not jsonl_files:
        return None
    # Sort by modification time, newest first
    jsonl_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return jsonl_files[0].stem


def get_session_path(project_dir: Path, session_id: str) -> Path:
    """Get the path to a session's JSONL file."""
    return project_dir / f"{session_id}.jsonl"


def parse_session_messages(session_path: Path, since_line: int = 0) -> Iterator[dict]:
    """
    Parse messages from a session file.

    Args:
        session_path: Path to the JSONL session file
        since_line: Skip lines before this (for incremental reading)

    Yields:
        Message dicts with role, content, timestamp
    """
    if not session_path.exists():
        return

    with open(session_path) as f:
        for i, line in enumerate(f):
            if i < since_line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Skip non-message entries
            if entry.get("type") not in ("user", "assistant"):
                # Check if it has a message field
                if "message" not in entry:
                    continue

            message = entry.get("message", {})
            role = message.get("role") or entry.get("type")

            if role not in ("user", "assistant"):
                continue

            # Extract content
            content = message.get("content", "")
            if isinstance(content, list):
                # Handle structured content (text blocks, tool_use, etc.)
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            # Summarize tool use
                            tool_name = block.get("name", "unknown")
                            text_parts.append(f"[Used tool: {tool_name}]")
                        elif block.get("type") == "tool_result":
                            # Skip detailed tool results
                            pass
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)

            if not content or not content.strip():
                continue

            yield {
                "line": i,
                "role": role,
                "content": content,
                "session_id": entry.get("sessionId"),
                "cwd": entry.get("cwd"),
                "branch": entry.get("gitBranch"),
            }


def get_conversation_text(session_path: Path, since_line: int = 0, max_chars: int = 50000) -> tuple[str, int]:
    """
    Get conversation as plain text for analysis.

    Args:
        session_path: Path to session JSONL
        since_line: Start from this line
        max_chars: Maximum characters to return

    Returns:
        Tuple of (conversation_text, last_line_processed)
    """
    lines = []
    last_line = since_line
    total_chars = 0

    for msg in parse_session_messages(session_path, since_line):
        role = "Human" if msg["role"] == "user" else "Assistant"
        text = f"{role}: {msg['content'][:2000]}"  # Truncate long messages

        if total_chars + len(text) > max_chars:
            break

        lines.append(text)
        total_chars += len(text)
        last_line = msg["line"]

    return "\n\n".join(lines), last_line


def find_all_sessions(cwd: str) -> list[dict]:
    """Find all sessions for a project directory."""
    project_dir = get_project_dir(cwd)
    if not project_dir.exists():
        return []

    sessions = []
    for jsonl_file in project_dir.glob("*.jsonl"):
        stat = jsonl_file.stat()
        sessions.append({
            "session_id": jsonl_file.stem,
            "path": jsonl_file,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "size": stat.st_size,
        })

    sessions.sort(key=lambda s: s["modified"], reverse=True)
    return sessions


def get_current_session_for_cwd(cwd: str = None) -> Optional[Path]:
    """Get the current/most recent session for a working directory."""
    if cwd is None:
        cwd = os.getcwd()

    project_dir = get_project_dir(cwd)
    if not project_dir.exists():
        return None

    session_id = get_active_session(project_dir)
    if not session_id:
        return None

    return get_session_path(project_dir, session_id)
