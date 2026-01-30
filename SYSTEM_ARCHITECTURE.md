# Flow Guardian System Architecture

> Local-first AI memory system with semantic search

## Overview

Flow Guardian provides persistent memory for AI coding assistants. The recent `razeen_sqlite` branch replaces the cloud-based Backboard.io dependency with a self-hosted solution using **Gemini embeddings** and **SQLite + sqlite-vec** for vector storage.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLOW GUARDIAN v2                                   │
│                    (Local Memory + Vector Search)                            │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   Claude Code   │
                              │   (MCP Client)  │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
             ┌──────────┐      ┌──────────┐      ┌──────────────┐
             │ /capture │      │ /recall  │      │ /learn       │
             └────┬─────┘      └────┬─────┘      └──────┬───────┘
                  │                 │                   │
                  └─────────────────┼───────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FlowService (flow_service.py)                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Priority Order:                                                     │    │
│  │  1. LocalMemoryService (vector search)                              │    │
│  │  2. Backboard.io (cloud) ← DEPRECATED/FALLBACK                      │    │
│  │  3. Local JSON search ← LAST RESORT                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│   EMBEDDINGS    │    │   VECTOR STORAGE    │    │   INFERENCE     │
│  (embeddings.py)│    │ (vector_storage.py) │    │(cerebras_client)│
├─────────────────┤    ├─────────────────────┤    ├─────────────────┤
│                 │    │                     │    │                 │
│ ┌─────────────┐ │    │  ┌───────────────┐  │    │ ┌─────────────┐ │
│ │ Gemini API  │ │───▶│  │ SQLite DB     │  │───▶│ │Cerebras API │ │
│ │ (Primary)   │ │    │  │ + sqlite-vec  │  │    │ │Llama 3.3 70B│ │
│ └─────────────┘ │    │  │               │  │    │ └─────────────┘ │
│        │        │    │  │ ~/.flow-      │  │    │                 │
│        ▼        │    │  │ guardian/     │  │    │ Used for:       │
│ ┌─────────────┐ │    │  │ vectors.db    │  │    │ • Synthesis     │
│ │ Local Model │ │    │  └───────────────┘  │    │ • Analysis      │
│ │ (Fallback)  │ │    │                     │    │ • Chat          │
│ │sentence-trf │ │    │  Vector dims: 768   │    │                 │
│ └─────────────┘ │    │  (Gemini output)    │    │                 │
└─────────────────┘    └─────────────────────┘    └─────────────────┘
```

---

## API Keys & Their Purpose

| Key | Provider | Purpose |
|-----|----------|---------|
| `GEMINI_API_KEY` | Google AI | Generates embeddings (text → 768-dim vectors) |
| `CEREBRAS_API_KEY` | Cerebras | LLM inference for synthesis, analysis, chat |
| `BACKBOARD_API_KEY` | Backboard.io | (Optional) Legacy cloud memory fallback |

### Key Insight

**Cerebras is NOT used for embeddings** — it's used for **response synthesis** after vector search retrieves relevant context:

- **Fast search**: Gemini embeddings + sqlite-vec (no LLM call needed)
- **Smart responses**: Cerebras synthesizes final answer from search results

---

## Data Flow

### Store Operation (capture/learn)

```
┌──────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Content  │────▶│ embeddings.py   │────▶│ vector_storage  │
│ (text)   │     │ get_embedding() │     │ SQLite + vec    │
└──────────┘     └─────────────────┘     └─────────────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Gemini API  │
                 │ 768-dim vec │
                 └─────────────┘
```

### Recall Operation (search)

```
┌───────┐     ┌─────────────┐     ┌────────────────┐     ┌─────────────┐
│ Query │────▶│ Gemini      │────▶│ sqlite-vec     │────▶│ Top-K       │
│       │     │ Embedding   │     │ Similarity     │     │ Results     │
└───────┘     └─────────────┘     └────────────────┘     └──────┬──────┘
                                                                │
                                         ┌──────────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │  synthesize=True?   │
                              └──────────┬──────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │ YES                           │ NO
                         ▼                               ▼
              ┌─────────────────────┐         ┌─────────────────┐
              │ Cerebras            │         │ Return raw      │
              │ quick_answer()      │         │ results         │
              │ (Llama 3.3 70B)     │         │                 │
              └──────────┬──────────┘         └─────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Synthesized         │
              │ Response            │
              └─────────────────────┘
