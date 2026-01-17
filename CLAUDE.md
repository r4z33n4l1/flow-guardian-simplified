# Flow Guardian - AI Team Memory System

This project provides persistent memory for AI coding assistants, allowing them to maintain context across sessions and share knowledge within teams.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd flow-web && npm install

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - CEREBRAS_API_KEY
# - BACKBOARD_API_KEY
# - BACKBOARD_PERSONAL_THREAD_ID
# - BACKBOARD_TEAM_THREAD_ID

# 3. Start the server (daemon + API)
/opt/homebrew/bin/python3.10 server.py all --foreground

# 4. Start the web UI (separate terminal)
cd flow-web && npm run dev
# Open http://localhost:3000
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web UI (Next.js)                          │
│                    http://localhost:3000                     │
├─────────────────────────────────────────────────────────────┤
│  Chat Interface    │  Activity Feed    │  Document Upload    │
│  (Ask questions)   │  (Live updates)   │  (Add context)      │
└────────────┬───────┴────────┬──────────┴────────┬───────────┘
             │                │                    │
             ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend                            │
│                    http://localhost:8090                     │
├─────────────────────────────────────────────────────────────┤
│  /recall    - Search memory (local + Backboard)              │
│  /learn     - Store new insights                             │
│  /capture   - Save session context                           │
│  /sessions  - List sessions                                  │
│  /learnings - List learnings                                 │
│  /documents - Upload files (PDF, TXT, MD)                    │
└────────────┬───────┴────────┬──────────┴────────┬───────────┘
             │                │                    │
             ▼                ▼                    ▼
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Local JSON  │    │ Backboard.io    │    │ Cerebras API    │
│ ~/.flow-    │    │ (Cloud Memory)  │    │ (LLM Inference) │
│ guardian/   │    │                 │    │ Llama 3.3 70B   │
└─────────────┘    └─────────────────┘    └─────────────────┘
```

## Key Features

### 1. Two-Phase Context Retrieval (Optimized for Speed)
```
Query → Local Search (instant) → Cerebras Quick Check
                                      ↓
                         Can answer? → YES → Return quick answer (~1-2s)
                                      ↓
                                      NO → Fetch Backboard → Full response (~5-10s)
```

### 2. Automatic Session Capture
The daemon watches Claude Code sessions and automatically extracts:
- Session summaries
- Key decisions
- Blockers
- Learnings

### 3. Document Upload
Upload PDFs, text files, and markdown to add context:
- PyMuPDF for PDF text extraction
- Automatic summarization via Cerebras

### 4. Linear Agent Integration (NEW)
Automatic issue creation in Linear based on conversations:

```
Chat Conversation → Cerebras Analysis → Linear Issues Created
                         ↓
              Identifies: bugs, blockers, features, tasks
                         ↓
              Creates issues with appropriate priority
```

**How it works:**
1. User chats in web UI about bugs, blockers, or issues
2. After response, conversation is analyzed by Cerebras
3. Actionable items are identified (bugs → Urgent, features → Medium)
4. Linear issues are created automatically in configured project

**Triggers:**
- `/capture` with blockers → Creates Linear issues for blockers
- `/learn` with bug keywords → Creates Linear issues for bugs
- Web chat → Analyzes full conversation and creates relevant issues

### 5. Auto-Documentation Generation
The daemon automatically generates documentation:

- **FAQ**: Generated from learnings and solved issues
- **Weekly Summary**: Sessions, issues, and learnings overview
- **Stored in Linear**: Documents saved to configured project

Triggers when:
- 5+ insights captured in a session
- 6+ hours since last report
- 20+ extractions since last report

## MCP Tools (for Claude Code)

```python
# Save current context
flow_capture(
  summary="Working on auth feature",
  decisions=["Using JWT for stateless auth"],
  next_steps=["Implement refresh tokens"],
  blockers=["Waiting for Redis setup"]
)

# Search memory
flow_recall(query="auth implementation")

