# Spec: `flow learn` Command

## Overview

The `flow learn` command stores explicit learnings/insights that persist across sessions. This is the "teach" functionality — users tell Flow Guardian something they've learned so it can be recalled later.

## Jobs to Be Done (JTBD)

When I discover something important during development (a gotcha, pattern, or insight), I want to store it so I (and my team) don't have to rediscover it later.

## Requirements

### Functional Requirements

1. The command shall accept a learning as text:
   ```bash
   flow learn "JWT tokens use UTC timestamps, not local time"
   ```

2. The command shall support tags for categorization:
   ```bash
   flow learn "..." --tag auth --tag jwt
   ```

3. The command shall support team sharing:
   ```bash
   flow learn "..." --team  # Shared with team
   ```

4. The command shall store learnings to:
   - Backboard.io (primary) — with semantic embeddings
   - Local storage (fallback) — ~/.flow-guardian/learnings.json

5. The command shall auto-detect relevant tags from content (optional enhancement)

6. The command shall confirm storage with the learning echoed back

### Non-Functional Requirements

- **Performance**: Store in <1 second
- **UX**: Minimal friction — one command, done

## Acceptance Criteria

- [ ] `flow learn "text"` stores a personal learning
- [ ] `flow learn "text" --tag x` adds tags
- [ ] `flow learn "text" --team` stores to team memory
- [ ] Learnings are stored in Backboard.io
- [ ] Learnings fall back to local storage if offline
- [ ] Confirmation shows the stored learning

## Data Schema

### Learning Object

```yaml
id: "learning_2026-01-17_10-45-00"
timestamp: "2026-01-17T10:45:00Z"
text: "JWT tokens use UTC timestamps, not local time"
tags: ["jwt", "auth", "timezone"]
team: false
author: "mike"  # From FLOW_GUARDIAN_USER env var
context:
  branch: "fix/jwt-expiry"  # Optional: where it was learned
  session_id: "session_2026-01-17_10-30-00"  # Link to session
```

## Output Format

```
╭──────────────────── Learning Stored ─────────────────────╮
│                                                           │
│  💡 "JWT tokens use UTC timestamps, not local time"      │
│                                                           │
│  🏷️  Tags: auth, jwt, timezone                           │
│  📍 Scope: personal                                       │
│                                                           │
╰───────────────────────────────────────────────────────────╯
```

For team learnings:
```
╭──────────────────── Team Learning Stored ────────────────╮
│                                                           │
│  💡 "JWT tokens use UTC timestamps, not local time"      │
│                                                           │
│  🏷️  Tags: auth, jwt, timezone                           │
│  👥 Shared with: team                                     │
│  👤 Author: mike                                          │
│                                                           │
╰───────────────────────────────────────────────────────────╯
```

## Implementation Notes

### Backboard.io Storage

```python
async def store_learning(thread_id: str, learning: str, tags: list, team: bool):
    await client.post(
        f"{BASE_URL}/threads/{thread_id}/messages",
        json={
            "content": f"**Learning:** {learning}",
            "metadata": {
                "type": "learning",
                "tags": tags,
                "team": team,
                "author": os.environ.get("FLOW_GUARDIAN_USER", "unknown"),
                "timestamp": datetime.now().isoformat()
            },
            "send_to_llm": False  # Just store, don't generate
        }
    )
```

## Edge Cases

- Empty learning text: Reject with helpful message
- Very long learning (>500 chars): Warn but allow
- Duplicate learning: Store anyway (timestamps differ)
- Offline: Store locally, sync later (stretch goal)

## Dependencies

- `backboard_client.py` — Primary storage
- `memory.py` — Local fallback
