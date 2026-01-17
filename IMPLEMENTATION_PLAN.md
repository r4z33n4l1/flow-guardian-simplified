# Implementation Plan

> Flow Guardian — "Claude forgets. Flow Guardian remembers."

**Last Updated:** 2026-01-17
**Status:** ✅ **Phase 2: Complete (339 tests passing)**

---

## Current State Summary

| File | Status | Lines of Code |
|------|--------|---------------|
| `flow_cli.py` | ✅ **Fully Implemented** | 817 |
| `capture.py` | ✅ **Fully Implemented** | 238 |
| `restore.py` | ✅ **Fully Implemented** | 378 |
| `backboard_client.py` | ✅ **Fully Implemented** | 404 |
| `setup_assistants.py` | ✅ **Fully Implemented** | 153 |
| `memory.py` | ✅ **Fully Implemented** | 388 |
| `cerebras_client.py` | ✅ **Fully Implemented** | 213 |
| `git_utils.py` | ✅ **Fully Implemented** | 55 |
| `daemon.py` | ✅ **Fully Implemented** | 506 |
| `session_parser.py` | ✅ **Fully Implemented** | 178 |
| `handoff.py` | ✅ **Fully Implemented** | 306 |
| `tldr.py` | ✅ **Fully Implemented** | 340 |
| `inject.py` | ✅ **Fully Implemented** | 362 |
| `flow.py` | ✅ **Fully Implemented** | 17 |
| **TOTAL** | **Phase 1 + Phase 2 Complete** | **4,355** |

**Test Suite:** 339 passing tests across 15 test files
**Specifications:** 16 complete spec files in `specs/` directory
**Dependencies:** Fully specified in `requirements.txt`

**Phase 1 (MVP) and Phase 2 (Seamless Context System) complete.**

---

## Phase 2: Seamless Context System ✅ COMPLETE

> Automatic context injection. When you open Claude Code, it just knows.

**Phase 2 Core Complete:**
- `handoff.py` — ✅ IMPLEMENTED (306 lines)
- `tldr.py` — ✅ IMPLEMENTED (340 lines)
- `inject.py` — ✅ IMPLEMENTED (362 lines)
- `flow inject` command — ✅ IMPLEMENTED
- `flow setup` command — ✅ IMPLEMENTED
- `.flow-guardian/` directory — ✅ Created by `flow setup`
- `.claude/` directory with hooks — ✅ Created by `flow setup`

**Dependencies:**
```
handoff.py ───┐
              ├──► inject.py ──► flow inject ──► hooks ──► flow setup
tldr.py ──────┘
```

---

### P0-1: Handoff System (Foundation — implement first) ✅

- [x] Create `handoff.py` module
  - [x] `find_project_root(cwd)` — find project root via .flow-guardian/, .git/, pyproject.toml
  - [x] `get_handoff_path(project_root)` — path to `.flow-guardian/handoff.yaml`
  - [x] `load_handoff(project_root)` — load YAML, return None if missing
  - [x] `save_handoff(data, project_root)` — save with validation
  - [x] `update_handoff(updates, project_root)` — merge updates
- Spec: `specs/11_HANDOFF_SYSTEM.md`

### P0-2: TLDR System (Foundation — implement second) ✅

- [x] Create `tldr.py` module
  - [x] `summarize_context(content, level, max_tokens)` — Cerebras summarization
  - [x] `summarize_handoff(handoff, level)` — handoff to TLDR string
  - [x] `summarize_recall(results, level)` — recall results to TLDR
  - [x] `estimate_tokens(text)` — rough token count (~4 chars per token)
- [x] Implement levels: L0 (paths), L1 (descriptions), L2 (logic), L3 (full)
- [x] Fallback when Cerebras unavailable (return content as-is or truncated)
- Spec: `specs/12_TLDR_SYSTEM.md`

### P0-3: Inject Module (Depends on handoff.py + tldr.py) ✅

- [x] Create `inject.py` module
  - [x] `generate_injection(level, quiet)` → formatted context string
  - [x] `save_current_state()` → save to handoff.yaml
  - [x] `format_injection(handoff, memory, quiet)` → output string
- [x] Integrate with Backboard semantic recall
- Spec: `specs/13_HOOKS_INTEGRATION.md`

### P0-4: Inject Command (Depends on inject.py) ✅

- [x] Add `flow inject` command to CLI (`flow_cli.py`)
  - [x] `--quiet/-q` — plain output for hooks
  - [x] `--level/-l` — TLDR depth (default: L1)
  - [x] `--save-state` — save state mode for PreCompact
