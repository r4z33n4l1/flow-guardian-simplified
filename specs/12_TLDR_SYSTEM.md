# TLDR System Specification

## Overview

Token-efficient summarization system. Never inject raw content—always compress via Cerebras first.

---

## Why TLDR?

```
Problem:
  Raw session history    = 50,000 tokens
  Claude context limit   = ~100,000 tokens
  Available for work     = 50,000 tokens (half wasted!)

Solution:
  Raw session history    = 50,000 tokens
  → Cerebras TLDR        = 500 tokens
  Available for work     = 99,500 tokens
```

---

## Depth Levels

| Level | Content | ~Tokens | Use Case |
|-------|---------|---------|----------|
| **L0** | File paths only | ~50 | Quick reference |
| **L1** | + One-line descriptions | ~200 | Default injection |
| **L2** | + Key logic summaries | ~500 | Detailed context |
| **L3** | Full context | Variable | Rarely needed |

### Example

**L0:**
```
Files: auth.py, test_auth.py, middleware.py
```

**L1:**
```
- auth.py: JWT authentication with token generation/validation
- test_auth.py: Unit tests for auth flows
- middleware.py: Request authentication middleware
```

**L2:**
```
- auth.py: JWT auth using HS256. Key functions: generate_token(user_id, expiry),
  validate_token(token) → user_id. Token includes iat, exp, sub claims.
- test_auth.py: Tests for valid/expired/malformed tokens, edge cases.
- middleware.py: FastAPI dependency that extracts and validates JWT from headers.
```

---

## Module: `tldr.py`

### Functions

```python
def summarize_context(
    content: str,
    level: str = "L1",
    max_tokens: int = 500
) -> str:
    """
    Summarize content to specified depth level using Cerebras.

    Args:
        content: Raw content to summarize
        level: "L0", "L1", "L2", or "L3"
        max_tokens: Maximum output tokens

    Returns:
        Compressed summary at specified level
    """

def summarize_handoff(handoff: dict, level: str = "L1") -> str:
    """
    Create TLDR of handoff state.

    Returns formatted summary like:
    "Working on: JWT auth. Current focus: debugging token expiry.
     Hypothesis: off-by-one error. Files: auth.py, test_auth.py"
    """

def summarize_recall(
    recall_results: list[dict],
    level: str = "L1",
    max_tokens: int = 300
) -> str:
    """
    Summarize Backboard recall results.

    Groups by category (learnings, decisions, context).
    Returns compact summary.
    """

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (4 chars = 1 token).
    Used to decide if TLDR is needed.
    """
```

---

## Cerebras Prompts

### L1 Summary (Default)
```
Summarize this context in 2-3 sentences. Focus on:
1. What is being worked on
2. Current state/progress
3. Key decisions made

Keep it actionable and concise.

CONTEXT:
{content}
```

### L2 Summary (Detailed)
```
Create a detailed but compact summary:
1. Goal and current focus
2. Key technical details and decisions
3. Blockers or hypotheses being tested
4. Important file/function references

Format as bullet points. Max 500 tokens.

CONTEXT:
{content}
```

---

## Token Thresholds

| Input Size | Action |
|------------|--------|
| < 500 tokens | No TLDR needed, use as-is |
| 500-2000 tokens | L1 summary |
| 2000-5000 tokens | L2 summary |
| > 5000 tokens | L2 summary with chunking |

---

## Error Handling

- Cerebras unavailable: Return truncated raw content
- Empty content: Return empty string
- Token estimation off: Err on side of summarizing

---

## Testing

```python
def test_summarize_small_content():
    """Small content returned as-is."""

def test_summarize_large_content():
    """Large content gets TLDR."""

def test_level_l0():
    """L0 returns only file paths."""

def test_level_l1():
    """L1 returns paths + descriptions."""

def test_cerebras_fallback():
    """Falls back gracefully when Cerebras unavailable."""

def test_estimate_tokens():
    """Token estimation is reasonably accurate."""
```
