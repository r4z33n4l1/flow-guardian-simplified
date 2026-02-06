---
name: flow-guardian
description: >
  Persistent session memory with TLDR compression. Automatically captures
  coding session context (goals, hypotheses, decisions, files) and restores
  it in future sessions. Compresses large content with 97% token savings.
  Use when you need to save session state, compress files for context,
  extract code structure, or search past learnings.
license: MIT
metadata:
  openclaw:
    emoji: "🧠"
    category: memory
    requirements:
      - python3
---

# Flow Guardian — Persistent Session Memory

"Your agent forgets. Flow Guardian remembers."

## What This Skill Does

1. **Structured Handoffs** — Save/restore session state as goal + status + hypothesis + outcome + decisions + learnings
2. **TLDR Compression** — Compress files and context to ~3% of original size while preserving key information
3. **Code-Aware TLDR** — AST-based extraction for Python/JS/TS that preserves exact function signatures, class structures, and complexity metrics
4. **Git Context** — Capture current branch, modified files, recent commits
5. **Learning Extraction** — Identify and store learnings, decisions, and insights from sessions

## Tools

### Handoff Management

**Save handoff** — Call when wrapping up a session or before switching tasks:
```bash
python3 ~/.openclaw/skills/flow-guardian/handoff.py save \
  --goal "Implement JWT auth" \
  --status in_progress \
  --now "Debugging token expiry" \
  --hypothesis "Off-by-one in timestamp comparison" \
  --outcome PARTIAL_PLUS \
  --files "src/auth.py,tests/test_auth.py" \
  --branch "fix/jwt-expiry" \
  --test "pytest tests/test_auth.py" \
  --done "Identified root cause" --done-files "src/auth.py" \
  --done "Added logging" --done-files "src/logger.py" \
  --decision "use_jwt=Better for stateless APIs" \
  --finding "Token TTL was correct, timezone was wrong" \
  --worked "TDD approach" \
  --failed-approach "Mocking entire DB layer" \
  --blocker "Need Redis 7+ for pub/sub" \
  --next-step "Write integration tests" \
  --next-step "Update docs"
```

**Load handoff** — Call at session start to restore context:
```bash
python3 ~/.openclaw/skills/flow-guardian/handoff.py load
python3 ~/.openclaw/skills/flow-guardian/handoff.py load --json  # JSON output
```
Output: YAML with goal, status, now, outcome, hypothesis, files, branch, decisions, findings, worked, failed, next, timestamp.

**Update handoff** — Partially update current handoff (list fields append by default):
```bash
python3 ~/.openclaw/skills/flow-guardian/handoff.py update \
  --now "Fix verified, writing tests" \
  --status completed \
  --outcome SUCCEEDED \
  --finding "Timezone must be UTC everywhere"
```

Use `--replace` to overwrite list fields instead of appending.

### Handoff Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| `goal` | Yes | What this session is about (shown in statusline) |
| `status` | Yes | `in_progress`, `completed`, `blocked` |
| `now` | Yes | Current focus / what next session does first (shown in statusline) |
| `outcome` | No | `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` |
| `hypothesis` | No | Current working theory |
| `test` | No | Command to verify work (e.g. `pytest tests/`) |
| `files` | No | Files being worked on |
| `branch` | No | Git branch |
| `done_this_session` | No | Tasks completed (with file refs) |
| `decisions` | No | Key decisions with rationale |
| `findings` | No | Learnings and discoveries |
| `worked` | No | Approaches that worked (repeat these) |
| `failed` | No | Approaches that failed (avoid these) |
| `blockers` | No | Blocking issues |
| `next` | No | Ordered action items for next session |

### TLDR Compression

**Summarize content** — Generate a structured prompt for compressing text/code at a specified depth level:
```bash
echo "large file content..." | python3 ~/.openclaw/skills/flow-guardian/tldr.py \
  --level L1 \
  --max-tokens 300
```

Levels:
- **L0**: File paths + function names only (~100 tokens)
- **L1**: + One-line descriptions (~300 tokens) — DEFAULT
- **L2**: + Key logic summaries (~600 tokens)
- **L3**: Full context, minimal compression

The tool outputs a structured prompt you can use directly with your LLM. For content below 500 tokens, it passes through unchanged.

**Code TLDR** — AST-based extraction (no LLM needed, instant):
```bash
python3 ~/.openclaw/skills/flow-guardian/tldr_code.py \
  --file src/server.py \
  --level L2
```
Output: Imports, constants, classes with methods, function signatures, docstrings.

**Level details for code TLDR:**
- **L1**: Function/class signatures, imports, constants
- **L2**: + Brief docstrings
- **L3**: + Internal call graph + cyclomatic complexity metrics + file metrics (SLOC, function count)

### Git Context

```bash
python3 ~/.openclaw/skills/flow-guardian/git_capture.py [--repo /path/to/repo]
python3 ~/.openclaw/skills/flow-guardian/git_capture.py --compact  # Minimal JSON
```
Output: JSON with branch, modified files, recent commits, diff summary.

## When to Use

- **Session start**: Load handoff → inject context (automated by hook)
- **Before reading large files**: Use code TLDR to extract structure instead of reading raw content
- **Session end**: Save handoff with current state (automated by hook)
- **After solving a problem**: Save decisions, findings, worked/failed for future reference
- **Before context compaction**: Save handoff to preserve state across compaction

## Integration with Memory

This skill writes to `memory/handoff.yaml` and `memory/learnings.md` in the workspace.
These files are automatically indexed by OpenClaw's memory search (`openclaw memory search`).
The hook handles auto-injection at session start and auto-save at session end.

## Zero External Dependencies

- **Code TLDR**: Pure Python AST parsing — no LLM calls, no API keys, instant results
- **Handoff**: Pure Python + PyYAML — local file read/write
- **Git Capture**: Uses system `git` via subprocess
- **TLDR prompts**: Generates structured prompts — your agent's own model does the summarization