- Spec: `specs/13_HOOKS_INTEGRATION.md`

### P0-5: Integration Updates (After inject command works) ✅

- [x] Update `flow save` to write handoff.yaml after session storage
- [x] Update `daemon.py` to update handoff.yaml on extraction

### P1-1: Claude Code Hooks (Depends on flow inject) ✅

- [x] Create `.claude/hooks/flow-inject.sh` — SessionStart hook (created via `flow setup`)
- [x] Create `.claude/hooks/flow-precompact.sh` — PreCompact hook (created via `flow setup`)
- [x] Define hook configuration for `.claude/settings.json`
- Spec: `specs/13_HOOKS_INTEGRATION.md`

### P1-2: Setup Command (Depends on hooks defined) ✅

- [x] Add `flow setup` command to CLI
  - [x] Create `.flow-guardian/` directory
  - [x] Create `.flow-guardian/handoff.yaml` (initial empty state)
  - [x] Create `.flow-guardian/config.yaml` (local overrides)
  - [x] Create `.claude/hooks/` with hook scripts
  - [x] Update/create `.claude/settings.json` with hook registration
  - [x] `--global/-g` for user-level hooks (`~/.claude/hooks/`)
  - [x] `--check/-c` for status check without modifying
  - [x] `--force/-f` to overwrite existing files
- [x] Verify environment (BACKBOARD_API_KEY, CEREBRAS_API_KEY)
- Spec: `specs/15_SETUP_COMMAND.md`

### P2-1: Semantic Recall Optimization

- [x] Context-aware queries in inject.py (include project name, branch, focus)
- [x] Result categorization (learnings, decisions, context, insights)
- [x] Relevance scoring (recency boost, branch match, file overlap)
- [x] Local fallback via memory.py when Backboard unavailable
- Spec: `specs/14_SEMANTIC_RECALL.md`

### P2-2: Testing & Polish

- [x] `test_handoff.py` — load/save/update/validation (32 tests)
- [x] `test_tldr.py` — summarization levels, token estimation, fallback (35 tests)
- [x] `test_inject.py` — injection generation, formatting, state save (19 tests)
- [x] `test_setup_command.py` — directory creation, hook scripts, settings, global mode, env vars, merging (19 tests)
- [x] End-to-end test: save → close → reopen → context restored (13 tests in test_e2e.py)
- [x] `test_daemon.py` — logging, state, JSON extraction, insight extraction, daemon control (28 tests)
- [x] `test_session_parser.py` — session discovery, message parsing, conversation text (23 tests)

---

## Stack

- **Cerebras** — Fast LLM inference (Llama 3.3 70B)
- **Backboard.io** — Persistent memory with semantic recall
- **Rich** — CLI output
- **Click** — CLI framework
- **Local JSON** — Offline fallback

---

## Priority 1: Core Infrastructure (MUST HAVE — P0) ✅ COMPLETE

### 1.1 Create `cerebras_client.py` — LLM Inference ✅
- [x] Import and configure Cerebras Cloud SDK
- [x] Implement `analyze_session_context(branch, files, diff_summary, user_message)` → returns dict with summary, hypothesis, next_steps, decisions, learnings
- [x] Implement `generate_restoration_message(context, changes)` → returns welcome-back string
- [x] Implement `complete(prompt, system, json_mode, max_tokens)` → generic completion
- [x] Define error classes: `CerebrasError`, `CerebrasAuthError`, `CerebrasRateLimitError`
- [x] Handle rate limiting with graceful fallback
- Spec: `specs/09_CEREBRAS_CLIENT.md`

### 1.2 Create `memory.py` — Local Storage Fallback ✅
- [x] Initialize storage directory `~/.flow-guardian/`
- [x] Implement `init_storage()` — create directories and index files
- [x] Implement `save_session(session)` → returns session_id
- [x] Implement `load_session(session_id)` → returns dict or None
- [x] Implement `get_latest_session()` → returns dict or None
- [x] Implement `list_sessions(limit, branch)` → returns list of session summaries
- [x] Implement `save_learning(learning)` → returns learning_id
- [x] Implement `search_learnings(query, tags)` → returns list (keyword-based fallback)
- [x] Implement `get_config()` / `set_config(key, value)`
- [x] Atomic file writes (write to temp, then rename)
- [x] Handle concurrent access, data validation, auto-create directories
- Spec: `specs/07_MEMORY_MODULE.md`

