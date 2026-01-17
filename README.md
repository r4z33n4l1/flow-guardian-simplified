# Flow Guardian

**"Claude forgets. Flow Guardian remembers."**

Persistent memory for AI coding sessions. Save your context, learnings, and decisions — restore them in future sessions. Now with a conversational web interface!

Built for the [8090 x Highline Beta: Build for Builders Hackathon](https://lu.ma/8090-hackathon).

## The Problem

1. You have a great coding session with Claude
2. You figure out how your codebase works, debug issues, make decisions
3. Session ends or context fills up
4. **Claude has amnesia.** You explain the same things. Again.

## The Solution

### Web Interface (New!)
A conversational chat interface where anyone can ask questions about the team's work:

```
You: What library did we install for PDF uploads?
Flow: The library installed is PyMuPDF.
      Source: learning, Time: 2026-01-17
```

### CLI / MCP Tools
```bash
flow_capture   # Checkpoint your session
flow_recall    # Search everything you've learned
flow_learn     # Store insights that persist forever
flow_team      # Search team's shared knowledge
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

### 3. Start the Server
```bash
# Use Python 3.10+ (required for type hints)
/opt/homebrew/bin/python3.10 server.py all --foreground
```

### 4. Start the Web UI
```bash
cd flow-web && npm run dev
# Open http://localhost:3000
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Next.js)                          │
│                    http://localhost:3000                     │
├─────────────────────────────────────────────────────────────┤
│  Chat Interface    │  Activity Feed    │  Document Upload    │
└────────────────────┴──────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend (:8090)                    │
│  • Daemon: Auto-captures Claude Code sessions                │
│  • API: Search, learn, recall endpoints                      │
│  • MCP: Claude Code integration                              │
└────────────────────┬──────────────────┬─────────────────────┘
                     │                  │
          ┌──────────┴──────┐    ┌──────┴──────┐
          │  Local Storage   │    │  Cloud APIs  │
          │  ~/.flow-guardian│    │  Backboard   │
          │                  │    │  Cerebras    │
          └──────────────────┘    └──────────────┘
```

## Key Features

### Two-Phase Retrieval (Optimized for Speed)
- **Fast Path**: Local context → Cerebras quick check → Instant answer (~1-2s)
- **Slow Path**: Only fetches from Backboard when needed (~5-10s)

### Automatic Session Capture
The daemon watches Claude Code sessions and extracts:
- Session summaries
- Key decisions
- Blockers
- Learnings

### Document Upload
Upload PDFs, text files, and markdown to add team context.

## Tech Stack

- **Next.js 14+** — React framework for web UI
- **Cerebras** — Fast LLM inference (Llama 3.3 70B)
- **Backboard.io** — Persistent cloud memory with semantic recall
- **FastAPI** — Python backend
- **shadcn/ui** — UI components

## Documentation

- **CLAUDE.md** — Detailed setup and API documentation
- **specs/** — Feature specifications

## License

MIT
