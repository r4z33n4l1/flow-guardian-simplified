# Spec: Cerebras Client (`cerebras_client.py`)

## Overview

Client for Cerebras Cloud SDK — handles fast LLM inference for context analysis and restoration message generation.

## Why Cerebras

- **Speed**: 10-100x faster inference than traditional GPU providers
- **Hackathon sponsor**: Free API access with increased rate limits
- **Models**: Llama 3.3 70B, others

## Configuration

```python
# Environment
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")

# Default model
DEFAULT_MODEL = "llama-3.3-70b"
```

## API Functions

### Context Analysis

```python
def analyze_session_context(
    branch: str,
    files: list[str],
    diff_summary: str,
    user_message: str = None
) -> dict:
    """
    Analyze current session state and extract structured context.

    Returns:
        {
            "summary": "What user is working on",
            "hypothesis": "Current theory/approach",
            "next_steps": ["step1", "step2"],
            "decisions": ["decision1"],
            "learnings": ["learning1"]
        }
    """
```

### Restoration Message

```python
def generate_restoration_message(
    context: dict,
    changes: dict
) -> str:
    """
    Generate a "welcome back" message.

    Args:
        context: Previous session context
        changes: What changed while away (commits, time, etc.)

    Returns:
        Natural language restoration message
    """
```

### Generic Completion

```python
def complete(
    prompt: str,
    system: str = None,
    json_mode: bool = False,
    max_tokens: int = 1000
) -> str:
    """
    Generic completion for custom prompts.

    Args:
        prompt: User prompt
        system: Optional system message
        json_mode: If True, request JSON response
        max_tokens: Max response length
    """
```

## Prompts

### Context Analysis Prompt

```
Analyze this coding session state and extract:

1. SUMMARY: One sentence describing what the user is working on
2. HYPOTHESIS: Their current theory or approach (if apparent)
3. NEXT_STEPS: List of 1-3 likely next actions
4. DECISIONS: Key decisions made (if any visible)
5. LEARNINGS: Insights discovered (if any visible)

Context:
- Git branch: {branch}
- Files modified: {files}
- Recent changes: {diff_summary}
- User note: {user_message}

Respond in JSON format with keys: summary, hypothesis, next_steps, decisions, learnings
Be concise. If you can't infer something, use null or empty array.
```

### Restoration Prompt

```
Generate a concise "welcome back" message for a developer.

THEIR LAST CONTEXT:
- Working on: {summary}
- Hypothesis: {hypothesis}
- Files: {files}
- Branch: {branch}

CHANGES WHILE AWAY:
- Time elapsed: {elapsed}
- New commits: {commits}
- Files changed: {files_changed}

Generate:
1. Quick reminder of what they were doing (1 sentence)
2. Their hypothesis (if they had one)
3. What changed while away (highlight if it affects their work!)
4. Suggested next action

Keep it under 10 lines. Be direct and useful. No fluff.
```

## Error Handling

```python
class CerebrasError(Exception):
    """Base exception for Cerebras errors."""

class CerebrasAuthError(CerebrasError):
    """Authentication failed."""

class CerebrasRateLimitError(CerebrasError):
    """Rate limited."""
```

## Requirements

### Functional

1. Must use official Cerebras SDK
2. Must handle rate limits gracefully
3. Must validate JSON responses
4. Must have reasonable defaults

### Non-Functional

- **Performance**: Responses in <2 seconds (Cerebras is fast)
- **Reliability**: Graceful fallback if unavailable
- **Cost**: Minimize tokens where possible

## Dependencies

- cerebras-cloud-sdk
- Standard library (os, json)