### 1.3 Implement `backboard_client.py` — Backboard.io API ✅
- [x] Configure httpx async client with connection pooling
- [x] Implement `_headers()` helper for auth
- [x] Implement `create_assistant(name, llm_provider)` → returns assistant_id
- [x] Implement `create_thread(assistant_id)` → returns thread_id
- [x] Implement `health_check()` → returns bool
- [x] Implement `store_message(thread_id, content, metadata)` with `send_to_llm=False`
- [x] Implement `store_session(thread_id, session)` — store context snapshot
- [x] Implement `store_learning(thread_id, text, tags, author)` — store learning
- [x] Implement `recall(thread_id, query)` with `memory="auto"`, `send_to_llm=True`
- [x] Implement `get_restoration_context(thread_id, changes_summary)`
- [x] Implement `store_team_learning(team_thread_id, learning, author, tags)`
- [x] Implement `query_team_memory(team_thread_id, query)`
- [x] Define error classes: `BackboardError`, `BackboardAuthError`, `BackboardConnectionError`, `BackboardRateLimitError`
- [x] Retry logic: max 3 attempts on 5xx, exponential backoff (1s, 2s, 4s), no retry on 4xx
- [x] 30-second timeout
- [x] Never log API keys
- Spec: `specs/08_BACKBOARD_CLIENT.md`
- Reference: `docs/HACKATHON_PLAN.md` lines 154-318

### 1.4 Implement `setup_assistants.py` — One-Time Setup ✅
- [x] Create personal assistant ("flow-guardian-personal")
- [x] Create personal thread
- [x] Create team assistant ("flow-guardian-team")
- [x] Create team thread
- [x] Print output for .env configuration (assistant/thread IDs)
- [x] Handle errors gracefully (API key missing, connection issues)

---

## Priority 2: Core Commands — Save & Resume (MUST HAVE — P0) ✅ COMPLETE

### 2.1 Implement `capture.py` — Context Capture ✅
- [x] `capture_git_state()` → returns branch, uncommitted files, recent commits, last commit message
- [x] `get_diff_summary()` → summarize uncommitted changes
- [x] `analyze_context(git_state, user_message)` → call Cerebras to extract structured context
- [x] Handle non-git repos gracefully
- Spec: `specs/01_SAVE_COMMAND.md`

### 2.2 Implement `restore.py` — Context Restoration ✅
- [x] `get_changes_since(checkpoint_timestamp)` → git commits, file changes since checkpoint
- [x] `calculate_time_elapsed(timestamp)` → human-readable duration
- [x] `generate_restoration_message(session, changes)` → call Cerebras for welcome-back message
- [x] `detect_conflicts(session)` → highlight if current state conflicts with checkpoint
- Spec: `specs/02_RESUME_COMMAND.md`

### 2.3 Implement `flow_cli.py` CLI — Core Commands ✅
- [x] Set up Click CLI framework with `flow` as main command group
- [x] Add Rich console for formatted output
- [x] Load environment variables with python-dotenv
- [x] **`flow save`** command:
  - [x] Flags: `--message/-m`, `--tag/-t` (repeatable), `--quiet/-q`
  - [x] Capture git state via `capture.py`
  - [x] Analyze with Cerebras
  - [x] Store to Backboard.io (primary) with local fallback
  - [x] Display Rich confirmation panel
  - [x] Performance target: <3 seconds
  - Spec: `specs/01_SAVE_COMMAND.md`
- [x] **`flow resume`** command:
  - [x] Flags: `--session/-s`, `--pick/-p` (interactive), `--raw`, `--copy`
  - [x] Load checkpoint (latest by default, or by ID, or via picker)
  - [x] Detect changes since checkpoint
  - [x] Generate welcome-back message via Cerebras
  - [x] Display Rich "Welcome Back" panel
  - [x] Support clipboard copy (--copy)
  - [x] Performance target: <2 seconds
  - Spec: `specs/02_RESUME_COMMAND.md`

---

## Priority 3: Learning Commands (SHOULD HAVE — P1) ✅ COMPLETE

### 3.1 `flow learn` Command ✅
- [x] Accept learning text as argument: `flow learn "insight text"`
- [x] Flags: `--tag/-t` (repeatable), `--team` (share with team)
- [x] Store to Backboard.io personal thread (or team thread if --team)
- [x] Local fallback storage via memory.py
- [x] Display confirmation with learning echoed back, tags, scope (personal/team)
- [x] Performance target: <1 second
- Spec: `specs/03_LEARN_COMMAND.md`

