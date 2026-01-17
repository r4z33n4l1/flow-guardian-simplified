"""TLDR System for Flow Guardian.

Token-efficient summarization system. Never inject raw content—always compress
via Cerebras first. Converts large content into concise summaries to maximize
the context window available for actual work.

Depth Levels:
- L0: File paths only (~50 tokens)
- L1: + One-line descriptions (~200 tokens) - DEFAULT
- L2: + Key logic summaries (~500 tokens)
- L3: Full context (variable)

Token Thresholds:
- < 500 tokens: No TLDR needed, use as-is
- 500-2000 tokens: L1 summary
- 2000-5000 tokens: L2 summary
- > 5000 tokens: L2 summary with chunking
"""
import logging
from typing import Optional

from cerebras_client import complete, CerebrasError


# ============ CONSTANTS ============

VALID_LEVELS = {"L0", "L1", "L2", "L3"}
DEFAULT_LEVEL = "L1"

# Token thresholds for automatic summarization
THRESHOLD_NO_TLDR = 500      # Below this, use as-is
THRESHOLD_L1 = 2000          # 500-2000 tokens → L1
THRESHOLD_L2 = 5000          # 2000-5000 tokens → L2
                              # Above 5000 → L2 with chunking

# Default max output tokens per level
MAX_TOKENS_L0 = 100
MAX_TOKENS_L1 = 300
MAX_TOKENS_L2 = 600
MAX_TOKENS_L3 = 1500

logger = logging.getLogger(__name__)


# ============ TOKEN ESTIMATION ============

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (4 chars = 1 token).
    Used to decide if TLDR is needed.

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Simple heuristic: ~4 characters per token (accounts for whitespace)
    return len(text) // 4


# ============ SUMMARIZATION FUNCTIONS ============

def summarize_context(
    content: str,
    level: str = "L1",
    max_tokens: Optional[int] = None
) -> str:
    """
    Summarize content to specified depth level using Cerebras.

    Args:
        content: Raw content to summarize
        level: "L0", "L1", "L2", or "L3"
        max_tokens: Maximum output tokens (auto-determined if None)

    Returns:
        Compressed summary at specified level
    """
    if not content or not content.strip():
        return ""

    # Validate level
    if level not in VALID_LEVELS:
        logger.warning(f"Invalid level '{level}', using default L1")
        level = DEFAULT_LEVEL

    # Determine if TLDR is needed
    estimated = estimate_tokens(content)

    # L3 = full context, no summarization unless huge
    if level == "L3":
        if estimated < 10000:  # Very large threshold for L3
            return content
        # Fall through to summarize very large content

    # Small content doesn't need TLDR (unless L0 requested)
    if estimated < THRESHOLD_NO_TLDR and level != "L0":
        return content

    # Set max tokens based on level if not specified
    if max_tokens is None:
        max_tokens = {
            "L0": MAX_TOKENS_L0,
            "L1": MAX_TOKENS_L1,
            "L2": MAX_TOKENS_L2,
            "L3": MAX_TOKENS_L3,
        }.get(level, MAX_TOKENS_L1)

    # Build prompt based on level
    prompt = _build_summarize_prompt(content, level)

    try:
        result = complete(
            prompt=prompt,
            system="You are a concise technical summarizer. Preserve key details, remove fluff.",
            max_tokens=max_tokens
        )
        return result.strip()
    except CerebrasError as e:
        logger.warning(f"Cerebras unavailable for TLDR: {e}")
        # Fallback: truncate if too long
        return _truncate_fallback(content, max_tokens * 4)


def _build_summarize_prompt(content: str, level: str) -> str:
    """Build the summarization prompt based on level."""
    if level == "L0":
        return f"""Extract ONLY the file paths mentioned in this content.
Return them as a simple list, one per line.
If no file paths, return "No files mentioned."

CONTENT:
{content}"""

    elif level == "L1":
        return f"""Summarize this context in 2-3 sentences. Focus on:
1. What is being worked on
2. Current state/progress
3. Key decisions made

Keep it actionable and concise.

CONTEXT:
{content}"""

    elif level == "L2":
        return f"""Create a detailed but compact summary:
1. Goal and current focus
2. Key technical details and decisions
3. Blockers or hypotheses being tested
4. Important file/function references

Format as bullet points. Be concise but thorough.

CONTEXT:
{content}"""

    else:  # L3 with very large content
        return f"""Preserve all important information while removing redundancy:
1. Main goals and context
2. All technical details and decisions
3. Current state and progress
4. All relevant file and code references
5. Blockers, hypotheses, and insights

CONTEXT:
{content}"""


