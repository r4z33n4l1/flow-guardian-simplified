# Flow Guardian Integration Guide

**For New Users: How Claude Code Sessions Connect to Flow Guardian**

---

## 🎯 Quick Answer

Flow Guardian has **TWO separate systems** that work together:

1. **MCP Tools** → You configure this in `~/.claude/.mcp.json`
2. **Daemon** → Runs in background (`python server.py daemon`)

**Both are independent. You can use one or both.**

---

## 📊 The Complete Picture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Session                       │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
           │ (1) Uses MCP Tools             │ (2) Creates session files
           │     in conversations           │     in ~/.claude/projects/
           │                                │
           ▼                                ▼
┌──────────────────────┐        ┌──────────────────────┐
│   MCP Server         │        │   Daemon Watcher     │
│   (stdio process)    │        │   (background)       │
│                      │        │                      │
│   - flow_recall()    │        │   - Watches files    │
│   - flow_learn()     │        │   - Auto-extracts    │
│   - flow_capture()   │        │   - Stores learnings │
│   - flow_team()      │        │                      │
│   - flow_status()    │        │                      │
└──────────┬───────────┘        └──────────┬───────────┘
           │                                │
           │                                │
           ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│            Local Memory (SQLite + Vectors)                   │
│            ~/.flow-guardian/memory.db                        │
│            ~/.flow-guardian/sessions/                        │
│            ~/.flow-guardian/learnings/                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ MCP Tools Integration

### What It Does
Allows Claude to **call Flow Guardian tools directly** in conversations.

**Example:**
```
You: "What did we learn about authentication?"
Claude: [Uses flow_recall("authentication")]
Claude: "Here's what we learned..."
```

### How to Set Up

**Step 1: Complete initial setup**
```bash
./setup.sh
source venv/bin/activate
cp .env.example .env
# Edit .env with your API keys
```

**Step 2: Configure Claude Code**

Create or edit `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "flow-guardian": {
      "command": "/path/to/flow-guardian-simplified/venv/bin/python",
      "args": ["server.py", "mcp"],
      "cwd": "/path/to/flow-guardian-simplified",
      "env": {
        "CEREBRAS_API_KEY": "csk-...",
        "GEMINI_API_KEY": "..."
      }
    }
  }
}
```

**💡 Tip:** Run `./setup.sh` - it prints the exact paths to use!

**Step 3: Restart Claude Code**

Close and reopen Claude Code. The MCP server will start automatically.

**Step 4: Test**

In Claude Code:
```
You: "Can you check flow guardian status?"
Claude: [Uses flow_status() tool]
```

### Available Tools

- `flow_recall(query)` - Search memory for previous context
- `flow_learn(insight, tags)` - Store a learning/insight
- `flow_capture(summary, decisions, next_steps, blockers)` - Save session context
- `flow_team(query)` - Search team's shared knowledge (requires team server)
- `flow_status()` - Get Flow Guardian status

---

## 2️⃣ Daemon Auto-Capture

### What It Does
**Automatically captures** your Claude Code sessions in the background without you having to do anything.

**What gets captured:**
- Session summaries
- Key decisions made
- Learnings discovered
- Blockers encountered
- Code patterns used

### How to Set Up

**Step 1: Start the daemon**

```bash
source venv/bin/activate
python server.py daemon
```

Or run with API server:
```bash
python server.py all --foreground
```

**Step 2: Verify it's running**

```bash
python server.py status
```

You should see:
```
✅ Daemon is running (PID: 12345)
✅ API server is running on http://localhost:8090
```

**Step 3: Use Claude Code normally**

The daemon watches `~/.claude/projects/` and auto-captures sessions.

**Step 4: Check captured data**

```bash
# List sessions
curl http://localhost:8090/sessions

# List learnings
curl http://localhost:8090/learnings

# Or use CLI
flow status
```

---

## 🔄 How They Work Together

### Scenario 1: Using MCP Tools Only

```bash
# Configure .mcp.json (one-time)
# Restart Claude Code

# In conversation:
You: "What did we learn about caching?"
Claude: [Uses flow_recall("caching")]
```

**No daemon needed** - MCP reads from existing memory.

---

### Scenario 2: Using Daemon Only

```bash
# Start daemon
python server.py daemon

# Use Claude Code normally
# Daemon captures sessions automatically

# Later, check what was captured:
curl http://localhost:8090/sessions
```

**No MCP needed** - Daemon stores, you retrieve via API/CLI.

---

### Scenario 3: Using Both (Recommended)

```bash
# 1. Start daemon
python server.py all --foreground

# 2. Configure .mcp.json
# 3. Restart Claude Code

# Now you have:
# - MCP tools for querying memory IN conversations
# - Daemon for automatic capture in background
```

**Best of both worlds** - Auto-capture + in-conversation recall.

---