```

---

## Core Components

### 1. Embeddings Layer (`embeddings.py`)

Multi-provider embedding system with automatic fallback:

```python
EMBEDDING_PROVIDER=auto  # Options: auto, gemini, local

# Provider selection:
# 1. "gemini" - Uses Gemini API (requires GEMINI_API_KEY)
# 2. "local"  - Uses sentence-transformers (requires torch)
# 3. "auto"   - Gemini if API key set, else local
```

| Provider | Model | Dimensions | Speed |
|----------|-------|------------|-------|
| Gemini | `text-embedding-004` | 768 | Fast (API) |
| Local | `all-MiniLM-L6-v2` | 384 | Slower (CPU) |

### 2. Vector Storage (`vector_storage.py`)

SQLite-based vector store using `sqlite-vec` extension:

```
~/.flow-guardian/vectors.db
├── memories (content, embedding, namespace, content_type, metadata)
└── sqlite-vec index (cosine similarity search)
```

Features:
- Semantic similarity search via `sqlite-vec`
- Keyword search fallback
- Namespace isolation (personal/team)
- Content type filtering

### 3. Local Memory Service (`local_memory.py`)

High-level service replacing Backboard.io:

| Method | Description |
|--------|-------------|
| `store_message()` | Store content with embedding |
| `recall()` | Semantic search + optional Cerebras synthesis |
| `search_raw()` | Raw vector search (no LLM) |
| `store_learning()` | Store insight with tags |
| `store_session()` | Store session context |

### 4. Inference Layer (`cerebras_client.py`)

Cerebras API for LLM inference:

| Function | Use Case |
|----------|----------|
| `quick_answer()` | Synthesize search results |
| `analyze_session_context()` | Extract structured context |
| `generate_restoration_message()` | Welcome-back messages |

---

## Service Priority (FlowService)

The `FlowService` uses a waterfall pattern for recalls:

```python
async def recall_context(self, request):
    # Priority 1: Local vector memory (new system)
    local_mem = _get_local_memory()
    if local_mem:
        results = await local_mem.search_raw(query, namespace="personal")
        if results:
            return results  # source: "vector"

    # Priority 2: Backboard.io (legacy cloud)
    if self.config.personal_thread_id:
        response = await backboard_client.recall(thread_id, query)
        if response:
            return response  # source: "backboard"

    # Priority 3: Local JSON keyword search
    return memory.search_learnings(query)  # source: "local"
```

---

## Session Injection (`inject.py`)

At session startup, context is injected using `search_raw()` (no Cerebras call):

```python
async def _recall_for_injection(handoff, limit=10):
    service = LocalMemoryService()

    # Vector search only - no LLM synthesis at startup
    results = await service.search_raw(
        query=query,
        namespace="personal",
        limit=limit,
    )
    return results
```

This ensures fast startup without waiting for LLM inference.

---

## Environment Configuration

```bash
# Required
CEREBRAS_API_KEY=csk-...          # LLM inference
GEMINI_API_KEY=AIza...            # Embeddings

# Local Memory (enabled by default)
USE_LOCAL_MEMORY=true
EMBEDDING_PROVIDER=auto           # auto, gemini, or local

# Optional (legacy)
BACKBOARD_API_KEY=espr_...        # Only if USE_LOCAL_MEMORY=false
BACKBOARD_PERSONAL_THREAD_ID=...
```

---

## File Structure

```
flow-guardian/
├── embeddings.py         # Multi-provider embedding (Gemini/local)
├── vector_storage.py     # SQLite + sqlite-vec storage
├── local_memory.py       # LocalMemoryService (replaces Backboard)
├── cerebras_client.py    # Cerebras LLM client
├── inject.py             # Session startup injection
├── server.py             # Unified backend (API + MCP + daemon)
├── memory.py             # Legacy JSON storage
└── services/
    ├── flow_service.py   # Core business logic
    ├── config.py         # Configuration
    └── models.py         # Pydantic models