# Store a learning
flow_learn(
  insight="PyMuPDF requires pip install pymupdf",
  tags=["pdf", "dependency"],
  share_with_team=True
)

# Check status
flow_status()

# Search team knowledge
flow_team(query="authentication patterns")
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recall` | POST | Search memory (supports `local_only` for speed) |
| `/learn` | POST | Store new insight (triggers Linear analysis for bugs) |
| `/capture` | POST | Save session context (triggers Linear issues for blockers) |
| `/analyze-for-linear` | POST | Analyze conversation and create Linear issues |
| `/sessions` | GET | List sessions |
| `/learnings` | GET | List learnings (filterable by tag) |
| `/documents` | POST | Upload file |
| `/stats` | GET | Get statistics |

## File Structure

```
flow-guardian/
├── server.py              # Unified backend (daemon + API + MCP)
├── memory.py              # Local JSON storage
├── backboard_client.py    # Backboard.io integration
├── cerebras_client.py     # Cerebras LLM client (+ async quick_answer)
├── capture.py             # Git state capture
├── session_parser.py      # Claude Code JSONL parser
├── linear_client.py       # Linear GraphQL API client (issues + docs)
├── linear_agent.py        # Intelligent issue creation from content
├── report_generator.py    # Auto-generates FAQ and Weekly Summary docs
│
├── flow-web/              # Next.js frontend
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat/route.ts      # Chat endpoint (two-phase)
│   │   │   ├── upload/route.ts    # File upload proxy
│   │   │   └── activity/stream/   # SSE for live updates
│   │   └── page.tsx               # Main chat interface
│   ├── components/
│   │   ├── chat/                  # Chat UI components
│   │   ├── activity/              # Activity feed
│   │   └── upload/                # File uploader
│   └── lib/
│       ├── cerebras.ts            # Cerebras streaming client
│       └── hooks/                 # React hooks (useActivityStream)
│
├── .env                   # API keys (not in git)
├── .mcp.json              # MCP server config
└── CLAUDE.md              # This file
```

## Environment Variables

```bash
# Required
CEREBRAS_API_KEY=csk-...
BACKBOARD_API_KEY=espr_...
BACKBOARD_PERSONAL_THREAD_ID=...

# Optional
BACKBOARD_TEAM_THREAD_ID=...
FLOW_GUARDIAN_URL=http://localhost:8090  # For web UI

# Linear Integration (optional)
LINEAR_API_KEY=lin_api_...              # Linear API key for issue/doc creation
LINEAR_PROJECT_ID=...                    # Project ID where docs are stored
```

## Running Modes

```bash
# Development: Run API server only
python server.py api

# Production: Run daemon + API together
python server.py all --foreground

# Background daemon only
python server.py daemon
python server.py status  # Check status
python server.py stop    # Stop daemon

# MCP server (for Claude Code integration)
python server.py mcp
```

## Key Optimizations Implemented

1. **Stop Word Filtering**: Search queries filter out common words (what, the, is, etc.)
2. **Score-Based Routing**: Local results with score >= 3 skip Backboard API
3. **Two-Phase Cerebras**: Quick check before full response
4. **Local-Only Mode**: `local_only=true` skips all cloud APIs

## Troubleshooting

### Python Version
Use Python 3.10+ (system Python 3.9 doesn't support union types):
```bash
/opt/homebrew/bin/python3.10 server.py all --foreground
```

### PDF Upload Fails
Install PyMuPDF:
```bash
pip install pymupdf
```

### UI Scrolling Issues
Fixed with CSS: `min-h-0` on flex containers + `overflow-hidden` on parents.

### Search Not Finding Results
Check that learnings use "insight" field (not "text"). The search_learnings function checks both.

## Next Steps for Development

1. **Add User Authentication**: Currently no auth, add JWT or OAuth
2. **Team Features**: Multi-user support with Backboard team threads
3. **Improved Caching**: Redis for faster repeated queries
4. **Vector Search**: Embed learnings for semantic search
5. **Mobile UI**: Responsive design for mobile access
