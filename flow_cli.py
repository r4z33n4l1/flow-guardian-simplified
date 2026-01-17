#!/usr/bin/env python3
"""Flow Guardian - CLI for persistent AI coding session memory.

"Claude forgets. Flow Guardian remembers."
"""
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

import capture
import memory
import restore
import backboard_client
from backboard_client import BackboardError, BackboardAuthError

# Load environment variables
load_dotenv()

# Rich console for beautiful output
console = Console()


# ============ CLI SETUP ============

@click.group()
@click.version_option(version="0.1.0", prog_name="flow-guardian")
def cli():
    """Flow Guardian - Persistent memory for AI coding sessions.

    "Claude forgets. Flow Guardian remembers."
    """
    pass


# ============ SAVE COMMAND ============

@cli.command()
@click.option("-m", "--message", help="Add a manual note to the checkpoint")
@click.option("-t", "--tag", multiple=True, help="Add tags for organization (repeatable)")
@click.option("-q", "--quiet", is_flag=True, help="Minimal output")
def save(message: Optional[str], tag: tuple, quiet: bool):
    """Save current session context to memory.

    Captures git state, analyzes context with AI, and stores
    to Backboard.io (or local fallback).

    Examples:
        flow save
        flow save -m "Debugging JWT expiry"
        flow save -t auth -t urgent
    """
    tags = list(tag)

    if not quiet:
        console.print("[dim]Capturing context...[/dim]")

    try:
        # Build session checkpoint
        session = capture.build_session(
            user_message=message,
            tags=tags
        )

        # Store locally first (always works)
        session_id = memory.save_session(session)

        # Try to store to Backboard.io
        backboard_stored = False
        thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")

        if thread_id:
            try:
                backboard_client.run_async(
                    backboard_client.store_session(thread_id, session)
                )
                backboard_stored = True
            except BackboardError:
                if not quiet:
                    console.print("[yellow]Backboard unavailable, using local storage[/yellow]")

        # Update handoff.yaml for seamless context restoration
        try:
            import handoff
            context = session.get("context", {})
            git = session.get("git", {})
            handoff.save_handoff({
                "goal": context.get("summary", message or "Working on project"),
                "status": "in_progress",
                "now": message or "Working on project",
                "hypothesis": context.get("hypothesis"),
                "files": git.get("uncommitted_files", []),
                "branch": git.get("branch"),
                "session_id": session_id,
            })
        except Exception as e:
            # Don't fail the save command if handoff update fails
            if not quiet:
                console.print(f"[dim]Note: Could not update handoff.yaml: {e}[/dim]")

        if quiet:
            console.print(session_id)
        else:
            _display_save_confirmation(session, backboard_stored)

    except Exception as e:
        console.print(f"[red]Error saving session: {e}[/red]")
        sys.exit(1)


def _display_save_confirmation(session: dict, backboard_stored: bool):
    """Display a beautiful confirmation panel for save."""
    context = session.get("context", {})
    git = session.get("git", {})
    metadata = session.get("metadata", {})

    lines = []

    # Summary
    summary = context.get("summary", "Context saved")
    lines.append(f"[bold]{summary}[/bold]")
    lines.append("")

    # Hypothesis
    hypothesis = context.get("hypothesis")
    if hypothesis:
        lines.append(f"[dim]Hypothesis:[/dim] {hypothesis}")

    # Files
    files = context.get("files", [])
    if files:
        lines.append(f"[dim]Files:[/dim] {', '.join(files[:5])}")

    # Branch
    branch = git.get("branch")
    if branch:
        lines.append(f"[dim]Branch:[/dim] {branch}")

    # Tags
    tags = metadata.get("tags", [])
    if tags:
        lines.append(f"[dim]Tags:[/dim] {', '.join(tags)}")

    lines.append("")

    # Storage status
    storage = "Backboard.io + local" if backboard_stored else "local"
    lines.append(f"[dim]Stored:[/dim] {storage}")
    lines.append(f"[dim]ID:[/dim] {session.get('id')}")

    panel = Panel(
        "\n".join(lines),
        title="[green]Context Saved[/green]",
        border_style="green"
    )
    console.print(panel)


# ============ RESUME COMMAND ============

