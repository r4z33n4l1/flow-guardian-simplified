"""Report Generator for Flow Guardian.

Creates documentation reports, bug summaries, and FAQs from:
- Linear issues
- Flow Guardian learnings and sessions
- Team knowledge base
"""
import os
import asyncio
from datetime import datetime
from typing import Optional

import linear_client
import memory
import cerebras_client
from dotenv import load_dotenv


async def generate_bug_report(days: int = 30) -> str:
    """
    Generate a documentation report of recent bugs/issues.

    Args:
        days: Number of days to look back

    Returns:
        Markdown formatted bug report
    """
    issues = await linear_client.get_all_issues(days=days, limit=50)

    # Group by state
    by_state = {}
    for issue in issues:
        state = issue.get("state", {}).get("name", "Unknown")
        if state not in by_state:
            by_state[state] = []
        by_state[state].append(issue)

    # Build report
    lines = [
        f"# Bug & Issue Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Period: Last {days} days",
        f"Total Issues: {len(issues)}",
        "",
    ]

    # Summary by state
    lines.append("## Summary by Status")
    lines.append("")
    for state, state_issues in sorted(by_state.items()):
        lines.append(f"- **{state}**: {len(state_issues)} issues")
    lines.append("")

    # Detailed listing
    for state, state_issues in sorted(by_state.items()):
        lines.append(f"## {state}")
        lines.append("")
        for issue in state_issues:
            identifier = issue.get("identifier", "?")
            title = issue.get("title", "No title")
            priority = issue.get("priorityLabel", "No priority")
            assignee = issue.get("assignee", {})
            assignee_name = assignee.get("name", "Unassigned") if assignee else "Unassigned"
            created = issue.get("createdAt", "")[:10]

            lines.append(f"### {identifier}: {title}")
            lines.append(f"- **Priority**: {priority}")
            lines.append(f"- **Assignee**: {assignee_name}")
            lines.append(f"- **Created**: {created}")

            # Labels
            labels = issue.get("labels", {}).get("nodes", [])
            if labels:
                label_names = [l["name"] for l in labels]
                lines.append(f"- **Labels**: {', '.join(label_names)}")

            # Description (truncated)
            desc = issue.get("description", "")
            if desc:
                desc_preview = desc[:200] + "..." if len(desc) > 200 else desc
                lines.append(f"\n{desc_preview}")

            lines.append("")

    return "\n".join(lines)


async def generate_faq_from_solved(days: int = 90) -> str:
    """
    Generate FAQ documentation from solved issues and learnings.

    Args:
        days: Number of days to look back

    Returns:
        Markdown formatted FAQ
    """
    # Get solved issues from Linear
    issues = await linear_client.get_all_issues(days=days, limit=100)
    solved = [i for i in issues if i.get("state", {}).get("type") in ["completed", "canceled"]]

    # Get learnings from Flow Guardian
    learnings = memory.get_all_learnings()

    lines = [
        "# FAQ - Frequently Asked Questions",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Based on {len(solved)} resolved issues and {len(learnings)} learnings",
        "",
    ]

    # Section: From solved issues
    if solved:
        lines.append("## From Resolved Issues")
        lines.append("")
        for issue in solved[:20]:
            title = issue.get("title", "")
            desc = issue.get("description", "")
            comments = issue.get("comments", {}).get("nodes", [])

            if title:
                lines.append(f"### Q: {title}")
                if desc:
                    lines.append(f"\n**Context**: {desc[:300]}...")
                if comments:
                    # Get resolution comment (last one usually)
                    last_comment = comments[-1]
                    lines.append(f"\n**Resolution**: {last_comment.get('body', '')[:300]}")
                lines.append("")

    # Section: From learnings
    if learnings:
        lines.append("## From Team Learnings")
        lines.append("")
        for learning in learnings[:20]:
            insight = learning.get("insight") or learning.get("text", "")
            tags = learning.get("tags", [])
            source = learning.get("source", "unknown")

            if insight:
                # Format as Q&A
                lines.append(f"### Insight: {insight[:100]}...")
                lines.append(f"\n{insight}")
                if tags:
                    lines.append(f"\n**Tags**: {', '.join(tags)}")
                lines.append("")

    return "\n".join(lines)


async def generate_weekly_summary() -> str:
    """
    Generate a weekly summary combining Linear issues and Flow Guardian sessions.

    Returns:
        Markdown formatted weekly summary
    """
    # Get data
    issues = await linear_client.get_all_issues(days=7, limit=50)
    sessions = memory.list_sessions(limit=20)
    learnings = memory.get_all_learnings()[:20]

    lines = [
        "# Weekly Summary Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Period: Last 7 days",
        "",
        "## Overview",
        f"- **Linear Issues**: {len(issues)}",
        f"- **Coding Sessions**: {len(sessions)}",
        f"- **New Learnings**: {len(learnings)}",
        "",
    ]

    # Issues summary
    if issues:
        lines.append("## Linear Issues")
        lines.append("")
        by_state = {}
        for issue in issues:
            state = issue.get("state", {}).get("name", "Unknown")
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(issue)

        for state, state_issues in sorted(by_state.items()):
            lines.append(f"### {state} ({len(state_issues)})")
            for issue in state_issues[:5]:
                lines.append(f"- {issue['identifier']}: {issue['title']}")
            lines.append("")

    # Sessions summary
    if sessions:
        lines.append("## Recent Sessions")
        lines.append("")
        for session in sessions[:10]:
            summary = session.get("summary", "No summary")
            timestamp = session.get("timestamp", "")[:10]
            branch = session.get("branch", "unknown")
            lines.append(f"- **{timestamp}** ({branch}): {summary[:80]}...")
        lines.append("")

    # Key learnings
    if learnings:
        lines.append("## Key Learnings")
        lines.append("")
        for learning in learnings[:10]:
            insight = learning.get("insight") or learning.get("text", "")
            if insight:
                lines.append(f"- {insight[:100]}...")
        lines.append("")

    return "\n".join(lines)


