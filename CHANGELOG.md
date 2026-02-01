# Changelog

All notable changes to Flow Guardian will be documented in this file.

## [2.0.0] - 2026-02-01 - Open Source Simplification

### 🎯 Goal
Simplified Flow Guardian for open source release by removing web UI, cloud dependencies, and complex integrations. Focus on core local-first memory functionality.

### ❌ Removed (BREAKING CHANGES)

**Web UI:**
- Removed entire `flow-web/` directory (55 TypeScript files)
- No more Next.js frontend, Tailwind UI, or chat interface
- Use REST API or CLI instead

**Cloud Integrations:**
- Removed Backboard.io cloud storage (`backboard_client.py`)
- Removed Linear integration (`linear_client.py`, `linear_agent.py`)
- Removed auto-documentation generator (`report_generator.py`)
- Removed helper modules (`setup_assistants.py`)

**API Endpoints:**
- `/graph` - Knowledge graph visualization
- `/suggestions` - AI-powered suggestions
- `/analyze-for-linear` - Conversation analysis for issue creation
- `/documents` - PDF/document upload

**MCP Tools:**
- `linear_status` - Linear connection status
- `linear_issues` - List Linear issues
- `linear_create_issue` - Create Linear issues

**Background Tasks:**
- Auto-creation of Linear issues from blockers
- Auto-creation of Linear issues from learnings
- Auto-generation of FAQ documents
- Auto-generation of weekly summaries

**Dependencies:**
- `backboard-sdk>=1.0.0` - Cloud storage removed

### ✅ Changed

**Architecture:**
- Now 100% local-first (SQLite + sqlite-vec)
- Simplified from 2,080 to 1,278 lines in `server.py` (38.6% reduction)
- Team features now work via self-hosted server (`FLOW_GUARDIAN_TEAM_URL`)

**Configuration:**
- Reduced from 10 to 4 required environment variables
- Removed: `BACKBOARD_API_KEY`, `BACKBOARD_PERSONAL_THREAD_ID`, `BACKBOARD_TEAM_THREAD_ID`, `LINEAR_API_KEY`, `LINEAR_PROJECT_ID`, `USE_LOCAL_MEMORY`
- Kept: `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `FLOW_GUARDIAN_USER`, `FLOW_GUARDIAN_URL`
- Added: `FLOW_GUARDIAN_TEAM_URL` for team server

**CLI (`flow_cli.py`):**
- Updated `save`, `learn`, `recall` commands to be local-only
- Updated `team` command to use HTTP requests to team server
- Updated `status` command to show team URL instead of Backboard config
- Removed all `backboard_client` imports and dependencies

### ✅ Kept (100% Functional)

**Core Features:**
- ✅ Daemon auto-capture (watches Claude Code sessions)
- ✅ Local memory (SQLite + sqlite-vec for semantic search)
- ✅ MCP tools (`flow_recall`, `flow_learn`, `flow_capture`, `flow_team`, `flow_status`)
- ✅ REST API (`/capture`, `/recall`, `/learn`, `/team`, `/sessions`, `/learnings`, `/stats`)
- ✅ CLI (`flow save`, `flow learn`, `flow recall`, etc.)
- ✅ Cerebras integration (LLM for extraction and synthesis)
- ✅ Gemini embeddings (semantic vector search)
- ✅ Team features (via self-hosted server architecture)

### 📊 Metrics

- **Lines of code removed:** 21,834 lines
- **Files deleted:** 76 files
- **Dependencies removed:** 1 (backboard-sdk)
- **server.py reduction:** 38.6% (2,080 → 1,278 lines)
- **Configuration simplification:** 60% (10 → 4 env vars)

### 📚 Documentation

**New Files:**
- `SETUP.md` - Complete setup guide with virtual env instructions
- `TEAM_SETUP.md` - Team configuration guide (3 deployment patterns)
- `CHANGELOG.md` - This file
- `setup.sh` - Automated setup script

**Updated Files:**
- `README.md` - Rewritten for local-first architecture
- `flow_cli.py` - Updated all commands for local-only operation
- `requirements.txt` - Removed backboard-sdk dependency

### 🔄 Migration from v1.0

**If you were using v1.0 with Backboard/Linear:**

1. **Data Export** (before upgrading):
   ```bash
   curl http://localhost:8090/sessions > sessions_backup.json
   curl http://localhost:8090/learnings > learnings_backup.json
   ```

2. **Environment Variables:**
   - Remove: `BACKBOARD_API_KEY`, `BACKBOARD_PERSONAL_THREAD_ID`, `BACKBOARD_TEAM_THREAD_ID`
   - Remove: `LINEAR_API_KEY`, `LINEAR_PROJECT_ID`
   - Keep: `CEREBRAS_API_KEY`, `GEMINI_API_KEY`

3. **Team Features:**
   - Old: Backboard team thread
   - New: Self-hosted server (`FLOW_GUARDIAN_TEAM_URL=http://team-server:8090`)

4. **Web UI:**
   - No replacement - use REST API or build custom UI
   - API docs: http://localhost:8090/docs

See [MIGRATION.md](MIGRATION.md) for complete migration guide.

---

## [1.0.0] - 2025-12-15 - Full-Featured Release

### Added

**Web UI:**
- Next.js + Tailwind + shadcn/ui frontend
- Real-time chat interface with Cerebras streaming
- Activity feed with SSE updates
- Document upload (PDF, TXT, MD)
- Knowledge graph visualization
- AI-powered suggestions panel

**Linear Integration:**
- Auto-create issues from blockers
- Auto-create issues from bugs in learnings
- Analyze conversations for actionable items
- Search Linear documents from `/recall`

**Backboard Cloud Storage:**
- Cloud sync via Backboard.io
- Team threads for knowledge sharing
- Semantic search via cloud API

**Auto-Documentation:**
- FAQ generation from learnings
- Weekly summary reports
- Automatic storage to Linear Docs

**Core Features:**
- Daemon auto-capture
- MCP tools for Claude Code
- REST API
- CLI commands
- Local JSON + SQLite storage
- Cerebras LLM integration

### Tech Stack

- **Backend:** Python + FastAPI
- **Frontend:** Next.js 15 + TypeScript
- **Storage:** Local JSON + Backboard.io
- **LLM:** Cerebras Llama 3.3 70B
- **Embeddings:** Gemini text-embedding-004
- **Vector DB:** SQLite + sqlite-vec (local) + Backboard (cloud)

---

## Version History

- **v2.0.0** (2026-02-01) - Open source simplification (current)
- **v1.0.0** (2025-12-15) - Full-featured release with web UI
