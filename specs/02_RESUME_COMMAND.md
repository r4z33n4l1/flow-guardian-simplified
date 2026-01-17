# Spec: `flow resume` Command

## Overview

The `flow resume` command restores context from a previous session, generating a "welcome back" message that helps the user (and their AI assistant) quickly regain context.

## Jobs to Be Done (JTBD)

When I'm starting a new coding session, I want to restore my previous context so I can continue where I left off without spending 20+ minutes remembering what I was doing.

## Requirements

### Functional Requirements

1. The command shall:
   - Load the most recent session checkpoint (default)
   - Or load a specific session by ID (`--session <id>`)
   - Or show interactive picker (`--pick`)

2. The command shall generate a "welcome back" message that includes:
   - What you were working on
   - Your hypothesis/approach
   - Key files involved
   - What changed while you were away (git diff)
   - Suggested next action

3. The command shall detect what changed since the checkpoint:
   - New commits on the branch
   - Files modified by others
   - Time elapsed

4. The command shall use Cerebras to generate a natural, helpful restoration prompt

5. The command shall support flags:
   - `--session <id>` or `-s <id>` — Restore specific session
   - `--pick` or `-p` — Interactive session picker
   - `--raw` — Output raw context (for piping to Claude)
   - `--copy` — Copy restoration prompt to clipboard

### Non-Functional Requirements

- **Performance**: Resume should complete in <2 seconds
- **UX**: Output should be immediately useful, not overwhelming

## Acceptance Criteria

- [ ] Running `flow resume` loads most recent checkpoint
- [ ] Running `flow resume` shows what changed while away
- [ ] Running `flow resume -s <id>` loads specific session
- [ ] Running `flow resume --pick` shows interactive picker
- [ ] Running `flow resume --raw` outputs context for piping
- [ ] Running `flow resume --copy` copies to clipboard
- [ ] Output is beautifully formatted with Rich panels

## Output Format

### Welcome Back Panel

```
╭─────────────────────── Welcome Back! ────────────────────────╮
│                                                               │
│  📍 You were: Debugging JWT token expiry in auth.py          │
│                                                               │
│  💡 Hypothesis: Off-by-one error in expiry timestamp         │
│                                                               │
│  📁 Files: auth.py, test_auth.py                             │
│                                                               │
│  ⏱️  Away for: 2h 15m                                        │
│                                                               │
│  📝 Changes while away:                                       │
│     • 2 new commits on fix/jwt-expiry                        │
│     • Sarah merged PR #47 (affects user.py → imports auth)   │
│                                                               │
│  ➡️  Suggested: Review Sarah's changes, then add logging     │
│                 to verify timestamp values                    │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

### Raw Output (for --raw flag)

```markdown
## Session Context

**Working on:** Debugging JWT token expiry in auth.py
**Hypothesis:** Off-by-one error in expiry timestamp comparison
**Files:** src/auth.py, tests/test_auth.py
**Branch:** fix/jwt-expiry

### Previous Learnings
- JWT timestamps are in UTC, not local time
- Token generation is not the issue

### Changes Since Last Session
- 2 new commits on this branch
- PR #47 merged (user.py, imports auth.py)

### Suggested Next Steps
1. Review Sarah's changes to user.py
2. Add logging to verify timestamp values
3. Check timezone handling
```

## Implementation Notes

### Change Detection

```python
def get_changes_since(checkpoint_timestamp: str) -> dict:
    # Git commits since checkpoint
    commits = git_log_since(checkpoint_timestamp)

    # Files changed
    files_changed = git_diff_names(checkpoint_timestamp)

    # Time elapsed
    elapsed = calculate_elapsed(checkpoint_timestamp)

    return {
        "commits": commits,
        "files_changed": files_changed,
        "elapsed": elapsed
    }
```

### Restoration Prompt (Cerebras)

```
Generate a concise "welcome back" message for a developer.

THEIR LAST CONTEXT:
- Working on: {summary}
- Hypothesis: {hypothesis}
- Files: {files}
- Branch: {branch}
- Learnings: {learnings}

CHANGES WHILE AWAY:
- Time elapsed: {elapsed}
- New commits: {commits}
- Files changed: {files_changed}

Generate:
1. Quick reminder of what they were doing (1 sentence)
2. Their hypothesis (if any)
3. What changed while away (highlight conflicts!)
4. Suggested next action

Keep it under 10 lines. Be direct and useful.
```

## Edge Cases

- No previous sessions: Show helpful "get started" message
- Session from different branch: Warn about branch mismatch
- Very old session (>7 days): Warn that context may be stale
- Git conflicts with checkpoint: Highlight prominently

## Dependencies

- `memory.py` — Load checkpoints
- `backboard_client.py` — Semantic recall
- `cerebras_client.py` — Generate restoration message
