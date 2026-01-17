#!/usr/bin/env python3
"""Flow Guardian Daemon - Automatic context capture from Claude Code sessions.

Watches Claude Code session files and automatically extracts insights,
storing them to Backboard.io for infinite memory.
"""
import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Import our modules
import session_parser
import cerebras_client
import backboard_client
from backboard_client import BackboardError


# ============ CONFIGURATION ============

DAEMON_STATE_DIR = Path.home() / ".flow-guardian" / "daemon"
PID_FILE = DAEMON_STATE_DIR / "daemon.pid"
STATE_FILE = DAEMON_STATE_DIR / "state.json"
LOG_FILE = DAEMON_STATE_DIR / "daemon.log"

# How often to check for new messages (seconds)
POLL_INTERVAL = 10

# Minimum messages before extracting insights
MIN_MESSAGES_BATCH = 5

# Maximum time between extractions (seconds)
MAX_EXTRACTION_INTERVAL = 300  # 5 minutes

# Maximum conversation chunk size for Cerebras
MAX_CHUNK_CHARS = 30000


# ============ LOGGING ============

def log(message: str):
    """Write to daemon log file."""
    DAEMON_STATE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    # Also print if running in foreground
    if sys.stdout.isatty():
        print(line, end="")


# ============ STATE MANAGEMENT ============

def load_state() -> dict:
    """Load daemon state (tracks processed lines per session)."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "sessions": {},  # session_id -> {"last_line": N, "last_extraction": timestamp}
        "started_at": None,
        "extractions_count": 0,
    }


def save_state(state: dict):
    """Save daemon state."""
    DAEMON_STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


# ============ INSIGHT EXTRACTION ============

EXTRACTION_PROMPT = """Analyze this Claude Code conversation and extract key insights.

Focus on:
1. LEARNINGS - Technical discoveries, solutions found, "aha" moments
2. DECISIONS - Architectural choices, approach decisions, tradeoffs made
3. CONTEXT - What the user is working on, their goals, current state

For each insight, provide:
- A concise statement (1-2 sentences)
- Category: learning, decision, or context

Format as JSON array:
[
  {{"category": "learning", "insight": "..."}},
  {{"category": "decision", "insight": "..."}},
  {{"category": "context", "insight": "..."}}
]

Only extract genuinely useful insights. Skip trivial interactions.
If no significant insights, return empty array: []

