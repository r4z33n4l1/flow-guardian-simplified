# Semantic Recall Specification

## Overview

Query patterns for Backboard.io semantic search to retrieve relevant context.

---

## Query Strategy

### Session Start Query

```python
query = f"""What do I need to know about {project_name}?
Include:
- Recent work and progress
- Key decisions made
- Important learnings
- Current blockers or hypotheses"""
```

### Focused Queries

```python
# For specific task context
query = f"What have I learned about {topic}?"

# For decision history
query = f"What decisions were made about {component}?"

# For debugging context
query = f"Previous issues with {error_type}?"
```

---

## Backboard Integration

### Recall with Memory

```python
async def recall_for_injection(
    thread_id: str,
    project_name: str,
    handoff: dict = None
) -> list[dict]:
    """
    Query Backboard for context relevant to current session.

    Uses memory="auto" for semantic search.
    Includes project name and current focus in query.
    """
    # Build contextual query
    query_parts = [f"Context for project: {project_name}"]

    if handoff:
        if handoff.get("goal"):
            query_parts.append(f"Goal: {handoff['goal']}")
        if handoff.get("now"):
            query_parts.append(f"Current focus: {handoff['now']}")

    query = ". ".join(query_parts)

    # Call Backboard with semantic search
    result = await backboard_client.recall(thread_id, query)
    return result
```

### Message Storage for Recall

```python
# When storing, include rich metadata for better recall
metadata = {
    "type": "learning",  # learning, decision, context, insight
    "project": project_name,
    "branch": git_branch,
    "files": affected_files,
    "tags": user_tags,
    "timestamp": datetime.now().isoformat(),
}

await backboard_client.store_message(
    thread_id,
    content=f"**{category}**: {text}",
    metadata=metadata
)
```

---

## Query Optimization

### Token Efficiency

1. **Query once, summarize locally**
   - Single Backboard query per injection
   - TLDR the results via Cerebras

2. **Limit results**
   - Default: 5-10 most relevant items
   - More available on-demand

3. **Category filtering**
   - Prioritize recent learnings
   - Include decisions for current branch
   - Add context for active files

### Query Examples

```python
# Generic project context
"What should I know about flow-guardian? Recent work, decisions, learnings."

# Branch-specific
"Context for branch feature/auth. Decisions, blockers, progress."

# File-focused
"What do I know about auth.py? Previous issues, decisions, patterns."

# Error debugging
"Previous solutions for token validation errors?"
```

---

## Response Processing

### Categorize Results

```python
def categorize_recall(results: list[dict]) -> dict:
    """
    Group recall results by type.

    Returns:
        {
            "learnings": [...],
            "decisions": [...],
            "context": [...],
            "insights": [...]
        }
    """
    categories = {
        "learnings": [],
        "decisions": [],
        "context": [],
        "insights": [],
    }

    for item in results:
        metadata = item.get("metadata", {})
        item_type = metadata.get("type", "context")
        if item_type in categories:
            categories[item_type].append(item)
        else:
            categories["context"].append(item)

    return categories
```

### Relevance Scoring

Backboard handles relevance via semantic search. Additional local filtering:

1. **Recency boost**: Items from last 24h get priority
2. **Branch match**: Same branch = higher relevance
3. **File overlap**: Matching files = higher relevance

---

## Fallback Behavior

### No Backboard Connection

```python
# Fall back to local memory.py
from memory import search_learnings

results = search_learnings(
    query=project_name,
    limit=10
)
```

### Empty Results

```python
# If no results, return minimal context
return {
    "learnings": [],
    "decisions": [],
    "context": [{
        "content": f"New project: {project_name}. No previous context found.",
        "metadata": {"type": "context"}
    }]
}
```

---

## Testing

```python
def test_recall_builds_contextual_query():
    """Query includes project name and handoff focus."""

def test_recall_categorizes_results():
    """Results are grouped by type."""

def test_recall_fallback_to_local():
    """Falls back to memory.py on connection error."""

def test_recall_empty_results():
    """Handles empty results gracefully."""

def test_recall_respects_limit():
    """Limits results to specified count."""
```