def _truncate_fallback(content: str, max_chars: int) -> str:
    """Fallback when Cerebras unavailable: truncate with ellipsis."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars - 20] + "\n...[truncated]..."


def summarize_handoff(handoff: dict, level: str = "L1") -> str:
    """
    Create TLDR of handoff state.

    Args:
        handoff: Handoff dictionary with goal, now, hypothesis, files, etc.
        level: TLDR level (L0, L1, L2, L3)

    Returns:
        Formatted summary string
    """
    if not handoff:
        return ""

    # For L0, just return files
    if level == "L0":
        files = handoff.get("files", [])
        if files:
            return "Files: " + ", ".join(files)
        return ""

    # Build summary parts
    parts = []

    goal = handoff.get("goal")
    if goal:
        parts.append(f"Goal: {goal}")

    now = handoff.get("now")
    if now:
        parts.append(f"Current focus: {now}")

    hypothesis = handoff.get("hypothesis")
    if hypothesis and level in ("L2", "L3"):
        parts.append(f"Hypothesis: {hypothesis}")

    outcome = handoff.get("outcome")
    if outcome and level in ("L2", "L3"):
        parts.append(f"Outcome: {outcome}")

    branch = handoff.get("branch")
    if branch:
        parts.append(f"Branch: {branch}")

    files = handoff.get("files", [])
    if files:
        if level == "L1":
            parts.append(f"Files: {', '.join(files[:5])}")
            if len(files) > 5:
                parts[-1] += f" (+{len(files) - 5} more)"
        else:
            parts.append(f"Files: {', '.join(files)}")

    status = handoff.get("status")
    if status:
        parts.append(f"Status: {status}")

    return ". ".join(parts)


def summarize_recall(
    recall_results: list,
    level: str = "L1",
    max_tokens: int = 300
) -> str:
    """
    Summarize Backboard recall results.
    Groups by category (learnings, decisions, context).

    Args:
        recall_results: List of recall result dictionaries
        level: TLDR level
        max_tokens: Maximum output tokens

    Returns:
        Compact summary of recall results
    """
    if not recall_results:
        return ""

    # Group by type
    categories = {
        "learnings": [],
        "decisions": [],
        "context": [],
        "insights": [],
    }

    for item in recall_results:
        content = item.get("content", "") or item.get("text", "")
        metadata = item.get("metadata", {})
        item_type = metadata.get("type", "context")

        if item_type in categories:
            categories[item_type].append(content)
        else:
            categories["context"].append(content)

    # For L0, just count items
    if level == "L0":
        counts = []
        for cat, items in categories.items():
            if items:
                counts.append(f"{len(items)} {cat}")
        return "Memory: " + ", ".join(counts) if counts else ""

    # Build formatted output
    parts = []

    for cat, items in categories.items():
        if not items:
            continue

        if level == "L1":
            # Just first item summary for each category
            snippet = items[0][:100] + "..." if len(items[0]) > 100 else items[0]
            parts.append(f"**{cat.title()}**: {snippet}")
            if len(items) > 1:
                parts[-1] += f" (+{len(items) - 1} more)"
        else:
            # L2/L3: Include more items
            parts.append(f"**{cat.title()}**:")
            for i, item in enumerate(items[:5]):  # Max 5 per category
                snippet = item[:200] + "..." if len(item) > 200 else item
                parts.append(f"  - {snippet}")
            if len(items) > 5:
                parts.append(f"  (+{len(items) - 5} more {cat})")

    combined = "\n".join(parts)

    # If output is too large, summarize with Cerebras
    if estimate_tokens(combined) > max_tokens and level != "L0":
        return summarize_context(combined, level, max_tokens)

    return combined


def auto_summarize(content: str, max_output_tokens: int = 500) -> str:
    """
    Automatically select appropriate TLDR level based on content size.

    Args:
        content: Content to summarize
        max_output_tokens: Maximum tokens for output

    Returns:
        Summarized content at appropriate level
    """
    if not content:
        return ""

    estimated = estimate_tokens(content)

    if estimated < THRESHOLD_NO_TLDR:
        return content
    elif estimated < THRESHOLD_L1:
        return summarize_context(content, "L1", max_output_tokens)
    elif estimated < THRESHOLD_L2:
        return summarize_context(content, "L2", max_output_tokens)
    else:
        return summarize_context(content, "L2", max_output_tokens)
