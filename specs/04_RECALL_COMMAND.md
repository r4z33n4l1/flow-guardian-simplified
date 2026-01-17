# Spec: `flow recall` Command

## Overview

The `flow recall` command searches stored learnings and session context using semantic search. This is the "remember" functionality — finding relevant past knowledge.

## Jobs to Be Done (JTBD)

When I need to remember something I learned previously (or context from a past session), I want to search my stored knowledge so I can find it quickly without re-discovering it.

## Requirements

### Functional Requirements

1. The command shall accept a natural language query:
   ```bash
   flow recall "authentication issues"
   flow recall "how did we fix the token bug"
   ```

2. The command shall search:
   - Stored learnings
   - Past session contexts
   - Decisions and hypotheses

3. The command shall use Backboard.io's semantic search (`memory="auto"`)

4. The command shall display results ranked by relevance

5. The command shall support filters:
   - `--tag <tag>` — Filter by tag
   - `--since <date>` — Filter by date
   - `--limit <n>` — Limit results (default: 10)

6. The command shall fall back to local keyword search if Backboard unavailable

### Non-Functional Requirements

- **Performance**: Results in <2 seconds
- **Relevance**: Semantic search should surface conceptually related items

## Acceptance Criteria

- [ ] `flow recall "query"` returns relevant learnings
- [ ] `flow recall "query"` searches session contexts too
- [ ] Results are ranked by relevance
- [ ] `--tag` filter works
- [ ] `--since` filter works
- [ ] `--limit` works
- [ ] Falls back to local search if offline

## Output Format

```
╭─────────────────── Recall: "auth issues" ────────────────────╮
│                                                               │
│  Found 3 relevant items:                                      │
│                                                               │
│  1. 💡 Learning (Jan 17, 2026)                               │
│     "JWT tokens use UTC timestamps, not local time"          │
│     Tags: auth, jwt, timezone                                │
│                                                               │
│  2. 📍 Session Context (Jan 16, 2026)                        │
│     Working on: Debugging auth token refresh                 │
│     Hypothesis: Race condition in refresh flow               │
│                                                               │
│  3. 💡 Learning (Jan 15, 2026)                               │
│     "Auth middleware must run before rate limiter"           │
│     Tags: auth, middleware                                   │
│                                                               │
╰───────────────────────────────────────────────────────────────╯
```

## Implementation Notes

### Backboard.io Semantic Search

```python
async def recall(thread_id: str, query: str) -> str:
    response = await client.post(
        f"{BASE_URL}/threads/{thread_id}/messages",
        json={
            "content": f"Search for: {query}\n\nReturn relevant learnings and context.",
            "memory": "auto",  # Key: enables semantic recall
            "send_to_llm": True
        }
    )
    return response.json()["content"]
```

### Local Fallback Search

```python
def local_recall(query: str, learnings: list) -> list:
    query_lower = query.lower()
    results = []
    for item in learnings:
        score = 0
        if query_lower in item["text"].lower():
            score += 2
        for tag in item.get("tags", []):
            if query_lower in tag.lower():
                score += 1
        if score > 0:
            results.append((score, item))
    return sorted(results, key=lambda x: -x[0])
```

## Edge Cases

- No results: Show helpful "no matches" message with suggestions
- Query too short: Require minimum 2 characters
- Very broad query: Limit results, suggest refinement

## Dependencies

- `backboard_client.py` — Semantic search
- `memory.py` — Local fallback
