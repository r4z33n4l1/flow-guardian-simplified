# Flow Guardian Context Management

This project has Flow Guardian MCP integration enabled. Use it to maintain persistent memory across sessions.

## Automatic Context Management

**You have access to these MCP tools - use them proactively:**

### `flow_capture` - Save Context
Use this BEFORE any context compaction or when:
- User says "I need to go", "let's stop", "save progress"
- Session is getting long (proactively save before /compact)
- Switching to a different task
- Making important decisions worth remembering

```
flow_capture(
  summary="Brief description of current work",
  decisions=["Key decision 1", "Key decision 2"],
  next_steps=["What to do next"],
  blockers=["Any blockers"]  # optional
)
```

### `flow_recall` - Retrieve Context
Use this when:
- User says "continue from yesterday", "what were we working on"
- Starting a new session
- User references previous work without full context
- You need context about past decisions

```
flow_recall(query="what to search for")
```

### `flow_learn` - Store Insights
Use this when:
- Discovering important patterns, bugs, or solutions
- User says "remember this", "note this down"
- Finding something that would help future sessions

```
flow_learn(
  insight="The learning to store",
  tags=["relevant", "tags"],
  share_with_team=false  # true to share with team
)
```

### `flow_status` - Check State
Use this to see what's currently stored and last save time.

### `flow_team` - Search Team Knowledge
Use this when user asks "has anyone dealt with..." or needs team conventions.

## Best Practices

1. **Before /compact**: Always `flow_capture` current context first
2. **Session start**: Use `flow_recall` with "recent work" query
3. **Key discoveries**: Use `flow_learn` to persist insights
4. **Be proactive**: Don't wait for user to ask - manage context automatically

## Running the Servers

```bash
# HTTP API (port 8090)
/opt/homebrew/bin/python3.10 -m uvicorn api.server:app --reload --port 8090

# API docs: http://localhost:8090/docs
```

## Project Structure

- `services/` - Shared business logic (FlowService)
- `api/` - FastAPI HTTP server
- `mcp_server.py` - MCP server for Claude Code
- `tests/` - 43 tests covering all functionality
