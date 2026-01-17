#!/usr/bin/env python3
"""Flow Guardian - CLI for persistent AI coding session memory.

"Claude forgets. Flow Guardian remembers."
"""
import os
import sys
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


# ============ MAIN ============

if __name__ == "__main__":
    cli()
