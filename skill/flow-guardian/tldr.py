#!/usr/bin/env python3
"""TLDR System for Flow Guardian (OpenClaw Edition).

Token-efficient summarization via structured prompts or Cerebras API.
By default, generates prompts for the agent's own model (zero deps).
With --cerebras flag, calls Cerebras API directly for fast, cheap summarization.

Depth Levels:
- L0: File paths only (~100 tokens)
- L1: + One-line descriptions (~300 tokens) - DEFAULT
- L2: + Key logic summaries (~600 tokens)
- L3: Full context (variable)

Token Thresholds:
- < 500 tokens: No TLDR needed, use as-is
- 500-2000 tokens: L1 summary
- 2000-5000 tokens: L2 summary
- > 5000 tokens: L2 summary with chunking

Usage:
    echo "content" | python3 tldr.py --level L1
    echo "content" | python3 tldr.py --level L2 --max-tokens 600
    python3 tldr.py --level L0 < large_file.txt
"""
import argparse
import json
import os
import sys


# ============ CONSTANTS ============

VALID_LEVELS = {"L0", "L1", "L2", "L3"}
DEFAULT_LEVEL = "L1"

# Token thresholds for automatic summarization
THRESHOLD_NO_TLDR = 500      # Below this, use as-is
THRESHOLD_L1 = 2000          # 500-2000 tokens → L1
THRESHOLD_L2 = 5000          # 2000-5000 tokens → L2

# Default max output tokens per level
MAX_TOKENS = {
    "L0": 100,
    "L1": 300,
    "L2": 600,
    "L3": 1500,
}


# ============ TOKEN ESTIMATION ============

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (4 chars = 1 token).

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


# ============ PROMPT BUILDERS ============

def build_summarize_prompt(content: str, level: str) -> str:
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

    else:  # L3
        return f"""Preserve all important information while removing redundancy:
1. Main goals and context
2. All technical details and decisions
3. Current state and progress
4. All relevant file and code references
5. Blockers, hypotheses, and insights

CONTEXT:
{content}"""


def auto_select_level(content: str) -> str:
    """
    Automatically select appropriate TLDR level based on content size.

    Args:
        content: Content to evaluate

    Returns:
        Recommended level string (L0, L1, L2, L3)
    """
    estimated = estimate_tokens(content)

    if estimated < THRESHOLD_NO_TLDR:
        return "passthrough"
    elif estimated < THRESHOLD_L1:
        return "L1"
    elif estimated < THRESHOLD_L2:
        return "L2"
    else:
        return "L2"


def generate_tldr_prompt(content: str, level: str = "L1", max_tokens: int = None) -> dict:
    """
    Generate a structured TLDR request.

    For small content, returns the content as-is (passthrough).
    For larger content, returns a prompt the agent should use with its LLM.

    Args:
        content: Raw content to summarize
        level: "L0", "L1", "L2", or "L3"
        max_tokens: Maximum output tokens (auto-determined if None)

    Returns:
        Dictionary with:
        - action: "passthrough" or "summarize"
        - content: Original content (if passthrough) or prompt (if summarize)
        - level: The TLDR level used
        - estimated_input_tokens: Estimated tokens in input
        - max_output_tokens: Suggested max tokens for output
        - system_prompt: System prompt to use for summarization
    """
    if not content or not content.strip():
        return {
            "action": "passthrough",
            "content": "",
            "level": level,
            "estimated_input_tokens": 0,
            "max_output_tokens": 0,
            "system_prompt": "",
        }

    if level not in VALID_LEVELS:
        level = DEFAULT_LEVEL

    estimated = estimate_tokens(content)

    if max_tokens is None:
        max_tokens = MAX_TOKENS.get(level, MAX_TOKENS["L1"])

    # Small content or L3 with small content: passthrough
    if estimated < THRESHOLD_NO_TLDR and level != "L0":
        return {
            "action": "passthrough",
            "content": content,
            "level": level,
            "estimated_input_tokens": estimated,
            "max_output_tokens": max_tokens,
            "system_prompt": "",
        }

    if level == "L3" and estimated < 10000:
        return {
            "action": "passthrough",
            "content": content,
            "level": "L3",
            "estimated_input_tokens": estimated,
            "max_output_tokens": max_tokens,
            "system_prompt": "",
        }

    prompt = build_summarize_prompt(content, level)

    return {
        "action": "summarize",
        "content": prompt,
        "level": level,
        "estimated_input_tokens": estimated,
        "max_output_tokens": max_tokens,
        "system_prompt": "You are a concise technical summarizer. Preserve key details, remove fluff.",
    }


