# Flow Guardian Setup Guide

Complete setup guide for local installation.

## Prerequisites

- **Python 3.10+** (required for union types)
- **Git** (for installation)

### Check Python Version

```bash
python3 --version
# Should show 3.10.x or higher
```

If you need to install Python 3.10+:

```bash
# macOS (Homebrew)
brew install python@3.10

# Ubuntu/Debian
sudo apt install python3.10 python3.10-venv

# Windows
# Download from python.org
```

---

## Quick Setup (Automated)

```bash
# 1. Clone repository
git clone <repository-url>
cd flow-guardian-simplified

# 2. Run setup script
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Configure environment variables
cp .env.example .env
nano .env  # Add your API keys

# 5. Start Flow Guardian
python server.py all --foreground
```

---

## Manual Setup

### 1. Create Virtual Environment

```bash
# Create venv
python3.10 -m venv venv

# Activate venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file with:

```bash
# REQUIRED
CEREBRAS_API_KEY=csk-...          # Get from: https://cloud.cerebras.ai/
GEMINI_API_KEY=...                # Get from: https://makersuite.google.com/app/apikey

# OPTIONAL
FLOW_GUARDIAN_USER=yourname       # For attribution
FLOW_GUARDIAN_URL=http://localhost:8090
```

**Getting API Keys:**

- **Cerebras**: Sign up at https://cloud.cerebras.ai/ → API Keys
- **Gemini**: Visit https://makersuite.google.com/app/apikey → Create API Key

### 4. Verify Installation

```bash
python server.py --help
# Should show available commands
```

---

## Running Flow Guardian

### Option 1: All-in-One (Recommended)

Run daemon + API server together:

```bash
python server.py all --foreground
```

### Option 2: Daemon Only

Auto-capture Claude Code sessions in background:

```bash
python server.py daemon
python server.py status   # Check status
python server.py stop     # Stop daemon
```

### Option 3: API Only

HTTP API server for programmatic access:

```bash
python server.py api
```

### Option 4: MCP Only

MCP server for Claude Code integration:

```bash
python server.py mcp
```

---

## MCP Integration (Claude Code)

Flow Guardian automatically provides MCP tools to Claude Code.

### Configure MCP

The `.mcp.json` file is already configured. Just ensure your virtual environment is active when Claude Code starts.

**Available MCP Tools:**
- `flow_recall(query)` - Search memory
- `flow_learn(insight, tags)` - Store learning
- `flow_capture(summary, decisions, next_steps, blockers)` - Save context
- `flow_team(query)` - Search team knowledge
- `flow_status()` - Get status

### Test MCP Tools

In Claude Code, try:

```
Can you recall what we learned about authentication?
```

Claude will automatically use the `flow_recall` tool.

---

## Team Setup (Optional)

For team knowledge sharing, you have two options:

### Option 1: Shared Network Drive

All team members point to the same SQLite database:

```bash
export FLOW_GUARDIAN_DATA_DIR=/Volumes/TeamDrive/flow-guardian/
python server.py all
```

### Option 2: Central Server

One team member hosts the server:

```bash
# Server (team-server.local)
python server.py all --host 0.0.0.0 --port 8090

# Clients add to .env:
FLOW_GUARDIAN_TEAM_URL=http://team-server.local:8090
```

See [TEAM_SETUP.md](TEAM_SETUP.md) for detailed configuration.

---

## CLI Usage

After setup, you can use the CLI:

```bash
# Save current context
flow save -m "Implementing auth feature"

# Store a learning
flow learn "JWT tokens use UTC timestamps" --tag auth

# Search memory
flow recall "authentication"

# Get status
flow status
```

---

## Troubleshooting

### Python Version Error

```
Error: Python 3.10+ required
```

**Solution:** Install Python 3.10 or higher:

```bash
brew install python@3.10  # macOS
```

### Module Not Found

```
ModuleNotFoundError: No module named 'cerebras_cloud_sdk'
```

**Solution:** Activate virtual environment:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Errors

```
Error: CEREBRAS_API_KEY not set
```

**Solution:** Add API keys to `.env` file:

```bash
cp .env.example .env
# Edit .env with your API keys
```

### Port Already in Use

```
ERROR: [Errno 48] Address already in use
```

**Solution:** Stop existing server or use different port:

```bash
python server.py stop
# or
python server.py all --port 8091
```

---

## Directory Structure

After setup, you'll have:

```
flow-guardian-simplified/
├── venv/                    # Virtual environment
├── .env                     # Your configuration (not in git)
├── .env.example             # Template
├── server.py                # Main server
├── flow_cli.py              # CLI tool
├── requirements.txt         # Dependencies
├── ~/.flow-guardian/        # Data directory
│   ├── sessions/            # Saved sessions
│   ├── learnings/           # Stored learnings
│   ├── memory.db            # SQLite vector database
│   └── daemon/              # Daemon state
```

---

## Next Steps

1. **Start Using It:**
   - Let the daemon auto-capture your Claude Code sessions
   - Use MCP tools directly in conversations
   - Store learnings as you discover them

2. **Explore Features:**
   - REST API: http://localhost:8090/docs
   - CLI help: `flow --help`
   - MCP tools: Ask Claude to recall or learn something

3. **Team Setup (Optional):**
   - See [TEAM_SETUP.md](TEAM_SETUP.md)
   - Set up shared server or network drive

---

## Getting Help

- **Issues:** https://github.com/yourusername/flow-guardian/issues
- **Docs:** See `README.md` for architecture and features
- **MCP:** See `.mcp.json` for tool configuration
