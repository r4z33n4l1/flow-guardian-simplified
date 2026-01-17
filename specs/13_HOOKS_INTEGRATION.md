# Hooks Integration Specification

## Overview

Claude Code hooks enable automatic context injection without user intervention.

---

## Hook Types

### 1. SessionStart Hook
Fires when a new Claude Code session begins.

**Purpose:** Inject context so Claude immediately knows project state.

**Trigger:** Session initialization

**Script:** `.claude/hooks/flow-inject.sh`

### 2. PreCompact Hook
Fires before context compaction (when context window is filling up).

**Purpose:** Save current state before context is compressed.

**Trigger:** Context approaching limit

**Script:** `.claude/hooks/flow-precompact.sh`

---

## Hook Configuration

### `.claude/settings.json`

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/flow-inject.sh"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/flow-precompact.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Hook Scripts

### `.claude/hooks/flow-inject.sh`

```bash
#!/bin/bash
# Flow Guardian SessionStart Hook
# Injects project context at session start

# Only run if .flow-guardian exists in project
if [ -d ".flow-guardian" ]; then
    # Source environment (API keys)
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    # Inject context (output goes to Claude)
    flow inject --quiet 2>/dev/null
fi
```

### `.claude/hooks/flow-precompact.sh`

```bash
#!/bin/bash
# Flow Guardian PreCompact Hook
# Saves state before context compaction

if [ -d ".flow-guardian" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi

    # Save current state
    flow inject --save-state 2>/dev/null
fi
```

---

## `flow inject` Command

### Usage

```bash
flow inject              # Full injection with formatting
flow inject --quiet      # No formatting, stdout only (for hooks)
flow inject --level L1   # Control TLDR depth
flow inject --save-state # Save current state (for PreCompact)
```

### Flags

| Flag | Description |
|------|-------------|
| `--quiet/-q` | Plain output, no Rich formatting |
| `--level/-l` | TLDR depth: L0, L1, L2, L3 (default: L1) |
| `--save-state` | Save state to handoff.yaml instead of output |

### Output Format (for Claude)

```
<flow-guardian-context>
## Current Session State

**Goal:** Implement user authentication with JWT
**Status:** in_progress
**Now:** Debugging token expiry in auth.py
**Hypothesis:** Off-by-one error in timestamp comparison
**Branch:** fix/jwt-expiry

## Relevant Memory

- **Learning:** JWT tokens need both iat and exp claims for proper validation
- **Decision:** Using HS256 algorithm for token signing (simpler than RS256)
- **Context:** Auth system integrates with existing user model

## Files

- src/auth.py
- tests/test_auth.py
</flow-guardian-context>
```

---

## Module: `inject.py`

### Functions

```python
async def generate_injection(
    level: str = "L1",
    quiet: bool = False
) -> str:
    """
    Generate context injection for Claude.

    1. Load handoff.yaml
    2. Query Backboard for relevant memory
    3. TLDR if needed
    4. Format output

    Returns formatted context string.
    """

async def save_current_state() -> dict:
    """
    Save current session state to handoff.yaml.
    Called by PreCompact hook.

    Returns saved handoff data.
    """

def format_injection(
    handoff: dict,
    memory: list[dict],
    quiet: bool = False
) -> str:
    """
    Format handoff + memory for injection.

    If quiet: plain text
    Otherwise: Rich formatted
    """
```

---

## Installation

Created by `flow setup` command:

1. Create `.claude/hooks/` directory
2. Write hook scripts with execute permission
3. Create/update `.claude/settings.json`
4. Create `.flow-guardian/` if missing

---

## Error Handling

- Hook script errors: Fail silently (don't block Claude)
- Missing `.flow-guardian`: Skip injection (no context)
- API errors: Use local fallback or skip
- Permission errors: Log warning to stderr

---

## Testing

```python
def test_inject_with_handoff():
    """Injection includes handoff state."""

def test_inject_with_memory():
    """Injection includes Backboard recall."""

def test_inject_quiet_mode():
    """Quiet mode outputs plain text."""

def test_inject_save_state():
    """Save state writes to handoff.yaml."""

def test_hook_script_generation():
    """Hook scripts are properly formatted."""
```
