"""Linear Agent - Agentic Linear integration for Flow Guardian.

Monitors Claude Code sessions, learnings, and blockers.
Uses Cerebras to analyze content and automatically creates
Linear issues when appropriate.
"""
import os
import asyncio
import json
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

import linear_client
import cerebras_client
import memory

load_dotenv()


# Issue detection prompt for Cerebras
ISSUE_DETECTION_PROMPT = """Analyze the following content from a coding session and determine if any Linear issues should be created.

Content:
{content}

For each potential issue, provide:
1. title: A clear, concise title
2. description: Detailed description of the issue
3. type: One of "bug", "task", "blocker", "feature"
4. priority: 1 (urgent), 2 (high), 3 (medium), 4 (low)

Return a JSON array of issues to create. If no issues should be created, return an empty array [].
Only create issues for actionable items - bugs to fix, blockers to resolve, features to implement.
Do NOT create issues for completed work or general observations.

Example response:
[
  {{"title": "Fix authentication timeout", "description": "Users are getting logged out after 5 minutes instead of 30", "type": "bug", "priority": 2}},
  {{"title": "Add dark mode support", "description": "Implement dark mode toggle in settings", "type": "feature", "priority": 3}}
]

Respond with ONLY the JSON array, no other text."""


async def analyze_for_issues(content: str) -> list[dict]:
    """
    Use Cerebras to analyze content and identify potential Linear issues.

    Args:
        content: Text content to analyze (session summary, blockers, etc.)

    Returns:
        List of issue dictionaries with title, description, type, priority
    """
    prompt = ISSUE_DETECTION_PROMPT.format(content=content)

    try:
        response = await cerebras_client.quick_answer(prompt)

        # Parse JSON response
        # Find JSON array in response
        start = response.find('[')
        end = response.rfind(']') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            issues = json.loads(json_str)
            return issues if isinstance(issues, list) else []
        return []
    except Exception as e:
        print(f"[LinearAgent] Error analyzing content: {e}")
        return []