def cerebras_summarize(content: str, level: str = "L1", max_tokens: int = None) -> str:
    """
    Summarize content using Cerebras API (fast + cheap).
    
    Requires CEREBRAS_API_KEY env var. Falls back to prompt generation if unavailable.
    
    Args:
        content: Content to summarize
        level: TLDR depth level
        max_tokens: Max output tokens
        
    Returns:
        Summarized text, or None if Cerebras unavailable
    """
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        return None
    
    try:
        import httpx
    except ImportError:
        # try urllib as fallback
        try:
            import urllib.request
            import urllib.error
            
            prompt = build_summarize_prompt(content, level)
            if max_tokens is None:
                max_tokens = MAX_TOKENS.get(level, MAX_TOKENS["L1"])
            
            payload = json.dumps({
                "model": "llama-4-scout-17b-16e-instruct",
                "messages": [
                    {"role": "system", "content": "You are a concise technical summarizer. Preserve key details, remove fluff."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            })
            
            req = urllib.request.Request(
                "https://api.cerebras.ai/v1/chat/completions",
                data=payload.encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None
    
    try:
        prompt = build_summarize_prompt(content, level)
        if max_tokens is None:
            max_tokens = MAX_TOKENS.get(level, MAX_TOKENS["L1"])
        
        resp = httpx.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-4-scout-17b-16e-instruct",
                "messages": [
                    {"role": "system", "content": "You are a concise technical summarizer. Preserve key details, remove fluff."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def summarize_handoff(handoff: dict, level: str = "L1") -> str:
    """
    Create TLDR of handoff state (no LLM needed — pure formatting).

    Supports both core fields (goal, now, status) and extended fields
    (done_this_session, decisions, findings, worked, failed, etc.).

    Args:
        handoff: Handoff dictionary with goal, now, hypothesis, files, etc.
        level: TLDR level (L0, L1, L2, L3)

    Returns:
        Formatted summary string
    """
    if not handoff:
        return ""

    if level == "L0":
        files = handoff.get("files", [])
        return ("Files: " + ", ".join(files)) if files else ""

    parts = []

    goal = handoff.get("goal")
    if goal:
        parts.append(f"Goal: {goal}")

    now = handoff.get("now")
    if now:
        parts.append(f"Current focus: {now}")

    status = handoff.get("status")
    if status:
        parts.append(f"Status: {status}")

    outcome = handoff.get("outcome")
    if outcome:
        parts.append(f"Outcome: {outcome}")

    branch = handoff.get("branch")
    if branch:
        parts.append(f"Branch: {branch}")

    hypothesis = handoff.get("hypothesis")
    if hypothesis and level in ("L2", "L3"):
        parts.append(f"Hypothesis: {hypothesis}")

    test = handoff.get("test")
    if test and level in ("L2", "L3"):
        parts.append(f"Verify: {test}")

    # Extended fields for L2/L3
    if level in ("L2", "L3"):
        done = handoff.get("done_this_session", [])
        if done:
            task_strs = []
            for item in done[:5]:
                if isinstance(item, dict):
                    task_strs.append(item.get("task", str(item)))
                else:
                    task_strs.append(str(item))
            parts.append(f"Done: {'; '.join(task_strs)}")

        decisions = handoff.get("decisions", [])
        if decisions:
            dec_strs = []
            for d in decisions[:3]:
                if isinstance(d, dict):
                    for k, v in d.items():
                        dec_strs.append(f"{k}: {v}")
                else:
                    dec_strs.append(str(d))
            parts.append(f"Decisions: {'; '.join(dec_strs)}")

        findings = handoff.get("findings", [])
        if findings:
            parts.append(f"Findings: {'; '.join(str(f) for f in findings[:3])}")

        worked = handoff.get("worked", [])
        if worked:
            parts.append(f"Worked: {'; '.join(str(w) for w in worked[:3])}")

        failed = handoff.get("failed", [])
        if failed:
            parts.append(f"Failed: {'; '.join(str(f) for f in failed[:3])}")

        blockers = handoff.get("blockers", [])
        if blockers:
            parts.append(f"Blockers: {'; '.join(str(b) for b in blockers[:3])}")

    files = handoff.get("files", [])
    if files:
        if level == "L1":
            parts.append(f"Files: {', '.join(files[:5])}")
            if len(files) > 5:
                parts[-1] += f" (+{len(files) - 5} more)"
        else:
            parts.append(f"Files: {', '.join(files)}")

    next_steps = handoff.get("next", [])
    if next_steps and level in ("L2", "L3"):
        parts.append(f"Next: {'; '.join(str(n) for n in next_steps[:3])}")

    return ". ".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="TLDR compression system. Reads from stdin, outputs structured prompts for LLM summarization."
    )
    parser.add_argument(
        "--level", "-l",
        choices=["L0", "L1", "L2", "L3"],
        default="L1",
        help="Depth level: L0=paths, L1=brief, L2=detailed, L3=full (default: L1)"
    )
    parser.add_argument(
        "--max-tokens", "-m",
        type=int,
        default=None,
        help="Maximum output tokens (auto-determined from level if omitted)"
    )
    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="Automatically select TLDR level based on content size"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON (includes metadata like action, level, token estimates)"
    )
    parser.add_argument(
        "--cerebras", "-c",
        action="store_true",
        help="Use Cerebras API for fast summarization (requires CEREBRAS_API_KEY env var)"
    )

    args = parser.parse_args()

    content = sys.stdin.read()

    if not content.strip():
        print("", end="")
        sys.exit(0)

    level = args.level
    if args.auto:
        level = auto_select_level(content)
        if level == "passthrough":
            if args.json:
                print(json.dumps({
                    "action": "passthrough",
                    "content": content,
                    "level": "auto",
                    "estimated_input_tokens": estimate_tokens(content),
                }, indent=2))
            else:
                print(content, end="")
            sys.exit(0)

    result = generate_tldr_prompt(content, level, args.max_tokens)

    # If cerebras flag is set and content needs summarization, call the API
    if args.cerebras and result["action"] == "summarize":
        summary = cerebras_summarize(content, level, args.max_tokens)
        if summary:
            if args.json:
                result["action"] = "cerebras_summarized"
                result["content"] = summary
                result["compressed_tokens"] = estimate_tokens(summary)
                print(json.dumps(result, indent=2))
            else:
                print(summary)
            sys.exit(0)
        else:
            print("⚠ Cerebras unavailable, falling back to prompt generation", file=sys.stderr)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["action"] == "passthrough":
            print(result["content"], end="")
        else:
            # Output the prompt that the agent should use
            print(result["content"])


if __name__ == "__main__":
    main()
