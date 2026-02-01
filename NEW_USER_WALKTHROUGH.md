# New User Walkthrough

**Exactly what happens when you set up Flow Guardian from scratch.**

---

## Step-by-Step: What You'll Experience

### 1. Download Flow Guardian

```bash
git clone https://github.com/yourusername/flow-guardian.git
cd flow-guardian
```

**You see:**
```
flow-guardian/
├── server.py
├── setup.sh
├── README.md
├── SETUP.md
├── PROVIDERS.md
├── requirements.txt
└── ...
```

---

### 2. Run Setup Script

```bash
./setup.sh
```

**You see:**

```
🚀 Setting up Flow Guardian...
✓ Found Python: Python 3.10.12
📦 Creating virtual environment...
✓ Virtual environment created
🔧 Activating virtual environment...
📦 Upgrading pip...
📦 Installing dependencies...
[... installation progress ...]

✅ Setup complete!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Activate virtual environment:
   source venv/bin/activate

2. Get FREE API keys (required):
   • Cerebras (LLM): https://cloud.cerebras.ai/ → API Keys
   • Gemini (Embeddings): https://ai.google.dev/ → Get API Key

3. Configure environment variables:
   cp .env.example .env
   nano .env  # Add your API keys

   Required in .env:
   CEREBRAS_API_KEY=csk-...  # For extracting insights
   GEMINI_API_KEY=...        # For semantic search

   💡 Want to use different providers? See PROVIDERS.md

4. Start Flow Guardian (daemon + API):
   python server.py all --foreground

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 MCP Integration (for Claude Code)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Add this to your ~/.claude/.mcp.json:

{
  "mcpServers": {
    "flow-guardian": {
      "command": "/Users/yourname/flow-guardian/venv/bin/python",
      "args": ["server.py", "mcp"],
      "cwd": "/Users/yourname/flow-guardian",
      "env": {
        "CEREBRAS_API_KEY": "csk-...",
        "GEMINI_API_KEY": "..."
      }
    }
  }
}

Then restart Claude Code to load the MCP tools.
```

**What just happened:**
- ✅ Python virtual environment created in `venv/`
- ✅ All Python dependencies installed (FastAPI, SQLite, etc.)
- ✅ Ready to configure

---

### 3. Get API Keys (FREE)

#### Cerebras Cloud API

**What it's for:** LLM inference (extracting insights from your Claude Code sessions)

**Steps:**
1. Visit: https://cloud.cerebras.ai/
2. Click "Sign Up" (email + password)
3. Go to: Dashboard → API Keys
4. Click "Create new key"
5. Copy key (starts with `csk-...`)

**Free Tier:**
- Generous limits for personal use
- Llama 3.3 70B model included
- No credit card required

**Example key:** `csk-abc123def456...`

---

#### Google Gemini API

**What it's for:** Embeddings for semantic search (finding similar sessions/learnings)

**Steps:**
1. Visit: https://ai.google.dev/
2. Click "Get API Key"
3. Sign in with Google account
4. Click "Create API key"
5. Copy key

**Free Tier:**
- 1,500 requests/day
- text-embedding-004 model (768 dimensions)
- No credit card required

**Example key:** `AIzaSyAbc123...`

---

### 4. Configure Environment

```bash
source venv/bin/activate
cp .env.example .env
nano .env  # or use your favorite editor
```

**You'll see .env with:**

```bash
# Required: LLM for extraction and synthesis
CEREBRAS_API_KEY=

# Required: Embeddings for semantic search
GEMINI_API_KEY=

# Optional: Your username (for team attribution)
FLOW_GUARDIAN_USER=

# Optional: API server URL (default: http://localhost:8090)
FLOW_GUARDIAN_URL=http://localhost:8090
```

**Fill in your keys:**

```bash
CEREBRAS_API_KEY=csk-abc123def456...
GEMINI_API_KEY=AIzaSyAbc123...
FLOW_GUARDIAN_USER=john
```

**Save and exit.**

---

### 5. Start Flow Guardian

```bash
python server.py all --foreground
```

**You see:**

