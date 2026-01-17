# Spec: `flow team` Command

## Overview

The `flow team` command searches the team's shared learnings. This enables knowledge sharing across developers — one person's insight helps the whole team.

## Jobs to Be Done (JTBD)

When I'm stuck on a problem, I want to search what my teammates have learned so I don't waste time re-discovering solutions they've already found.

## Requirements

### Functional Requirements

1. The command shall search team-shared learnings:
   ```bash
   flow team "database connection pooling"
   ```

2. The command shall show who shared each learning (author attribution)

3. The command shall use the team's shared Backboard.io assistant

4. The command shall support the same filters as `flow recall`:
   - `--tag <tag>`
   - `--since <date>`
   - `--limit <n>`

### Non-Functional Requirements

- **Performance**: Results in <2 seconds
- **Privacy**: Only searches explicitly shared learnings (--team flag)

## Acceptance Criteria

- [ ] `flow team "query"` searches team learnings
- [ ] Results show author attribution
- [ ] Only --team learnings are searchable
- [ ] Filters work same as recall

## Output Format

```
╭─────────────────── Team Knowledge: "caching" ────────────────╮
│                                                               │
│  Found 2 team learnings:                                      │
│                                                               │
│  1. 💡 From: sarah (Jan 16, 2026)                            │
│     "Redis SCAN is better than KEYS for large datasets"      │
│     Tags: redis, performance                                  │
│                                                               │
│  2. 💡 From: mike (Jan 14, 2026)                             │
│     "Cache invalidation needs to be event-driven"            │
│     Tags: cache, architecture                                 │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

## Implementation Notes

Uses same pattern as `recall` but with team thread:

```python
async def team_recall(query: str) -> str:
    team_thread_id = os.environ.get("BACKBOARD_TEAM_THREAD_ID")
    return await recall(team_thread_id, query)
```

## Edge Cases

- Team not configured: Show setup instructions
- No team learnings: Encourage sharing with `flow learn --team`

## Dependencies

- `backboard_client.py` — Team memory search