async def save_report(content: str, filename: str) -> str:
    """Save report to file."""
    reports_dir = os.path.expanduser("~/.flow-guardian/reports")
    os.makedirs(reports_dir, exist_ok=True)

    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)

    return filepath


async def auto_generate_reports(interval_hours: int = 24):
    """
    Background service that auto-generates reports periodically.

    This runs as a long-lived service, generating reports based on:
    - Time intervals (daily/weekly)
    - Activity thresholds (X new sessions triggers report)
    - Pattern detection (bugs found/fixed)
    """
    print(f"[AutoReport] Starting auto-report service (interval: {interval_hours}h)")
    reports_dir = os.path.expanduser("~/.flow-guardian/reports")
    state_file = os.path.join(reports_dir, ".auto_report_state.json")

    # Load state
    state = {"last_report": None, "session_count": 0, "learning_count": 0}
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)

    while True:
        try:
            # Check current counts
            sessions = memory.list_sessions(limit=100)
            learnings = memory.get_all_learnings()

            current_sessions = len(sessions)
            current_learnings = len(learnings)

            # Determine if we should generate a report
            should_generate = False
            reason = ""

            # Time-based: every interval_hours
            if state["last_report"]:
                last = datetime.fromisoformat(state["last_report"])
                hours_since = (datetime.now() - last).total_seconds() / 3600
                if hours_since >= interval_hours:
                    should_generate = True
                    reason = f"Scheduled ({interval_hours}h interval)"
            else:
                should_generate = True
                reason = "Initial report"

            # Activity-based: 10+ new sessions or learnings
            new_sessions = current_sessions - state.get("session_count", 0)
            new_learnings = current_learnings - state.get("learning_count", 0)
            if new_sessions >= 10 or new_learnings >= 20:
                should_generate = True
                reason = f"Activity threshold ({new_sessions} sessions, {new_learnings} learnings)"

            if should_generate:
                print(f"[AutoReport] Generating reports... Reason: {reason}")

                # Generate all report types
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                try:
                    weekly = await generate_weekly_summary()
                    await save_report(weekly, f"auto_weekly_{timestamp}.md")
                    print(f"[AutoReport] Generated weekly summary")
                except Exception as e:
                    print(f"[AutoReport] Weekly summary failed: {e}")

                try:
                    bugs = await generate_bug_report(days=30)
                    await save_report(bugs, f"auto_bugs_{timestamp}.md")
                    print(f"[AutoReport] Generated bug report")
                except Exception as e:
                    print(f"[AutoReport] Bug report failed: {e}")

                # Update state
                state = {
                    "last_report": datetime.now().isoformat(),
                    "session_count": current_sessions,
                    "learning_count": current_learnings,
                }
                os.makedirs(reports_dir, exist_ok=True)
                with open(state_file, "w") as f:
                    json.dump(state, f)

                print(f"[AutoReport] Reports saved to {reports_dir}")

            # Sleep before next check (check every hour)
            await asyncio.sleep(3600)

        except Exception as e:
            print(f"[AutoReport] Error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes


import json

# CLI interface
if __name__ == "__main__":
    import argparse

    load_dotenv()

    parser = argparse.ArgumentParser(description="Generate documentation reports")
    parser.add_argument("--type", "-t", choices=["bugs", "faq", "weekly", "auto"], default="weekly",
                        help="Type of report to generate (auto runs background service)")
    parser.add_argument("--days", "-d", type=int, default=30,
                        help="Number of days to look back")
    parser.add_argument("--save", "-s", action="store_true",
                        help="Save report to file")
    parser.add_argument("--interval", "-i", type=int, default=24,
                        help="Hours between auto-reports (for auto mode)")
    args = parser.parse_args()

    async def main():
        if args.type == "auto":
            # Run auto-report service
            await auto_generate_reports(interval_hours=args.interval)
        elif args.type == "bugs":
            report = await generate_bug_report(days=args.days)
        elif args.type == "faq":
            report = await generate_faq_from_solved(days=args.days)
        else:
            report = await generate_weekly_summary()

        if args.type != "auto":
            print(report)

            if args.save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{args.type}_report_{timestamp}.md"
                filepath = await save_report(report, filename)
                print(f"\n---\nSaved to: {filepath}")

    asyncio.run(main())