```
[2026-02-01 10:30:15] Starting Flow Guardian v2.0...
[2026-02-01 10:30:15] ✓ Cerebras client initialized
[2026-02-01 10:30:15] ✓ Local memory initialized (SQLite + vectors)
[2026-02-01 10:30:15] ✓ Database: ~/.flow-guardian/memory.db
[2026-02-01 10:30:16] Starting daemon mode...
[2026-02-01 10:30:16] ✓ Watching: ~/.claude/projects/
[2026-02-01 10:30:16] Starting API server...
[2026-02-01 10:30:17] ✓ API server running on http://localhost:8090
[2026-02-01 10:30:17] ✓ Health endpoint: http://localhost:8090/health
[2026-02-01 10:30:17] ✓ API docs: http://localhost:8090/docs
[2026-02-01 10:30:17]
[2026-02-01 10:30:17] Flow Guardian is ready! 🎉
[2026-02-01 10:30:17]
[2026-02-01 10:30:17] Services running:
[2026-02-01 10:30:17]   - Daemon: Auto-capturing Claude Code sessions
[2026-02-01 10:30:17]   - API: http://localhost:8090
[2026-02-01 10:30:17]
[2026-02-01 10:30:17] Press Ctrl+C to stop
```

**What's running:**
- ✅ **Daemon** - Watching `~/.claude/projects/` for new sessions
- ✅ **API Server** - REST API on port 8090
- ✅ **Local Memory** - SQLite database ready

**Test it:**

Open a new terminal:
```bash
curl http://localhost:8090/health
# Response: {"status":"healthy"}

curl http://localhost:8090/status
# Response: Shows service status
```

---

### 6. Configure MCP (Claude Code Integration)

**What this does:** Allows Claude to use Flow Guardian tools directly in conversations.

**Steps:**

1. **Create/edit MCP config:**

```bash
nano ~/.claude/.mcp.json
```

2. **Add Flow Guardian server** (use paths from setup.sh output):

```json
{
  "mcpServers": {
    "flow-guardian": {
      "command": "/Users/yourname/flow-guardian/venv/bin/python",
      "args": ["server.py", "mcp"],
      "cwd": "/Users/yourname/flow-guardian",
      "env": {
        "CEREBRAS_API_KEY": "csk-abc123def456...",
        "GEMINI_API_KEY": "AIzaSyAbc123..."
      }
    }
  }
}
```

**💡 Tip:** Copy the JSON from `setup.sh` output - paths are already filled in!

3. **Restart Claude Code**

Close and reopen Claude Code.

4. **Verify MCP is working:**

In Claude Code, type:
```
Can you check flow guardian status?
```

**You should see:**

```
I'll check the Flow Guardian status.

[Uses flow_status() tool]

Flow Guardian is running with these services:
- Daemon: Active, watching sessions
- API: Running on http://localhost:8090
- Memory: 5 sessions, 12 learnings stored
```

---

### 7. Test Auto-Capture

**Have a conversation in Claude Code:**

```
You: "Can you help me implement JWT authentication?"
Claude: [Helps you implement JWT auth]
```

**After the conversation, check if it was captured:**

```bash
curl http://localhost:8090/sessions | jq '.[-1]'
```

**You should see:**

```json
{
  "id": "session_20260201_103045",
  "timestamp": "2026-02-01T10:30:45Z",
  "summary": "Implemented JWT authentication with RS256 signing",
  "decisions": [
    "Use RS256 for JWT signing (more secure)",
    "Store tokens in httpOnly cookies"
  ],
  "learnings": [
    "JWT exp claim must be in UTC seconds since epoch",
    "RS256 requires public/private key pair"
  ],
  "blockers": [],
  "next_steps": [
    "Add refresh token logic",
    "Implement token rotation"
  ]
}
```

**What happened:**
1. ✅ Daemon detected the Claude Code session
2. ✅ Cerebras extracted key information
3. ✅ Gemini generated embeddings
4. ✅ All stored in SQLite memory

---

### 8. Test MCP Recall

**In a new Claude Code conversation:**

```
You: "What did we learn about JWT authentication?"
```

**Claude uses flow_recall() tool:**

```
I'll search the memory for JWT authentication learnings.

[Uses flow_recall("JWT authentication")]

Based on previous sessions, here's what we learned:
- JWT exp claim must be in UTC seconds since epoch
- RS256 requires public/private key pair
- Use RS256 for JWT signing (more secure than HS256)
- Store tokens in httpOnly cookies
```

