# Flow Guardian System Architecture

## Overview

Flow Guardian provides persistent memory for AI coding sessions. It captures context when developers stop working and restores it when they return.

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
│  │                         MCP SERVER                                       ││
│  │                      (mcp_server.py)                                     ││
│  │                                                                          ││
│  │   5 Tools: flow_recall, flow_capture, flow_learn, flow_team, flow_status││
│  │                              │                                           ││
│  └──────────────────────────────┼───────────────────────────────────────────┘│
│                                 │                                            │
│                                 ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      SERVICES LAYER                                      ││
│  │                   (services/flow_service.py)                             ││
│  │                                                                          ││
│  │   FlowService: Core business logic for all operations                   ││
│  │   - capture_context()  - recall_context()  - store_learning()           ││
│  │   - query_team()       - get_status()                                   ││
│  │                              │                                           ││
│  └──────────────────────────────┼───────────────────────────────────────────┘│
│                                 │                                            │
│         ┌───────────────────────┼───────────────────────┐                   │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  ┌─────────────┐    ┌───────────────────┐    ┌─────────────────┐           │
│  │   capture   │    │ backboard_client  │    │     memory      │           │
│  │   restore   │    │ cerebras_client   │    │  (local JSON)   │           │
│  │  (git ops)  │    │  (API clients)    │    │ ~/.flow-guardian│           │
│  └─────────────┘    └───────────────────┘    └─────────────────┘           │
│                                 │                                            │
└─────────────────────────────────┼────────────────────────────────────────────┘
                                  │
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CLOUD SERVICES                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         BACKBOARD.IO                                     ││
│  │                   (Semantic Memory Storage)                              ││
│  │                                                                          ││
│  │  - Assistants: Named memory containers                                  ││
│  │  - Threads: Conversation/context streams                                ││
│  │  - Messages: Individual context snapshots                               ││
│  │  - memory="auto": Semantic search & retrieval                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         CEREBRAS                                         ││
│  │                    (Fast LLM Inference)                                  ││
│  │                                                                          ││
│  │  - Model: Llama 3.3 70B                                                 ││
│  │  - Speed: 3000+ tokens/sec                                              ││
│  │  - Used for: Context analysis & summarization                           ││
│  │                                                                          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. MCP Server (`mcp_server.py`)

Entry point for Claude Code integration via Model Context Protocol.

**Tools exposed:**
| Tool | Purpose | Trigger |
|------|---------|---------|
| `flow_recall` | Retrieve past context | "continue from yesterday" |
| `flow_capture` | Save current context | "save progress", before /compact |
| `flow_learn` | Store insights | "remember this" |
| `flow_team` | Search team knowledge | "has anyone dealt with" |
| `flow_status` | Check system state | "is Flow Guardian connected" |

**Communication:** JSON-RPC over stdio

### 2. HTTP API (`api/server.py`)

FastAPI REST server for external integrations.

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/capture` | Save context |
| POST | `/recall` | Search memory |
| POST | `/learn` | Store learning |
| POST | `/team` | Search team |
| GET | `/status` | System status |

**Port:** 8090
**Docs:** http://localhost:8090/docs

### 3. Services Layer (`services/`)

Shared business logic used by both MCP server and HTTP API.

```
services/
├── __init__.py
├── config.py        # FlowConfig: Environment configuration
├── models.py        # Pydantic request/response models
└── flow_service.py  # FlowService: Core business logic
```

### 4. Storage Layer

**Local Storage (`memory.py`):**
- Location: `~/.flow-guardian/`
- Format: JSON files
- Always available (offline fallback)

**Cloud Storage (Backboard.io):**
- Semantic search via embeddings
- Cross-device sync
- Team knowledge sharing

### 5. Context Capture (`capture.py`, `restore.py`)

**Captures:**
- Git state (branch, uncommitted files, recent commits)
- User-provided summary
- Decisions made
- Next steps
- Blockers

**Restores:**
- Detects changes since last capture
- Generates welcome-back message
- Identifies conflicts

## Data Flow

### Capture Flow
```
User: "Save my progress"
         │
         ▼
┌─────────────────┐
│  flow_capture   │
│  (MCP tool)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FlowService.   │
│  capture_context│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│ Local │ │ Backboard │
│ JSON  │ │ (cloud)   │
└───────┘ └───────────┘
```

### Recall Flow
```
User: "What were we working on?"
         │
         ▼
┌─────────────────┐
│  flow_recall    │
│  (MCP tool)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FlowService.   │
│  recall_context │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Try Backboard   │────▶│ Fallback to     │
│ semantic search │     │ local keyword   │
└─────────────────┘     └─────────────────┘
```

## File Structure

```
flow-guardian/
├── mcp_server.py           # MCP server entry point
├── api/
│   ├── server.py           # FastAPI application
│   ├── dependencies.py     # Dependency injection
│   └── routes/             # API endpoints
│       ├── capture.py
│       ├── recall.py
│       ├── learn.py
│       ├── team.py
│       └── status.py
├── services/
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic models
│   └── flow_service.py     # Core business logic
├── backboard_client.py     # Backboard.io API client
├── cerebras_client.py      # Cerebras API client
├── capture.py              # Git context capture
├── restore.py              # Context restoration
├── memory.py               # Local JSON storage
├── flow.py                 # CLI commands
├── tests/
│   ├── test_api/           # API tests
│   ├── test_mcp/           # MCP tests
│   └── test_services/      # Service tests
├── .mcp.json               # MCP server config for Claude
├── .env                    # API keys (not in git)
├── CLAUDE.md               # Instructions for Claude
└── requirements.txt        # Dependencies
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BACKBOARD_API_KEY` | Yes* | Backboard.io API key |
| `CEREBRAS_API_KEY` | No | Cerebras API key |
| `FLOW_GUARDIAN_USER` | Yes | Username for attribution |
| `BACKBOARD_PERSONAL_THREAD_ID` | Yes* | Personal memory thread |
| `BACKBOARD_TEAM_THREAD_ID` | No | Team memory thread |

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
| HTTP API | FastAPI + Uvicorn |
| MCP Server | mcp library (Anthropic) |
| HTTP Client | httpx (async) |
| CLI | Click + Rich |
| Validation | Pydantic |
| Testing | pytest + pytest-asyncio |
| Cloud Memory | Backboard.io |
| LLM | Cerebras (Llama 3.3 70B) |
