# Flow Guardian System Architecture

## Overview

Flow Guardian provides persistent memory for AI coding sessions. It automatically captures context when developers stop working and restores it when they return — no manual commands needed.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM OVERVIEW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                          ┌─────────────────┐                                 │
│                          │   Claude Code   │                                 │
│                          │    Session      │                                 │
│                          └────────┬────────┘                                 │
│                                   │                                          │
│                    ┌──────────────┼──────────────┐                          │
│                    │              │              │                          │
│                    ▼              ▼              ▼                          │
│           ┌────────────┐  ┌────────────┐  ┌────────────┐                    │
│           │SessionStart│  │PreToolUse  │  │ PreCompact │                    │
│           │   Hook     │  │  :Read     │  │   Hook     │                    │
│           └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                    │
│                 │               │               │                          │
│                 ▼               ▼               ▼                          │
│           Auto-inject     TLDR summary    Save state                       │
│           context         (97% savings)   before compact                   │
│                                                                              │
│                    ┌──────────────┴──────────────┐                          │
│                    │                             │                          │
│                    ▼                             ▼                          │
│           ┌────────────────┐           ┌────────────────┐                   │
│           │  Local Storage │           │ Cloud Services │                   │
│           │ .flow-guardian/│           │   Backboard    │                   │
│           │  ~/.flow-      │           │   Cerebras     │                   │
│           │    guardian/   │           │                │                   │
│           └────────────────┘           └────────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Hooks System (Automatic Context Management)

The hooks system is the core innovation — everything happens automatically.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOOKS ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ SessionStart Hook                                                        ││
│  │ ════════════════                                                         ││
│  │ Trigger: New Claude Code session starts                                  ││
│  │ Script: .claude/hooks/flow-inject.sh                                     ││
│  │                                                                          ││
│  │ Action:                                                                  ││
│  │   1. Load .flow-guardian/handoff.yaml                                    ││
│  │   2. Query Backboard for semantic context                                ││
│  │   3. Generate TLDR summary via Cerebras                                  ││
│  │   4. Output to stdout → injected into Claude's context                   ││
│  │                                                                          ││
│  │ Result: Claude immediately knows what you were working on                ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PreToolUse:Read Hook (TLDR Enforcer)                                     ││
│  │ ════════════════════════════════════                                     ││
│  │ Trigger: Claude attempts to read any file                                ││
│  │ Script: .claude/hooks/tldr-read-enforcer.py                              ││
│  │                                                                          ││
│  │ Action:                                                                  ││
│  │   1. Check if file should bypass (config, tests, small files)            ││
│  │   2. If code file: generate TLDR via Cerebras                            ││
│  │   3. Return summary instead of raw content                               ││
│  │   4. 97% token savings!                                                  ││
│  │                                                                          ││
│  │ Bypass Rules:                                                            ││
│  │   • Config files: .json, .yaml, .toml, .env, .ini                       ││
│  │   • Test files: test_*.py, *_test.py                                    ││
│  │   • Small files: < 100 lines                                            ││
│  │   • Non-code: .md, .txt, images                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PreCompact Hook                                                          ││
│  │ ═══════════════                                                          ││
│  │ Trigger: Context compaction about to happen                              ││
│  │ Script: .claude/hooks/flow-precompact.sh                                 ││
│  │                                                                          ││
│  │ Action:                                                                  ││
│  │   1. Run `flow save --auto`                                              ││
│  │   2. Capture current state to handoff.yaml                               ││
│  │   3. Sync to Backboard                                                   ││
│  │                                                                          ││
│  │ Result: Nothing lost when context compacts                               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Hook Configuration (`.claude/settings.json`)

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": ".claude/hooks/flow-inject.sh"
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/tldr-read-enforcer.py",
            "timeout": 30
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "type": "command",
        "command": ".claude/hooks/flow-precompact.sh"
      }
    ]
  }
}
```

## Handoff System

YAML checkpoints that persist session state across restarts.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HANDOFF SYSTEM                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  .flow-guardian/handoff.yaml                                                 │
│  ───────────────────────────                                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ goal: "Implement user authentication with JWT"                          ││
│  │ status: in_progress                                                     ││
│  │ now: "Debugging token expiry in auth.py"                                ││
│  │ hypothesis: "Off-by-one error in timestamp comparison"                  ││
│  │ outcome: null                                                           ││
│  │ files:                                                                  ││
│  │   - src/auth.py                                                         ││
│  │   - tests/test_auth.py                                                  ││
│  │ branch: fix/jwt-expiry                                                  ││
│  │ session_id: session_2026-01-17_10-30-00                                 ││
│  │ timestamp: '2026-01-17T10:30:00Z'                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  Auto-updated on:                                                            │
│  • `flow save` (manual checkpoint)                                          │
│  • Session end (daemon captures)                                            │
│  • PreCompact hook (before context compaction)                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## TLDR System (Token Efficiency)

Never inject raw content. Summarize via Cerebras first.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TLDR TOKEN EFFICIENCY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Raw Content (14 files)                    TLDR Summary                      │
│  ──────────────────────                    ────────────                      │
│  51,612 tokens                             1,480 tokens                      │
│                                                                              │
│  ████████████████████████████████████████  █                                │
│                                                                              │
│                           97% SAVINGS                                        │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TLDR Depth Levels:                                                          │
│                                                                              │
│  L0 (Skeleton)    ~100 tokens   File paths + function signatures            │
│  L1 (Standard)    ~500 tokens   + One-line descriptions (DEFAULT)           │
│  L2 (Detailed)    ~2000 tokens  + Key logic summaries                       │
│                                                                              │
│  Usage: `flow inject --level L2` or in code: tldr.generate(content, "L2")  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Session Start (Automatic)
```
New Claude Session
       │
       ▼
