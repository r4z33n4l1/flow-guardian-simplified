---
name: flow-guardian
description: "Auto-capture and restore session context via structured handoffs"
metadata:
  openclaw:
    emoji: "🧠"
    events:
      - agent:bootstrap
      - command:stop
      - command:reset
      - command:new
---

# Flow Guardian Hook

Automatically manages session context persistence.

## Events

### `agent:bootstrap` (Session Start)
1. Reads `memory/handoff.yaml` if it exists
2. Reads recent `memory/learnings.md` entries (last 5)
3. Captures current git state (branch, modified files, recent commits)
4. Logs structured context for the agent

### `command:stop` / `command:reset` / `command:new` (Session End)
1. Logs reminder to save handoff state
2. The agent should call `handoff.py save` before shutdown

## Configuration

No configuration required. Works out of the box.

Optional environment variables:
- `FLOW_GUARDIAN_AUTO_INJECT` — Set to `false` to disable auto-injection (default: `true`)
- `FLOW_GUARDIAN_AUTO_CAPTURE` — Set to `false` to disable auto-capture (default: `true`)
- `FLOW_GUARDIAN_TLDR_LEVEL` — Default TLDR level for injection (default: `L1`)

## What Gets Injected

On session start, the agent receives context like:

```yaml
# Previous Session State
goal: "Implement JWT authentication"
status: in_progress
now: "Debugging token expiry in auth.py"
hypothesis: "Off-by-one in timestamp comparison"
files:
  - src/auth.py
  - tests/test_auth.py
branch: fix/jwt-expiry
last_session: "2026-02-05T22:30:00Z"

# Recent Learnings
- PyMuPDF requires `pip install pymupdf` not `pip install PyMuPDF`
- JWT tokens use UTC timestamps, not local time
```

## Installation

Copy the `hook/flow-guardian/` directory to `~/.openclaw/hooks/flow-guardian/` and the hook will auto-register on the next agent bootstrap.