### 3.2 `flow recall` Command ✅
- [x] Accept natural language query: `flow recall "query"`
- [x] Flags: `--tag/-t`, `--since`, `--limit` (default: 10)
- [x] Use Backboard.io semantic search with `memory="auto"`
- [x] Display results ranked by relevance with timestamps, tags, snippets
- [x] Local fallback: keyword search via memory.py
- [x] Performance target: <2 seconds
- Spec: `specs/04_RECALL_COMMAND.md`

### 3.3 `flow team` Command ✅
- [x] Search team-shared learnings: `flow team "query"`
- [x] Flags: `--tag/-t`, `--since`, `--limit`
- [x] Show author attribution for each result
- [x] Use team's Backboard.io assistant
- [x] Display team knowledge panel
- Spec: `specs/05_TEAM_COMMAND.md`

---

## Priority 4: Utility Commands (NICE TO HAVE — P2) ✅ COMPLETE

### 4.1 `flow status` Command ✅
- [x] Show current Flow Guardian state
- [x] Display: last save time, active session, branch, working context
- [x] Memory stats: sessions count, learnings count (personal/team)
- [x] Storage status (Backboard.io connected or local-only)
- Spec: `specs/06_STATUS_HISTORY_COMMANDS.md`

### 4.2 `flow history` Command ✅
- [x] Show past sessions and checkpoints
- [x] Flags: `-n <number>` (limit), `--all`, `--branch <name>`
- [x] Display: timestamp, branch, summary, session ID
- [x] Show how to resume specific sessions
- Spec: `specs/06_STATUS_HISTORY_COMMANDS.md`

---

## Priority 5: Polish & Error Handling (P2) ✅ COMPLETE

- [x] Comprehensive error handling across all modules — Custom exception hierarchies in all API clients
- [x] Graceful degradation when Backboard.io unavailable — Local fallback storage used automatically
- [x] Graceful degradation when Cerebras unavailable — Fallback messages generated in capture.py and restore.py
- [x] Beautiful Rich output panels for all commands — Color-coded panels for save, resume, learn, recall, team, status, history
- [x] Edge case handling: non-git repos, empty repos, API failures — Verified working in non-git directories
- [ ] Demo script preparation — Optional polish item
- [x] **Test infrastructure** — 139 passing tests covering all core modules

---

## Files Structure

```
flow-guardian/
├── flow_cli.py          # ✅ CLI entry (Click + Rich) - 817 lines
├── capture.py           # ✅ Git state extraction + Cerebras analysis - 238 lines
├── restore.py           # ✅ Change detection + restoration - 378 lines
├── memory.py            # ✅ Local storage fallback - 388 lines
├── cerebras_client.py   # ✅ Cerebras LLM client - 213 lines
├── backboard_client.py  # ✅ Backboard.io API client - 404 lines
├── setup_assistants.py  # ✅ One-time Backboard.io setup - 153 lines
├── git_utils.py         # ✅ Shared git utilities - 55 lines
├── daemon.py            # ✅ Background session watcher - 506 lines
├── session_parser.py    # ✅ Claude session file parser - 178 lines
├── handoff.py           # ✅ Handoff state management - 306 lines
├── tldr.py              # ✅ TLDR summarization system - 340 lines
├── inject.py            # ✅ Context injection module - 362 lines
├── flow.py              # ✅ CLI entry point - 17 lines
├── specs/               # Feature PRDs (16 files, complete)
├── docs/                # HACKATHON_PLAN.md with reference code
├── tests/               # ✅ Test suite - 324 passing tests
│   ├── __init__.py
│   ├── test_memory.py
│   ├── test_capture.py
│   ├── test_restore.py
│   ├── test_cerebras_client.py
│   ├── test_backboard_client.py
│   ├── test_flow_cli.py
│   ├── test_setup_assistants.py
│   ├── test_git_utils.py
│   ├── test_handoff.py
│   ├── test_tldr.py
│   ├── test_inject.py
│   └── test_setup_command.py
└── pytest.ini           # ✅ Pytest configuration
```

**Phase 2 will add:**
```
.flow-guardian/          # Per-project state directory
├── handoff.yaml         # Session handoff state
└── config.yaml          # Local configuration overrides

.claude/                 # Claude Code integration
├── hooks/
│   ├── flow-inject.sh   # SessionStart hook
│   └── flow-precompact.sh # PreCompact hook
└── settings.json        # Hook registration
```

---

## Implementation Order (Critical Path)

### Phase 1 ✅ ALL COMPLETE

