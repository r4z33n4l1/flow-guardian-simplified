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

1. **Structured Handoffs** — Save/restore session state as goal + status + hypothesis + files + branch
2. **TLDR Compression** — Compress files and context to ~3% of original size while preserving key information
3. **Code-Aware TLDR** — AST-based extraction for Python/JS/TS that preserves exact function signatures and class structures
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
  --files "src/auth.py,tests/test_auth.py" \
  --branch "fix/jwt-expiry"
```

**Load handoff** — Call at session start to restore context:
```bash
python3 ~/.openclaw/skills/flow-guardian/handoff.py load
```
Output: YAML with goal, status, now, hypothesis, files, branch, timestamp.

**Update handoff** — Partially update current handoff:
```bash
python3 ~/.openclaw/skills/flow-guardian/handoff.py update \
  --now "Fix verified, writing tests" \
  --status completed
```

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

### Git Context

```bash
python3 ~/.openclaw/skills/flow-guardian/git_capture.py [--repo /path/to/repo]
```
Output: JSON with branch, modified files, recent commits, diff summary.

## When to Use

- **Session start**: Load handoff → inject context (automated by hook)
- **Before reading large files**: Use code TLDR to extract structure instead of reading raw content
- **Session end**: Save handoff with current state (automated by hook)
- **After solving a problem**: Extract the learning for future reference
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
