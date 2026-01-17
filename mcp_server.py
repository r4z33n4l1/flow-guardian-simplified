#!/usr/bin/env python3
"""Flow Guardian MCP Server for Claude Code integration.

Provides persistent memory tools via Model Context Protocol (MCP).
Uses stdio transport for communication with Claude Code.
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Load environment
load_dotenv()

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.config import FlowConfig
from services.flow_service import FlowService
from services.models import (
    CaptureRequest,
    LearnRequest,
    RecallRequest,
    TeamQueryRequest,
)

# Initialize MCP server
server = Server("flow-guardian")


# ============ TOOL DEFINITIONS ============

TOOLS = [
    Tool(
        name="flow_recall",
        description="""Recall previous coding context from Flow Guardian's memory.

USE THIS WHEN:
- User says "continue from yesterday/last time"
- User references previous work without full context
- Starting a new session on an existing project
- User asks "what were we working on?"

The tool searches semantic memory and returns relevant past context including:
- What was being worked on
- Key decisions made
- Suggested next steps""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for (e.g., 'auth refactoring', 'recent work')",
                }
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="flow_capture",
        description="""Capture current coding context to Flow Guardian's memory.

USE THIS WHEN:
- User says they need to stop/leave/take a break
- Session is ending
- Switching to a different task
- User asks to "save progress" or "remember this"

Captures:
- Summary of current work
- Key decisions made
- Next steps to continue
- Git state (branch, files)""",
        inputSchema={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief description of what we were working on",
                },
                "decisions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key decisions made during this session",
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What should be done next when returning",
                },
                "blockers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any blockers or issues to remember",
                },
            },
            "required": ["summary"],
        },
    ),
    Tool(
        name="flow_learn",
        description="""Store a learning or insight for future reference.

USE THIS WHEN:
- We discover something important (bug cause, best practice, gotcha)
- User says "remember this" or "note this down"
- Finding a solution that others might need
- Debugging reveals root cause

Set share_with_team=true for insights that would help teammates.""",
        inputSchema={
            "type": "object",
            "properties": {
                "insight": {
                    "type": "string",
                    "description": "The learning or insight to store",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to categorize (e.g., ['auth', 'jwt', 'bug'])",
                },
                "share_with_team": {
                    "type": "boolean",
                    "description": "Whether to share with team (default: false)",
                    "default": False,
                },
            },
            "required": ["insight"],
        },
    ),
    Tool(
        name="flow_team",
        description="""Search team's shared knowledge base.

USE THIS WHEN:
- Looking for solutions others may have found
- User asks "has anyone dealt with..."
- Debugging common issues
- Looking for team conventions or patterns""",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in team knowledge",
                }
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="flow_status",
        description="""Get current Flow Guardian status and last captured context.

USE THIS WHEN:
- User asks about Flow Guardian status
- Checking if memory is connected
- Seeing what was last captured""",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# ============ HANDLERS ============


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from Claude Code."""
    config = FlowConfig.from_env()
    service = FlowService(config)

    try:
        if name == "flow_recall":
            request = RecallRequest(query=arguments.get("query", "recent work"))
            result = await service.recall_context(request)
            return [TextContent(type="text", text=_format_recall_response(result))]

        elif name == "flow_capture":
            request = CaptureRequest(
                summary=arguments.get("summary", "Coding session"),
                decisions=arguments.get("decisions", []),
                next_steps=arguments.get("next_steps", []),
                blockers=arguments.get("blockers", []),
            )
            result = await service.capture_context(request)
            return [TextContent(type="text", text=_format_capture_response(result))]

        elif name == "flow_learn":
            request = LearnRequest(
                insight=arguments.get("insight", ""),
                tags=arguments.get("tags", []),
                share_with_team=arguments.get("share_with_team", False),
            )
            result = await service.store_learning(request)
            return [TextContent(type="text", text=_format_learn_response(result))]

        elif name == "flow_team":
            request = TeamQueryRequest(query=arguments.get("query", ""))
            result = await service.query_team(request)
            return [TextContent(type="text", text=_format_team_response(result))]

        elif name == "flow_status":
            result = await service.get_status()
            return [TextContent(type="text", text=_format_status_response(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ RESPONSE FORMATTERS ============


def _format_recall_response(result) -> str:
    """Format recall response for Claude Code."""
    response = "## Retrieved Context\n\n"

    if result.results:
        for item in result.results:
            if isinstance(item, dict):
                content = item.get("content", item.get("text", str(item)))
                response += f"{content}\n\n"
    else:
        response += "No matching context found in memory."

    response += f"\n*Source: {result.source}*"
    return response


def _format_capture_response(result) -> str:
    """Format capture response for Claude Code."""
    response = "## Context Captured\n\n"
    response += f"**Summary:** {result.summary}\n"
    response += f"**Branch:** `{result.branch}`\n"
    if result.files:
        files_str = ", ".join(result.files[:5])
        if len(result.files) > 5:
            files_str += f" (+{len(result.files) - 5} more)"
        response += f"**Files:** `{files_str}`\n"
    response += f"**Session ID:** {result.session_id}\n"

    storage = []
    if result.stored_backboard:
        storage.append("Backboard.io")
    if result.stored_local:
        storage.append("local")
    response += f"**Stored:** {', '.join(storage)}\n"

    response += '\n---\n*You can pick up where you left off by saying "continue from last session"*'
    return response


def _format_learn_response(result) -> str:
    """Format learn response for Claude Code."""
    title = "Shared with Team" if result.scope == "team" else "Learning Saved"
    response = f"## {title}\n\n"
    response += f"**Insight:** {result.insight}\n"
    if result.tags:
        response += f"**Tags:** {', '.join(result.tags)}\n"
    response += f"**Scope:** {result.scope}\n"
    return response


def _format_team_response(result) -> str:
    """Format team response for Claude Code."""
    response = f'## Team Knowledge: "{result.query}"\n\n'
    if not result.team_configured:
        response += "Team memory not configured.\n"
        response += "\nRun `flow init --user yourname --team teamname` to set up team memory."
    else:
        response += result.results
    return response


def _format_status_response(result) -> str:
    """Format status response for Claude Code."""
    response = "## Flow Guardian Status\n\n"
    response += f"**User:** {result.user}\n"
    response += f"**Last Save:** {result.last_save or 'Never'}\n"
    if result.branch:
        response += f"**Branch:** `{result.branch}`\n"
    if result.working_on:
        response += f"**Working On:** {result.working_on}\n"

    response += "\n---\n\n"
    response += "**Memory Stats**\n"
    response += f"- Sessions: {result.sessions_count}\n"
    response += f"- Personal learnings: {result.personal_learnings}\n"
    response += f"- Team learnings: {result.team_learnings}\n"

    response += f"\n**Storage:** {result.storage}\n"
    response += f"**Backboard:** {'Connected' if result.backboard_connected else 'Not configured'}\n"
    response += f"**Team:** {'Configured' if result.team_configured else 'Not configured'}\n"
    return response


# ============ MAIN ============


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
