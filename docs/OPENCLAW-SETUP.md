# OpenClaw Integration Guide

How Flow Guardian works inside OpenClaw — and how to wire it up for automatic use.

## OpenClaw vs Claude Code

| Concept | Claude Code | OpenClaw |
|---------|------------|----------|
| Session start | `SessionStart` hook fires | First message after a gap |
| Session end | `SessionEnd` / `PreCompact` hook fires | No explicit end — agent sleeps between messages |
| Context reset | Compaction (automatic) | Compaction (automatic) |
| Lifecycle hooks | `.claude/hooks/` directory | `~/.openclaw/hooks/` directory |
| Memory | Manual / MCP tools | `MEMORY.md` + `memory/*.md` + qmd vectors |
| Periodic checks | Not built-in | Heartbeat system (every ~30 min) |

## How to Wire It Up

### 1. Install the skill + hook

```bash
cp -r skill/flow-guardian/ ~/.openclaw/skills/flow-guardian/
cp -r hook/flow-guardian/ ~/.openclaw/hooks/flow-guardian/
```

### 2. Add to AGENTS.md

Add this section to your agent's `AGENTS.md` (in `~/.openclaw/workspace/`):

```markdown
## Flow Guardian (Session Memory)

On session start (first message after a gap):
  python3 ~/.openclaw/skills/flow-guardian/handoff.py load

After completing something meaningful:
  python3 ~/.openclaw/skills/flow-guardian/handoff.py save \
    --goal "..." --now "..." --status in_progress

Before large file reads (save tokens):
  python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file <path> --level L1

Quick orientation:
  python3 ~/.openclaw/skills/flow-guardian/handoff.py status
  python3 ~/.openclaw/skills/flow-guardian/git_capture.py --pretty
```

### 3. Add to HEARTBEAT.md

Add to your heartbeat checklist:

```markdown
## Flow Guardian (auto-save)
- Load memory/handoff.yaml — if stale (>2 hours), update with current context
- If significant work was done since last handoff, save a new one
```

This ensures the handoff stays current even during long sessions.

### 4. Model cost optimization

The TLDR prompt generator (`tldr.py`) outputs prompts that need an LLM to summarize.
Tell your agent (via SKILL.md or AGENTS.md) to use a **cheap/fast model** for this —
don't burn expensive tokens on summarization grunt work.

Code TLDR (`tldr_code.py`) needs **no model at all** — it's pure AST parsing.

## Lifecycle in OpenClaw

Since OpenClaw doesn't have clean session start/end events like Claude Code,
Flow Guardian uses these patterns:

```
Message arrives (after gap)
    │
    ▼
Agent reads AGENTS.md
    │
    ▼
Sees "load handoff" instruction
    │
    ▼
python3 handoff.py load
    │
    ▼
Agent has full context from last session
    │
    ...works...
    │
    ▼
Meaningful milestone reached
    │
    ▼
python3 handoff.py save --goal "..." --done "..."
    │
    ▼
Heartbeat fires (~30 min)
    │
    ▼
Agent checks if handoff is stale
    │
    ▼
Updates handoff if needed
    │
    ...eventually human says goodnight...
    │
    ▼
python3 handoff.py save --status completed --outcome SUCCEEDED
```

## What Gets Persisted

All state lives in `~/.openclaw/workspace/memory/`:

- `handoff.yaml` — Current session state (structured YAML)
- `learnings.md` — Auto-extracted insights (future feature)
- `YYYY-MM-DD.md` — Daily notes (existing OpenClaw convention)
- `MEMORY.md` — Long-term curated memory (existing OpenClaw convention)

Flow Guardian's `handoff.yaml` complements the existing memory system.
It doesn't replace `MEMORY.md` — it adds structured session continuity on top.
