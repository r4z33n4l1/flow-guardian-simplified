# Flow Guardian

**Persistent memory for AI coding sessions — now as an OpenClaw skill.**

Flow Guardian captures your coding session context (goals, hypotheses, decisions, files) and restores it seamlessly in future sessions. With AST-based TLDR compression, it achieves 97% token savings while preserving the exact symbols your agent needs.

## Features

- 🧠 **Structured Handoffs** — Save/restore session state as goal + status + hypothesis + files + branch
- 📦 **97% Token Savings** — TLDR compression at L0/L1/L2/L3 depth levels
- 🌳 **AST-Aware Code TLDR** — Python/JS/TS structure extraction via AST parsing (no LLM needed)
- 🔀 **Git Context** — Auto-capture branch, modified files, recent commits
- 📝 **Learning Extraction** — Identify and store insights from sessions
- 🔒 **Zero External Services** — No API keys. No cloud. Pure local processing.
- ⚡ **OpenClaw Native** — Skill + Hook integration with OpenClaw's memory and session system

## Quick Start (OpenClaw)

```bash
# Install skill + hook
cp -r skill/flow-guardian/ ~/.openclaw/skills/flow-guardian/
cp -r hook/flow-guardian/ ~/.openclaw/hooks/flow-guardian/
pip install PyYAML>=6.0.0
```

See [INSTALL.md](INSTALL.md) for detailed setup instructions.

## How It Works

```
Session Start                          Session End
    │                                      │
    ▼                                      ▼
┌─────────────┐                    ┌─────────────┐
│ Hook fires  │                    │ Hook fires  │
│ bootstrap   │                    │ stop/reset  │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       ▼                                  ▼
┌─────────────┐                    ┌─────────────┐
│ Load        │                    │ Save        │
│ handoff.yaml│                    │ handoff.yaml│
│ learnings.md│                    │ learnings.md│
│ git state   │                    │ git state   │
└──────┬──────┘                    └─────────────┘
       │
       ▼
   Agent has
   full context
```

## Tools

### Code TLDR (No LLM needed — instant)

```bash
# Extract Python/JS/TS structure via AST parsing
python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file src/server.py --level L2

# Output:
## server.py
**Imports:** flask, sqlalchemy, jwt, ...
**Classes:**
- `AuthController(BaseController)`
  Methods: login(self, request), logout(self, request), refresh_token(self, request)
**Functions:**
- `create_app(config: dict) -> Flask`
- `setup_routes(app: Flask) -> None`
```

### Handoff Management

```bash
# Save session state
python3 handoff.py save \
  --goal "Implement JWT auth" \
  --status in_progress \
  --now "Debugging token expiry" \
  --hypothesis "Off-by-one in timestamp comparison" \
  --files "src/auth.py,tests/test_auth.py" \
  --branch "fix/jwt-expiry"

# Load previous session
python3 handoff.py load

# Update current session
python3 handoff.py update --now "Fix verified, writing tests" --status completed
```

### TLDR Compression

```bash
# Generate summarization prompt at specified depth
cat large_file.py | python3 tldr.py --level L1

# Auto-select level based on content size
cat large_file.py | python3 tldr.py --auto

# JSON output with metadata
cat large_file.py | python3 tldr.py --level L2 --json
```

### Git Context

```bash
# Capture repository state as JSON
python3 git_capture.py --repo /path/to/project
```

## TLDR Depth Levels

| Level | Content | Typical Tokens | Use Case |
|-------|---------|---------------|----------|
| **L0** | File paths only | ~100 | Quick orientation |
| **L1** | + One-line descriptions | ~300 | Default, session handoffs |
| **L2** | + Key logic summaries | ~600 | Detailed context restoration |
| **L3** | Full context, minimal compression | ~1500 | Deep debugging sessions |

## Architecture

### Skill (On-Demand Tools)

| Tool | Purpose | Dependencies |
|------|---------|-------------|
| `tldr_code.py` | AST-based code structure extraction | Python stdlib |
| `tldr.py` | TLDR prompt generation for LLM summarization | Python stdlib |
| `handoff.py` | Session state save/load/update | PyYAML |
| `git_capture.py` | Git repository state capture | subprocess + git |

### Hook (Automated Events)

| Event | Action |
|-------|--------|
| `agent:bootstrap` | Load handoff + learnings + git state → inject into session |
| `command:stop` | Remind agent to save handoff state |
| `command:reset` | Remind agent to save handoff state |
| `command:new` | Remind agent to save handoff state |

## What's Different from the Original

The original Flow Guardian required Cerebras API, Backboard.io, FastAPI, and a background daemon. This OpenClaw edition:

| Removed | Replaced By |
|---------|-------------|
| Cerebras client | Agent's own LLM (via structured prompts) |
| Backboard.io | `openclaw memory search` (qmd vectors) |
| FastAPI server | OpenClaw Gateway |
| Background daemon | OpenClaw hooks |
| MCP server | Direct tool calls |
| Web UI | OpenClaw Control UI |

**Result:** Zero external dependencies. Zero API keys. Works offline.

## Requirements

- Python 3.10+
- PyYAML >= 6.0.0
- Git (for `git_capture.py`)
- OpenClaw (for hook integration)

## License

MIT

---

**"Your agent forgets. Flow Guardian remembers."**
