# Session Summary: Flow Guardian Server Implementation

**Date:** January 16, 2026
**Branch:** backboardtest
**Goal:** Set up full server with HTTP API and MCP service for Claude Code integration

---

## What We Built

### 1. Services Layer (`services/`)
Shared business logic extracted from CLI for reuse by both API and MCP server.

| File | Purpose |
|------|---------|
| `services/__init__.py` | Package exports |
| `services/config.py` | `FlowConfig` - centralized environment config |
| `services/models.py` | Pydantic request/response models |
| `services/flow_service.py` | `FlowService` - core business logic |

### 2. HTTP API (`api/`)
FastAPI REST server running on port 8090.

| File | Purpose |
|------|---------|
| `api/server.py` | FastAPI app with CORS, lifespan |
| `api/dependencies.py` | Dependency injection |
| `api/routes/capture.py` | POST /capture |
| `api/routes/recall.py` | POST /recall |
| `api/routes/learn.py` | POST /learn |
| `api/routes/team.py` | POST /team |
| `api/routes/status.py` | GET /status |

### 3. MCP Server (`mcp_server.py`)
Model Context Protocol server for Claude Code integration via stdio.

**5 Tools:**
- `flow_recall` - Retrieve past context
- `flow_capture` - Save current context
- `flow_learn` - Store insights
- `flow_team` - Search team knowledge
- `flow_status` - Check system state

### 4. Tests (`tests/`)
43 tests covering all new functionality.

| Directory | Tests |
|-----------|-------|
| `tests/test_services/` | FlowService unit tests |
| `tests/test_api/` | API endpoint tests |
| `tests/test_mcp/` | MCP tool tests |
| `tests/conftest.py` | Shared fixtures and mocks |

### 5. Documentation
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Instructions for Claude to use Flow Guardian |
| `ARCHITECTURE.md` | Full system architecture diagrams |

### 6. Configuration
| File | Changes |
|------|---------|
| `.mcp.json` | MCP server config for Claude Code |
| `.env` | Added Backboard credentials and thread IDs |
| `requirements.txt` | Added FastAPI, uvicorn, pydantic, mcp |

---

## Bug Fixes

### Backboard API Integration
- **Header fix:** Changed from `Authorization: Bearer` to `X-API-Key`
- **Response parsing:** Fixed to use `assistant_id` and `thread_id` (not `id`)
- **Thread creation:** Added required empty JSON body `{}`

---

## Files Created/Modified

### New Files (12)
```
api/__init__.py
api/server.py
api/dependencies.py
api/routes/__init__.py
api/routes/capture.py
api/routes/recall.py
api/routes/learn.py
api/routes/team.py
api/routes/status.py
services/__init__.py
services/config.py
services/models.py
services/flow_service.py
mcp_server.py
tests/conftest.py
tests/test_api/__init__.py
tests/test_api/test_capture.py
tests/test_api/test_recall.py
tests/test_api/test_learn.py
tests/test_api/test_team.py
tests/test_api/test_status.py
tests/test_mcp/__init__.py
tests/test_mcp/test_mcp_tools.py
tests/test_services/__init__.py
tests/test_services/test_flow_service.py
.mcp.json
CLAUDE.md
ARCHITECTURE.md
```

### Modified Files (2)
```
backboard_client.py  - Fixed API header and response parsing
requirements.txt     - Added FastAPI, uvicorn, pydantic, mcp, pytest-cov
```

---

## How to Use

### Run HTTP API
```bash
/opt/homebrew/bin/python3.10 -m uvicorn api.server:app --reload --port 8090
# Docs at http://localhost:8090/docs
```

### Run Tests
```bash
/opt/homebrew/bin/python3.10 -m pytest tests/ -v
# 43 tests, all passing
```

### Enable MCP in Claude Code
1. `.mcp.json` is already configured
2. Restart Claude Code
3. Approve the flow-guardian MCP server when prompted

---

## Next Steps
- [ ] Merge into main branch
- [ ] Test full Backboard integration after Claude restart
- [ ] Add team memory configuration
- [ ] Consider authentication for production