1. ✅ **`cerebras_client.py`** — Required by capture.py and restore.py
2. ✅ **`memory.py`** — Required for local fallback (always needed)
3. ✅ **`backboard_client.py`** — Required for cloud storage
4. ✅ **`capture.py`** — Depends on cerebras_client
5. ✅ **`restore.py`** — Depends on cerebras_client
6. ✅ **`flow_cli.py` (save + resume)** — Depends on all above
7. ✅ **`setup_assistants.py`** — Depends on backboard_client
8. ✅ **`flow_cli.py` (learn + recall + team)** — Depends on backboard_client
9. ✅ **`flow_cli.py` (status + history)** — Depends on memory.py
10. ✅ **`daemon.py`** — Background session watcher
11. ✅ **`session_parser.py`** — Claude session file parser

### Phase 2 (CURRENT) — Implementation Order

1. ✅ **`handoff.py`** — Foundation module, no dependencies
2. ✅ **`tldr.py`** — Foundation module, depends on cerebras_client
3. ✅ **`inject.py`** — Depends on handoff.py, tldr.py, backboard_client
4. ✅ **`flow inject` command** — Depends on inject.py
5. ✅ **Update `flow save`** — Add handoff.yaml write after session storage
6. ✅ **Update `daemon.py`** — Add handoff.yaml update on extraction
7. ✅ **Hook scripts** — Depends on flow inject working
8. ✅ **`flow setup` command** — Depends on hooks being defined

---

## Hackathon MVP Priority ✅ ALL IMPLEMENTED

**MUST work for demo:**
- ✅ `flow save` — Capture context before interruption
- ✅ `flow resume` — Restore context after returning

**WOW factor for judges:**
- ✅ `flow learn --team` — Store team insight
- ✅ `flow team` — Search team knowledge

**Bonus features (also completed):**
- ✅ `flow status` — View current state and stats
- ✅ `flow history` — Browse past sessions
- ✅ `flow recall` — Search personal learnings

---

## Testing

**Test Suite:** 339 passing tests

| Module | Test File | Coverage |
|--------|-----------|----------|
| `git_utils.py` | `test_git_utils.py` | Git command execution, repo detection, branch retrieval |
| `memory.py` | `test_memory.py` | Storage, sessions, learnings, config |
| `capture.py` | `test_capture.py` | Git state capture, diff summary, context analysis |
| `restore.py` | `test_restore.py` | Change detection, restoration messages, conflicts |
| `cerebras_client.py` | `test_cerebras_client.py` | LLM inference, error handling, rate limiting |
| `backboard_client.py` | `test_backboard_client.py` | API calls, retry logic, error classes, create_assistant, create_thread |
| `flow_cli.py` | `test_flow_cli.py` | All CLI commands (save, resume, learn, recall, team, status, history, setup) |
| `setup_assistants.py` | `test_setup_assistants.py` | Personal and team assistant setup, error handling |
| `handoff.py` | `test_handoff.py` | Load/save/update, validation, project root detection |
| `tldr.py` | `test_tldr.py` | Summarization levels, token estimation, fallback |
| `inject.py` | `test_inject.py` | Injection generation, formatting, state save |
| `flow setup` | `test_flow_cli.py` | Directory creation, hook scripts, settings, global mode, env vars, JSON merge (19 tests) |
| `daemon.py` | `test_daemon.py` | Logging, state management, insight extraction, daemon control |
| `session_parser.py` | `test_session_parser.py` | Session discovery, message parsing, conversation text |
| `e2e` | `test_e2e.py` | Save/restore flow, context persistence, injection levels |
| `semantic recall` | `test_semantic_recall.py` | Query building, scoring, categorization, fallback |

**Run tests:** `pytest` or `pytest -v` for verbose output

---

## Known Issues & Technical Debt

### Minor Code Quality Issues
- ~~`restore.py`: Timezone handling logic repeated multiple times — could be extracted to helper~~ ✅ **FIXED:** Extracted `_parse_timestamp_naive()` helper
- ~~`backboard_client.py`: `store_message()` checks API_KEY twice redundantly~~ ✅ **FIXED:** Check moved to start of function
- `cerebras_client.py`: Error detection uses string parsing ("401" in error_str) — common pattern when SDKs don't expose typed error codes
- Multiple files use `# type: ignore` for loose SDK type hints — acceptable for SDK compatibility

### Test Suite Notes
- Some tests in `test_git_utils.py`, `test_capture.py`, `test_restore.py` run actual git commands (integration-style)
- Time-sensitive tests in `test_restore.py` use `datetime.now()` — could be flaky during DST transitions
