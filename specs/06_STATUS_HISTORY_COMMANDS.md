# Spec: `flow status` and `flow history` Commands

## Overview

Utility commands for viewing current state and past activity.

---

## `flow status` Command

### Purpose
Show the current Flow Guardian state — last save, active session, memory stats.

### Usage
```bash
flow status
```

### Output Format

```
╭─────────────────── Flow Guardian Status ─────────────────────╮
│                                                               │
│  📍 Last Save: 2h 15m ago (Jan 17, 10:30 AM)                 │
│  🌿 Branch: fix/jwt-expiry                                   │
│  📝 Working on: Debugging JWT token expiry                   │
│                                                               │
│  📊 Memory Stats:                                             │
│     Sessions: 12                                              │
│     Learnings: 8 personal, 15 team                           │
│     Storage: Backboard.io ✓                                  │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

### Acceptance Criteria

- [ ] Shows time since last save
- [ ] Shows current branch
- [ ] Shows last working context
- [ ] Shows memory stats (sessions, learnings count)
- [ ] Shows storage status (Backboard vs local)

---

## `flow history` Command

### Purpose
Show past sessions and checkpoints.

### Usage
```bash
flow history           # Last 10 sessions
flow history -n 20     # Last 20 sessions
flow history --all     # All sessions
```

### Output Format

```
╭─────────────────── Session History ──────────────────────────╮
│                                                               │
│  #  Time              Branch           Summary                │
│  ─────────────────────────────────────────────────────────── │
│  1  Today 10:30 AM    fix/jwt-expiry   JWT token debugging   │
│  2  Today 8:15 AM     fix/jwt-expiry   Initial investigation │
│  3  Yesterday 4:00 PM main             PR review #45         │
│  4  Yesterday 11:00 AM feature/oauth   OAuth integration     │
│  5  Jan 15, 2:30 PM   main             Refactoring auth      │
│                                                               │
│  Use `flow resume -s <#>` to restore a specific session      │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

### Flags

- `-n <number>` — Limit results (default: 10)
- `--all` — Show all sessions
- `--branch <name>` — Filter by branch

### Acceptance Criteria

- [ ] Shows past sessions in reverse chronological order
- [ ] Shows timestamp, branch, and summary
- [ ] `-n` flag limits results
- [ ] `--branch` filter works
- [ ] Indicates how to resume a session

---

## Dependencies

- `memory.py` — Load session data