@cli.command()
@click.option("-s", "--session", "session_id", help="Resume a specific session by ID")
@click.option("-p", "--pick", is_flag=True, help="Interactive session picker")
@click.option("--raw", is_flag=True, help="Output raw context for piping")
@click.option("--copy", "copy_to_clipboard", is_flag=True, help="Copy to clipboard")
def resume(session_id: Optional[str], pick: bool, raw: bool, copy_to_clipboard: bool):
    """Restore context from a previous session.

    Loads the checkpoint, detects what changed while you were away,
    and generates a helpful "welcome back" message.

    Examples:
        flow resume
        flow resume -s session_2026-01-17_10-30-00
        flow resume --pick
        flow resume --raw | claude
    """
    try:
        # Get the session to restore
        session = None

        if pick:
            session = _interactive_session_picker()
        elif session_id:
            session = memory.load_session(session_id)
            if not session:
                console.print(f"[red]Session not found: {session_id}[/red]")
                sys.exit(1)
        else:
            session = memory.get_latest_session()

        if not session:
            console.print("[yellow]No saved sessions found.[/yellow]")
            console.print("Get started with: [bold]flow save[/bold]")
            return

        # Detect changes since checkpoint
        timestamp = session.get("timestamp", "")
        changes = restore.get_changes_since(timestamp)

        # Detect conflicts
        conflicts = restore.detect_conflicts(session)

        if raw:
            # Output raw context for piping
            output = restore.build_raw_context(session, changes)
            console.print(output)
            return

        # Generate restoration message
        restoration_msg = restore.generate_restoration_message(session, changes)

        if copy_to_clipboard:
            try:
                import subprocess
                process = subprocess.Popen(
                    ['pbcopy'] if sys.platform == 'darwin' else ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE
                )
                process.communicate(restoration_msg.encode())
                console.print("[green]Copied to clipboard![/green]")
            except Exception:
                console.print("[yellow]Could not copy to clipboard[/yellow]")

        _display_resume_panel(session, changes, conflicts, restoration_msg)

    except Exception as e:
        console.print(f"[red]Error resuming session: {e}[/red]")
        sys.exit(1)


def _interactive_session_picker() -> Optional[dict]:
    """Show an interactive picker for sessions."""
    sessions = memory.list_sessions(limit=10)

    if not sessions:
        return None

    console.print("\n[bold]Recent Sessions:[/bold]\n")

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=3)
    table.add_column("Time")
    table.add_column("Branch")
    table.add_column("Summary")

    for i, s in enumerate(sessions, 1):
        timestamp = s.get("timestamp", "")
        elapsed = restore.calculate_time_elapsed(timestamp) if timestamp else "?"
        table.add_row(
            str(i),
            elapsed + " ago",
            s.get("branch", "?"),
            s.get("summary", "")[:50]
        )

    console.print(table)
    console.print()

    choice = Prompt.ask("Select session", default="1")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(sessions):
            return memory.load_session(sessions[idx].get("id", ""))
    except ValueError:
        pass

    return None


def _display_resume_panel(session: dict, changes: dict, conflicts: list, message: str):
    """Display a beautiful welcome back panel."""
    lines = []

    # Warnings
    if changes.get("is_stale"):
        lines.append("[yellow]Warning: This session is >7 days old. Context may be stale.[/yellow]")
        lines.append("")

    if conflicts:
        for conflict in conflicts:
            lines.append(f"[yellow]Warning: {conflict}[/yellow]")
        lines.append("")

    # Main message
    lines.append(message)

    panel = Panel(
        "\n".join(lines),
        title="[blue]Welcome Back[/blue]",
        border_style="blue"
    )
    console.print(panel)


# ============ LEARN COMMAND ============