## 🚀 Deployment Patterns

### Pattern 1: Solo Developer (Local Only)

```bash
# Setup
./setup.sh
source venv/bin/activate

# Configure
cp .env.example .env
# Add API keys to .env

# Run daemon + API
python server.py all --foreground

# Configure MCP in ~/.claude/.mcp.json
# Restart Claude Code
```

**Result:** All data local, full functionality.

---

### Pattern 2: Team with Shared Drive

```bash
# Each team member:
export FLOW_GUARDIAN_DATA_DIR=/Volumes/TeamDrive/flow-guardian
python server.py all

# Configure MCP in ~/.claude/.mcp.json
```

**Result:** Shared memory on network drive.

---

### Pattern 3: Team with Central Server

**Server (one person):**
```bash
python server.py all --host 0.0.0.0 --port 8090
```

**Clients (team members):**
```bash
# In .env
FLOW_GUARDIAN_TEAM_URL=http://team-server:8090

# Configure MCP normally
# Use flow_team() tool for team queries
```

**Result:** Personal local memory + shared team knowledge.

---

## 🧪 Testing Your Setup

### Test 1: MCP Tools

```
In Claude Code:
"Can you check flow guardian status?"
```

**Expected:** Claude uses `flow_status()` and shows service info.

---

### Test 2: Daemon Capture

```bash
# 1. Start daemon
python server.py daemon

# 2. Have a conversation in Claude Code
# 3. Check if captured:
curl http://localhost:8090/sessions | jq '.[-1]'
```

**Expected:** See your recent session.

---

### Test 3: Memory Recall

```
In Claude Code:
"Remember that we use orange-500 as primary color"
# Claude uses flow_learn()

Later:
"What color should I use for the primary button?"
# Claude uses flow_recall("primary color")
```

**Expected:** Claude finds and uses the stored learning.

---

## ❓ FAQ

### Q: Do I need both MCP and daemon?

**A:** No, but recommended:
- MCP only = Manual queries in conversations
- Daemon only = Auto-capture, manual retrieval via API
- Both = Auto-capture + in-conversation recall

---

### Q: Can Claude Code start the daemon?

**A:** No. Claude Code can only start the MCP server (stdio mode). Daemon must run separately.

---

### Q: Why are there two separate processes?

**A:** MCP runs in stdio mode (stdin/stdout), which is incompatible with daemon mode. They serve different purposes:
- MCP = Real-time tool calls during conversations
- Daemon = Background watching and auto-extraction

---

### Q: What if I only want MCP tools, no auto-capture?

**A:** Just configure `.mcp.json`, don't start the daemon. Tools will read from existing memory.

---

### Q: What if I only want auto-capture, no MCP tools?

**A:** Just start the daemon, don't configure `.mcp.json`. Retrieve via API or CLI.

---

### Q: How do I know if MCP is working?

**A:** In Claude Code, ask "Can you check flow guardian status?" If Claude uses the tool, it's working.

---

### Q: How do I know if daemon is working?

**A:** Run `python server.py status` or `curl http://localhost:8090/health`

---

## 🔧 Troubleshooting

### MCP Not Working

**Symptom:** Claude says "I don't have access to flow guardian tools"

**Fix:**
1. Check `~/.claude/.mcp.json` exists
2. Verify Python path is correct: `ls -l /path/to/venv/bin/python`
3. Check API keys are in `.mcp.json` env section
4. Restart Claude Code

---

### Daemon Not Capturing

**Symptom:** Sessions not appearing in `/sessions` endpoint

**Fix:**
1. Verify daemon is running: `python server.py status`
2. Check logs: `tail -f ~/.flow-guardian/daemon/server.log`
3. Ensure `~/.claude/projects/` exists and has sessions
4. Check API keys in `.env` file

---

### Permission Errors

**Symptom:** "Permission denied" when starting MCP

**Fix:**
```bash
chmod +x /path/to/venv/bin/python
```

---

### API Key Errors

**Symptom:** "CEREBRAS_API_KEY not set"

**Fix:**
- For MCP: Add keys to `.mcp.json` env section
- For daemon: Add keys to `.env` file in project root

---

## 📚 Related Documentation

- **SETUP.md** - Complete installation guide
- **TEAM_SETUP.md** - Multi-user deployment patterns
- **README.md** - Project overview and features
- **AUDIT.md** - Feature verification and status
- **CHANGELOG.md** - Version history

---

## 🎉 Summary

**For Claude Code Integration:**
1. ✅ Configure `.mcp.json` with paths from `./setup.sh`
2. ✅ Restart Claude Code
3. ✅ Start daemon separately if you want auto-capture
4. ✅ Use `flow_recall()`, `flow_learn()` etc. in conversations

**That's it!** Claude can now remember context across sessions.

---

**Questions?** See SETUP.md or open an issue.
