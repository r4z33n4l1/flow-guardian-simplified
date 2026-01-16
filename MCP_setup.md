# Flow Guardian MCP Integration Plan

## Claude Code + Flow Guardian: Persistent Memory for AI Coding Sessions

**Version:** 1.0  
**Date:** January 16, 2026  
**Purpose:** Enable Claude Code to capture and recall coding context across sessions using Flow Guardian's memory layer.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [What is MCP?](#2-what-is-mcp)
3. [Architecture Overview](#3-architecture-overview)
4. [Prerequisites](#4-prerequisites)
5. [Implementation Plan](#5-implementation-plan)
6. [MCP Server Implementation](#6-mcp-server-implementation)
7. [Configuration Guide](#7-configuration-guide)
8. [Testing Procedures](#8-testing-procedures)
9. [Usage Examples](#9-usage-examples)
10. [Troubleshooting](#10-troubleshooting)
11. [Demo Script](#11-demo-script)

---

## 1. Executive Summary

### The Problem

Claude Code sessions are stateless. Every new session starts fresh with no memory of:
- What you were working on yesterday
- Decisions made in previous sessions
- Context built up over hours of collaboration
- Team learnings and institutional knowledge

### The Solution

Flow Guardian becomes an **MCP (Model Context Protocol) server** that Claude Code can call to:
- **Capture** coding context at end of sessions
- **Recall** previous context at start of new sessions
- **Learn** and store insights for future reference
- **Search** team knowledge base

### The Result

```
Before: "Continue from yesterday" → "I don't have previous context"
After:  "Continue from yesterday" → "You were refactoring auth.py..."
```

---

## 2. What is MCP?

### Model Context Protocol Overview

MCP (Model Context Protocol) is Anthropic's open standard for connecting AI assistants to external tools and data sources. Think of it as "USB for AI" — a standard way to plug capabilities into Claude.

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE                             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   MCP CLIENT                            │ │
│  │  • Discovers available tools from MCP servers          │ │
│  │  • Calls tools when needed                             │ │
│  │  • Receives results and incorporates into response     │ │
│  └────────────────────────────────────────────────────────┘ │
│                            │                                 │
│                            │ stdio / SSE                     │
│                            ▼                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              MCP SERVERS (External)                     │ │
│  │                                                         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │ │
│  │  │ Filesystem│  │ GitHub   │  │ Flow Guardian        │  │ │
│  │  │ Server   │  │ Server   │  │ (Our MCP Server)     │  │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘  │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### How MCP Works

1. **Discovery:** Claude Code reads config, finds MCP servers
2. **Initialization:** Starts each MCP server process
3. **Tool Listing:** Asks each server "what tools do you have?"
4. **Tool Calling:** When needed, calls tools with arguments
5. **Response:** Server returns results, Claude incorporates them

### MCP Communication

MCP servers communicate via **stdio** (standard input/output):
- Claude Code writes JSON-RPC requests to server's stdin
- Server writes JSON-RPC responses to stdout
- Simple, secure, no network required

---

## 3. Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEVELOPER MACHINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           CLAUDE CODE                                    ││
│  │                                                                          ││
│  │  User: "Continue the auth refactoring from yesterday"                   ││
│  │                              │                                           ││
│  │                              ▼                                           ││
│  │  Claude decides to call flow_recall tool                                ││
│  │                              │                                           ││
│  └──────────────────────────────┼───────────────────────────────────────────┘│
│                                 │                                            │
│                                 │ JSON-RPC over stdio                        │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    FLOW GUARDIAN MCP SERVER                              ││
│  │                       (Python process)                                   ││
│  │                                                                          ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 ││
│  │  │ flow_capture│    │ flow_recall │    │ flow_learn  │                 ││
│  │  │ flow_team   │    │ flow_status │    │             │                 ││
│  │  └─────────────┘    └─────────────┘    └─────────────┘                 ││
│  │          │                  │                  │                        ││
│  └──────────┼──────────────────┼──────────────────┼────────────────────────┘│
│             │                  │                  │                          │
│             └──────────────────┼──────────────────┘                          │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        LOCAL SERVICES                                    ││
│  │                                                                          ││
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     ││
│  │  │ Git Repository  │    │ .flowguardian/  │    │ Cerebras API    │     ││
│  │  │ (context source)│    │ (local state)   │    │ (fast analysis) │     ││
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘     ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   │
                                   │ HTTPS
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLOUD SERVICES                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         BACKBOARD.IO                                     ││
│  │                                                                          ││
│  │  ┌─────────────────────────┐    ┌─────────────────────────┐            ││
│  │  │   Personal Assistant    │    │    Team Assistant       │            ││
│  │  │                         │    │                         │            ││
│  │  │  • Context snapshots    │    │  • Shared learnings     │            ││
│  │  │  • Personal learnings   │    │  • Team knowledge       │            ││
│  │  │  • Session history      │    │  • Cross-member recall  │            ││
│  │  │                         │    │                         │            ││
│  │  │  memory="auto"          │    │  memory="auto"          │            ││
│  │  │  (semantic recall)      │    │  (semantic recall)      │            ││
│  │  └─────────────────────────┘    └─────────────────────────┘            ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: Recall Operation

```
User: "Continue the auth work from yesterday"
                    │
                    ▼
┌─────────────────────────────────────┐
│ 1. Claude Code receives message     │
│    Decides context recall needed    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 2. MCP Tool Call                    │
│    {                                │
│      "method": "tools/call",        │
│      "params": {                    │
│        "name": "flow_recall",       │
│        "arguments": {               │
│          "query": "auth work"       │
│        }                            │
│      }                              │
│    }                                │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 3. Flow Guardian MCP Server         │
│    • Loads config from .flowguardian│
│    • Calls Backboard.io API         │
│    • memory="auto" semantic search  │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 4. Backboard.io                     │
│    • Searches vector embeddings     │
│    • Finds relevant context         │
│    • Returns with LLM synthesis     │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 5. Response to Claude Code          │
│    "Yesterday you were refactoring  │
│     auth.py to use JWT refresh      │
│     tokens. Key decisions:          │
│     - 15 min access token           │
│     - 7 day refresh token           │
│     Next: implement rotation"       │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 6. Claude Code incorporates         │
│    context and continues working    │
└─────────────────────────────────────┘
```

### Data Flow: Capture Operation

```
User: "Let's save our progress, I need to go"
                    │
                    ▼
┌─────────────────────────────────────┐
│ 1. Claude Code receives message     │
│    Decides to capture context       │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 2. MCP Tool Call                    │
│    {                                │
│      "name": "flow_capture",        │
│      "arguments": {                 │
│        "summary": "JWT refresh...", │
│        "next_steps": [...],         │
│        "decisions": [...]           │
│      }                              │
│    }                                │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 3. Flow Guardian MCP Server         │
│    • Extracts git state             │
│    • Combines with Claude's summary │
│    • Stores to Backboard.io         │
│    • Saves local state              │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ 4. Confirmation to Claude Code      │
│    "✓ Context captured.             │
│     Next steps saved for tomorrow." │
└─────────────────────────────────────┘
```

---

## 4. Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| Python | 3.11+ | MCP server runtime | `brew install python@3.11` |
| Claude Code | Latest | AI coding assistant | `npm install -g @anthropic-ai/claude-code` |
| Git | 2.x+ | Context source | Usually pre-installed |
| pip | Latest | Python packages | Comes with Python |

### Required Accounts & API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| Cerebras | Fast LLM inference | https://cloud.cerebras.ai |
| Backboard.io | Persistent memory | https://backboard.io (code: `8090JAN`) |

### Required Python Packages

```txt
# requirements-mcp.txt
mcp>=1.0.0                   # MCP server framework
cerebras-cloud-sdk>=1.0.0    # Cerebras API
httpx>=0.25.0                # Async HTTP
gitpython>=3.1.0             # Git operations
pydantic>=2.0.0              # Data validation
python-dotenv>=1.0.0         # Environment management
```

---

## 5. Implementation Plan

### Phase 1: Core MCP Server (2 hours)

**Goal:** Basic MCP server that Claude Code can connect to

| Task | Time | Description |
|------|------|-------------|
| 1.1 | 15 min | Set up project structure |
| 1.2 | 30 min | Implement MCP server skeleton |
| 1.3 | 30 min | Add tool definitions |
| 1.4 | 30 min | Configure Claude Code connection |
| 1.5 | 15 min | Test basic connectivity |

**Deliverable:** Claude Code can list Flow Guardian tools

### Phase 2: Tool Implementations (3 hours)

**Goal:** All five tools working

| Task | Time | Description |
|------|------|-------------|
| 2.1 | 45 min | `flow_recall` - Query Backboard memory |
| 2.2 | 45 min | `flow_capture` - Store context snapshot |
| 2.3 | 30 min | `flow_learn` - Store learnings |
| 2.4 | 30 min | `flow_team` - Query team memory |
| 2.5 | 30 min | `flow_status` - Return current state |

**Deliverable:** All tools return meaningful responses

### Phase 3: Integration Testing (1.5 hours)

**Goal:** End-to-end flows work in Claude Code

| Task | Time | Description |
|------|------|-------------|
| 3.1 | 30 min | Test capture → recall cycle |
| 3.2 | 30 min | Test learning → team query cycle |
| 3.3 | 30 min | Test error handling and edge cases |

**Deliverable:** Reliable operation in real usage

### Phase 4: Polish & Demo Prep (1 hour)

**Goal:** Demo-ready integration

| Task | Time | Description |
|------|------|-------------|
| 4.1 | 30 min | Improve response formatting |
| 4.2 | 30 min | Prepare demo script and test |

**Deliverable:** Impressive demo of Claude Code + Flow Guardian

---

## 6. MCP Server Implementation

### Project Structure

```
flow-guardian/
├── flow/
│   ├── __init__.py
│   ├── state.py              # Local state management
│   ├── cerebras_client.py    # Cerebras API
│   ├── backboard_client.py   # Backboard API
│   ├── git_utils.py          # Git operations
│   └── ui.py                 # Rich terminal UI (for CLI)
├── mcp_server.py             # ★ MCP server entry point
├── requirements.txt          # CLI dependencies
├── requirements-mcp.txt      # MCP dependencies
├── .env                      # API keys
└── README.md
```

### Complete MCP Server Code

```python
#!/usr/bin/env python3
"""
Flow Guardian MCP Server
Provides persistent memory for Claude Code sessions.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
    LATEST_PROTOCOL_VERSION
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Flow Guardian imports (reuse from CLI)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow.state import load_config, load_last_capture, save_last_capture, LastCapture, FlowConfig
from flow.git_utils import get_repo, get_git_state, get_changes_since
from flow.backboard_client import (
    store_context_snapshot,
    recall_context,
    store_learning,
    store_team_learning,
    query_team_memory
)

# Initialize MCP server
server = Server("flow-guardian")

# ============================================================
# TOOL DEFINITIONS
# ============================================================

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
                    "description": "What to search for (e.g., 'auth refactoring', 'database migration', 'recent work')"
                }
            },
            "required": ["query"]
        }
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
                    "description": "Brief description of what we were working on"
                },
                "decisions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key decisions made during this session"
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What should be done next when returning"
                },
                "blockers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Any blockers or issues to remember"
                }
            },
            "required": ["summary"]
        }
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
                    "description": "The learning or insight to store"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to categorize (e.g., ['auth', 'jwt', 'bug'])"
                },
                "share_with_team": {
                    "type": "boolean",
                    "description": "Whether to share with team (default: false)",
                    "default": False
                }
            },
            "required": ["insight"]
        }
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
                    "description": "What to search for in team knowledge"
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="flow_status",
        description="""Get current Flow Guardian status and last captured context.
        
USE THIS WHEN:
- User asks about Flow Guardian status
- Checking if memory is connected
- Seeing what was last captured""",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
]

# ============================================================
# TOOL HANDLERS
# ============================================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return list of available tools."""
    return TOOLS

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from Claude Code."""
    
    try:
        if name == "flow_recall":
            return await tool_flow_recall(arguments)
        elif name == "flow_capture":
            return await tool_flow_capture(arguments)
        elif name == "flow_learn":
            return await tool_flow_learn(arguments)
        elif name == "flow_team":
            return await tool_flow_team(arguments)
        elif name == "flow_status":
            return await tool_flow_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def tool_flow_recall(arguments: dict) -> list[TextContent]:
    """Recall previous coding context."""
    
    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="⚠️ Flow Guardian not initialized.\n\nRun `flow init --user yourname` in terminal first."
        )]
    
    query = arguments.get("query", "recent work")
    
    # Get semantic recall from Backboard
    recall_query = f"""Recall coding context about: {query}

Please provide:
1. What was being worked on
2. Key decisions made
3. Important files involved
4. Suggested next steps

Be specific and actionable."""

    try:
        result = await recall_context(config.personal_thread_id, recall_query)
    except Exception as e:
        result = f"Could not reach memory service: {str(e)}"
    
    # Also include last local capture for immediate context
    last_capture = load_last_capture()
    
    response = "## 🔄 Retrieved Context\n\n"
    response += result if result else "No matching context found in memory."
    
    if last_capture:
        response += "\n\n---\n\n## 📌 Last Captured Session\n\n"
        response += f"**When:** {last_capture.timestamp[:19].replace('T', ' ')}\n"
        response += f"**Branch:** `{last_capture.branch}`\n"
        response += f"**Summary:** {last_capture.summary}\n"
        if last_capture.files:
            response += f"**Files:** `{', '.join(last_capture.files[:5])}`"
            if len(last_capture.files) > 5:
                response += f" (+{len(last_capture.files) - 5} more)"
    
    return [TextContent(type="text", text=response)]

async def tool_flow_capture(arguments: dict) -> list[TextContent]:
    """Capture current coding context."""
    
    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="⚠️ Flow Guardian not initialized.\n\nRun `flow init --user yourname` in terminal first."
        )]
    
    # Extract arguments
    summary = arguments.get("summary", "Coding session")
    decisions = arguments.get("decisions", [])
    next_steps = arguments.get("next_steps", [])
    blockers = arguments.get("blockers", [])
    
    # Get git state
    repo = get_repo()
    if repo:
        git_state = get_git_state(repo)
        branch = git_state.get("branch", "unknown")
        head = git_state.get("head", "unknown")
        files = git_state.get("modified_files", [])
    else:
        branch = "unknown"
        head = "unknown"
        files = []
    
    # Build context object
    context = {
        "summary": summary,
        "decisions": decisions,
        "next_steps": next_steps,
        "blockers": blockers,
        "branch": branch,
        "key_files": files[:10],
        "hypothesis": None,
        "complexity": "medium",
        "source": "claude_code_mcp"
    }
    
    # Store to Backboard
    try:
        await store_context_snapshot(config.personal_thread_id, context)
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"⚠️ Could not save to cloud memory: {str(e)}\n\nLocal state will still be saved."
        )]
    
    # Save local state
    timestamp = datetime.now().isoformat()
    save_last_capture(LastCapture(
        timestamp=timestamp,
        branch=branch,
        files=files,
        summary=summary,
        git_head=head
    ))
    
    # Build response
    response = "## ✅ Context Captured\n\n"
    response += f"**Summary:** {summary}\n\n"
    
    if decisions:
        response += "**Decisions Made:**\n"
        for d in decisions:
            response += f"  • {d}\n"
        response += "\n"
    
    if next_steps:
        response += "**Next Steps (for next session):**\n"
        for s in next_steps:
            response += f"  • {s}\n"
        response += "\n"
    
    if blockers:
        response += "**Blockers to Remember:**\n"
        for b in blockers:
            response += f"  ⚠️ {b}\n"
        response += "\n"
    
    response += f"**Branch:** `{branch}`\n"
    if files:
        response += f"**Files:** `{', '.join(files[:5])}`\n"
    
    response += "\n---\n*You can pick up where you left off by saying \"continue from last session\"*"
    
    return [TextContent(type="text", text=response)]

async def tool_flow_learn(arguments: dict) -> list[TextContent]:
    """Store a learning or insight."""
    
    config = load_config()
    if not config:
        return [TextContent(
            type="text",
            text="⚠️ Flow Guardian not initialized."
        )]
    
    insight = arguments.get("insight")
    tags = arguments.get("tags", [])
    share = arguments.get("share_with_team", False)
    
    if not insight:
        return [TextContent(type="text", text="⚠️ No insight provided.")]
    
    try:
        if share and config.team_thread_id:
            await store_team_learning(
                config.team_thread_id,
                insight,
                config.username,
                tags
            )
            response = f"## ✅ Shared with Team\n\n"
            response += f"**Insight:** {insight}\n"
            response += f"**Author:** {config.username}\n"
            if tags:
                response += f"**Tags:** {', '.join(tags)}\n"
            response += "\n*Your teammates can find this with `flow team` search.*"
        else:
            await store_learning(config.personal_thread_id, insight, tags)
            response = f"## ✅ Learning Saved\n\n"
            response += f"**Insight:** {insight}\n"
            if tags:
                response += f"**Tags:** {', '.join(tags)}\n"
            response += "\n*You can recall this later with `flow recall`.*"
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"⚠️ Could not save learning: {str(e)}")]

async def tool_flow_team(arguments: dict) -> list[TextContent]:
    """Search team's shared knowledge."""
    
    config = load_config()
    if not config:
        return [TextContent(type="text", text="⚠️ Flow Guardian not initialized.")]
    
    if not config.team_thread_id:
        return [TextContent(
            type="text",
            text="⚠️ Team memory not configured.\n\nRun `flow init --user yourname --team teamname` to set up team memory."
        )]
    
    query = arguments.get("query", "")
    if not query:
        return [TextContent(type="text", text="⚠️ No search query provided.")]
    
    try:
        result = await query_team_memory(config.team_thread_id, query)
        
        response = f"## 👥 Team Knowledge: \"{query}\"\n\n"
        response += result if result else "No matching team knowledge found."
        
        return [TextContent(type="text", text=response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"⚠️ Could not search team memory: {str(e)}")]

async def tool_flow_status(arguments: dict) -> list[TextContent]:
    """Get Flow Guardian status."""
    
    config = load_config()
    last_capture = load_last_capture()
    
    response = "## 📊 Flow Guardian Status\n\n"
    
    if config:
        response += f"**User:** {config.username}\n"
        response += f"**Personal Memory:** ✅ Connected\n"
        response += f"**Team Memory:** {'✅ Connected' if config.team_thread_id else '⭕ Not configured'}\n"
    else:
        response += "**Status:** ⚠️ Not initialized\n"
        response += "\n*Run `flow init --user yourname` in terminal to set up.*\n"
        return [TextContent(type="text", text=response)]
    
    response += "\n---\n\n"
    
    if last_capture:
        response += "## 📌 Last Capture\n\n"
        response += f"**When:** {last_capture.timestamp[:19].replace('T', ' ')}\n"
        response += f"**Branch:** `{last_capture.branch}`\n"
        response += f"**Summary:** {last_capture.summary}\n"
        if last_capture.files:
            response += f"**Files:** `{', '.join(last_capture.files[:5])}`\n"
    else:
        response += "*No context captured yet. Use `flow_capture` to save your first session.*"
    
    return [TextContent(type="text", text=response)]

# ============================================================
# MAIN ENTRY POINT
# ============================================================

async def main():
    """Run the MCP server."""
    
    # Verify environment
    if not os.environ.get("BACKBOARD_API_KEY"):
        print("Warning: BACKBOARD_API_KEY not set", file=sys.stderr)
    
    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Dependencies Installation

```bash
# Install MCP dependencies
pip install mcp cerebras-cloud-sdk httpx gitpython pydantic python-dotenv
```

---

## 7. Configuration Guide

### Step 1: Locate Claude Code Config

Claude Code stores its configuration in different locations depending on your OS:

| OS | Config Location |
|----|-----------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

For Claude Code CLI, the config is typically at:
```
~/.claude/config.json
```

### Step 2: Add Flow Guardian MCP Server

Edit the config file to add Flow Guardian:

```json
{
  "mcpServers": {
    "flow-guardian": {
      "command": "python",
      "args": [
        "/absolute/path/to/flow-guardian/mcp_server.py"
      ],
      "env": {
        "CEREBRAS_API_KEY": "csk-your-key-here",
        "BACKBOARD_API_KEY": "bb-your-key-here",
        "BACKBOARD_BASE_URL": "https://app.backboard.io/api"
      }
    }
  }
}
```

**Important Notes:**
- Use **absolute paths** for the Python script
- Include all required environment variables
- JSON must be valid (no trailing commas)

### Step 3: Alternative - Use a Wrapper Script

For easier management, create a wrapper script:

```bash
#!/bin/bash
# flow-guardian-mcp.sh

# Set environment
export CEREBRAS_API_KEY="csk-your-key-here"
export BACKBOARD_API_KEY="bb-your-key-here"
export BACKBOARD_BASE_URL="https://app.backboard.io/api"

# Activate virtual environment (if using one)
source /path/to/flow-guardian/venv/bin/activate

# Run MCP server
python /path/to/flow-guardian/mcp_server.py
```

Then configure Claude Code to use the wrapper:

```json
{
  "mcpServers": {
    "flow-guardian": {
      "command": "/path/to/flow-guardian-mcp.sh",
      "args": []
    }
  }
}
```

### Step 4: Restart Claude Code

After configuration:
1. Completely quit Claude Code
2. Restart Claude Code
3. Flow Guardian tools should now be available

### Step 5: Verify Installation

In Claude Code, try:
```
What tools do you have available from Flow Guardian?
```

Claude should respond listing the five Flow Guardian tools.

---

## 8. Testing Procedures

### Test 1: MCP Server Starts

```bash
# Run server directly to check for errors
python mcp_server.py

# Should not produce any output (waiting for stdio)
# Press Ctrl+C to exit
```

### Test 2: Tool Listing

In Claude Code:
```
List all your available tools and briefly describe each one.
```

**Expected:** Claude lists flow_recall, flow_capture, flow_learn, flow_team, flow_status

### Test 3: Status Check

In Claude Code:
```
Check Flow Guardian status
```

**Expected:** Shows config status and last capture (if any)

### Test 4: Capture → Recall Cycle

```
# Step 1: In Claude Code
Let's pretend we're working on a user authentication feature. 
We decided to use JWT with 15-minute access tokens.
Now capture this context.

# Expected: Claude calls flow_capture, shows confirmation

# Step 2: Start new Claude Code session (or ask Claude to forget)
Recall what we were working on with authentication

# Expected: Claude calls flow_recall, returns JWT context
```

### Test 5: Learning System

```
# Step 1: Store a learning
I just discovered that JWT timestamps are always in UTC. 
Remember this and share with team.

# Expected: Claude calls flow_learn with share_with_team=true

# Step 2: Search team knowledge
Has anyone on the team dealt with timezone issues in JWT?

# Expected: Claude calls flow_team, returns the learning
```

### Test 6: Error Handling

```
# Test without initialization
# (Delete .flowguardian folder first)
rm -rf .flowguardian

# Then in Claude Code:
Recall my previous work

# Expected: Claude shows "Flow Guardian not initialized" message
```

### Automated Test Script

```python
# test_mcp_tools.py
"""Test Flow Guardian MCP tools."""
import asyncio
import sys
sys.path.insert(0, '.')

from mcp_server import (
    tool_flow_status,
    tool_flow_capture,
    tool_flow_recall,
    tool_flow_learn
)

async def run_tests():
    print("=" * 50)
    print("Flow Guardian MCP Tool Tests")
    print("=" * 50)
    
    # Test 1: Status
    print("\n[Test 1] flow_status")
    result = await tool_flow_status({})
    print(result[0].text[:200] + "...")
    
    # Test 2: Capture
    print("\n[Test 2] flow_capture")
    result = await tool_flow_capture({
        "summary": "Testing MCP integration",
        "decisions": ["Use pytest for testing"],
        "next_steps": ["Add more tests"]
    })
    print(result[0].text[:200] + "...")
    
    # Test 3: Recall
    print("\n[Test 3] flow_recall")
    result = await tool_flow_recall({
        "query": "testing"
    })
    print(result[0].text[:200] + "...")
    
    # Test 4: Learn
    print("\n[Test 4] flow_learn")
    result = await tool_flow_learn({
        "insight": "MCP servers communicate via stdio",
        "tags": ["mcp", "architecture"]
    })
    print(result[0].text[:200] + "...")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_tests())
```

---

## 9. Usage Examples

### Example 1: Starting a New Session

**User:** Continue working on what we did yesterday

**Claude Code:** *[calls flow_recall with query "yesterday's work"]*

> Based on your Flow Guardian memory, yesterday you were:
>
> **Working on:** Refactoring the authentication module to support OAuth2
>
> **Key Decisions:**
> - Using PKCE flow for mobile clients
> - Storing tokens in Redis with 1-hour TTL
> - Adding refresh token rotation
>
> **Files:** `src/auth/oauth.py`, `src/auth/tokens.py`
>
> **Next Step:** Implement the token refresh endpoint
>
> Shall I continue from the token refresh endpoint?

### Example 2: Ending a Session

**User:** I need to head out, let's save our progress

**Claude Code:** *[calls flow_capture with current context]*

> ✅ Context Captured
>
> **Summary:** Implementing OAuth2 token refresh endpoint
>
> **Decisions Made:**
> - Token rotation on every refresh
> - Blacklist old refresh tokens in Redis
> - Return 401 for reused tokens (detect theft)
>
> **Next Steps:**
> - Add rate limiting to refresh endpoint
> - Write integration tests
> - Update API documentation
>
> **Branch:** `feature/oauth2-refresh`
> **Files:** `src/auth/tokens.py`, `tests/test_tokens.py`
>
> You can pick up where you left off by saying "continue from last session"

### Example 3: Storing a Learning

**User:** Oh interesting, I just realized that refresh tokens should be single-use to prevent replay attacks

**Claude Code:** *[calls flow_learn with share_with_team=true]*

> ✅ Shared with Team
>
> **Insight:** Refresh tokens should be single-use to prevent replay attacks - implement token rotation on every refresh
>
> **Author:** raz
> **Tags:** auth, security, oauth2
>
> Your teammates can find this with a team search.

### Example 4: Searching Team Knowledge

**User:** Has anyone on the team dealt with rate limiting auth endpoints?

**Claude Code:** *[calls flow_team with query "rate limiting auth"]*

> ## 👥 Team Knowledge: "rate limiting auth"
>
> **From Sarah (2 weeks ago):**
> "Auth endpoints should have stricter rate limits - we use 10 req/min for login, 30 req/min for token refresh. Store counters in Redis with sliding window."
>
> **From Mike (1 month ago):**
> "Remember to rate limit by both IP and user ID for auth endpoints - prevents distributed attacks while allowing legitimate users behind NAT."

### Example 5: Checking Status

**User:** Is Flow Guardian connected?

**Claude Code:** *[calls flow_status]*

> ## 📊 Flow Guardian Status
>
> **User:** raz
> **Personal Memory:** ✅ Connected
> **Team Memory:** ✅ Connected
>
> ---
>
> ## 📌 Last Capture
>
> **When:** 2026-01-16 14:30:00
> **Branch:** `feature/oauth2-refresh`
> **Summary:** Implementing OAuth2 token refresh endpoint
> **Files:** `src/auth/tokens.py`, `tests/test_tokens.py`

---

## 10. Troubleshooting

### Issue: "Flow Guardian not initialized"

**Cause:** The `.flowguardian` directory doesn't exist

**Solution:**
```bash
# In your project directory
flow init --user yourname

# Or with team
flow init --user yourname --team yourteam
```

### Issue: MCP Server Not Found

**Cause:** Claude Code can't find the Python script

**Solution:**
1. Check the path in config is absolute
2. Verify Python is in PATH
3. Check file permissions

```bash
# Test the path
python /your/path/to/mcp_server.py
# Should start without errors
```

### Issue: "BACKBOARD_API_KEY not set"

**Cause:** Environment variables not passed to MCP server

**Solution:**
1. Add env variables to Claude Code config
2. Or use wrapper script with exports
3. Or add to system environment

### Issue: Tools Not Appearing

**Cause:** MCP server not properly registered

**Solution:**
1. Verify JSON config is valid (no syntax errors)
2. Restart Claude Code completely
3. Check Claude Code logs for errors

```bash
# View logs (macOS)
tail -f ~/Library/Logs/Claude/mcp.log
```

### Issue: Slow Responses

**Cause:** Backboard.io API latency

**Solution:**
1. Check internet connection
2. Verify API key is valid
3. Check Backboard.io status page

### Issue: "Could not reach memory service"

**Cause:** Network or API issues

**Solution:**
1. Test API directly:
```bash
curl -H "Authorization: Bearer $BACKBOARD_API_KEY" \
     https://app.backboard.io/api/assistants
```
2. Check firewall settings
3. Verify API key permissions

### Debug Mode

Enable verbose logging:

```python
# At top of mcp_server.py
import logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='/tmp/flow-guardian-mcp.log'
)
```

Then check logs:
```bash
tail -f /tmp/flow-guardian-mcp.log
```

---

## 11. Demo Script

### Setup (Before Demo)

1. ✅ Flow Guardian initialized (`flow init`)
2. ✅ MCP server configured in Claude Code
3. ✅ Some pre-captured context in memory
4. ✅ A realistic project to demonstrate with

### Demo Script (3 minutes)

**[0:00 - 0:30] The Problem**

> "Claude Code is amazing, but it has goldfish memory. Every session starts fresh. Watch what happens when I try to continue yesterday's work..."

*Open Claude Code fresh*

```
Continue the auth refactoring from yesterday
```

*Claude responds: "I don't have context from previous sessions..."*

> "I now have to spend 20 minutes re-explaining everything."

**[0:30 - 1:00] The Solution**

> "But with Flow Guardian integrated as an MCP server..."

*Show the config briefly*

> "Claude Code now has access to persistent memory."

**[1:00 - 1:45] Demo: Recall**

```
Continue the auth refactoring from yesterday
```

*Claude calls flow_recall, returns full context*

> "Claude instantly knows what I was working on, the decisions I made, and where to continue. That's Backboard.io's semantic memory in action."

**[1:45 - 2:15] Demo: Capture**

> "And when I need to stop..."

```
I need to head out. Save our progress - we decided to use 
Redis for token storage and the next step is adding tests.
```

*Claude calls flow_capture, shows confirmation*

> "Context captured. Tomorrow I can pick up exactly where I left off."

**[2:15 - 2:45] Demo: Team Knowledge**

> "But here's the really powerful part - team memory."

```
I just realized that refresh tokens should be rotated on 
every use. Share this with the team.
```

*Claude calls flow_learn with share_with_team=true*

```
Has anyone dealt with token security best practices?
```

*Claude calls flow_team, returns the learning*

> "Knowledge compounds across the team. No more re-learning the same lessons."

**[2:45 - 3:00] Close**

> "Flow Guardian + Claude Code. Persistent memory for AI coding sessions. Built with Cerebras for instant inference and Backboard.io for semantic memory. Never lose context again."

---

## Appendix: Quick Reference

### MCP Tool Summary

| Tool | Trigger Phrases | Key Arguments |
|------|-----------------|---------------|
| `flow_recall` | "continue from", "what were we working on", "yesterday" | `query` |
| `flow_capture` | "save progress", "I need to stop", "remember this session" | `summary`, `decisions`, `next_steps` |
| `flow_learn` | "remember this", "note this down", "save this insight" | `insight`, `tags`, `share_with_team` |
| `flow_team` | "has anyone", "team knowledge", "what did others find" | `query` |
| `flow_status` | "is Flow Guardian connected", "status" | (none) |

### File Locations

| File | Purpose |
|------|---------|
| `mcp_server.py` | MCP server entry point |
| `.flowguardian/config.json` | Assistant IDs, username |
| `.flowguardian/last_capture.json` | Most recent capture |
| `~/.claude/config.json` | Claude Code MCP config |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CEREBRAS_API_KEY` | Yes | Cerebras Cloud API key |
| `BACKBOARD_API_KEY` | Yes | Backboard.io API key |
| `BACKBOARD_BASE_URL` | No | API base URL (default: https://app.backboard.io/api) |

---

*End of MCP Setup Plan*