@cli.command()
@click.argument("text")
@click.option("-t", "--tag", multiple=True, help="Add tags (repeatable)")
@click.option("--team", is_flag=True, help="Share with team")
def learn(text: str, tag: tuple, team: bool):
    """Store a learning or insight.

    Examples:
        flow learn "JWT tokens use UTC timestamps, not local time"
        flow learn "Redis SCAN is better than KEYS" --tag redis --tag performance
        flow learn "Cache invalidation needs events" --team
    """
    if not text.strip():
        console.print("[red]Learning text cannot be empty[/red]")
        sys.exit(1)

    if len(text) > 500:
        console.print("[yellow]Warning: Learning is quite long (>500 chars)[/yellow]")

    tags = list(tag)
    author = os.environ.get("FLOW_GUARDIAN_USER", "unknown")

    try:
        # Build learning object
        learning = {
            "text": text,
            "tags": tags,
            "team": team,
            "author": author,
        }

        # Store locally
        memory.save_learning(learning)

        # Try to store to Backboard.io
        backboard_stored = False
        thread_id = os.environ.get(
            "BACKBOARD_TEAM_THREAD_ID" if team else "BACKBOARD_PERSONAL_THREAD_ID"
        )

        if thread_id:
            try:
                if team:
                    backboard_client.run_async(
                        backboard_client.store_team_learning(
                            thread_id, text, author, tags
                        )
                    )
                else:
                    backboard_client.run_async(
                        backboard_client.store_learning(
                            thread_id, text, tags, author
                        )
                    )
                backboard_stored = True
            except BackboardError:
                pass

        _display_learning_confirmation(text, tags, team, author, backboard_stored)

    except Exception as e:
        console.print(f"[red]Error storing learning: {e}[/red]")
        sys.exit(1)


def _display_learning_confirmation(text: str, tags: list, team: bool, author: str, backboard_stored: bool):
    """Display confirmation for stored learning."""
    lines = []
    lines.append(f'[bold]"{text}"[/bold]')
    lines.append("")

    if tags:
        lines.append(f"[dim]Tags:[/dim] {', '.join(tags)}")

    scope = "team" if team else "personal"
    lines.append(f"[dim]Scope:[/dim] {scope}")

    if team:
        lines.append(f"[dim]Author:[/dim] {author}")

    title = "[green]Team Learning Stored[/green]" if team else "[green]Learning Stored[/green]"
    panel = Panel("\n".join(lines), title=title, border_style="green")
    console.print(panel)


# ============ RECALL COMMAND ============

@cli.command()
@click.argument("query")
@click.option("-t", "--tag", multiple=True, help="Filter by tags")
@click.option("--limit", default=10, help="Limit results (default: 10)")
def recall(query: str, tag: tuple, limit: int):
    """Search your stored learnings and context.

    Uses semantic search when Backboard.io is available,
    falls back to keyword search locally.

    Examples:
        flow recall "authentication"
        flow recall "how to fix token expiry" --tag auth
    """
    if len(query) < 2:
        console.print("[red]Query must be at least 2 characters[/red]")
        sys.exit(1)

    tags = list(tag)

    try:
        results = []
        used_backboard = False

        # Try Backboard.io first
        thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
        if thread_id:
            try:
                response = backboard_client.run_async(
                    backboard_client.recall(thread_id, query)
                )
                if response:
                    results = [{"type": "recall", "content": response}]
                    used_backboard = True
            except BackboardError:
                pass

        # Fall back to local search
        if not results:
            results = memory.search_learnings(query, tags)[:limit]

        _display_recall_results(query, results, used_backboard)

    except Exception as e:
        console.print(f"[red]Error searching: {e}[/red]")
        sys.exit(1)


def _display_recall_results(query: str, results: list, used_backboard: bool):
    """Display recall results."""
    if not results:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        console.print("Try a different query or add learnings with: [bold]flow learn[/bold]")
        return

    lines = []

    if used_backboard and results:
        # Backboard returns a summary
        lines.append(results[0].get("content", ""))
    else:
        # Local results
        lines.append(f"Found {len(results)} relevant items:\n")
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                text = result.get("text", "")
                tags = result.get("tags", [])
                timestamp = result.get("timestamp", "")

                lines.append(f"[bold]{i}.[/bold] {text}")
                if tags:
                    lines.append(f"   [dim]Tags: {', '.join(tags)}[/dim]")
                if timestamp:
                    elapsed = restore.calculate_time_elapsed(timestamp)
                    lines.append(f"   [dim]{elapsed} ago[/dim]")
                lines.append("")

    panel = Panel(
        "\n".join(lines),
        title=f"[blue]Recall: \"{query}\"[/blue]",
        border_style="blue"
    )
    console.print(panel)


# ============ TEAM COMMAND ============

