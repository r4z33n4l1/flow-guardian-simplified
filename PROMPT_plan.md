0a. Study `specs/*` with up to 250 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `*.py` (root Python files) with up to 250 parallel Sonnet subagents to understand the codebase.
0d. For reference, the application source code is in the root directory (`*.py` files).

1. Study @IMPLEMENTATION_PLAN.md (if present; it may be incorrect) and use up to 500 Sonnet subagents to study existing source code (`*.py` at root) and compare it against `specs/*`. Use an Opus subagent to analyze findings, prioritize tasks, and create/update @IMPLEMENTATION_PLAN.md as a bullet point list sorted in priority of items yet to be implemented. Ultrathink. Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests, and inconsistent patterns. Study @IMPLEMENTATION_PLAN.md to determine starting point for research and keep it up to date with items considered complete/incomplete using subagents.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing; confirm with code search first.

ULTIMATE GOAL: Build "Flow Guardian" — persistent memory for AI coding sessions. Claude forgets, Flow Guardian remembers. Users can save session context, learnings, and decisions, then restore them in future sessions. Integrates with Cerebras (fast inference) and Backboard.io (persistent memory layer). Built for 8090 x Highline Beta Hackathon.

IMPORTANT RULES:
- NEVER add "Co-Authored-By: Claude" or any AI attribution to commits. All commits are by the user.
- NEVER mention "Continuous Claude" or "CC-v3" in any code, comments, or documentation.