```

---

## Migration from Backboard

The system supports gradual migration:

1. Set `USE_LOCAL_MEMORY=true` in `.env`
2. Run `python migrate_to_vectors.py` to import existing data
3. Backboard remains as fallback if local search returns no results
4. Remove Backboard config once migration is verified

---

## Performance Characteristics

| Operation | Latency | API Calls |
|-----------|---------|-----------|
| Store (embed + write) | ~200ms | 1 Gemini |
| Search (raw) | ~50ms | 1 Gemini |
| Search (synthesized) | ~2-3s | 1 Gemini + 1 Cerebras |
| Session injection | ~100ms | 1 Gemini (no Cerebras) |

---

## Claude Session Data Flow

**Yes, Claude session data IS stored in SQLite.** Here's how:

### Data Sources

```
~/.claude/projects/<hash>/sessions/<session_id>.jsonl
    │
    │ Daemon watches for new messages
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    DaemonMode.watch_loop()                   │
│                        (server.py)                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. session_parser.py reads JSONL                    │    │
│  │ 2. Cerebras extracts insights from conversation     │    │
│  │ 3. service.store_learning() saves each insight      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┴──────────────────┐
           ▼                                      ▼
┌─────────────────────────┐          ┌──────────────────────────┐
│  memory.py (JSON)       │          │  local_memory.py (SQLite)│
│  ~/.flow-guardian/      │          │  ~/.flow-guardian/       │
│  └── learnings.json     │          │  └── vectors.db          │
│  └── sessions/          │          │      └── memories table  │
└─────────────────────────┘          └──────────────────────────┘
```

### What Gets Stored

| Content Type | Source | Storage |
|--------------|--------|---------|
| **Sessions** | `flow_capture()` | JSON + SQLite |
| **Learnings** | `flow_learn()` or auto-extracted | JSON + SQLite |
| **Documents** | File upload | JSON + SQLite |
| **Team insights** | `share_with_team=true` | JSON + SQLite (team namespace) |

### Dual-Write System

Every piece of data is written to **both** storage backends:

```python
# In memory.py - save_learning()
_atomic_write(LEARNINGS_FILE, learnings)  # JSON

if _is_vector_write_enabled():
    _store_to_vector(content, "learning", ...)  # SQLite + embedding
```

### SQLite Database Contents

```
~/.flow-guardian/vectors.db (3.2 MB)
├── memories table
│   ├── id (UUID)
│   ├── content (text)
│   ├── embedding (768-dim vector blob)
│   ├── namespace (personal/team)
│   ├── content_type (session/learning/document)
│   ├── metadata (JSON)
│   └── created_at
└── sqlite-vec index (for similarity search)
```

### Automatic Session Extraction (Daemon)

The daemon continuously watches Claude sessions and extracts insights:

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code Session                                         │
│  ~/.claude/projects/<hash>/sessions/<id>.jsonl              │
└─────────────────────────────────────────────────────────────┘
                              │
                    Daemon watches (every 5 min)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  DaemonMode.process_session()                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Read new messages from JSONL                     │    │
│  │ 2. Build conversation text                          │    │
│  │ 3. extract_insights() → Cerebras API                │    │
│  │    "What are the key decisions/blockers/learnings?" │    │
│  │ 4. For each insight:                                │    │
│  │    → store_learning() → JSON + SQLite               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits for Claude Code Context

### Why This Architecture Matters for AI Assistants

The local-first design directly addresses Claude Code's context limitations:

#### 1. Persistent Memory Across Sessions
```
Session 1: "We decided to use JWT for auth"
    ↓ flow_learn()
Session 2: "What auth approach did we choose?"
    ↓ flow_recall() → "JWT for stateless auth"
