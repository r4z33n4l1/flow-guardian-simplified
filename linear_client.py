"""Linear API client for Flow Guardian.

Fetches bugs, issues, and project data from Linear for PM dashboards
and documentation generation.
"""
import os
import httpx
from typing import Optional
from datetime import datetime, timedelta


LINEAR_API_URL = "https://api.linear.app/graphql"


def get_api_key() -> Optional[str]:
    """Get Linear API key from environment."""
    return os.environ.get("LINEAR_API_KEY")


async def linear_query(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL query against Linear API."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("LINEAR_API_KEY not set in environment")

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    async with httpx.AsyncClient() as client:
        response = await client.post(
            LINEAR_API_URL,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


async def get_all_issues(days: int = 30, limit: int = 50) -> list[dict]:
    """
    Fetch all recent issues from Linear (not just bugs).

    Args:
        days: Number of days to look back
        limit: Maximum number of issues to return

    Returns:
        List of issue dictionaries
    """
    since_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
    query AllIssues($first: Int!, $filter: IssueFilter) {
        issues(first: $first, filter: $filter, orderBy: createdAt) {
            nodes {
                id
                identifier
                title
                description
                state {
                    name
                    type
                }
                priority
                priorityLabel
                assignee {
                    name
                    email
                }
                labels {
                    nodes {
                        name
                    }
                }
                createdAt
                updatedAt
                completedAt
                comments {
                    nodes {
                        body
                        user {
                            name
                        }
                        createdAt
                    }
                }
            }
        }
    }
    """

    variables = {
        "first": limit,
        "filter": {
            "createdAt": {"gte": since_date}
        }
    }

    result = await linear_query(query, variables)
    return result.get("data", {}).get("issues", {}).get("nodes", [])


async def get_recent_bugs(days: int = 30, limit: int = 50) -> list[dict]:
    """
    Fetch recent bugs/issues from Linear.

    Args:
        days: Number of days to look back
        limit: Maximum number of issues to return

    Returns:
        List of bug dictionaries with id, title, description, state, etc.
    """
    since_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
    query RecentIssues($first: Int!, $filter: IssueFilter) {
        issues(first: $first, filter: $filter, orderBy: createdAt) {
            nodes {
                id
                identifier
                title
                description
                state {
                    name
                    type
                }
                priority
                priorityLabel
                assignee {
                    name
                    email
                }
                labels {
                    nodes {
                        name
                    }
                }
                createdAt
                updatedAt
                completedAt
                comments {
                    nodes {
                        body
                        user {
                            name
                        }
                        createdAt
                    }
                }
            }
        }
    }
    """

    variables = {
        "first": limit,
        "filter": {
            "createdAt": {"gte": since_date},
            "labels": {"name": {"containsIgnoreCase": "bug"}}
        }
    }

    result = await linear_query(query, variables)
    return result.get("data", {}).get("issues", {}).get("nodes", [])


async def get_solved_bugs(days: int = 90, limit: int = 100) -> list[dict]:
    """
    Fetch recently solved/completed bugs from Linear.

    Args:
        days: Number of days to look back
        limit: Maximum number of issues to return

    Returns:
        List of solved bug dictionaries
    """
    since_date = (datetime.now() - timedelta(days=days)).isoformat()

    query = """
    query SolvedBugs($first: Int!, $filter: IssueFilter) {
        issues(first: $first, filter: $filter, orderBy: completedAt) {
            nodes {
                id
                identifier
                title
                description
                state {
                    name
                    type
                }
                priority
                priorityLabel
                assignee {
                    name
                }
                labels {
                    nodes {
                        name
                    }
                }
                createdAt
                completedAt
                comments {
                    nodes {
                        body
                        user {
                            name
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "first": limit,
        "filter": {
            "completedAt": {"gte": since_date},
            "state": {"type": {"in": ["completed", "canceled"]}}
        }
    }

    result = await linear_query(query, variables)
    return result.get("data", {}).get("issues", {}).get("nodes", [])


async def get_team_info() -> dict:
    """Get information about the Linear workspace/team."""
    query = """
    query TeamInfo {
        viewer {
            id
            name
            email
        }
        teams {
            nodes {
                id
                name
                key
                issueCount
            }
        }
    }
    """

    result = await linear_query(query)
    return result.get("data", {})


async def test_connection() -> dict:
    """Test the Linear API connection and return viewer info."""
    try:
        info = await get_team_info()
        viewer = info.get("viewer", {})
        teams = info.get("teams", {}).get("nodes", [])
        return {
            "connected": True,
            "user": viewer.get("name"),
            "email": viewer.get("email"),
            "teams": [{"name": t["name"], "key": t["key"], "issues": t["issueCount"]} for t in teams]
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


async def get_default_team_id() -> Optional[str]:
    """Get the default team ID for document creation."""
    try:
        info = await get_team_info()
        teams = info.get("teams", {}).get("nodes", [])
        if teams:
            return teams[0]["id"]
    except Exception:
        pass
    return None


async def get_default_project_id() -> Optional[str]:
    """Get the default project ID for document creation (from env or first project)."""
    # Check for configured project ID
    project_id = os.environ.get("LINEAR_PROJECT_ID")
    if project_id:
        return project_id

    # Fall back to first project
    try:
        query = """
        query Projects {
            projects(first: 1) {
                nodes { id }
            }
        }
        """
        result = await linear_query(query)
        projects = result.get("data", {}).get("projects", {}).get("nodes", [])
        if projects:
            return projects[0]["id"]
    except Exception:
        pass
    return None


async def create_document(title: str, content: str, project_id: str = None) -> Optional[dict]:
    """
    Create a document in Linear, associated with a project.

    Args:
        title: Document title
        content: Markdown content for the document
        project_id: Project ID to associate with (uses default if not provided)

    Returns:
        Created document data or None if failed
    """
    # Get project ID if not provided
    if not project_id:
        project_id = await get_default_project_id()
        if not project_id:
            # Fall back to team ID if no project
            team_id = await get_default_team_id()
            if not team_id:
                print("[Linear] No project or team found for document creation")
                return None
        else:
            team_id = None
    else:
        team_id = None

    query = """
    mutation CreateDocument($input: DocumentCreateInput!) {
        documentCreate(input: $input) {
            success
            document {
                id
                title
                url
                createdAt
            }
        }
    }
    """

    variables = {
        "input": {
            "title": title,
            "content": content,
        }
    }

    # Use projectId if available, otherwise teamId
    if project_id:
        variables["input"]["projectId"] = project_id
    elif team_id:
        variables["input"]["teamId"] = team_id

    try:
        result = await linear_query(query, variables)

        if result.get("errors"):
            print(f"[Linear] GraphQL errors: {result['errors']}")
            return None

        doc_data = result.get("data", {}).get("documentCreate", {})

        if doc_data and doc_data.get("success"):
            return doc_data.get("document")
        else:
            print(f"[Linear] Failed to create document: {title}")
            return None
    except Exception as e:
        print(f"[Linear] Error creating document: {e}")
        return None


async def update_document(document_id: str, content: str) -> bool:
    """
    Update an existing Linear document.

    Args:
        document_id: The document ID to update
        content: New markdown content

    Returns:
        True if successful
    """
    query = """
    mutation UpdateDocument($id: String!, $input: DocumentUpdateInput!) {
        documentUpdate(id: $id, input: $input) {
            success
        }
    }
    """

    variables = {
        "id": document_id,
        "input": {
            "content": content,
        }
    }

    try:
        result = await linear_query(query, variables)
        return result.get("data", {}).get("documentUpdate", {}).get("success", False)
    except Exception as e:
        print(f"[Linear] Error updating document: {e}")
        return False


async def find_document_by_title(title: str, project_id: str = None) -> Optional[dict]:
    """
    Find a document by title, optionally within a specific project.

    Args:
        title: Document title to search for
        project_id: Optional project ID to search within

    Returns:
        Document data or None if not found
    """
    # If project_id provided, search within project
    if project_id:
        query = """
        query ProjectDocs($projectId: String!) {
            project(id: $projectId) {
                documents {
                    nodes {
                        id
                        title
                        url
                        createdAt
                        updatedAt
                    }
                }
            }
        }
        """
        try:
            result = await linear_query(query, {"projectId": project_id})
            docs = result.get("data", {}).get("project", {}).get("documents", {}).get("nodes", [])
            for doc in docs:
                if doc.get("title") == title:
                    return doc
            return None
        except Exception as e:
            print(f"[Linear] Error finding document in project: {e}")
            return None

    # Otherwise search globally
    query = """
    query FindDocument($filter: DocumentFilter) {
        documents(filter: $filter, first: 1) {
            nodes {
                id
                title
                url
                createdAt
                updatedAt
            }
        }
    }
    """

    variables = {
        "filter": {
            "title": {"eq": title}
        }
    }

    try:
        result = await linear_query(query, variables)
        docs = result.get("data", {}).get("documents", {}).get("nodes", [])
        return docs[0] if docs else None
    except Exception as e:
        print(f"[Linear] Error finding document: {e}")
        return None


async def create_or_update_document(title: str, content: str) -> Optional[dict]:
    """
    Create a new document or update existing one with same title.

    Documents are scoped to the configured project (LINEAR_PROJECT_ID).

    Args:
        title: Document title
        content: Markdown content

    Returns:
        Document data or None if failed
    """
    # Get project ID for scoped search
    project_id = await get_default_project_id()

    # Check if document exists in the project
    existing = await find_document_by_title(title, project_id=project_id)

    if existing:
        # Update existing document
        success = await update_document(existing["id"], content)
        if success:
            print(f"[Linear] Updated document: {title}")
            return existing
        return None
    else:
        # Create new document in project
        doc = await create_document(title, content, project_id=project_id)
        if doc:
            print(f"[Linear] Created document: {title} -> {doc.get('url')}")
        return doc


# CLI test
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv

    load_dotenv()

    async def main():
        print("Testing Linear connection...")
        result = await test_connection()
        print(f"Result: {result}")

        if result["connected"]:
            print("\nFetching all recent issues...")
            issues = await get_all_issues(days=90, limit=20)
            print(f"Found {len(issues)} issues")
            for issue in issues[:10]:
                state = issue.get("state", {}).get("name", "?")
                print(f"  - [{state}] {issue['identifier']}: {issue['title']}")

    asyncio.run(main())
