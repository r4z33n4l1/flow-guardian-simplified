# Spec: `flow save` Command

## Overview

The `flow save` command captures the current AI coding session state and persists it to memory. This is the core "checkpoint" functionality that enables session continuity.

## Jobs to Be Done (JTBD)

When I'm ending a coding session with Claude (or context is filling up), I want to save my current context, learnings, and progress, so I can restore it later without re-explaining everything.

## Requirements

### Functional Requirements

1. The command shall capture:
   - Current working context (what the user is working on)
   - Hypothesis/approach (if any)
   - Key files involved
   - Recent decisions made
   - Learnings discovered
   - Git state (branch, uncommitted changes)

2. The command shall analyze context using Cerebras fast inference to:
   - Summarize what the user is working on
   - Extract key decisions and learnings
   - Identify the current hypothesis/approach

3. The command shall store the checkpoint to:
   - Backboard.io (primary) — for semantic recall
   - Local storage (fallback) — ~/.flow-guardian/sessions/

4. The command shall support optional flags:
   - `--message "..."` or `-m "..."` — Add a manual note
   - `--tag "..."` or `-t "..."` — Add tags for organization
   - `--quiet` or `-q` — Minimal output

5. The command shall display a confirmation panel showing:
   - Summary of what was saved
   - Timestamp
   - Session ID (for reference)

### Non-Functional Requirements

- **Performance**: Save operation should complete in <3 seconds
- **Reliability**: Must work offline (fallback to local storage)
- **UX**: Beautiful Rich panel output

## Acceptance Criteria

- [ ] Running `flow save` captures current git state
- [ ] Running `flow save` analyzes context with Cerebras
- [ ] Running `flow save` stores to Backboard.io
- [ ] Running `flow save` falls back to local if Backboard unavailable
- [ ] Running `flow save -m "note"` includes the note
- [ ] Running `flow save -t "tag1" -t "tag2"` adds tags
- [ ] Output shows clear confirmation of what was saved

## Data Schema

### Session Checkpoint (YAML/JSON)

```yaml
id: "session_2026-01-17_10-30-00"
timestamp: "2026-01-17T10:30:00Z"
version: 1

context:
  summary: "Debugging JWT token expiry in auth.py"
  hypothesis: "Off-by-one error in expiry timestamp comparison"
  files:
    - path: "src/auth.py"
      relevance: "primary"
    - path: "tests/test_auth.py"
      relevance: "secondary"
  next_steps:
    - "Add logging to verify timestamp values"
    - "Check timezone handling"

decisions:
  - "Ruled out: issue is not in token generation"
  - "Confirmed: problem only occurs after 24h"

learnings:
  - text: "JWT timestamps are in UTC, not local time"
    tags: ["jwt", "auth", "timezone"]

git_state:
  branch: "fix/jwt-expiry"
  uncommitted_files: ["src/auth.py"]
  last_commit: "abc123 - Add token validation"

metadata:
  message: "Before standup meeting"
  tags: ["auth", "debugging"]
  trigger: "manual"
```

## Implementation Notes

### Context Analysis Prompt (Cerebras)

```
Analyze this coding session state and extract:

1. SUMMARY: One sentence describing what the user is working on
2. HYPOTHESIS: Their current theory or approach (if apparent)
3. NEXT_STEPS: List of likely next actions
4. DECISIONS: Key decisions made during this session
5. LEARNINGS: Insights discovered

Git branch: {branch}
Uncommitted files: {files}
User message: {message}

Respond in JSON format.
```

### Backboard.io Storage

Store as a message in the user's personal thread:
- `send_to_llm: False` — Just store, don't generate response
- `metadata`: Include session ID, timestamp, tags
- `content`: Formatted checkpoint summary

## Edge Cases

- No git repo: Skip git state, still capture other context
- Backboard.io unavailable: Fall back to local storage
- Empty context: Allow save with just a message
- Rapid saves: Debounce or warn if <1 min since last save

## Dependencies

- `cerebras_client.py` — For context analysis
- `backboard_client.py` — For persistent storage
- `memory.py` — For local fallback storage