@cli.command()
@click.argument("query")
@click.option("-t", "--tag", multiple=True, help="Filter by tags")
@click.option("--limit", default=10, help="Limit results (default: 10)")
def team(query: str, tag: tuple, limit: int):
    """Search team-shared learnings.

    Examples:
        flow team "caching strategies"
        flow team "database" --tag performance
    """
    team_thread_id = os.environ.get("BACKBOARD_TEAM_THREAD_ID")

    if not team_thread_id:
        console.print("[yellow]Team not configured.[/yellow]")
        console.print("Run [bold]python setup_assistants.py[/bold] to set up team memory.")
        return

    try:
        response = backboard_client.run_async(
            backboard_client.query_team_memory(team_thread_id, query)
        )

        lines = []
        if response:
            lines.append(response)
        else:
            lines.append("No team learnings found.")
            lines.append("Share learnings with: [bold]flow learn \"...\" --team[/bold]")

        panel = Panel(
            "\n".join(lines),
            title=f"[magenta]Team Knowledge: \"{query}\"[/magenta]",
            border_style="magenta"
        )
        console.print(panel)

    except BackboardAuthError:
        console.print("[red]Authentication failed. Check BACKBOARD_API_KEY.[/red]")
    except BackboardError as e:
        console.print(f"[yellow]Team search unavailable: {e}[/yellow]")


# ============ STATUS COMMAND ============