┌─────────────────┐
│ SessionStart    │
│ Hook fires      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ flow-inject.sh  │
│ runs            │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│handoff│ │ Backboard │
│ .yaml │ │  recall   │
└───┬───┘ └─────┬─────┘
    │           │
    └─────┬─────┘
          │
          ▼
┌─────────────────┐
│ Cerebras TLDR   │
│ (if too long)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Inject into     │
│ Claude context  │
└─────────────────┘
```

### File Read (TLDR Enforcer)
```
Claude: Read(file.py)
       │
       ▼
┌─────────────────┐
│ PreToolUse:Read │
│ Hook fires      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ tldr-read-      │
│ enforcer.py     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│Bypass?│ │ Generate  │
│ YES   │ │   TLDR    │
└───┬───┘ └─────┬─────┘
    │           │
    ▼           ▼
┌───────┐ ┌───────────┐
│ Allow │ │ Return    │
│ raw   │ │ summary   │
│ read  │ │ (deny raw)│
└───────┘ └───────────┘
```

### Context Save
```
User: flow save --summary "..."
       │
       ▼
┌─────────────────┐
│  flow_cli.py    │
│  save command   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│handoff│ │ Backboard │
│ .yaml │ │  store    │
└───────┘ └───────────┘
```

## Component Details

### 1. CLI (`flow_cli.py`)

The main interface for developers.

| Command | Description |
|---------|-------------|
| `flow setup` | Initialize .flow-guardian/ in project |
| `flow save` | Checkpoint current session state |
| `flow inject` | Manually inject context (usually automatic) |
| `flow recall <query>` | Search memory semantically |
| `flow learn <insight>` | Store persistent learning |
| `flow status` | Check system status |
| `flow history` | View session history |

### 2. MCP Server (`mcp_server.py`)

Entry point for Claude Code integration via Model Context Protocol.

| Tool | Purpose |
|------|---------|
| `flow_recall` | Retrieve past context |
| `flow_capture` | Save current context |
| `flow_learn` | Store insights |
| `flow_team` | Search team knowledge |
| `flow_status` | Check system state |

### 3. Services Layer (`services/`)

Shared business logic.

```
services/
├── __init__.py
├── config.py        # FlowConfig: Environment configuration
├── models.py        # Pydantic request/response models
└── flow_service.py  # FlowService: Core business logic
```

### 4. Storage

**Local Storage (`memory.py`):**
- Location: `~/.flow-guardian/`
- Format: JSON files
- Always available (offline fallback)

**Project Storage (`.flow-guardian/`):**
- `handoff.yaml` — Session state checkpoint
- `config.yaml` — Project configuration
- `sessions/` — Session history

**Cloud Storage (Backboard.io):**
- Semantic search via embeddings
- Cross-device sync
- Team knowledge sharing
- Model: Gemini 2.5 Flash

### 5. LLM Integration

**Cerebras (`cerebras_client.py`):**
- Model: zai-glm-4.7
- Speed: 3000+ tokens/sec
- Used for: TLDR generation, context analysis

**Backboard.io (`backboard_client.py`):**
- Semantic memory storage
- memory="auto" for retrieval
- Model: Gemini 2.5 Flash

## File Structure

```
flow-guardian/
├── .claude/
│   ├── settings.json              # Hook configuration
│   └── hooks/
│       ├── flow-inject.sh         # SessionStart hook
│       ├── flow-precompact.sh     # PreCompact hook
│       └── tldr-read-enforcer.py  # TLDR Read Enforcer
├── .flow-guardian/
│   ├── config.yaml                # Project config
│   └── handoff.yaml               # Session state checkpoint
├── api/
│   ├── server.py                  # FastAPI application
│   └── dependencies.py            # Dependency injection
├── services/
│   ├── config.py                  # Configuration management
│   ├── models.py                  # Pydantic models
│   └── flow_service.py            # Core business logic
├── scripts/
│   └── benchmark_tokens.py        # Token efficiency benchmark
├── flow-web/                      # Next.js web interface
├── tests/                         # 413 tests
│
├── handoff.py                     # YAML checkpoint management
├── tldr.py                        # Token-efficient summarization
├── inject.py                      # Context injection orchestrator
├── flow_cli.py                    # CLI commands
├── memory.py                      # Local JSON storage
├── backboard_client.py            # Backboard.io API client
├── cerebras_client.py             # Cerebras API client
├── capture.py                     # Git context capture
├── restore.py                     # Context restoration
├── daemon.py                      # Background session watcher
├── server.py                      # Unified backend
├── mcp_server.py                  # MCP server for Claude
│
├── .mcp.json                      # MCP server config
├── .env                           # API keys (not in git)
├── CLAUDE.md                      # Instructions for Claude
└── requirements.txt               # Dependencies
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CEREBRAS_API_KEY` | Yes | Cerebras API key |
| `BACKBOARD_API_KEY` | Yes* | Backboard.io API key |
| `BACKBOARD_PERSONAL_THREAD_ID` | Yes* | Personal memory thread |
| `BACKBOARD_TEAM_THREAD_ID` | No | Team memory thread |
| `FLOW_GUARDIAN_USER` | No | Username for attribution |

*Required for cloud features; local storage works without them.

### MCP Configuration (`.mcp.json`)

```json
{
  "mcpServers": {
    "flow-guardian": {
      "command": "/opt/homebrew/bin/python3.10",
      "args": ["mcp_server.py"],
      "env": {
        "BACKBOARD_API_KEY": "...",
        "BACKBOARD_PERSONAL_THREAD_ID": "..."
      }
    }
  }
}
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| LLM (TLDR) | Cerebras (zai-glm-4.7) |
| Cloud Memory | Backboard.io (Gemini 2.5 Flash) |
| HTTP API | FastAPI + Uvicorn |
| MCP Server | mcp library (Anthropic) |
| HTTP Client | httpx (async) |
| CLI | Click + Rich |
| Validation | Pydantic |
| Testing | pytest + pytest-asyncio |
| Web UI | Next.js 14+ |

## Test Results

```
413 tests passing
97% token savings with TLDR
< 2 second context injection
```