```

Claude Code has no memory between sessions. Flow Guardian provides:
- **Decisions persistence**: Architecture choices survive session restarts
- **Context continuity**: Pick up exactly where you left off
- **Learning accumulation**: Insights compound over time

#### 2. Semantic Search vs Keyword Matching
```
Query: "how do we handle user login?"
    ↓
Vector Search finds:
- "Using JWT for stateless authentication"
- "Auth middleware validates tokens"
- "Session captured: implementing login flow"
```

Traditional search would miss these without exact keyword matches. Semantic search understands **intent**.

#### 3. Fast Session Startup
```
┌─────────────────────────────────────────────────────────┐
│ Claude Code Session Start                               │
├─────────────────────────────────────────────────────────┤
│ 1. inject.py queries LocalMemoryService.search_raw()   │
│ 2. Vector search returns relevant context (~50ms)       │
│ 3. No LLM call needed for retrieval                    │
│ 4. Context injected into system prompt                 │
└─────────────────────────────────────────────────────────┘
```

Using `search_raw()` (no Cerebras synthesis) keeps startup fast.

#### 4. Context Window Optimization
```
Before: Dump entire conversation history (wastes tokens)
After:  Retrieve only semantically relevant context

┌──────────────────────────────────────────┐
│ 200K context window                      │
│ ┌──────────────────────────────────────┐ │
│ │ Relevant learnings (vector search)   │ │  ← Targeted
│ │ Recent session context               │ │
│ │ Current git state                    │ │
│ └──────────────────────────────────────┘ │
│ [ Available for actual work ]            │  ← Preserved
└──────────────────────────────────────────┘
```

#### 5. Team Knowledge Sharing
```
Developer A: flow_learn("PyMuPDF requires pip install pymupdf", share_with_team=True)
    ↓
Developer B: flow_team("pdf library") → Gets the insight
```

Team namespace enables shared learnings without duplicating context.

#### 6. Local-First Privacy
```
┌─────────────────────────────────────────┐
│ All data stays on your machine:        │
│ ~/.flow-guardian/vectors.db            │
│                                         │
│ No cloud dependency for core features  │
│ Backboard.io is optional fallback only │
└─────────────────────────────────────────┘
```

Sensitive code context never leaves your machine.

#### 7. Cost Efficiency
| Operation | API Cost |
|-----------|----------|
| Embed (Gemini) | Free tier available |
| Search (sqlite-vec) | $0 (local) |
| Synthesis (Cerebras) | Only when needed |

Synthesis is optional — raw search results often suffice.

---

## Future Improvements

- [ ] Batch embedding for bulk imports
- [ ] Hybrid search (vector + keyword fusion)
- [ ] Embedding cache for repeated queries
- [ ] Team namespace with shared vectors
- [ ] Incremental sync with cloud backup

---

## Verification Testing (2026-01-30)

### Test Results

| Test | Status | Evidence |
|------|--------|----------|
| SQLite vector store | ✅ | `~/.flow-guardian/vectors.db` (3.2 MB) |
| Gemini embeddings | ✅ | Query embedded and matched semantically |
| Cerebras synthesis | ✅ | Response synthesized from search results |
| Claude session capture | ✅ | 1,828 learnings auto-extracted from sessions |
| Dual-write (JSON + SQLite) | ✅ | Both `learnings.json` and `vectors.db` populated |
| Web UI | ✅ | Chat, Dashboard, Knowledge Graph all functional |

### Web UI Screenshots

**Chat Interface**: Semantic search returned relevant learning about Gemini embeddings
```
Q: "What embedding provider does Flow Guardian use for semantic search?"
A: "Flow Guardian uses Gemini embeddings with sqlite-vec for local semantic search,
    replacing the previous dependency on Backboard.io."
   Source: learning, 2026-01-30T00:27:58.962392
```

**Dashboard Stats**:
- Sessions: 15
- Learnings: 1,828
- Team Insights: 3
- Active Tags: 10

**Knowledge Graph**: Interactive visualization of sessions → learnings → tags relationships
