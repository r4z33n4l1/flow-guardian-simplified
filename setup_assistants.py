#!/usr/bin/env python3
"""One-time setup script for Backboard.io assistants.

Creates personal and team assistants with their threads.
Run this once to get the IDs needed for .env configuration.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

import backboard_client
from backboard_client import BackboardError, BackboardAuthError

# Load environment variables
load_dotenv()

console = Console()


async def setup_personal_assistant(username: str) -> tuple[str, str]:
    """
    Create personal assistant and thread.

    Args:
        username: User identifier for the assistant name

    Returns:
        Tuple of (assistant_id, thread_id)
    """
    assistant_name = f"flow-guardian-personal-{username}"
    console.print(f"[dim]Creating personal assistant: {assistant_name}[/dim]")

    assistant_id = await backboard_client.create_assistant(assistant_name)
    console.print(f"[green]Created assistant: {assistant_id}[/green]")

    console.print("[dim]Creating personal thread...[/dim]")
    thread_id = await backboard_client.create_thread(assistant_id)
    console.print(f"[green]Created thread: {thread_id}[/green]")

    return assistant_id, thread_id


async def setup_team_assistant(team_name: str) -> tuple[str, str]:
    """
    Create team assistant and thread.

    Args:
        team_name: Team identifier for the assistant name

    Returns:
        Tuple of (assistant_id, thread_id)
    """
    assistant_name = f"flow-guardian-team-{team_name}"
    console.print(f"[dim]Creating team assistant: {assistant_name}[/dim]")

    assistant_id = await backboard_client.create_assistant(assistant_name)
    console.print(f"[green]Created assistant: {assistant_id}[/green]")

    console.print("[dim]Creating team thread...[/dim]")
    thread_id = await backboard_client.create_thread(assistant_id)
    console.print(f"[green]Created thread: {thread_id}[/green]")

    return assistant_id, thread_id


async def main():
    """Main setup function."""
    console.print(Panel(
        "[bold]Flow Guardian - Backboard.io Setup[/bold]\n\n"
        "This script creates the assistants and threads needed for\n"
        "persistent memory with Backboard.io.",
        border_style="blue"
    ))

    # Check for API key
    if not os.environ.get("BACKBOARD_API_KEY"):
        console.print("[red]Error: BACKBOARD_API_KEY not set[/red]")
        console.print("\nSet it in your .env file:")
        console.print("  BACKBOARD_API_KEY=your-api-key")
        console.print("\nGet your API key at: https://backboard.io/hackathons/")
        sys.exit(1)

    # Get username
    username = os.environ.get("FLOW_GUARDIAN_USER")
    if not username:
        console.print("\n[yellow]FLOW_GUARDIAN_USER not set in .env[/yellow]")
        from rich.prompt import Prompt
        username = Prompt.ask("Enter your username", default="user")

    # Get team name
    from rich.prompt import Prompt, Confirm
    setup_team = Confirm.ask("\nDo you want to set up team memory?", default=True)
    team_name = None
    if setup_team:
        team_name = Prompt.ask("Enter team name", default="default-team")

    console.print()

    try:
        # Create personal assistant
        console.print("[bold]Setting up personal memory...[/bold]")
        personal_assistant_id, personal_thread_id = await setup_personal_assistant(username)

        # Create team assistant if requested
        team_assistant_id = None
        team_thread_id = None
        if team_name:
            console.print("\n[bold]Setting up team memory...[/bold]")
            team_assistant_id, team_thread_id = await setup_team_assistant(team_name)

        # Output configuration
        console.print("\n")
        console.print(Panel(
            "[bold green]Setup Complete![/bold green]\n\n"
            "Add these to your .env file:\n",
            border_style="green"
        ))

        console.print("[bold]# Personal Memory[/bold]")
        console.print(f"BACKBOARD_PERSONAL_ASSISTANT_ID={personal_assistant_id}")
        console.print(f"BACKBOARD_PERSONAL_THREAD_ID={personal_thread_id}")

        if team_assistant_id:
            console.print("\n[bold]# Team Memory[/bold]")
            console.print(f"BACKBOARD_TEAM_ASSISTANT_ID={team_assistant_id}")
            console.print(f"BACKBOARD_TEAM_THREAD_ID={team_thread_id}")

        console.print("\n[bold]# User[/bold]")
        console.print(f"FLOW_GUARDIAN_USER={username}")

        console.print("\n[dim]Copy these values to your .env file to enable cloud memory.[/dim]")

    except BackboardAuthError as e:
        console.print(f"[red]Authentication failed: {e}[/red]")
        console.print("\nCheck that your BACKBOARD_API_KEY is correct.")
        sys.exit(1)

    except BackboardError as e:
        console.print(f"[red]Backboard.io error: {e}[/red]")
        console.print("\nCheck your internet connection and try again.")
        sys.exit(1)

    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