async def create_linear_issue(
    title: str,
    description: str,
    issue_type: str = "task",
    priority: int = 3,
    labels: list[str] = None
) -> Optional[dict]:
    """
    Create an issue in Linear.

    Args:
        title: Issue title
        description: Issue description
        issue_type: bug, task, blocker, or feature
        priority: 1-4 (1 = urgent)
        labels: Optional list of label names

    Returns:
        Created issue data or None if failed
    """
    # Get team ID first
    team_info = await linear_client.get_team_info()
    teams = team_info.get("teams", {}).get("nodes", [])
    if not teams:
        print("[LinearAgent] No teams found in Linear")
        return None

    team_id = teams[0]["id"]

    # Create issue mutation
    query = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                title
                url
            }
        }
    }
    """

    # Map priority (Linear uses 0-4, we use 1-4)
    linear_priority = min(max(priority, 1), 4)

    variables = {
        "input": {
            "teamId": team_id,
            "title": title,
            "description": f"{description}\n\n---\n_Auto-created by Flow Guardian_",
            "priority": linear_priority,
        }
    }

    try:
        result = await linear_client.linear_query(query, variables)
        issue_data = result.get("data", {}).get("issueCreate", {})

        if issue_data.get("success"):
            issue = issue_data.get("issue", {})
            print(f"[LinearAgent] Created issue: {issue.get('identifier')} - {title}")
            return issue
        else:
            print(f"[LinearAgent] Failed to create issue: {title}")
            return None
    except Exception as e:
        print(f"[LinearAgent] Error creating issue: {e}")
        return None


async def process_session(session: dict) -> list[dict]:
    """
    Process a session and create Linear issues for blockers/tasks.

    Args:
        session: Session dictionary from Flow Guardian

    Returns:
        List of created issues
    """
    created_issues = []

    # Build content to analyze
    content_parts = []

    summary = session.get("summary") or session.get("context", {}).get("summary", "")
    if summary:
        content_parts.append(f"Session Summary: {summary}")

    # Blockers are high priority for issue creation
    blockers = session.get("context", {}).get("blockers") or session.get("metadata", {}).get("blockers", [])
    if blockers:
        content_parts.append(f"Blockers: {', '.join(blockers)}")

    # Next steps might become tasks
    next_steps = session.get("context", {}).get("next_steps", [])
    if next_steps:
        content_parts.append(f"Next Steps: {', '.join(next_steps)}")

    if not content_parts:
        return []

    content = "\n".join(content_parts)

    # Analyze with Cerebras
    issues_to_create = await analyze_for_issues(content)

    # Create issues in Linear
    for issue in issues_to_create:
        created = await create_linear_issue(
            title=issue.get("title", "Untitled"),
            description=issue.get("description", ""),
            issue_type=issue.get("type", "task"),
            priority=issue.get("priority", 3)
        )
        if created:
            created_issues.append(created)

    return created_issues


async def process_learning(learning: dict) -> Optional[dict]:
    """
    Process a learning and create a Linear issue if it's a bug or actionable item.

    Args:
        learning: Learning dictionary from Flow Guardian

    Returns:
        Created issue or None
    """
    content = learning.get("insight") or learning.get("text", "")
    tags = learning.get("tags", [])

    # Quick check - only process if it looks like a bug or issue
    bug_indicators = ["bug", "error", "fix", "broken", "issue", "problem", "fail"]
    is_potential_issue = any(ind in content.lower() for ind in bug_indicators) or \
                         any(ind in tag.lower() for tag in tags for ind in bug_indicators)

    if not is_potential_issue:
        return None

    # Analyze with Cerebras
    issues = await analyze_for_issues(f"Learning: {content}\nTags: {', '.join(tags)}")

    if issues:
        issue = issues[0]  # Take first suggested issue
        return await create_linear_issue(
            title=issue.get("title", "Untitled"),
            description=issue.get("description", ""),
            issue_type=issue.get("type", "bug"),
            priority=issue.get("priority", 2)
        )

    return None


async def run_agent(check_interval: int = 60):
    """
    Run the Linear agent continuously.

    Monitors new sessions and learnings, creates Linear issues as needed.

    Args:
        check_interval: Seconds between checks
    """
    print("[LinearAgent] Starting Linear agent...")

    # Track what we've processed
    processed_sessions = set()
    processed_learnings = set()

    # Load initial state
    sessions = memory.list_sessions(limit=100)
    for s in sessions:
        processed_sessions.add(s.get("id"))

    learnings = memory.get_all_learnings()
    for l in learnings:
        processed_learnings.add(l.get("id"))

    print(f"[LinearAgent] Initialized with {len(processed_sessions)} sessions, {len(processed_learnings)} learnings")

    while True:
        try:
            # Check for new sessions
            current_sessions = memory.list_sessions(limit=20)
            for session in current_sessions:
                session_id = session.get("id")
                if session_id and session_id not in processed_sessions:
                    print(f"[LinearAgent] Processing new session: {session_id}")

                    # Load full session
                    full_session = memory.get_session(session_id) if hasattr(memory, 'get_session') else session

                    issues = await process_session(full_session)
                    if issues:
                        print(f"[LinearAgent] Created {len(issues)} issues from session")

                    processed_sessions.add(session_id)

            # Check for new learnings
            current_learnings = memory.get_all_learnings()
            for learning in current_learnings[:20]:  # Check recent ones
                learning_id = learning.get("id")
                if learning_id and learning_id not in processed_learnings:
                    print(f"[LinearAgent] Processing new learning: {learning_id[:20]}...")

                    issue = await process_learning(learning)
                    if issue:
                        print(f"[LinearAgent] Created issue from learning")

                    processed_learnings.add(learning_id)

            await asyncio.sleep(check_interval)

        except Exception as e:
            print(f"[LinearAgent] Error in agent loop: {e}")
            await asyncio.sleep(check_interval)


async def process_now():
    """
    Process all unprocessed sessions and learnings immediately.
    Useful for manual triggering.
    """
    print("[LinearAgent] Processing all sessions and learnings...")

    sessions = memory.list_sessions(limit=10)
    all_issues = []

    for session in sessions:
        print(f"[LinearAgent] Analyzing session: {session.get('summary', '')[:50]}...")
        issues = await process_session(session)
        all_issues.extend(issues)

    print(f"[LinearAgent] Created {len(all_issues)} total issues")
    return all_issues


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Linear Agent - Auto-create issues from Flow Guardian")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", "-i", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--process", "-p", action="store_true", help="Process all sessions now")
    parser.add_argument("--test", "-t", action="store_true", help="Test issue creation")
    args = parser.parse_args()

    async def main():
        if args.test:
            # Test creating a single issue
            issue = await create_linear_issue(
                title="Test Issue from Flow Guardian",
                description="This is a test issue created by the Linear Agent.",
                issue_type="task",
                priority=4
            )
            print(f"Test result: {issue}")
        elif args.process:
            await process_now()
        elif args.daemon:
            await run_agent(check_interval=args.interval)
        else:
            # Default: process once
            await process_now()

    asyncio.run(main())
