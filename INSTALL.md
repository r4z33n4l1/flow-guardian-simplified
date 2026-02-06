# Installing Flow Guardian for OpenClaw

## Prerequisites

- **Python 3.10+** (for skill tools)
- **PyYAML** (`pip install PyYAML>=6.0.0`)
- **Git** (for git state capture)
- An OpenClaw installation with `~/.openclaw/` directory

## Quick Install

```bash
# 1. Clone the repo
git clone https://github.com/user/flow-guardian.git
cd flow-guardian

# 2. Install the skill
cp -r skill/flow-guardian/ ~/.openclaw/skills/flow-guardian/

# 3. Install the hook (optional, for auto-inject/capture)
cp -r hook/flow-guardian/ ~/.openclaw/hooks/flow-guardian/

# 4. Install Python dependency
pip install PyYAML>=6.0.0

# 5. Create memory directory
mkdir -p ~/.openclaw/workspace/memory
```

## Verify Installation

```bash
# Test code TLDR (should output structured summary)
python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file ~/.openclaw/skills/flow-guardian/tldr_code.py --level L1

# Test handoff save/load
python3 ~/.openclaw/skills/flow-guardian/handoff.py save \
  --goal "Test installation" \
  --now "Verifying tools work" \
  --status in_progress

python3 ~/.openclaw/skills/flow-guardian/handoff.py load

# Test git capture (run from any git repo)
cd /path/to/any/git/repo
python3 ~/.openclaw/skills/flow-guardian/git_capture.py
```

## Add to AGENTS.md (Recommended)

Add the following to your `~/.openclaw/workspace/AGENTS.md` so the agent knows about the skill:

```markdown
## Flow Guardian (Session Memory)

At session start, check `memory/handoff.yaml` for previous session state.
Use it to understand what was being worked on and continue seamlessly.

Before ending a session or when asked to save state, run:
`python3 ~/.openclaw/skills/flow-guardian/handoff.py save --goal "..." --now "..." --status "..."`

For large code files, use TLDR compression to extract structure:
`python3 ~/.openclaw/skills/flow-guardian/tldr_code.py --file <path> --level L1`
```

## Directory Structure After Install

```
~/.openclaw/
├── skills/
│   └── flow-guardian/
│       ├── SKILL.md
│       ├── tldr_code.py
│       ├── tldr.py
│       ├── handoff.py
│       ├── git_capture.py
│       └── requirements.txt
├── hooks/
│   └── flow-guardian/
│       ├── HOOK.md
│       └── handler.ts
└── workspace/
    └── memory/
        ├── handoff.yaml      ← created by handoff.py
        └── learnings.md      ← created by agent
```

## Uninstall

```bash
rm -rf ~/.openclaw/skills/flow-guardian/
rm -rf ~/.openclaw/hooks/flow-guardian/
# Optionally remove handoff data:
# rm ~/.openclaw/workspace/memory/handoff.yaml
```

## No API Keys Needed

Flow Guardian works entirely locally:
- **Code TLDR** uses Python's built-in `ast` module — no LLM calls
- **TLDR prompts** generate structured prompts your agent processes with its own model
- **Handoff** reads/writes local YAML files
- **Git capture** uses the system `git` command

Zero external services. Works offline.
