# Flow Guardian

**Persistent session memory for OpenClaw agents.**

Your agent wakes up fresh every session. Flow Guardian gives it a memory — structured handoffs, AST-based code compression (97% token savings), and automatic context restoration. Zero API keys. Works offline.

## Install

```bash
# clone
git clone https://github.com/r4z33n4l1/flow-guardian-simplified.git /tmp/flow-guardian

# install skill + hook
cp -r /tmp/flow-guardian/skill/flow-guardian/ ~/.openclaw/skills/flow-guardian/
cp -r /tmp/flow-guardian/hook/flow-guardian/ ~/.openclaw/hooks/flow-guardian/

# only dependency
pip install PyYAML
```

That's it. Your agent now has persistent memory.

### OpenClaw self-setup

If you're an OpenClaw agent setting this up for your human, run:

```bash
# 1. clone the repo
git clone https://github.com/r4z33n4l1/flow-guardian-simplified.git /tmp/flow-guardian

# 2. install skill
mkdir -p ~/.openclaw/skills/flow-guardian
cp /tmp/flow-guardian/skill/flow-guardian/* ~/.openclaw/skills/flow-guardian/

# 3. install hook
mkdir -p ~/.openclaw/hooks/flow-guardian
cp /tmp/flow-guardian/hook/flow-guardian/* ~/.openclaw/hooks/flow-guardian/

# 4. verify
python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file ~/.openclaw/skills/flow-guardian/handoff.py --level L1
python3 ~/.openclaw/skills/flow-guardian/handoff.py save --goal "Test install" --now "Verifying" --status in_progress
python3 ~/.openclaw/skills/flow-guardian/handoff.py load
python3 ~/.openclaw/skills/flow-guardian/git_capture.py --compact
```

If all four commands output without errors, you're good. Add this to your `AGENTS.md`:

```markdown
## Flow Guardian (Session Memory)

At session start, check `memory/handoff.yaml` for previous session state.
Before ending a session, save state with:
  python3 ~/.openclaw/skills/flow-guardian/handoff.py save --goal "..." --now "..." --status in_progress

For large file reads, compress first:
  python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file <path> --level L1
```

## What it does

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
│ learnings   │                    │ learnings   │
│ git state   │                    │ git state   │
└──────┬──────┘                    └─────────────┘
       │
       ▼
   Agent resumes
   with full context
```

## Tools

### `tldr_code.py` — Code structure extraction

AST-based. No LLM. Instant. Supports Python, JavaScript, TypeScript.

```bash
python3 tldr_code.py --file src/server.py --level L1    # signatures only
python3 tldr_code.py --file src/server.py --level L2    # + docstrings
python3 tldr_code.py --file src/server.py --level L3    # + call graph hints
cat file.py | python3 tldr_code.py --level L1           # stdin
```

**Depth levels:**

| Level | What you get | Tokens | Use case |
|-------|-------------|--------|----------|
| L1 | Imports, function signatures, class names | ~300 | Quick orientation |
| L2 | + Docstrings, method signatures | ~600 | Working context |
| L3 | + Call graph hints, constants | ~1200 | Deep debugging |

### `handoff.py` — Session state management

Save what you're working on. Load it next session.

```bash
# save
python3 handoff.py save \
  --goal "Implement JWT auth" \
  --now "Debugging token expiry" \
  --status in_progress \
  --hypothesis "Off-by-one in timestamp comparison" \
  --files "src/auth.py,tests/test_auth.py" \
  --branch fix/jwt-expiry \
  --done "Set up auth middleware" \
  --done "Added token refresh endpoint" \
  --decision "Use RS256 over HS256: better key rotation" \
  --finding "JWT timestamps are UTC, not local" \
  --worked "Testing with httpie instead of curl" \
  --failed-approach "Tried monkey-patching datetime.now — broke other tests" \
  --next "Write integration tests" \
  --outcome PARTIAL_PLUS

# load
python3 handoff.py load

# update (appends to lists)
python3 handoff.py update --done "Fixed token expiry bug" --status completed --outcome SUCCEEDED
```

**Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `goal` | yes | What you're trying to accomplish |
| `now` | yes | Current focus |
| `status` | yes | `in_progress`, `completed`, `blocked` |
| `hypothesis` | no | Current working theory |
| `outcome` | no | `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` |
| `files` | no | Files being worked on |
| `branch` | no | Git branch |
| `done_this_session` | no | Completed tasks (repeatable `--done`) |
| `decisions` | no | Key decisions with rationale (repeatable `--decision`) |
| `findings` | no | Learnings/discoveries (repeatable `--finding`) |
| `worked` | no | Approaches that worked (repeatable `--worked`) |
| `failed` | no | Approaches that failed (repeatable `--failed-approach`) |
| `next` | no | Action items for next session (repeatable `--next`) |

### `tldr.py` — Content compression

Generates structured prompts for your agent's LLM. No external API.

```bash
cat large_file.py | python3 tldr.py --level L1      # brief summary prompt
cat large_file.py | python3 tldr.py --auto           # auto-select level by size
cat large_file.py | python3 tldr.py --json           # JSON with metadata
echo "short" | python3 tldr.py                        # small content passes through
```

### `git_capture.py` — Repository state

```bash
python3 git_capture.py                     # current directory
python3 git_capture.py --repo /path/to/project
python3 git_capture.py --compact           # single-line JSON
```

## Hook events

| Event | What happens |
|-------|-------------|
| `agent:bootstrap` | Loads `memory/handoff.yaml` + recent learnings + git state into session |
| `command:stop` | Reminds agent to save handoff before ending |
| `command:reset` | Reminds agent to save handoff before reset |
| `command:new` | Reminds agent to save handoff before new session |

## What OpenClaw replaces

The original Flow Guardian needed Cerebras, Backboard.io, FastAPI, a daemon, and an MCP server. This edition needs none of that:

| Removed | OpenClaw handles it |
|---------|-------------------|
| Cerebras client | Agent's own LLM |
| Backboard.io vectors | `openclaw memory search` |
| FastAPI server | OpenClaw Gateway |
| Background daemon | OpenClaw hooks |
| MCP server | Direct tool access |

**Result:** 1 dependency (PyYAML). Zero API keys. Works offline.

## Requirements

- Python 3.10+
- PyYAML
- Git (for git_capture.py)
- OpenClaw

## License

MIT