**What happened:**
1. ✅ Claude used `flow_recall()` MCP tool
2. ✅ Gemini generated embedding for query
3. ✅ SQLite vector search found similar content
4. ✅ Results returned to Claude
5. ✅ Claude synthesized response

---

## What You Now Have

### Running Services

1. **Daemon** (background)
   - Auto-captures Claude Code sessions
   - Extracts insights, learnings, decisions
   - Stores to SQLite + vectors

2. **API Server** (port 8090)
   - REST endpoints for programmatic access
   - API docs: http://localhost:8090/docs

3. **MCP Server** (stdio, managed by Claude Code)
   - Provides tools: `flow_recall()`, `flow_learn()`, `flow_capture()`
   - Started automatically when Claude Code launches

### Data Storage

```
~/.flow-guardian/
├── memory.db          # SQLite + vector embeddings
├── sessions/          # JSON files (one per session)
├── learnings/         # JSON files (one per learning)
└── daemon/            # Daemon state and logs
```

### Available Commands

**CLI:**
```bash
flow recall "query"             # Search memory
flow learn "insight" --tag foo  # Store learning
flow save -m "message"          # Save current context
flow team "query"               # Search team knowledge
flow status                     # Get status
```

**MCP Tools (in Claude Code):**
- `flow_recall(query)` - Search memory
- `flow_learn(insight, tags)` - Store learning
- `flow_capture(summary, decisions, ...)` - Save context
- `flow_team(query)` - Search team knowledge
- `flow_status()` - Get status

**API Endpoints:**
```bash
GET  /health                    # Health check
GET  /status                    # Service status
POST /recall                    # Search memory
POST /capture                   # Save session
POST /learn                     # Store learning
POST /team                      # Search team knowledge
GET  /sessions                  # List sessions
GET  /learnings                 # List learnings
GET  /stats                     # Get statistics
```

---

## Common First-Time Questions

### Q: Do I need to keep `python server.py all` running?

**A:** Yes, for auto-capture to work. Run it in background or in tmux/screen.

Alternatively, run just the daemon:
```bash
python server.py daemon
```

---

### Q: Can I use Claude Code without the daemon?

**A:** Yes! The MCP tools work independently. Just configure `.mcp.json` and restart Claude Code.

Without daemon:
- ✅ MCP tools work
- ❌ No auto-capture
- You manually use `flow_capture()` to save context

---

### Q: What if I don't want to use Cerebras/Gemini?

**A:** See [PROVIDERS.md](PROVIDERS.md) for alternatives:
- OpenAI GPT-4
- Local Ollama (free, no API keys)
- Local embeddings (sentence-transformers)

---

### Q: How much does it cost?

**A:** With default providers (Cerebras + Gemini):
- **Free tier is generous** for personal use
- Typical usage: $0/month if under free limits

For heavy use:
- Cerebras: Pay-as-you-go after free tier
- Gemini: Free up to 1,500 requests/day

**Want zero cost?** Use local providers (see PROVIDERS.md).

---

### Q: Is my data private?

**A:** Yes:
- All session data stored locally in `~/.flow-guardian/`
- Only API calls: LLM inference (Cerebras) and embeddings (Gemini)
- No data stored on external servers
- You can use local providers for 100% offline operation

---

### Q: What if setup.sh fails?

**A:** Common issues:

1. **Python version:** Requires Python 3.10+
   ```bash
   python3 --version
   # If < 3.10, install: brew install python@3.10
   ```

2. **Permission denied:**
   ```bash
   chmod +x setup.sh
   ```

3. **Dependencies fail to install:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

See [SETUP.md](SETUP.md) for detailed troubleshooting.

---

## Next Steps

1. **Use Flow Guardian naturally** - Just use Claude Code as normal, daemon auto-captures
2. **Try MCP tools** - Ask Claude to recall or learn something
3. **Explore team features** - See [TEAM_SETUP.md](TEAM_SETUP.md) for multi-user setup
4. **Customize providers** - See [PROVIDERS.md](PROVIDERS.md) to swap LLM/embeddings

---

**Questions?** See the full documentation or open an issue on GitHub.