@cli.command()
def status():
    """Show current Flow Guardian state.

    Displays last save time, current branch, memory stats,
    and storage status.
    """
    try:
        latest = memory.get_latest_session()
        stats = memory.get_stats()
        current_branch = restore.get_current_branch()

        lines = []

        # Last save
        if latest:
            timestamp = latest.get("timestamp", "")
            elapsed = restore.calculate_time_elapsed(timestamp)
            lines.append(f"[dim]Last Save:[/dim] {elapsed} ago")
        else:
            lines.append("[dim]Last Save:[/dim] Never")

        # Current branch
        if current_branch:
            lines.append(f"[dim]Branch:[/dim] {current_branch}")

        # Working context
        if latest:
            summary = latest.get("context", {}).get("summary", "")
            if summary:
                lines.append(f"[dim]Working on:[/dim] {summary}")

        lines.append("")

        # Stats
        lines.append("[bold]Memory Stats[/bold]")
        lines.append(f"  Sessions: {stats.get('sessions_count', 0)}")
        lines.append(f"  Personal learnings: {stats.get('personal_learnings', 0)}")
        lines.append(f"  Team learnings: {stats.get('team_learnings', 0)}")

        # Storage status
        lines.append("")
        backboard_configured = bool(os.environ.get("BACKBOARD_PERSONAL_THREAD_ID"))
        storage_status = "Backboard.io + local" if backboard_configured else "local only"
        lines.append(f"[dim]Storage:[/dim] {storage_status}")

        panel = Panel(
            "\n".join(lines),
            title="[cyan]Flow Guardian Status[/cyan]",
            border_style="cyan"
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        sys.exit(1)


# ============ HISTORY COMMAND ============

@cli.command()
@click.option("-n", "--limit", default=10, help="Number of sessions to show")
@click.option("--all", "show_all", is_flag=True, help="Show all sessions")
@click.option("--branch", help="Filter by branch name")
def history(limit: int, show_all: bool, branch: Optional[str]):
    """Show past sessions and checkpoints.

    Examples:
        flow history
        flow history -n 20
        flow history --branch main
    """
    try:
        if show_all:
            limit = 1000

        sessions = memory.list_sessions(limit=limit, branch=branch)

        if not sessions:
            console.print("[yellow]No sessions found.[/yellow]")
            console.print("Get started with: [bold]flow save[/bold]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=3)
        table.add_column("Time", width=20)
        table.add_column("Branch", width=20)
        table.add_column("Summary")

        for i, s in enumerate(sessions, 1):
            timestamp = s.get("timestamp", "")

            # Format time
            if timestamp:
                elapsed = restore.calculate_time_elapsed(timestamp)
                time_str = elapsed + " ago"
            else:
                time_str = "?"

            table.add_row(
                str(i),
                time_str,
                s.get("branch", "?")[:20],
                s.get("summary", "")[:50]
            )

        console.print(table)
        console.print()
        console.print("[dim]Resume a session with: flow resume -s <session_id>[/dim]")

    except Exception as e:
        console.print(f"[red]Error listing history: {e}[/red]")
        sys.exit(1)


# ============ DAEMON COMMAND GROUP ============

@cli.group()
def daemon():
    """Auto-capture daemon for Claude Code sessions.

    Watches your Claude Code sessions and automatically extracts
    insights, storing them for infinite memory.

    Examples:
        flow daemon start     # Start background watcher
        flow daemon stop      # Stop the daemon
        flow daemon status    # Check daemon status
    """
    pass


@daemon.command("start")
@click.option("--foreground", "-f", is_flag=True, help="Run in foreground (don't daemonize)")
def daemon_start(foreground: bool):
    """Start the auto-capture daemon."""
    import daemon as daemon_module

    if foreground:
        console.print("[dim]Starting daemon in foreground...[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        daemon_module.start_daemon(foreground=True)
    else:
        if daemon_module.is_running():
            console.print("[yellow]Daemon is already running[/yellow]")
            return
        daemon_module.start_daemon(foreground=False)
        console.print("[green]Daemon started[/green]")
        console.print("[dim]Check status with: flow daemon status[/dim]")


@daemon.command("stop")
def daemon_stop():
    """Stop the auto-capture daemon."""
    import daemon as daemon_module

    if daemon_module.stop_daemon():
        console.print("[green]Daemon stopped[/green]")
    else:
        console.print("[yellow]Daemon was not running[/yellow]")


@daemon.command("status")
def daemon_status():
    """Check daemon status."""
    import daemon as daemon_module

    status = daemon_module.daemon_status()

    lines = []

    if status["running"]:
        lines.append(f"[green]Daemon is running[/green] (PID: {status['pid']})")
        if status.get("started_at"):
            lines.append(f"[dim]Started:[/dim] {status['started_at']}")
        lines.append(f"[dim]Extractions:[/dim] {status['extractions_count']}")
        lines.append(f"[dim]Sessions tracked:[/dim] {status['sessions_tracked']}")
    else:
        lines.append("[yellow]Daemon is not running[/yellow]")
        lines.append("")
        lines.append("Start with: [bold]flow daemon start[/bold]")

    if status.get("recent_logs"):
        lines.append("")
        lines.append("[bold]Recent activity:[/bold]")
        for log in status["recent_logs"]:
            lines.append(f"  [dim]{log}[/dim]")

    panel = Panel(
        "\n".join(lines),
        title="[cyan]Daemon Status[/cyan]",
        border_style="cyan"
    )
    console.print(panel)


@daemon.command("logs")
@click.option("-n", "--lines", default=20, help="Number of lines to show")
def daemon_logs(lines: int):
    """Show daemon logs."""
    import daemon as daemon_module
    from pathlib import Path

    log_file = daemon_module.LOG_FILE
    if not log_file.exists():
        console.print("[yellow]No logs found[/yellow]")
        return

    with open(log_file) as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            console.print(f"[dim]{line.rstrip()}[/dim]")


# ============ CONTEXT COMMAND ============

@cli.command()
@click.option("--project", "-p", help="Project path (default: current directory)")
def context(project: str):
    """Show what Flow Guardian knows about this project.

    Queries all stored memory (sessions, learnings, auto-captured insights)
    and provides a summary of everything relevant to the current project.

    This is what you'd paste into a new Claude session to give it
    full context about your project.

    Examples:
        flow context
        flow context --project /path/to/project
    """
    cwd = project or os.getcwd()

    try:
        # Build comprehensive context query
        query = f"""Provide a comprehensive summary of everything you know about this project.

Project directory: {cwd}

Include:
1. What the user has been working on (from sessions)
2. Key decisions and their rationale
3. Technical learnings and insights
4. Any patterns or preferences noted
5. Current state and likely next steps

Be specific and actionable. This will be used to restore context in a new session."""

        results = []
        used_backboard = False

        # Try Backboard.io
        thread_id = os.environ.get("BACKBOARD_PERSONAL_THREAD_ID")
        if thread_id:
            try:
                response = backboard_client.run_async(
                    backboard_client.recall(thread_id, query)
                )
                if response:
                    results.append(response)
                    used_backboard = True
            except BackboardError:
                pass

        # Add local sessions info
        sessions = memory.list_sessions(limit=5)
        if sessions and not used_backboard:
            results.append("\n[bold]Recent Sessions:[/bold]")
            for s in sessions:
                summary = s.get("summary", "No summary")
                branch = s.get("branch", "?")
                elapsed = restore.calculate_time_elapsed(s.get("timestamp", ""))
                results.append(f"  • {summary} ({branch}, {elapsed} ago)")

        # Add local learnings
        learnings = memory.search_learnings("", [])[:5]
        if learnings and not used_backboard:
            results.append("\n[bold]Recent Learnings:[/bold]")
            for l in learnings:
                text = l.get("text", "")[:100]
                results.append(f"  • {text}")

        if not results:
            console.print("[yellow]No context found for this project.[/yellow]")
            console.print("\nStart building memory with:")
            console.print("  [bold]flow save[/bold]          - Save session context")
            console.print("  [bold]flow learn \"...\"[/bold]  - Store insights")
            console.print("  [bold]flow daemon start[/bold]  - Auto-capture from Claude Code")
            return

        content = "\n".join(results) if isinstance(results, list) else results

        panel = Panel(
            content,
            title=f"[cyan]Project Context: {os.path.basename(cwd)}[/cyan]",
            border_style="cyan"
        )
        console.print(panel)

        if used_backboard:
            console.print("\n[dim]Source: Backboard.io semantic memory[/dim]")
        else:
            console.print("\n[dim]Source: Local storage (connect Backboard.io for semantic search)[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting context: {e}[/red]")
        sys.exit(1)


# ============ INJECT COMMAND ============

@cli.command()
@click.option("-q", "--quiet", is_flag=True, help="Plain output, no Rich formatting (for hooks)")
@click.option("-l", "--level", default="L1", type=click.Choice(["L0", "L1", "L2", "L3"]),
              help="TLDR depth (default: L1)")
@click.option("--save-state", is_flag=True, help="Save current state to handoff.yaml")
def inject(quiet: bool, level: str, save_state: bool):
    """Inject context for Claude Code sessions.

    Generates context from handoff.yaml and Backboard memory,
    formatted for Claude to understand your session state.

    Used by:
    - SessionStart hook (automatic injection)
    - PreCompact hook (state preservation)
    - Manual context loading

    Examples:
        flow inject              # Full injection with formatting
        flow inject --quiet      # Plain output for hooks
        flow inject --level L2   # More detailed context
        flow inject --save-state # Save state before compaction
    """
    import inject as inject_module

    try:
        if save_state:
            # Save current state to handoff.yaml (PreCompact mode)
            data = inject_module.save_current_state_sync()

            if quiet:
                console.print("state saved")
            else:
                lines = []
                lines.append("[bold]Session state saved[/bold]")
                lines.append("")
                lines.append(f"[dim]Goal:[/dim] {data.get('goal', 'N/A')}")
                lines.append(f"[dim]Status:[/dim] {data.get('status', 'N/A')}")
                lines.append(f"[dim]Now:[/dim] {data.get('now', 'N/A')}")

                branch = data.get('branch')
                if branch:
                    lines.append(f"[dim]Branch:[/dim] {branch}")

                files = data.get('files', [])
                if files:
                    lines.append(f"[dim]Files:[/dim] {', '.join(files[:5])}")

                panel = Panel(
                    "\n".join(lines),
                    title="[green]State Saved[/green]",
                    border_style="green"
                )
                console.print(panel)
        else:
            # Generate and output injection
            output = inject_module.generate_injection_sync(level=level, quiet=quiet)

            if quiet:
                # Direct output for hooks (no Rich formatting)
                console.print(output, highlight=False)
            else:
                # Beautiful panel for interactive use
                panel = Panel(
                    output,
                    title="[blue]Context Injection[/blue]",
                    border_style="blue"
                )
                console.print(panel)

    except Exception as e:
        if quiet:
            # Silent failure for hooks
            console.print(f"error: {e}", highlight=False)
        else:
            console.print(f"[red]Error generating injection: {e}[/red]")
        sys.exit(1)


# ============ SETUP COMMAND ============

# Hook script templates
FLOW_INJECT_HOOK = '''#!/bin/bash
# Flow Guardian SessionStart Hook
# Injects project context at session start

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --quiet 2>/dev/null
fi
'''

FLOW_PRECOMPACT_HOOK = '''#!/bin/bash
# Flow Guardian PreCompact Hook
# Saves state before context compaction

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --quiet --save-state 2>/dev/null
fi
'''

HOOKS_SETTINGS_JSON = '''{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/flow-inject.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/flow-precompact.sh"
          }
        ]
      }
    ]
  }
}
'''

INITIAL_HANDOFF_YAML = '''# Flow Guardian Handoff State
# Auto-updated by flow save, daemon, and hooks
goal: null
status: null
now: null
timestamp: null
'''

INITIAL_CONFIG_YAML = '''# Flow Guardian Local Config
# Overrides global settings for this project

# TLDR depth for injection (L0, L1, L2, L3)
tldr_level: L1

# Include files in context
include_files: true

# Auto-inject on session start
auto_inject: true
'''


@cli.command()
@click.option("-g", "--global", "global_mode", is_flag=True,
              help="Install hooks globally for all projects")
@click.option("-c", "--check", "check_mode", is_flag=True,
              help="Check setup status without modifying")
@click.option("-f", "--force", is_flag=True,
              help="Overwrite existing files")
def setup(global_mode: bool, check_mode: bool, force: bool):
    """Initialize Flow Guardian for a project.

    Creates necessary directories and configures Claude Code hooks
    for automatic context injection.

    Examples:
        flow setup              # Set up current project
        flow setup --global     # Set up global hooks (all projects)
        flow setup --check      # Check setup status
    """
    from pathlib import Path

    if global_mode:
        base_dir = Path.home()
    else:
        base_dir = Path.cwd()

    if check_mode:
        _display_setup_status(base_dir, global_mode)
        return

    try:
        results = []

        # Create .flow-guardian/ directory (skip for global mode)
        if not global_mode:
            fg_dir = base_dir / ".flow-guardian"
            if not fg_dir.exists():
                fg_dir.mkdir(parents=True)
                results.append(("Created .flow-guardian/", True))
            elif force:
                results.append(("Updated .flow-guardian/", True))
            else:
                results.append((".flow-guardian/ exists", True))

            # Create handoff.yaml
            handoff_path = fg_dir / "handoff.yaml"
            if not handoff_path.exists() or force:
                handoff_path.write_text(INITIAL_HANDOFF_YAML)
                results.append(("Created .flow-guardian/handoff.yaml", True))
            else:
                results.append((".flow-guardian/handoff.yaml exists", True))

            # Create config.yaml
            config_path = fg_dir / "config.yaml"
            if not config_path.exists() or force:
                config_path.write_text(INITIAL_CONFIG_YAML)
                results.append(("Created .flow-guardian/config.yaml", True))
            else:
                results.append((".flow-guardian/config.yaml exists", True))

        # Create .claude/hooks/ directory
        hooks_dir = base_dir / ".claude" / "hooks"
        if not hooks_dir.exists():
            hooks_dir.mkdir(parents=True)
            results.append(("Created .claude/hooks/", True))
        else:
            results.append((".claude/hooks/ exists", True))

        # Create hook scripts
        inject_hook_path = hooks_dir / "flow-inject.sh"
        if not inject_hook_path.exists() or force:
            inject_hook_path.write_text(FLOW_INJECT_HOOK)
            inject_hook_path.chmod(0o755)  # Make executable
            results.append(("Created .claude/hooks/flow-inject.sh", True))
        else:
            results.append((".claude/hooks/flow-inject.sh exists", True))

        precompact_hook_path = hooks_dir / "flow-precompact.sh"
        if not precompact_hook_path.exists() or force:
            precompact_hook_path.write_text(FLOW_PRECOMPACT_HOOK)
            precompact_hook_path.chmod(0o755)  # Make executable
            results.append(("Created .claude/hooks/flow-precompact.sh", True))
        else:
            results.append((".claude/hooks/flow-precompact.sh exists", True))

        # Create/update settings.json
        settings_path = base_dir / ".claude" / "settings.json"
        if not settings_path.exists() or force:
            settings_path.write_text(HOOKS_SETTINGS_JSON)
            results.append(("Created .claude/settings.json", True))
        else:
            # Try to merge hooks into existing settings
            try:
                import json
                with open(settings_path) as f:
                    existing = json.load(f)
                hooks_config = json.loads(HOOKS_SETTINGS_JSON)
                if "hooks" not in existing:
                    existing["hooks"] = hooks_config["hooks"]
                    with open(settings_path, "w") as f:
                        json.dump(existing, f, indent=2)
                    results.append(("Updated .claude/settings.json", True))
                else:
                    results.append((".claude/settings.json exists (hooks may need manual merge)", False))
            except Exception:
                results.append((".claude/settings.json exists", True))

        # Check environment variables
        env_results = []
        if os.environ.get("CEREBRAS_API_KEY"):
            env_results.append(("CEREBRAS_API_KEY", True))
        else:
            env_results.append(("CEREBRAS_API_KEY not set", False))

        if os.environ.get("BACKBOARD_API_KEY"):
            env_results.append(("BACKBOARD_API_KEY", True))
        else:
            env_results.append(("BACKBOARD_API_KEY not set", False))

        if os.environ.get("BACKBOARD_PERSONAL_THREAD_ID"):
            env_results.append(("BACKBOARD_PERSONAL_THREAD_ID", True))
        else:
            env_results.append(("BACKBOARD_PERSONAL_THREAD_ID not set (run setup_assistants.py)", False))

        # Display results
        _display_setup_results(results, env_results, global_mode)

    except PermissionError as e:
        console.print(f"[red]Permission denied: {e}[/red]")
        console.print("Try running with appropriate permissions.")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        sys.exit(1)


def _display_setup_status(base_dir: Path, global_mode: bool):
    """Display current setup status."""
    lines = []
    location = "Global (~/.claude)" if global_mode else f"Project: {base_dir}"
    lines.append(f"[bold]{location}[/bold]")
    lines.append("")

    # Check directories and files
    lines.append("[bold]Local Setup:[/bold]")

    if not global_mode:
        fg_dir = base_dir / ".flow-guardian"
        if fg_dir.exists():
            lines.append("  .flow-guardian/          [green]✓ exists[/green]")
        else:
            lines.append("  .flow-guardian/          [yellow]✗ missing[/yellow]")

        handoff_path = fg_dir / "handoff.yaml"
        if handoff_path.exists():
            lines.append("  .flow-guardian/handoff.yaml  [green]✓ exists[/green]")
        else:
            lines.append("  .flow-guardian/handoff.yaml  [yellow]✗ missing[/yellow]")

    hooks_dir = base_dir / ".claude" / "hooks"
    if hooks_dir.exists():
        lines.append("  .claude/hooks/           [green]✓ exists[/green]")
    else:
        lines.append("  .claude/hooks/           [yellow]✗ missing[/yellow]")

    settings_path = base_dir / ".claude" / "settings.json"
    if settings_path.exists():
        lines.append("  .claude/settings.json    [green]✓ exists[/green]")
    else:
        lines.append("  .claude/settings.json    [yellow]✗ missing[/yellow]")

    # Check environment
    lines.append("")
    lines.append("[bold]Environment:[/bold]")

    if os.environ.get("CEREBRAS_API_KEY"):
        lines.append("  CEREBRAS_API_KEY         [green]✓ set[/green]")
    else:
        lines.append("  CEREBRAS_API_KEY         [yellow]✗ not set[/yellow]")

    if os.environ.get("BACKBOARD_API_KEY"):
        lines.append("  BACKBOARD_API_KEY        [green]✓ set[/green]")
    else:
        lines.append("  BACKBOARD_API_KEY        [yellow]✗ not set[/yellow]")

    if os.environ.get("BACKBOARD_PERSONAL_THREAD_ID"):
        lines.append("  BACKBOARD_PERSONAL_THREAD_ID  [green]✓ set[/green]")
    else:
        lines.append("  BACKBOARD_PERSONAL_THREAD_ID  [yellow]✗ not set[/yellow]")

    panel = Panel(
        "\n".join(lines),
        title="[cyan]Flow Guardian Setup Status[/cyan]",
        border_style="cyan"
    )
    console.print(panel)


def _display_setup_results(results: list, env_results: list, global_mode: bool):
    """Display setup completion results."""
    lines = []

    for msg, success in results:
        if success:
            lines.append(f"[green]✓[/green] {msg}")
        else:
            lines.append(f"[yellow]⚠[/yellow] {msg}")

    lines.append("")
    lines.append("[bold]Environment:[/bold]")

    for msg, success in env_results:
        if success:
            lines.append(f"[green]✓[/green] {msg}")
        else:
            lines.append(f"[yellow]⚠[/yellow] {msg}")

    lines.append("")
    lines.append("[bold]Setup complete![/bold] Flow Guardian will now:")
    lines.append("• Automatically inject context on session start")
    lines.append("• Save state before context compaction")
    lines.append("• Remember your learnings across sessions")
    lines.append("")
    lines.append("Run [bold]flow save[/bold] to create your first checkpoint.")

    title = "[green]Global Setup Complete[/green]" if global_mode else "[green]Project Setup Complete[/green]"
    panel = Panel(
        "\n".join(lines),
        title=title,
        border_style="green"
    )
    console.print(panel)


# ============ MAIN ============

if __name__ == "__main__":
    cli()
