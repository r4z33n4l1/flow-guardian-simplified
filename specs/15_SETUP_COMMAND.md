# Setup Command Specification

## Overview

One-time `flow setup` command to initialize Flow Guardian for a project.

---

## Usage

```bash
flow setup              # Interactive setup in current directory
flow setup --global     # Set up global hooks (all projects)
flow setup --check      # Verify setup without modifying
```

---

## What Setup Does

### 1. Create `.flow-guardian/` Directory

```
.flow-guardian/
├── handoff.yaml       # Empty/initial state
└── config.yaml        # Local config overrides
```

### 2. Create Hook Scripts

```
.claude/
├── hooks/
│   ├── flow-inject.sh      # SessionStart hook
│   └── flow-precompact.sh  # PreCompact hook
└── settings.json           # Hook configuration
```

### 3. Verify Environment

- Check for `CEREBRAS_API_KEY`
- Check for `BACKBOARD_API_KEY`
- Warn if missing (don't fail)

### 4. Optional: Run Assistant Setup

If Backboard keys exist but thread IDs missing:
- Offer to run `python setup_assistants.py`
- Display thread IDs for `.env`

---

## Command Implementation

### Flags

| Flag | Description |
|------|-------------|
| `--global/-g` | Install hooks globally (user-level) |
| `--check/-c` | Check setup status without modifying |
| `--force/-f` | Overwrite existing files |

### Output

```
Flow Guardian Setup
═══════════════════

✓ Created .flow-guardian/
✓ Created .flow-guardian/handoff.yaml
✓ Created .claude/hooks/flow-inject.sh
✓ Created .claude/hooks/flow-precompact.sh
✓ Updated .claude/settings.json

Environment:
✓ CEREBRAS_API_KEY found
✓ BACKBOARD_API_KEY found
✓ BACKBOARD_PERSONAL_THREAD_ID found

Setup complete! Flow Guardian will now:
• Automatically inject context on session start
• Save state before context compaction
• Remember your learnings across sessions

Run 'flow save' to create your first checkpoint.
```

---

## Files Created

### `.flow-guardian/handoff.yaml`

```yaml
# Flow Guardian Handoff State
# Auto-updated by flow save, daemon, and hooks
goal: null
status: null
now: null
timestamp: null
```

### `.flow-guardian/config.yaml`

```yaml
# Flow Guardian Local Config
# Overrides global settings for this project

# TLDR depth for injection (L0, L1, L2, L3)
tldr_level: L1

# Include files in context
include_files: true

# Auto-inject on session start
auto_inject: true
```

### `.claude/hooks/flow-inject.sh`

```bash
#!/bin/bash
# Flow Guardian SessionStart Hook

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --quiet 2>/dev/null
fi
```

### `.claude/hooks/flow-precompact.sh`

```bash
#!/bin/bash
# Flow Guardian PreCompact Hook

if [ -d ".flow-guardian" ]; then
    [ -f ".env" ] && export $(grep -v '^#' .env | xargs)
    flow inject --save-state 2>/dev/null
fi
```

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

## Global Setup (`--global`)

For user-level hooks (all projects):

### Location

```
~/.claude/
├── hooks/
│   ├── flow-inject.sh
│   └── flow-precompact.sh
└── settings.json
```

### Behavior

- Hooks run for all projects
- Only inject if `.flow-guardian/` exists in project
- Falls back gracefully if flow CLI not installed

---

## Check Mode (`--check`)

```
Flow Guardian Setup Status
══════════════════════════

Project: /Users/dev/my-project

Local Setup:
  .flow-guardian/          ✓ exists
  .flow-guardian/handoff.yaml  ✓ exists
  .claude/hooks/           ✓ exists
  .claude/settings.json    ✓ configured

Environment:
  CEREBRAS_API_KEY         ✓ set
  BACKBOARD_API_KEY        ✓ set
  BACKBOARD_PERSONAL_THREAD_ID  ✓ set
  BACKBOARD_TEAM_THREAD_ID ⚠ not set (team features disabled)

Status: Ready
```

---

## Error Handling

- Existing files: Skip with message (use `--force` to overwrite)
- Permission denied: Clear error with suggestion
- Missing flow CLI: Link to installation instructions

---

## Testing

```python
def test_setup_creates_directories():
    """Creates .flow-guardian and .claude/hooks."""

def test_setup_creates_hook_scripts():
    """Hook scripts are executable."""

def test_setup_updates_settings():
    """settings.json includes hook config."""

def test_setup_check_mode():
    """Check mode doesn't modify files."""

def test_setup_global_mode():
    """Global setup writes to ~/.claude/."""

def test_setup_force_overwrites():
    """Force flag overwrites existing files."""
```
