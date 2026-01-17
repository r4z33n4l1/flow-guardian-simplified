"""Cerebras Cloud SDK client for Flow Guardian.

Provides fast LLM inference for context analysis and restoration message generation.
Uses Llama 3.3 70B via Cerebras for 10-100x faster inference.
"""
import os
import json
from typing import Optional
from cerebras.cloud.sdk import Cerebras


# ============ CONFIGURATION ============

API_KEY = os.environ.get("CEREBRAS_API_KEY")
DEFAULT_MODEL = "llama-3.3-70b"


# ============ EXCEPTIONS ============

class CerebrasError(Exception):
    """Base exception for Cerebras-related errors."""
    pass


class CerebrasAuthError(CerebrasError):
    """Authentication failure with Cerebras API."""
    pass


class CerebrasRateLimitError(CerebrasError):
    """Rate limit exceeded on Cerebras API."""
    pass


# ============ CLIENT ============

def _get_client() -> Cerebras:
    """Get configured Cerebras client."""
    if not API_KEY:
        raise CerebrasAuthError("CEREBRAS_API_KEY environment variable not set")
    return Cerebras(api_key=API_KEY)


def complete(
    prompt: str,
    system: Optional[str] = None,
    json_mode: bool = False,
    max_tokens: int = 1000
) -> str:
    """
    Generic completion function for custom prompts.

    Args:
        prompt: The user prompt to complete
        system: Optional system message
        json_mode: If True, request JSON-formatted response
        max_tokens: Maximum tokens in response (default: 1000)

    Returns:
        String response from the model

    Raises:
        CerebrasError: On API errors
        CerebrasAuthError: On authentication failure
        CerebrasRateLimitError: On rate limit exceeded
    """
    try:
        client = _get_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Build create arguments
        response_format = {"type": "json_object"} if json_mode else None

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            response_format=response_format,  # type: ignore[arg-type]
        )

        if hasattr(response, 'choices') and response.choices:
            choices = response.choices
            if len(choices) > 0:  # type: ignore[arg-type]
                return choices[0].message.content or ""  # type: ignore[index]
        return ""

    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
            raise CerebrasAuthError(f"Authentication failed: {e}")
        elif "429" in error_str or "rate" in error_str:
            raise CerebrasRateLimitError(f"Rate limit exceeded: {e}")
        else:
            raise CerebrasError(f"Cerebras API error: {e}")


def analyze_session_context(
    branch: str,
    files: list[str],
    diff_summary: str,
    user_message: Optional[str] = None
) -> dict:
    """
    Analyze current session state and extract structured context.

    Args:
        branch: Current git branch name
        files: List of modified/relevant files
        diff_summary: Summary of uncommitted changes
        user_message: Optional user-provided context note

    Returns:
        Dictionary with keys:
        - summary: One-sentence description of work
        - hypothesis: Current theory or approach
        - next_steps: List of 1-3 likely next actions
        - decisions: Key decisions made
        - learnings: Insights discovered
    """
    prompt = f"""Analyze this coding session state and extract:
1. SUMMARY: One sentence describing what the user is working on
2. HYPOTHESIS: Their current theory or approach (if apparent)
3. NEXT_STEPS: List of likely next actions (1-3 items)
4. DECISIONS: Key decisions made during this session
5. LEARNINGS: Insights discovered

Git branch: {branch}
Modified files: {', '.join(files) if files else 'none'}
Recent changes: {diff_summary if diff_summary else 'none'}
User message: {user_message if user_message else 'none provided'}

Respond in JSON format with these exact keys: summary, hypothesis, next_steps, decisions, learnings.
Use null for hypothesis if not apparent. Use empty arrays [] for next_steps, decisions, learnings if none identified."""

    system = "You are a coding session analyzer. Extract structured context from development sessions. Be concise and accurate. Always respond with valid JSON."

    try:
        response = complete(prompt, system=system, json_mode=True, max_tokens=800)
        result = json.loads(response)

        # Ensure all expected keys exist with defaults
        return {
            "summary": result.get("summary") or "Working on code changes",
            "hypothesis": result.get("hypothesis"),
            "next_steps": result.get("next_steps") or [],
            "decisions": result.get("decisions") or [],
            "learnings": result.get("learnings") or [],
        }
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "summary": user_message or "Working on code changes",
            "hypothesis": None,
            "next_steps": [],
            "decisions": [],
            "learnings": [],
        }


def generate_restoration_message(context: dict, changes: dict) -> str:
    """
    Generate a "welcome back" message for developers returning to work.

    Args:
        context: Previous session context with keys:
            - summary: What they were working on
            - hypothesis: Their approach
            - files: Relevant files
            - branch: Git branch
            - learnings: Previous learnings
        changes: What changed while away:
            - elapsed: Time elapsed (human readable)
            - commits: New commits (list)
            - files_changed: Files modified by others

    Returns:
        Natural language restoration message (under 10 lines)
    """
    prompt = f"""Generate a concise "welcome back" summary for a developer returning to their coding session.

PREVIOUS CONTEXT:
- Working on: {context.get('summary', 'unknown')}
- Hypothesis: {context.get('hypothesis', 'none')}
- Key files: {', '.join(context.get('files', [])) if context.get('files') else 'none'}
- Branch: {context.get('branch', 'unknown')}
- Previous learnings: {', '.join(context.get('learnings', [])) if context.get('learnings') else 'none'}

CHANGES WHILE AWAY:
- Time elapsed: {changes.get('elapsed', 'unknown')}
- New commits: {len(changes.get('commits', []))} commits
- Files changed by others: {', '.join(changes.get('files_changed', [])) if changes.get('files_changed') else 'none'}

Generate a message with:
1. Quick reminder of what they were working on (1 sentence)
2. Their hypothesis (if any)
3. What changed while away (highlight if it affects their work!)
4. Suggested next action

Keep it under 10 lines. Be direct and useful, no fluff."""

    system = "You are a helpful coding assistant. Generate concise, actionable restoration messages for developers returning to their work."

    try:
        return complete(prompt, system=system, max_tokens=500)
    except CerebrasError:
        # Graceful fallback if Cerebras is unavailable
        summary = context.get('summary', 'your previous work')
        elapsed = changes.get('elapsed', 'some time')
        return f"Welcome back! You were working on: {summary}\nTime away: {elapsed}\nReady to continue where you left off."