CONVERSATION:
{conversation}
"""


def _extract_json_from_response(response: str) -> list:
    """Extract JSON array from response, handling markdown wrapping."""
    import re

    # Try direct parse first
    try:
        result = json.loads(response)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code_block_match:
        try:
            result = json.loads(code_block_match.group(1))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Try to find array in response
    array_match = re.search(r'\[[\s\S]*\]', response)
    if array_match:
        try:
            result = json.loads(array_match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


async def extract_insights(conversation_text: str) -> list[dict]:
    """Use Cerebras to extract insights from conversation."""
    if not conversation_text.strip():
        return []

    try:
        prompt = EXTRACTION_PROMPT.format(conversation=conversation_text[:MAX_CHUNK_CHARS])
        response = cerebras_client.complete(
            prompt=prompt,
            system="You are an expert at identifying key technical insights from conversations. Output valid JSON only.",
            json_mode=True,
            max_tokens=2000
        )

        # Parse JSON response with robust extraction
        insights = _extract_json_from_response(response)

        # Validate that each insight is a dict with required fields
        valid_insights = []
        for item in insights:
            if isinstance(item, dict) and "insight" in item:
                valid_insights.append({
                    "category": item.get("category", "learning"),
                    "insight": item.get("insight", "")
                })

        if valid_insights:
            return valid_insights
        elif response:
            log(f"No valid insights from response: {response[:100]}")
        return []

    except Exception as e:
        import traceback
        log(f"Error extracting insights: {type(e).__name__}: {e}")
        log(f"Traceback: {traceback.format_exc()[:500]}")

    return []


async def store_insights(insights: list[dict], session_id: str, cwd: str):
    """Store extracted insights to Backboard."""
    thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
    if not thread_id:
        log("No BACKBOARD_PERSONAL_THREAD_ID, skipping cloud storage")
        return

    for insight in insights:
        category = insight.get("category", "learning")
        text = insight.get("insight", "")

        if not text:
            continue

        try:
            content = f"**{category.title()}** (auto-captured): {text}"
            metadata = {
                "type": f"auto_{category}",
                "source": "daemon",
                "session_id": session_id,
                "cwd": cwd,
                "timestamp": datetime.now().isoformat(),
            }
            await backboard_client.store_message(thread_id, content, metadata)
            log(f"Stored {category}: {text[:50]}...")

        except BackboardError as e:
            log(f"Failed to store insight: {e}")


# ============ SESSION WATCHING ============

async def process_session(session_path: Path, state: dict) -> bool:
    """
    Process new messages in a session file.

    Returns True if insights were extracted.
    """
    session_id = session_path.stem

    # Get tracking state for this session
    session_state = state["sessions"].get(session_id, {
        "last_line": 0,
        "last_extraction": None,
        "pending_messages": 0,
    })

    last_line = session_state.get("last_line", 0)
    last_extraction = session_state.get("last_extraction")
    pending = session_state.get("pending_messages", 0)

    # Get new conversation text
    conversation, new_last_line = session_parser.get_conversation_text(
        session_path,
        since_line=last_line,
        max_chars=MAX_CHUNK_CHARS
    )

    if new_last_line <= last_line:
        return False  # No new messages

    # Count new messages
    new_messages = new_last_line - last_line
    pending += new_messages

    # Update state
    session_state["last_line"] = new_last_line
    session_state["pending_messages"] = pending
    state["sessions"][session_id] = session_state

    # Decide if we should extract
    time_since_extraction = float("inf")
    if last_extraction:
        try:
            last_dt = datetime.fromisoformat(last_extraction)
            time_since_extraction = (datetime.now() - last_dt).total_seconds()
        except (ValueError, TypeError):
            pass

    should_extract = (
        pending >= MIN_MESSAGES_BATCH or
        time_since_extraction >= MAX_EXTRACTION_INTERVAL
    )

    if not should_extract:
        log(f"Session {session_id[:8]}: {pending} pending messages, waiting for batch")
        save_state(state)
        return False

    # Extract insights
    log(f"Session {session_id[:8]}: Extracting insights from {pending} messages...")

    # Get more context for extraction (not just since last line)
    full_conversation, _ = session_parser.get_conversation_text(
        session_path,
        since_line=max(0, new_last_line - 50),  # Get last 50 messages for context
        max_chars=MAX_CHUNK_CHARS
    )

    insights = await extract_insights(full_conversation)

    if insights:
        # Get cwd from session for metadata
        cwd = None
        for msg in session_parser.parse_session_messages(session_path, 0):
            cwd = msg.get("cwd")
            if cwd:
                break

        await store_insights(insights, session_id, cwd or "unknown")
        log(f"Extracted {len(insights)} insights from session {session_id[:8]}")
        state["extractions_count"] = state.get("extractions_count", 0) + 1

        # Update handoff.yaml with latest insight
        try:
            import handoff
            # Get the most recent insight to update "now" field
            latest_insight = insights[-1] if insights else None
            if latest_insight and cwd:
                handoff.update_handoff({
                    "now": latest_insight.get("insight", "Working on project"),
                    "session_id": session_id,
                }, project_root=Path(cwd) if cwd else None)
        except Exception as e:
            log(f"Could not update handoff.yaml: {e}")

    # Update extraction time
    session_state["last_extraction"] = datetime.now().isoformat()
    session_state["pending_messages"] = 0
    state["sessions"][session_id] = session_state
    save_state(state)

    return len(insights) > 0


async def watch_sessions():
    """Main daemon loop - watch all Claude Code sessions."""
    state = load_state()
    state["started_at"] = datetime.now().isoformat()
    save_state(state)

    log("Daemon started, watching for Claude Code sessions...")

    while True:
        try:
            # Find all project directories
            if not session_parser.CLAUDE_PROJECTS_DIR.exists():
                await asyncio.sleep(POLL_INTERVAL)
                continue

            for project_dir in session_parser.CLAUDE_PROJECTS_DIR.iterdir():
                if not project_dir.is_dir():
                    continue

                # Find most recent session
                session_id = session_parser.get_active_session(project_dir)
                if not session_id:
                    continue

                session_path = session_parser.get_session_path(project_dir, session_id)
                if session_path.exists():
                    await process_session(session_path, state)

        except Exception as e:
            log(f"Error in watch loop: {e}")

        await asyncio.sleep(POLL_INTERVAL)


# ============ DAEMON CONTROL ============

def is_running() -> Optional[int]:
    """Check if daemon is running, return PID if so."""
    if not PID_FILE.exists():
        return None

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())

        # Check if process exists
        os.kill(pid, 0)
        return pid

    except (ValueError, ProcessLookupError, PermissionError):
        # PID file exists but process doesn't
        PID_FILE.unlink(missing_ok=True)
        return None


def start_daemon(foreground: bool = False):
    """Start the daemon."""
    if is_running():
        print("Daemon is already running")
        return False

    DAEMON_STATE_DIR.mkdir(parents=True, exist_ok=True)

    if foreground:
        # Run in foreground
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        def cleanup(sig, frame):
            PID_FILE.unlink(missing_ok=True)
            log("Daemon stopped")
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        try:
            asyncio.run(watch_sessions())
        finally:
            PID_FILE.unlink(missing_ok=True)
    else:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent
            print(f"Daemon started with PID {pid}")
            return True

        # Child - become session leader
        os.setsid()

        # Fork again to prevent zombie
        pid = os.fork()
        if pid > 0:
            sys.exit(0)

        # Write PID file
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

        # Redirect stdout/stderr to log
        sys.stdout = open(LOG_FILE, "a")
        sys.stderr = sys.stdout

        def cleanup(sig, frame):
            PID_FILE.unlink(missing_ok=True)
            log("Daemon stopped")
            sys.exit(0)

        signal.signal(signal.SIGTERM, cleanup)

        try:
            asyncio.run(watch_sessions())
        finally:
            PID_FILE.unlink(missing_ok=True)

    return True


def stop_daemon():
    """Stop the daemon."""
    pid = is_running()
    if not pid:
        print("Daemon is not running")
        return False

    try:
        os.kill(pid, signal.SIGTERM)
        # Wait for it to stop
        for _ in range(10):
            time.sleep(0.5)
            if not is_running():
                print("Daemon stopped")
                return True
        print("Daemon did not stop gracefully, forcing...")
        os.kill(pid, signal.SIGKILL)
        PID_FILE.unlink(missing_ok=True)
        return True

    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        print("Daemon was not running")
        return False


def daemon_status() -> dict:
    """Get daemon status."""
    pid = is_running()
    state = load_state()

    status = {
        "running": pid is not None,
        "pid": pid,
        "started_at": state.get("started_at"),
        "extractions_count": state.get("extractions_count", 0),
        "sessions_tracked": len(state.get("sessions", {})),
    }

    if LOG_FILE.exists():
        # Get last few log lines
        with open(LOG_FILE) as f:
            lines = f.readlines()
            status["recent_logs"] = [l.strip() for l in lines[-5:]]

    return status


# ============ CLI ============

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flow Guardian Daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "foreground"])
    args = parser.parse_args()

    if args.command == "start":
        start_daemon(foreground=False)
    elif args.command == "foreground":
        start_daemon(foreground=True)
    elif args.command == "stop":
        stop_daemon()
    elif args.command == "status":
        status = daemon_status()
        if status["running"]:
            print(f"Daemon is running (PID: {status['pid']})")
            print(f"Started: {status['started_at']}")
            print(f"Extractions: {status['extractions_count']}")
            print(f"Sessions tracked: {status['sessions_tracked']}")
            if status.get("recent_logs"):
                print("\nRecent logs:")
                for log_line in status["recent_logs"]:
                    print(f"  {log_line}")
        else:
            print("Daemon is not running")
