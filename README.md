# Flow Guardian

**"Claude forgets. Flow Guardian remembers."**

Persistent memory for AI coding sessions. Save your context, learnings, and decisions — restore them automatically in future sessions.

Built for the [8090 x Highline Beta: Build for Builders Hackathon](https://lu.ma/8090-hackathon).

## The Problem

1. You have a great coding session with Claude
2. You figure out how your codebase works, debug issues, make decisions
3. Session ends or context fills up
4. **Claude has amnesia.** You explain the same things. Again.

## The Solution

Flow Guardian automatically captures your session context and restores it when you return — no manual commands needed.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HOW FLOW GUARDIAN WORKS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   SESSION 1                          SESSION 2 (Next Day)                   │
│   ─────────                          ────────────────────                   │
│                                                                              │
│   You: "Debug the JWT auth"          You: "Continue working"                │
│        │                                   │                                │
│        ▼                                   ▼                                │
│   ┌─────────────┐                    ┌─────────────────────────────────┐   │
│   │ Claude works│                    │ Flow Guardian auto-injects:     │   │
│   │ finds bug   │                    │                                 │   │
│   │ fixes code  │                    │ "You were debugging JWT auth.   │   │
│   └─────────────┘                    │  Your hypothesis: off-by-one    │   │
│        │                             │  in timestamp comparison.       │   │
│        ▼                             │  Files: src/auth.py             │   │
│   Session ends                       │  Status: Fix verified"          │   │
│        │                             └─────────────────────────────────┘   │
│        ▼                                   │                                │
│   ┌─────────────────┐                      ▼                                │
│   │ Auto-captured:  │                Claude immediately knows context       │
│   │ • Goal          │                No re-explaining needed!               │
│   │ • Hypothesis    │                                                       │
│   │ • Files touched │                                                       │
│   │ • Branch        │                                                       │
│   └─────────────────┘                                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Innovation: 97% Token Savings

Flow Guardian's TLDR system compresses context before injection:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TLDR TOKEN EFFICIENCY                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Without Flow Guardian          With Flow Guardian                     │
│   ──────────────────────         ───────────────────                    │
│                                                                         │
│   Raw file read: 51,612 tokens   TLDR summary: 1,480 tokens            │
│                                                                         │
│   ████████████████████████████   █                                      │
│                                                                         │
│   Context fills up fast          97% SAVINGS = More room for work      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FLOW GUARDIAN                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         HOOKS (Automatic)                              │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                                                                        │  │
│  │  SessionStart ──► Auto-inject context from last session               │  │
│  │                                                                        │  │
│  │  PreToolUse:Read ──► TLDR Enforcer (97% token savings)                │  │
│  │                                                                        │  │
│  │  PreCompact ──► Save state before context compaction                  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CORE MODULES                                   │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                                                                        │  │
│  │  handoff.py ──► YAML checkpoints (.flow-guardian/handoff.yaml)        │  │
│  │                                                                        │  │
│  │  tldr.py ──► Cerebras-powered summarization (L0/L1/L2 depth)          │  │
│  │                                                                        │  │
│  │  inject.py ──► Context injection orchestrator                         │  │
│  │                                                                        │  │
│  │  memory.py ──► Local JSON storage (~/.flow-guardian/)                 │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CLOUD SERVICES                                 │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                                                                        │  │
│  │  Backboard.io ──► Semantic memory (search past sessions by meaning)   │  │
│  │                   Model: Gemini 2.5 Flash                              │  │
│  │                                                                        │  │
│  │  Cerebras ──► Fast LLM inference for TLDR generation                  │  │
│  │              Model: zai-glm-4.7 (3000+ tokens/sec)                     │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
cd flow-web && npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with:
# - CEREBRAS_API_KEY
# - BACKBOARD_API_KEY
# - BACKBOARD_PERSONAL_THREAD_ID
```

### 3. Setup Flow Guardian in Your Project
```bash
cd your-project
flow setup  # Creates .flow-guardian/ and hooks
```

### 4. Start Working
```bash
# Start a Claude Code session - context auto-injects!
claude

# Manually save progress anytime
flow save --summary "Working on auth" --hypothesis "Token expiry bug"

# Search past sessions
flow recall "authentication"

# Store a learning
flow learn "PyMuPDF requires pip install pymupdf" --tags pdf,dependency
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `flow setup` | Initialize Flow Guardian in a project |
| `flow save` | Checkpoint current session state |
| `flow inject` | Manually inject context (usually automatic) |
| `flow recall <query>` | Search memory semantically |
| `flow learn <insight>` | Store a persistent learning |
| `flow status` | Check system status |
| `flow history` | View session history |

## MCP Tools (for Claude Code)

```python
flow_capture(summary, decisions, next_steps, blockers)  # Save context
flow_recall(query)                                       # Search memory
flow_learn(insight, tags, share_with_team)              # Store learning
flow_team(query)                                         # Search team knowledge
flow_status()                                            # Check status
```

## Web Interface

A conversational chat interface for searching team knowledge:

```bash
cd flow-web && npm run dev
# Open http://localhost:3000
```

```
You: What library did we install for PDF uploads?
Flow: The library installed is PyMuPDF.
      Source: learning, Time: 2026-01-17
```

## How It Works

### Handoff System
Every session state is captured in `.flow-guardian/handoff.yaml`:

```yaml
goal: "Implement user authentication with JWT"
status: in_progress
now: "Debugging token expiry in auth.py"
hypothesis: "Off-by-one error in timestamp comparison"
files:
  - src/auth.py
  - tests/test_auth.py
branch: fix/jwt-expiry
timestamp: 2026-01-17T10:30:00Z
```

### TLDR System (Token Efficiency)
Never inject raw content. Summarize via Cerebras first:

- **L0**: File paths + function names only (~100 tokens)
- **L1**: + One-line descriptions (~500 tokens)
- **L2**: + Key logic summaries (~2000 tokens)

### Hooks (Automatic)
No manual commands needed. Hooks fire automatically:

| Hook | When | Action |
|------|------|--------|
| SessionStart | New session | Inject context from handoff.yaml |
| PreToolUse:Read | Reading files | TLDR summary instead of raw (97% savings) |
| PreCompact | Before compaction | Save state to handoff.yaml |

## File Structure

```
flow-guardian/
├── .claude/
│   ├── settings.json           # Hook configuration
│   └── hooks/
│       ├── flow-inject.sh      # SessionStart hook
│       ├── flow-precompact.sh  # PreCompact hook
│       └── tldr-read-enforcer.py  # TLDR Read Enforcer
├── .flow-guardian/
│   ├── config.yaml             # Project config
│   └── handoff.yaml            # Session state checkpoint
├── handoff.py                  # YAML checkpoint management
├── tldr.py                     # Token-efficient summarization
├── inject.py                   # Context injection orchestrator
├── flow_cli.py                 # CLI commands
├── memory.py                   # Local JSON storage
├── backboard_client.py         # Backboard.io integration
├── cerebras_client.py          # Cerebras LLM client
├── server.py                   # Unified backend (daemon + API + MCP)
├── flow-web/                   # Next.js web interface
└── tests/                      # 413 tests
```

## Tech Stack

- **Cerebras** — Fast LLM inference (zai-glm-4.7, 3000+ tokens/sec)
- **Backboard.io** — Semantic memory with Gemini 2.5 Flash
- **Next.js 14+** — React framework for web UI
- **FastAPI** — Python backend
- **Claude Code Hooks** — Automatic context injection

## Test Results

```
413 tests passing
97% token savings with TLDR
< 2 second context injection
```

## License

MIT
