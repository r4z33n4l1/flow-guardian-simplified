# Flow Guardian - Hackathon Plan

**Hackathon:** 8090 x Highline Beta: Build for Builders
**Date:** January 16-17, 2026
**Team:** [Your names here]

---

## TL;DR

We're building **Flow Guardian** — a CLI tool that captures developer context before interruptions and restores it instantly when they return. Solves the "23 minutes to regain focus" problem using Cerebras fast inference + Backboard.io for team memory.

---

## 1. The Problem

### By the Numbers
- **23 minutes** — time to regain focus after an interruption (UC Irvine research)
- **69%** of developers lose 8+ hours/week to inefficiencies (Stack Overflow 2024)
- **62%** cite context switching as their #1 frustration
- **$6.9M/year** — cost for a 500-developer company

### The Pain
Every developer knows this feeling:
1. You're deep in debugging, holding 5 things in your head
2. Slack ping / meeting / someone taps your shoulder
3. You come back 30 mins later
4. "Wait, what was I doing? What file was I in? What was my hypothesis?"
5. Spend 20+ minutes rebuilding mental context

**No tool solves this today.**

---

## 2. The Solution

### Flow Guardian
A lightweight CLI that:
1. **Captures** your coding context (files, git state, what you're working on)
2. **Analyzes** it with Cerebras fast inference (<1 sec)
3. **Stores** it in Backboard.io (personal + team memory with semantic recall)
4. **Restores** it instantly when you return, including "what changed while you were away"

### Commands
```bash
flow capture              # Save current context (before meeting)
flow resume               # Restore context (after meeting)
flow status               # See current state
flow learn "insight"      # Store a learning (personal)
flow learn "insight" -t   # Store a learning (team-shared)
flow recall "query"       # Search your learnings
flow team "query"         # Search team's shared learnings
```

---

## 3. Why This Wins

### Sponsor Alignment

| Sponsor | How We Use Them | Why They'll Love It |
|---------|-----------------|---------------------|
| **Cerebras** | Fast inference for instant context analysis | Speed IS the feature. Shows why fast inference matters. |
| **Backboard.io** | Stateful memory layer with semantic recall | Uses their core differentiator: persistent memory across sessions + auto RAG |
| **8090** | Aligns with AI-native SDLC vision | Context preservation is missing piece in agentic workflows |

### Differentiation
- **Novel:** No existing tool does proactive context capture + smart restoration
- **Universal:** Every developer has this problem, regardless of stack
- **Demo-able:** Before/after is visceral and easy to understand
- **Buildable:** MVP achievable in 12 hours

---

## 4. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLOW GUARDIAN                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐      ┌─────────────┐      ┌───────────────────┐   │
│  │   CAPTURE   │      │   ANALYZE   │      │   BACKBOARD.IO    │   │
│  │             │      │             │      │                   │   │
│  │ • Git state │─────▶│  Cerebras   │─────▶│ Personal Assistant│   │
│  │ • Open files│      │  Llama 3.3  │      │ (your snapshots)  │   │
│  │ • Cursor pos│      │  (<1 sec)   │      │                   │   │
│  └─────────────┘      └─────────────┘      │ Team Assistant    │   │
│                                             │ (shared learnings)│   │
│                                             └─────────┬─────────┘   │
│                                                       │             │
│                                            memory="auto"            │
│                                            (semantic recall)        │
│                                                       │             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────▼─────────┐   │
│  │   OUTPUT    │◀─────│  GENERATE   │◀─────│   RECALL +        │   │
│  │             │      │             │      │   DIFF DETECTION  │   │
│  │ Rich CLI    │      │  Cerebras   │      │                   │   │
│  │ Panel       │      │  Restore    │      │ What changed      │   │
│  └─────────────┘      └─────────────┘      │ while away        │   │
│                                             └───────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Language:** Python 3.11+
- **LLM:** Cerebras Cloud SDK (Llama 3.3 70B) — fast inference
- **Memory:** Backboard.io API — stateful memory with semantic recall
- **CLI Framework:** Rich (for beautiful terminal output)
- **HTTP Client:** httpx (async support)

### File Structure
```
flow-guardian/
├── flow.py              # CLI entry point
├── capture.py           # Context capture + Cerebras analysis
├── restore.py           # Context restoration + diff detection
├── backboard_client.py  # Backboard.io API wrapper
├── requirements.txt
└── README.md
```

---

## 5. Backboard.io Integration (Key Section)

### What Backboard.io Actually Is
Backboard is **"the memory layer for AI"** — a unified API that:
- Routes to 2,200+ LLMs through one endpoint
- Provides **persistent memory across sessions, models, and apps**
- Auto-handles RAG (indexing, chunking, vectorization)
- Achieved **90.1% accuracy** on LoCoMo memory benchmark (best in class)

### Core Concepts

| Concept | Purpose | Our Usage |
|---------|---------|-----------|
| **Assistant** | Isolated memory container | One per user (personal) + one shared (team) |
| **Thread** | Conversation session | One thread per day or project |
| **Message** | Content with metadata | Context snapshots, learnings |
| **memory="auto"** | Semantic recall | Auto-retrieves relevant past context |

### API Structure

```python
# Environment
BACKBOARD_API_KEY=your_key
BACKBOARD_BASE_URL=https://app.backboard.io/api
```

### backboard_client.py (Full Implementation)

```python
"""Backboard.io client for Flow Guardian."""
import os
import httpx
from datetime import datetime
from typing import Optional

BASE_URL = os.environ.get("BACKBOARD_BASE_URL", "https://app.backboard.io/api")
API_KEY = os.environ.get("BACKBOARD_API_KEY")

def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

# ============ SETUP ============

async def create_assistant(name: str) -> str:
    """Create a Backboard assistant (memory container)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants",
            headers=_headers(),
            json={
                "name": name,
                "llm_provider": "cerebras",  # Use Cerebras through Backboard!
                "llm_model_name": "llama-3.3-70b",
                "tools": []
            }
        )
        resp.raise_for_status()
        return resp.json()["id"]

async def create_thread(assistant_id: str) -> str:
    """Create a conversation thread within an assistant."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/assistants/{assistant_id}/threads",
            headers=_headers()
        )
        resp.raise_for_status()
        return resp.json()["id"]

# ============ STORE (No LLM call) ============

async def store_context_snapshot(thread_id: str, context: dict):
    """
    Store a context snapshot WITHOUT calling the LLM.
    Uses send_to_llm=False to just save to memory.
    """
    content = f"""## Context Snapshot
**Working on:** {context.get('summary', 'unknown')}
**Hypothesis:** {context.get('hypothesis', 'none')}
**Files:** {', '.join(context.get('files', []))}
**Branch:** {context.get('branch', 'unknown')}
**Next steps:** {', '.join(context.get('next_steps', []))}
**Trigger:** {context.get('trigger', 'manual')}"""

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": content,
                "metadata": {
                    "type": "context_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    "trigger": context.get("trigger", "manual"),
                    "branch": context.get("branch"),
                    "files": context.get("files", [])
                },
                "send_to_llm": False  # Just store, don't generate response
            }
        )
        resp.raise_for_status()
        return resp.json()

async def store_learning(thread_id: str, learning: str, tags: list = None):
    """Store a learning/insight for future recall."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Learning:** {learning}",
                "metadata": {
                    "type": "learning",
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()

# ============ RECALL (With LLM + Memory) ============

async def recall_context(thread_id: str, query: str) -> str:
    """
    Query memory with semantic recall.
    Uses memory="auto" to automatically retrieve relevant past context.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=_headers(),
            json={
                "content": query,
                "memory": "auto",  # Key feature: auto-retrieves relevant context
                "send_to_llm": True
            },
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json().get("content", "")

async def get_restoration_prompt(thread_id: str, changes_summary: str) -> str:
    """Generate a welcome-back message using stored context + what changed."""
    query = f"""Based on my most recent context snapshot, generate a concise "welcome back" summary.

Also consider these changes that happened while I was away:
{changes_summary}

Format:
1. What I was working on (1 sentence)
2. My hypothesis (if any)
3. What changed while away (highlight if it affects my work!)
4. Suggested next action

Keep it under 10 lines. Be direct."""

    return await recall_context(thread_id, query)

# ============ TEAM MEMORY ============

async def store_team_learning(team_thread_id: str, learning: str, author: str, tags: list = None):
    """Store a learning to the team's shared memory."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/threads/{team_thread_id}/messages",
            headers=_headers(),
            json={
                "content": f"**Team Learning** (from {author}): {learning}",
                "metadata": {
                    "type": "team_learning",
                    "author": author,
                    "timestamp": datetime.now().isoformat(),
                    "tags": tags or []
                },
                "send_to_llm": False
            }
        )
        resp.raise_for_status()
        return resp.json()

async def query_team_memory(team_thread_id: str, query: str) -> str:
    """Search the team's shared learnings."""
    full_query = f"""Search team learnings for: {query}

Summarize relevant learnings from the team. Include who shared each insight."""

    return await recall_context(team_thread_id, full_query)
```

### Usage Flow

```python
# SETUP (once per user)
personal_assistant_id = await create_assistant(f"flow-guardian-{username}")
personal_thread_id = await create_thread(personal_assistant_id)

# CAPTURE (before interruption)
await store_context_snapshot(personal_thread_id, {
    "summary": "Debugging JWT token expiry in auth.py",
    "hypothesis": "Off-by-one error in expiry check",
    "files": ["src/auth.py", "tests/test_auth.py"],
    "branch": "fix/jwt-expiry",
    "next_steps": ["Add logging to verify expiry timestamp"],
    "trigger": "meeting"
})

# RESUME (after returning)
changes = "Sarah merged PR #47 affecting user.py (imports auth.py)"
welcome_back = await get_restoration_prompt(personal_thread_id, changes)
print(welcome_back)

# TEAM LEARNING
await store_team_learning(team_thread_id,
    "JWT tokens use UTC timestamps, not local time",
    author="mike",
    tags=["auth", "jwt", "timezone"]
)

# TEAM QUERY
insights = await query_team_memory(team_thread_id, "authentication issues")
```

---

## 6. Implementation Plan

### Phase 1: Core Foundation (1.5 hours)
- [ ] Project setup (venv, requirements, structure)
- [ ] Backboard.io client (`backboard_client.py`)
- [ ] Basic CLI skeleton with Rich
- [ ] Environment setup script

### Phase 2: Context Capture (2.5 hours)
- [ ] Git state extraction (branch, uncommitted files, diff)
- [ ] Cerebras integration for context analysis
- [ ] Store to Backboard.io personal assistant
- [ ] `flow capture` command working end-to-end

### Phase 3: Context Restoration (2.5 hours)
- [ ] Diff detection (what changed since snapshot)
- [ ] Backboard.io recall with `memory="auto"`
- [ ] Cerebras-powered restoration message
- [ ] `flow resume` command working end-to-end

### Phase 4: Learning System (2 hours)
- [ ] `flow learn` — store personal learnings
- [ ] `flow learn --team` — store to team memory
- [ ] `flow recall` — search personal learnings
- [ ] `flow team` — search team learnings
- [ ] `flow status` — show current state

### Phase 5: Polish & Demo (2.5 hours)
- [ ] Error handling & edge cases
- [ ] Beautiful Rich output panels
- [ ] Demo script rehearsal
- [ ] README & presentation prep

---

## 7. Team Roles

| Role | Responsibilities | Suggested Assignment |
|------|------------------|---------------------|
| **Backboard Lead** | backboard_client.py, API integration, memory architecture | |
| **Capture Lead** | Git integration, Cerebras capture prompt, `flow capture` | |
| **Restore Lead** | Diff detection, restoration prompt, `flow resume` | |
| **CLI/Demo Lead** | Rich UI, all commands, error handling, demo prep | |

*For 2-person team: One does Backboard+Capture, one does Restore+CLI*
*For 3-person team: Backboard, Capture+Restore, CLI+Demo*

---

## 8. Timeline

### Friday Night (Kickoff - Jan 16, 5-7 PM)
- Finalize team & roles
- Set up dev environment
- Get Cerebras + Backboard.io API keys working
- Create personal + team assistants in Backboard.io
- Start Phase 1

### Friday Night (Optional - 7 PM onwards)
- Complete Phase 1
- Start Phase 2

### Saturday Morning (Jan 17, 8 AM - 12 PM)
- Complete Phase 2 (Capture)
- Complete Phase 3 (Restore)
- **Checkpoint:** Core flow working end-to-end

### Saturday Afternoon (12 PM - 5 PM)
- Phase 4 (Learning + Team features)
- Bug fixes & edge cases
- Start polish

### Saturday Evening (5 PM - 7 PM)
- Phase 5 (Polish)
- Demo rehearsal (multiple run-throughs!)
- Prepare presentation

### Presentations (7 PM - 8 PM)
- Demo time!

---

## 9. Demo Script (3 minutes)

### Setup
- Split screen: VS Code on left, terminal on right
- Have a real bug to "debug" (auth.py JWT issue)

### Script

**[0:00 - 0:30] The Problem**
> "Every developer knows this: you're deep in flow, holding 5 things in your head, and then—Slack ping. Meeting time. When you come back, you spend 20 minutes just remembering what you were doing. Research shows this costs 23 minutes per interruption."

**[0:30 - 1:00] Show the Pain**
- *Show yourself coding, multiple files open*
> "I'm debugging a JWT token issue. I think the expiry check is off by one. I was about to add logging to verify..."

- *Calendar notification pops up*
> "But standup is in 5 minutes."

**[1:00 - 1:30] The Capture**
```bash
$ flow capture --trigger meeting
```
- *Show the beautiful Rich output*
> "Flow Guardian captures my context in under a second using Cerebras, and stores it in Backboard.io's memory layer. It knows what I'm working on, my hypothesis, my next step."

**[1:30 - 2:00] The Return**
> "I come back from my meeting. Normally I'd spend 20 minutes going 'wait, what was I doing?' But instead..."

```bash
$ flow resume
```
- *Show the restoration panel with semantic recall*
> "Backboard.io's semantic memory instantly recalls my context. And look—it tells me Sarah merged a PR that affects auth.py while I was gone. That's critical context I would have missed."

**[2:00 - 2:30] Team Memory (The Wow Moment)**
> "But here's where it gets really powerful. I store a learning..."

```bash
$ flow learn "JWT tokens use UTC, not local time" --team --tags auth jwt
```

> "Now my teammate can find this later..."

```bash
$ flow team "timezone issues in auth"
```
- *Show team memory result*
> "Sarah discovers my insight without having to ask me. The team's knowledge compounds."

**[2:30 - 3:00] The Impact**
> "We're saving developers 23 minutes per interruption. With 3-4 interruptions per day, that's over an hour recovered. And with team memory, we stop re-discovering the same solutions."

> "Built with Cerebras for instant inference, Backboard.io for persistent memory with semantic recall. Flow Guardian. Return to flow state in 30 seconds, not 23 minutes."

---

## 10. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Cerebras rate limits | We got rate limit increase via form. Test early. |
| Backboard.io API issues | They're a sponsor—reach out on Discord if stuck. Have local JSON fallback. |
| Git edge cases | Focus on happy path for demo. Handle errors gracefully. |
| Demo fails live | Have backup recording. Test on demo machine beforehand. |
| Scope creep | Core flow first (capture/resume). Team features are the wow factor. |
| Team coordination | Clear role ownership. Sync every 2 hours. |

---

## 11. API Keys & Setup

### Cerebras (Required)
1. Sign up: https://cloud.cerebras.ai
2. Fill rate limit increase form: https://form.typeform.com/to/IpWtfYd1
3. Get API key from dashboard
4. `export CEREBRAS_API_KEY="your-key"`

### Backboard.io (Required)
1. Portal: https://backboard.io/hackathons/
2. Promo code: `8090JAN`
3. Get API key from dashboard
4. Set environment variables:
```bash
export BACKBOARD_API_KEY="your-key"
export BACKBOARD_BASE_URL="https://app.backboard.io/api"
```

### First-Time Setup Script
```python
# setup_assistants.py - Run once to create assistants
import asyncio
from backboard_client import create_assistant, create_thread

async def setup():
    # Personal assistant
    personal_id = await create_assistant("flow-guardian-personal")
    personal_thread = await create_thread(personal_id)
    print(f"BACKBOARD_PERSONAL_ASSISTANT_ID={personal_id}")
    print(f"BACKBOARD_PERSONAL_THREAD_ID={personal_thread}")

    # Team assistant
    team_id = await create_assistant("flow-guardian-team")
    team_thread = await create_thread(team_id)
    print(f"BACKBOARD_TEAM_ASSISTANT_ID={team_id}")
    print(f"BACKBOARD_TEAM_THREAD_ID={team_thread}")

asyncio.run(setup())
```

---

## 12. Judging Criteria Alignment

| Criteria | How We Score |
|----------|--------------|
| **Developer Productivity** | Direct impact on the #1 time waster (context switching) |
| **Code Quality** | Preserved context = fewer bugs from context loss |
| **Collaboration** | Team memory via Backboard.io — learnings compound |
| **Innovation** | Novel approach to unsolved problem |
| **Technical Execution** | Clean code, working demo, smooth UX |
| **Sponsor Tech Usage** | Cerebras (speed), Backboard.io (core memory layer, not checkbox) |

---

## 13. Quick Reference

### Install
```bash
pip install cerebras-cloud-sdk httpx rich
export CEREBRAS_API_KEY="your-key"
export BACKBOARD_API_KEY="your-key"
export BACKBOARD_BASE_URL="https://app.backboard.io/api"
```

### requirements.txt
```
cerebras-cloud-sdk>=1.0.0
httpx>=0.25.0
rich>=13.0.0
```

### Test Commands
```bash
python flow.py capture --trigger meeting
python flow.py status
python flow.py resume
python flow.py learn "JWT tokens use UTC, not local time" --tags auth jwt
python flow.py learn "Redis cache TTL should match JWT expiry" --team --tags auth cache
python flow.py recall jwt
python flow.py team "authentication"
```

### Key Files to Build (in order)
1. `backboard_client.py` — API wrapper (copy from Section 5)
2. `capture.py` — git state + Cerebras analysis
3. `restore.py` — diff detection + restoration prompt
4. `flow.py` — CLI with all commands

---

## 14. Backboard.io Quick API Reference

| Operation | Endpoint | Key Params |
|-----------|----------|------------|
| Create Assistant | `POST /assistants` | `name`, `llm_provider`, `llm_model_name` |
| Create Thread | `POST /assistants/{id}/threads` | — |
| Store (no LLM) | `POST /threads/{id}/messages` | `content`, `metadata`, `send_to_llm=False` |
| Recall (with LLM) | `POST /threads/{id}/messages` | `content`, `memory="auto"`, `send_to_llm=True` |

**Key insight:** `send_to_llm=False` stores without generating. `memory="auto"` enables semantic recall.

---

## Let's Build This!

Questions? Concerns? Ideas? Discuss now before we start coding.

**Remember:** Working demo > perfect code. Ship it.

**Priority order:**
1. `flow capture` + `flow resume` (core value)
2. `flow team` (wow factor for judges)
3. Everything else (nice to have)
