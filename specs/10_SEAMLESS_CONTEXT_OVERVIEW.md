# Seamless Context System Overview

> "Claude forgets. Flow Guardian remembers."

## Vision

When you open Claude Code in any project folder, it automatically knows:
- What this project is about
- What you were working on
- Key decisions and learnings
- Everything relevant from past sessions

No manual commands. No copy-paste. It just works.

---

## Architecture Components

### 1. Handoff System (spec 11)
YAML checkpoints that track session state. Auto-updated on:
- `flow save` (manual checkpoint)
- Session end (daemon captures)
- Context compaction (PreCompact hook)

### 2. TLDR System (spec 12)
Never inject raw content. Always summarize via Cerebras for token efficiency.
Layers: L0 (paths only) → L1 (descriptions) → L2 (logic) → L3 (full)

### 3. Hooks Integration (spec 13)
Claude Code hooks for automatic injection:
- SessionStart: Inject context on session start
- PreCompact: Save state before compaction

### 4. Semantic Recall (spec 14)
Query Backboard.io semantically: "What do I need to know about this project?"

### 5. Setup Command (spec 15)
One-time `flow setup` to initialize hooks and config.

---

## Data Flow

```
┌───────────────────────────────────────────────────────────────┐
│                      CAPTURE                                   │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  Daemon (background)          Manual                           │
│  ├─ Watches sessions          ├─ flow save                    │
│  ├─ Extracts insights         ├─ flow learn                   │
│  └─ Updates handoff.yaml      └─ Updates handoff.yaml         │
│                                                                │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                      STORAGE                                   │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  Local (always works)         Cloud (semantic search)          │
│  ├─ .flow-guardian/           ├─ Backboard.io                 │
│  │   ├─ handoff.yaml          │   ├─ Personal thread          │
│  │   └─ learnings.json        │   └─ Team thread              │
│  └─ ~/.flow-guardian/         └─ Cerebras (TLDR generation)   │
│                                                                │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────────┐
│                      INJECTION                                 │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  SessionStart Hook                                             │
│  ├─ Detect project folder                                     │
│  ├─ Load handoff.yaml                                         │
│  ├─ Query Backboard semantically                              │
│  ├─ Cerebras TLDR (if needed)                                 │
│  └─ Output → Claude context                                   │
│                                                                │
│  PreCompact Hook                                               │
│  ├─ Save current state to handoff.yaml                        │
│  └─ Store summary to Backboard                                │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `handoff.py` | Handoff YAML management |
| `tldr.py` | Token-efficient summarization |
| `inject.py` | Context injection orchestrator |
| `flow_cli.py` | Add inject, setup commands |
| `daemon.py` | Update to write handoff.yaml |

---

## Implementation Priority

1. **P0**: Handoff system (`handoff.py`)
2. **P0**: TLDR system (`tldr.py`)
3. **P0**: Inject command (`inject.py` + `flow inject`)
4. **P1**: Hooks integration (SessionStart, PreCompact)
5. **P1**: Setup command (`flow setup`)
6. **P2**: Polish and testing

---

## Verification

1. `flow save` creates valid `handoff.yaml`
2. Large context → compact summary via TLDR
3. `flow inject` outputs formatted context
4. New Claude session auto-receives context
5. Full cycle: save → close → reopen → context restored
