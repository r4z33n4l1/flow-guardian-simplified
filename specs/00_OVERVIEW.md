# Flow Guardian — Product Overview

## Vision

**"Claude forgets. Flow Guardian remembers."**

Flow Guardian provides persistent memory for AI coding sessions. It solves the fundamental problem that AI assistants (Claude, GPT, etc.) lose context when sessions end or context windows fill up.

## The Problem

1. **Session Amnesia**: AI coding sessions end → all context lost
2. **Context Compaction**: Long conversations get compressed → nuance and decisions lost
3. **Repeated Explanations**: Users explain the same codebase patterns, decisions, and context repeatedly
4. **Lost Learnings**: Insights discovered during debugging/development don't persist

## The Solution

A CLI tool that:
1. **Saves** session context, learnings, and decisions to persistent memory
2. **Restores** context in new sessions so the AI "remembers"
3. **Learns** from explicit user insights
4. **Recalls** relevant past knowledge via semantic search
5. **Shares** team learnings across developers

## Core Commands

| Command | Description |
|---------|-------------|
| `flow save` | Checkpoint current session (context, learnings, state) |
| `flow resume` | Start new session with restored context |
| `flow learn "..."` | Store an explicit learning/insight |
| `flow recall "..."` | Semantic search across all stored knowledge |
| `flow team "..."` | Search team's shared learnings |
| `flow status` | Show current memory state |
| `flow history` | Show past sessions/checkpoints |

## Tech Stack

- **Python 3.11+** — Core language
- **Cerebras Cloud SDK** — Fast LLM inference for context analysis
- **Backboard.io** — Persistent memory with semantic recall
- **Rich** — Beautiful CLI output
- **Click or Argparse** — CLI framework

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FLOW GUARDIAN                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLI Layer (flow.py)                                            │
│  ├── save, resume, learn, recall, team, status, history        │
│                                                                  │
│  Core Logic                                                      │
│  ├── capture.py    — Extract context from current state         │
│  ├── restore.py    — Generate restoration prompts               │
│  ├── memory.py     — Local storage + indexing                   │
│                                                                  │
│  External Services                                               │
│  ├── cerebras_client.py   — Fast inference                      │
│  ├── backboard_client.py  — Persistent memory + semantic search │
│                                                                  │
│  Storage                                                         │
│  ├── Local: ~/.flow-guardian/ (fallback)                        │
│  └── Cloud: Backboard.io assistants/threads                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Hackathon Scope (MVP)

**Must Have (Demo-ready):**
1. `flow save` — Save current context
2. `flow resume` — Restore context with "welcome back" message
3. `flow learn` — Store learnings
4. `flow recall` — Search learnings

**Should Have:**
5. `flow team` — Team memory
6. `flow history` — Past sessions

**Nice to Have:**
7. Automatic context capture
8. Git integration for change detection
9. IDE integration
