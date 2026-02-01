# Flow Guardian

**Persistent memory for Claude Code sessions.**

Flow Guardian runs in the background, automatically capturing your coding sessions and making them searchable. Stop re-explaining your codebase to Claude every time.

## Features

- 🤖 **Auto-Capture** - Daemon watches Claude Code sessions automatically
- 🔍 **Semantic Search** - Vector embeddings + keyword search (SQLite + sqlite-vec)
- 🛠️ **MCP Tools** - Use memory directly in Claude Code conversations
- 🌐 **REST API** - Programmatic access for integrations
- 💾 **Local-First** - All data stored locally in SQLite
- 👥 **Team Mode** - Share knowledge via self-hosted server
- 🚀 **Zero Config** - Works out of the box with sensible defaults

## Quick Start

```bash
# 1. Setup
./setup.sh

# 2. Configure (add your API keys)
cp .env.example .env
nano .env

# 3. Run
source venv/bin/activate
python server.py all --foreground
```

That's it! Flow Guardian is now auto-capturing your Claude Code sessions.

## How It Works

```
┌─────────────────────────────────────────┐
│  Claude Code Session                     │
│  ↓ (auto-capture)                        │
│  Daemon                                  │
│  ↓ (stores to)                           │
│  SQLite + Vectors (local)                │
│  ↓ (searchable via)                      │
│  MCP Tools / REST API / CLI              │
└─────────────────────────────────────────┘
```

**What gets captured:**
- Session summaries
- Key decisions
- Learnings and insights
- Code patterns
- Blockers and next steps

**How you access it:**
- MCP tools in Claude Code (automatic)
- CLI: `flow recall "auth implementation"`
- REST API: `POST /recall`

## Usage

### MCP Tools (Claude Code)

Flow Guardian provides tools that Claude can use directly:

```python
# In Claude Code, just ask:
"What did we learn about authentication?"

# Claude automatically uses:
flow_recall("authentication")

# Store a learning:
"Remember that JWT tokens use UTC timestamps"

# Claude uses:
flow_learn("JWT tokens use UTC timestamps", tags=["auth"])
```

**Available MCP Tools:**
- `flow_recall(query)` - Search memory
- `flow_learn(insight, tags)` - Store learning
- `flow_capture(summary, decisions)` - Save session context
- `flow_team(query)` - Search team knowledge
- `flow_status()` - Get status

### CLI (Terminal)

```bash
# Search memory
flow recall "how did we implement caching"

# Store learning
flow learn "Tailwind needs --watch flag in dev" --tags css,dev

# Save context
flow save -m "Completed auth refactor"

# Get status
flow status
```

### REST API

```bash
# Search memory
curl -X POST http://localhost:8090/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication"}'

# Store learning
curl -X POST http://localhost:8090/learn \
  -H "Content-Type: application/json" \
  -d '{"insight": "Use RS256 for JWT", "tags": ["auth"]}'
```

## Architecture

### Local-First Storage

All data stored in `~/.flow-guardian/`:

```
~/.flow-guardian/
├── sessions/           # Session JSON files
├── learnings/          # Learning JSON files
├── memory.db           # SQLite + vector embeddings
└── daemon/             # Daemon state
```

### Components

1. **Daemon** - Background watcher for Claude Code sessions
2. **Local Memory** - SQLite database with vector search (sqlite-vec)
3. **MCP Server** - Provides tools to Claude Code
4. **REST API** - HTTP interface for integrations
5. **CLI** - Command-line interface

### Tech Stack

- **Storage**: SQLite + sqlite-vec (local vector database)
- **Embeddings**: Google Gemini text-embedding-004 (768 dimensions)
- **LLM**: Cerebras Llama 3.3 70B (for extraction and synthesis)
- **MCP**: Model Context Protocol for Claude Code integration
- **API**: FastAPI + Uvicorn

## Team Features

Flow Guardian supports team knowledge sharing through self-hosted servers:

### Option 1: Shared Network Drive

Point all team members to the same SQLite database:

```bash
export FLOW_GUARDIAN_DATA_DIR=/Volumes/TeamDrive/flow-guardian/
python server.py all
```

### Option 2: Central Server (Recommended)

One team member hosts the server:

```bash
# Server
python server.py all --host 0.0.0.0 --port 8090

# Clients (add to .env)
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090
```

Team members can now use:

```bash
flow team "authentication patterns"  # Queries team server
```

See [TEAM_SETUP.md](TEAM_SETUP.md) for detailed configuration.

## Configuration

### Required Environment Variables

```bash
# LLM for extraction and synthesis
CEREBRAS_API_KEY=csk-...

# Embeddings for semantic search
GEMINI_API_KEY=...
```

### Optional Configuration

```bash
# Your username (for team attribution)
FLOW_GUARDIAN_USER=yourname

# Team server URL
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090

# Data directory (default: ~/.flow-guardian)
FLOW_GUARDIAN_DATA_DIR=~/.flow-guardian
```

See `.env.example` for all options.

## Running Modes

```bash
# Daemon + API (recommended)
python server.py all --foreground

# Daemon only (background auto-capture)
python server.py daemon
python server.py status
python server.py stop

# API only (HTTP server)
python server.py api

# MCP only (stdio for Claude Code)
python server.py mcp
```

## Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run in development mode
python server.py all --foreground

# Check status
curl http://localhost:8090/health

# View logs
tail -f ~/.flow-guardian/daemon/server.log
```

## Documentation

- **Setup Guide**: [SETUP.md](SETUP.md) - Detailed installation instructions
- **Team Setup**: [TEAM_SETUP.md](TEAM_SETUP.md) - Multi-user configuration
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System design details
- **API Reference**: http://localhost:8090/docs (when running)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md) - Version history

## Requirements

- Python 3.10+
- API keys (free tiers available):
  - Cerebras Cloud API
  - Google Gemini API

## What's Different from v1.0?

This is the simplified, local-first version:

**Removed:**
- Web UI (use REST API instead)
- Linear integration
- Backboard cloud storage
- Document upload
- Auto-documentation generation

**Kept (100% functional):**
- Auto-capture daemon
- MCP tools
- REST API
- CLI
- Local vector search
- Team features (via self-hosted server)

See [MIGRATION.md](MIGRATION.md) for upgrading from v1.x.

## License

MIT

---

**"Claude forgets. Flow Guardian remembers."**
